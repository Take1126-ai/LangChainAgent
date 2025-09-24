import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv(override=True)

class Config: # クラス名を変更
    """
    アプリケーション全体の共通設定を管理するクラス。
    LLM設定、デバッグモード、会話履歴設定などを一元的に管理する。
    """
    # LLM設定
    MODEL_NAME: str = os.getenv("GEMINI_MODEL_NAME", "models/gemini-2.0-flash")
    API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    API_BASE: Optional[str] = os.getenv("GEMINI_API_BASE")
    TAVILY_API_KEY: Optional[str] = os.getenv("TAVILY_API_KEY")

    # 会話履歴設定
    # MAX_CONVERSATION_TURNS: 会話履歴がこのターン数を超えたら要約を開始する。0の場合は要約しない。
    MAX_CONVERSATION_TURNS: int = int(os.getenv("MAX_CONVERSATION_TURNS", "10"))
    # SUMMARY_CONVERSATION_TURNS: 要約後に保持する会話のターン数。
    SUMMARY_CONVERSATION_TURNS: int = int(os.getenv("SUMMARY_CONVERSATION_TURNS", "5"))

    # デバッグ設定
    DEBUG_MODE: bool = False
    # エージェントの内部思考を表示するかどうか
    WRITE_INNER_THOUGHTS: bool = True
