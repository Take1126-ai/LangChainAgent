import typer
import os
import sys
from pathlib import Path
from langchain_core.messages import BaseMessage, AIMessage

# Add project root to sys.path for module discovery
current_file_path = Path(__file__).resolve()
project_root_path = current_file_path.parent
sys.path.append(str(project_root_path))

from src.core.agent import create_agent_graph

app = typer.Typer()

@app.command()
def chat():
    """
    CLI AIアシスタントと会話します。
    """
    typer.echo("CLI AIアシスタントと会話を開始します。終了するには 'exit' と入力してください。")
    agent_app = create_agent_graph()
    
    # 会話のスレッドIDを定義
    config = {"configurable": {"thread_id": "main_chat_session"}}

    while True:
        user_input = input("あなた: ")
        if user_input.lower() == "exit":
            typer.echo("会話を終了します。")
            break

        # エージェントを呼び出し、応答を取得
        # input と chat_history は LangGraph の State に自動的にマージされる
        initial_state = {"input": user_input}
        result = agent_app.invoke(initial_state, config=config)
        
        # エージェントの最終応答を表示
        final_ai_message = result.get("chat_history", [])[-1]
        if isinstance(final_ai_message, AIMessage):
            typer.echo(f"AI: {final_ai_message.content}")

if __name__ == "__main__":
    app()