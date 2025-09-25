from typing import TypedDict, List, Annotated, Optional, Dict, Any
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI
import operator

import os
import sys
from pathlib import Path

# Add project root to sys.path for module discovery
current_file_path = Path(__file__).resolve()
project_root_path = current_file_path.parent.parent.parent # Adjusted for src/core
sys.path.append(str(project_root_path))

from src.config import Config
from src.core.prompts import create_agent_prompt
from src.logging_config import logger

from src.tools.file_operations import file_tools, read_many_files, search_file_content
from src.tools.internet_search import internet_search
from src.tools.command_execution import run_shell_command
from src.tools.think_tool import think_tool
from src.tools.work_tool import work_tool
from src.tools.web_fetch import web_fetch

# Define the tools
all_tools = file_tools + [internet_search, run_shell_command, read_many_files, search_file_content, think_tool, work_tool, web_fetch]
tools = {t.name: t for t in all_tools}

# Initialize LLM and bind tools
llm = ChatGoogleGenerativeAI(model=Config.MODEL_NAME, temperature=0)
llm_with_tools = llm.bind_tools(all_tools)

# Define the state for our graph
class AgentState(TypedDict):
    input: str
    chat_history: Annotated[list[BaseMessage], operator.add]
    always_allowed_tools: Annotated[set[str], operator.or_]

    # Fields for work_tool
    overall_policy: Optional[str]
    worker_role: Optional[str]
    work_rules: Optional[str]
    work_plan: Optional[str]
    work_content: Optional[str]
    work_purpose: Optional[str]
    work_results: Optional[str]
    current_issues: Optional[str]
    issue_countermeasures: Optional[str]
    next_steps: Optional[str]
    memos: Optional[str]
    todo_list: Optional[List[Dict[str, Any]]]

# Agent node function
def run_agent(state: AgentState):
    if Config.DEBUG_MODE:
        logger.debug(f"--- 1. Entering run_agent ---")
        logger.debug(f"Current State: {state}")

    # Dynamically create the prompt and chain for this turn
    system_prompt_str = create_agent_prompt(state)
    if Config.DEBUG_MODE:
        logger.debug(f"Generated System Prompt:\n{system_prompt_str}")
        
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt_str),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
        ]
    )
    chain = prompt | llm_with_tools

    # Invoke the chain with the current state
    result = chain.invoke({
        "input": state["input"],
        "chat_history": state["chat_history"]
    })
    
    if Config.DEBUG_MODE:
        logger.debug(f"LLM Result: {result}")

    if Config.WRITE_INNER_THOUGHTS:
        print(f"\n<INNER_THOUGHT>\n: Agent generated AIMessage: {result.content}\n</INNER_THOUGHT>\n")
        if result.tool_calls:
            for tool_call in result.tool_calls:
                print(f"\n<INNER_THOUGHT>\n Tool Call: {tool_call['name']} with args {tool_call['args']}\n</INNER_THOUGHT>\n")

    # 会話履歴の要約処理
    if Config.MAX_CONVERSATION_TURNS > 0 and len(state["chat_history"]) >= Config.MAX_CONVERSATION_TURNS:
        
        # --- 要約境界の調整ロジック ---
        # AIMessage(tool_calls)とToolMessageのペアが分断されるのを防ぐ
        split_point = len(state["chat_history"]) - Config.SUMMARY_CONVERSATION_TURNS
        
        # split_pointが0より大きく、かつその位置のメッセージがToolMessageである場合、
        # ToolMessageシーケンスの前に来るAIMessageを含めるようにsplit_pointを後退させる
        if split_point > 0:
            while split_point > 0 and isinstance(state["chat_history"][split_point], ToolMessage):
                split_point -= 1
        
        # split_pointが負になるのを防ぐ
        split_point = max(0, split_point)
        
        # 境界調整後のメッセージリストを定義
        messages_to_summarize = state["chat_history"][:split_point]
        recent_history = state["chat_history"][split_point:]

        # 要約対象のメッセージがない場合は、要約処理をスキップ
        if not messages_to_summarize:
            return {"chat_history": state["chat_history"] + [result]}

        # 要約プロンプト
        summarize_prompt = ChatPromptTemplate.from_messages([
            ("system", "以下の「会話履歴全体」を参考にし、「要約対象の会話」を簡潔に要約してください。要約は、会話の主要なテーマ、決定事項、ユーザーの要求、要求への対応に関係する情報、未解決の課題に焦点を当てて必ず出力してください。要約中にtool_call_idを含めないでください。"),
            ("system", "--- 会話履歴全体 ---"),
            MessagesPlaceholder(variable_name="full_context_history"), # Full history for context
            ("system", "--- 要約対象の会話 ---"),
            MessagesPlaceholder(variable_name="messages_to_summarize") # Only the part to summarize
        ])
        summarize_chain = summarize_prompt | llm
        
        # LLMで要約を実行
        summary_response = summarize_chain.invoke({
            "full_context_history": state["chat_history"],
            "messages_to_summarize": messages_to_summarize
        })
        summary_message = AIMessage(content=f"会話の要約: {summary_response.content}")
        
        # 新しい会話履歴を構築
        # 要約メッセージ + 調整後の最新の会話履歴 + 現在のLLMの応答
        new_chat_history = [summary_message] + recent_history
        
        if Config.WRITE_INNER_THOUGHTS:
            print(f"\n<INNER_THOUGHT>\n: 古い会話が要約されました: {summary_message.content}\n</INNER_THOUGHT>\n")
        if Config.DEBUG_MODE:
            logger.debug(f"--- Conversation Summarized ---")
            logger.debug(f"Original history length: {len(state['chat_history'])}")
            logger.debug(f"Summarized history length: {len(new_chat_history)}")
            logger.debug(f"Summary: {summary_message.content}")
        
        return {"chat_history": new_chat_history + [result]}
    
    # 要約が不要な場合、通常の処理
    return {"chat_history": state["chat_history"] + [result]}

# Custom tool execution node
def execute_tools(state: AgentState):
    if Config.DEBUG_MODE:
        logger.debug("--- 3. Entering execute_tools ---")
        
    last_message = state["chat_history"][-1]
    if Config.DEBUG_MODE:
        logger.debug(f"Last message (containing tool calls): {last_message}")
        
    tool_messages = []
    
    # always_allowed_tools を state から取得
    current_always_allowed_tools = state.get("always_allowed_tools", set())
    updated_always_allowed_tools = set(current_always_allowed_tools) # 更新用コピー

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_to_call = tools[tool_name]
        tool_args = tool_call["args"]
        if Config.DEBUG_MODE:
            logger.debug(f"Processing tool call: {tool_name} with args: {tool_args}")

        def _invoke_tool():
            try:
                output = tool_to_call.invoke(tool_args)
                return ToolMessage(content=str(output), tool_call_id=tool_call["id"])
            except Exception as e:
                error_message = f"ツール '{tool_name}' の実行中にエラーが発生しました: {e}"
                if Config.DEBUG_MODE:
                    logger.debug(f"--- Tool Execution Error ---\n{error_message}")
                return ToolMessage(content=error_message, tool_call_id=tool_call["id"])

        # ファイルシステムを変更する可能性のあるツールを特定
        is_modifying_tool = tool_name not in ["list_directory_contents", "read_file", "internet_search", "read_many_files", "search_file_content", "think_tool", "work_tool", "web_fetch"]
        # run_shell_command はファイルシステムを変更する可能性があるため、常に承認を求める
        if tool_name == "run_shell_command":
            is_modifying_tool = True

        # 常に許可されているツールか、変更操作でない場合は直接実行
        if not is_modifying_tool or tool_name in current_always_allowed_tools:
            if Config.DEBUG_MODE:
                logger.debug(f"Executing tool '{tool_name}' directly (always allowed or non-modifying).")
            tool_messages.append(_invoke_tool())
            continue # 次のツール呼び出しへ

        # ユーザーに確認を求める
        print(f"\n--- ツール実行の確認 ---")
        print(f"AIは '{tool_name}' を実行しようとしています。引数: {tool_args}")
        print("選択肢:")
        print("  1. 一度だけ実行許可")
        print("  2. 今後も実行許可 (この種類のツールは次回から確認しません)")
        print("  3. 実行を許可せず、新しい指示を入力する")

        user_choice = None
        try:
            # uv run 環境での EOFError を考慮
            user_choice = input("選択肢 (1/2/3): ")
        except EOFError:
            if Config.DEBUG_MODE:
                logger.debug("非対話環境のため、ツール実行をスキップします。")
            tool_messages.append(ToolMessage(content=f"ツール '{tool_name}' は非対話環境のためスキップされました。", tool_call_id=tool_call["id"]))
            continue # 次のツール呼び出しへ

        if user_choice == "1":
            if Config.DEBUG_MODE:
                logger.debug(f"ユーザーが '{tool_name}' の一度限りの実行を許可しました。")
            tool_messages.append(_invoke_tool())
        elif user_choice == "2":
            if Config.DEBUG_MODE:
                logger.debug(f"ユーザーが '{tool_name}' の今後も実行を許可しました。")
            updated_always_allowed_tools.add(tool_name) # セットに追加
            tool_messages.append(_invoke_tool())
        elif user_choice == "3":
            if Config.DEBUG_MODE:
                logger.debug(f"ユーザーが '{tool_name}' の実行を拒否しました。")
            tool_messages.append(ToolMessage(content=f"ツール '{tool_name}' の実行はユーザーによって拒否されました。", tool_call_id=tool_call["id"]))
        else:
            if Config.DEBUG_MODE:
                logger.debug("無効な選択です。ツール実行をスキップします。")
            tool_messages.append(ToolMessage(content=f"ツール '{tool_name}' の実行は無効な選択のためスキップされました。", tool_call_id=tool_call["id"]))
            
    if Config.DEBUG_MODE:
        logger.debug(f"Final Tool Messages: {tool_messages}")
        
    if Config.WRITE_INNER_THOUGHTS:
        print(f"\n<INNER_THOUGHT>\nTool execution completed. Results: {tool_messages}\n</INNER_THOUGHT>\n")
    # 更新された always_allowed_tools を state に含めて返す
    return {"chat_history": tool_messages, "always_allowed_tools": updated_always_allowed_tools}

# Conditional logic for branching
def should_continue(state: AgentState):
    if Config.DEBUG_MODE:
        logger.debug(f"--- 2. Entering should_continue ---")
        logger.debug(f"Current State: {state}")
        
    last_message = state["chat_history"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        decision = "tools"
    else:
        decision = "end"
        
    if Config.DEBUG_MODE:
        logger.debug(f"Decision: {decision}")
        
    return decision


# Build the graph
def create_agent_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", run_agent)
    workflow.add_node("tools", execute_tools)
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", "end": END},
    )
    workflow.add_edge("tools", "agent")
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)