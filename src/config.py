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
    # MEMORY_TURNS: 会話履歴に保持するターン数。0の場合は上限なし。
    MEMORY_TURNS: int = int("0")


    # デバッグ設定
    DEBUG_MODE: bool = False

    # 検証エージェント設定
    MAX_VERIFICATION_ATTEMPTS: int = 3