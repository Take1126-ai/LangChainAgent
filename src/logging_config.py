import logging
import os
from datetime import datetime
import uuid

def setup_logging():
    """
    ファイルベースのロガーをセットアップします。

    ロガーは 'logs' ディレクトリ内に一意の名前を持つファイルに書き込みます。
    ログファイル名は YYYY-MM-DD_HH-MM-SS_UUID.log の形式になります。
    コンソールにはINFOレベル以上のログを出力し、ファイルにはDEBUGレベル以上の
    全てのログを記録します。

    Args:
        なし

    Returns:
        logging.Logger: 設定済みのロガーオブジェクト。
    """
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 一意のファイル名を生成
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    unique_id = str(uuid.uuid4())[:8]
    log_filename = f"{timestamp}_{unique_id}.log"
    log_filepath = os.path.join(log_dir, log_filename)

    # ルートロガーではなく、名前付きロガーを取得
    logger = logging.getLogger("LangChainCLIAgent")
    logger.setLevel(logging.DEBUG) # 全てのメッセージをキャプチャするために最低レベルを設定

    # 親ロガーへの伝播を防ぐ
    logger.propagate = False

    # ログの重複を避けるために既存のハンドラを削除
    if logger.hasHandlers():
        logger.handlers.clear()

    # ファイルハンドラを作成
    file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG) # ファイルハンドラのレベルを設定

    # コンソールハンドラを作成
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO) # コンソールにはINFO以上のみ表示

    # フォーマッタを作成
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # ハンドラをロガーに追加
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# 他のモジュールからインポートするためのロガーインスタンス
logger = setup_logging()
