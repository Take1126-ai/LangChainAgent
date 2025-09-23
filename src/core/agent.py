from typing import TypedDict, List, Annotated, Optional, Dict, Any
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage, HumanMessage # HumanMessage を追加
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

from src.tools.file_operations import file_tools, read_many_files, search_file_content # 変更
from src.tools.internet_search import internet_search # 追加
from src.tools.command_execution import run_shell_command # 追加
from src.tools.think_tool import think_tool # 追加
from src.tools.work_tool import work_tool # 追加

# Define the tools
# file_tools と internet_search と run_shell_command を結合
all_tools = file_tools + [internet_search, run_shell_command, read_many_files, search_file_content, think_tool, work_tool] # 変更
tools = {t.name: t for t in all_tools} # 変更

# Initialize LLM and bind tools
llm = ChatGoogleGenerativeAI(model=Config.MODEL_NAME, temperature=0)
llm_with_tools = llm.bind_tools(all_tools) # 変更

# NOTE: The prompt and chain are now created dynamically inside the run_agent node

# Define the state for our graph # ここに移動
class AgentState(TypedDict):
    input: str
    chat_history: Annotated[list[BaseMessage], operator.add]
    # The 'tool_results' field is for holding the output of the last tool call.
    # It is cleared after being used by the agent.
    tool_results: Annotated[list, operator.add]
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
    if Config.DEBUG_MODE: # 追加
        print("\n--- 1. Entering run_agent ---")
        print(f"State: {state}")

    # Dynamically create the prompt and chain for this turn
    system_prompt_str = create_agent_prompt(state)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt_str),
            MessagesPlaceholder(variable_name="chat_history"),
            MessagesPlaceholder(variable_name="tool_results", optional=True),
            ("user", "{input}"),
        ]
    )
    chain = prompt | llm_with_tools

    # Invoke the chain with the current state
    result = chain.invoke({
        "input": state["input"],
        "chat_history": state["chat_history"],
        "tool_results": state.get("tool_results", [])
    })
    
    if Config.WRITE_INNER_THOUGHTS:
        print(f"\nINNER_THOUGHT: Agent generated AIMessage: {result.content}\n")
        if result.tool_calls:
            for tool_call in result.tool_calls:
                print(f"\nINNER_THOUGHT:   Tool Call: {tool_call['name']} with args {tool_call['args']}\n")

    # Clear tool_results after they have been "consumed" by the agent
    return {"chat_history": [result], "tool_results": []}

# Custom tool execution node
def execute_tools(state: AgentState):
    if Config.DEBUG_MODE: # 追加
        print("\n--- 3. Entering execute_tools ---")
    last_message = state["chat_history"][-1]
    tool_messages = []
    
    # always_allowed_tools を state から取得
    current_always_allowed_tools = state.get("always_allowed_tools", set())
    updated_always_allowed_tools = set(current_always_allowed_tools) # 更新用コピー

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_to_call = tools[tool_name]
        tool_args = tool_call["args"]

        # ファイルシステムを変更する可能性のあるツールを特定
        is_modifying_tool = tool_name not in ["list_directory_contents", "read_file", "internet_search", "read_many_files", "search_file_content", "think_tool", "work_tool"] # 変更
        # run_shell_command はファイルシステムを変更する可能性があるため、常に承認を求める
        if tool_name == "run_shell_command": # 追加
            is_modifying_tool = True # 追加

        # 常に許可されているツールか、変更操作でない場合は直接実行
        if not is_modifying_tool or tool_name in current_always_allowed_tools:
            if Config.DEBUG_MODE: # 追加
                print(f"Executing tool '{tool_name}' directly (always allowed or non-modifying).\n")
            tool_output = tool_to_call.invoke(tool_args)
            tool_messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"]))
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
            if Config.DEBUG_MODE: # 追加
                print("\n非対話環境のため、ツール実行をスキップします。")
            tool_messages.append(ToolMessage(content=f"ツール '{tool_name}' は非対話環境のためスキップされました。", tool_call_id=tool_call["id"]))
            continue # 次のツール呼び出しへ

        if user_choice == "1":
            if Config.DEBUG_MODE: # 追加
                print(f"ユーザーが '{tool_name}' の一度限りの実行を許可しました。")
            tool_output = tool_to_call.invoke(tool_args)
            tool_messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"]))
        elif user_choice == "2":
            if Config.DEBUG_MODE: # 追加
                print(f"ユーザーが '{tool_name}' の今後も実行を許可しました。")
            updated_always_allowed_tools.add(tool_name) # セットに追加
            tool_output = tool_to_call.invoke(tool_args)
            tool_messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"]))
        elif user_choice == "3":
            if Config.DEBUG_MODE: # 追加
                print(f"ユーザーが '{tool_name}' の実行を拒否しました。")
            tool_messages.append(ToolMessage(content=f"ツール '{tool_name}' の実行はユーザーによって拒否されました。", tool_call_id=tool_call["id"]))
        else:
            if Config.DEBUG_MODE: # 追加
                print("無効な選択です。ツール実行をスキップします。")
            tool_messages.append(ToolMessage(content=f"ツール '{tool_name}' の実行は無効な選択のためスキップされました。", tool_call_id=tool_call["id"]))
            
    if Config.DEBUG_MODE: # 追加
        print(f"Tool Messages: {tool_messages}")
    if Config.WRITE_INNER_THOUGHTS:
        print(f"\nINNER_THOUGHT: Tool execution completed. Results: {tool_messages}\n")
    # 更新された always_allowed_tools を state に含めて返す
    return {"tool_results": tool_messages, "always_allowed_tools": updated_always_allowed_tools}

# 検証エージェントノード
# Conditional logic for branching
def should_continue(state: AgentState):
    if Config.DEBUG_MODE: # 追加
        print("\n--- 2. Entering should_continue ---")
        print(f"State: {state}")
    if isinstance(state["chat_history"][-1], AIMessage) and state["chat_history"][-1].tool_calls:
        return "tools"
    # ツール呼び出しがない場合、処理を終了する
    return "end"



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
