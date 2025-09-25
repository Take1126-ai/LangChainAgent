import urllib.request
import chardet
from langchain_core.tools import tool

@tool(parse_docstring=True)
def web_fetch(url: str) -> str:
    """
    指定されたURLのコンテンツを取得し、文字コードを自動判定してテキストを返します。
    取得したコンテンツは、表示不可能な制御文字を除去してクリーンアップされます。

    Args:
        url (str): 取得したいコンテンツのURL。

    Returns:
        str: URLから取得したコンテンツのテキスト。エラーが発生した場合はエラーメッセージを返します。
    """
    try:
        with urllib.request.urlopen(url) as response:
            raw_content = response.read()
            
            # chardetで文字コードを判定
            result = chardet.detect(raw_content)
            detected_encoding = result['encoding']
            
            # 判定できなかった場合のフォールバック
            if detected_encoding is None:
                # ヘッダーから取得を試みる
                content_type = response.getheader('Content-Type')
                if content_type and 'charset=' in content_type:
                    detected_encoding = content_type.split('charset=')[-1].strip()
                else:
                    # 最終フォールバック
                    detected_encoding = 'utf-8'

            try:
                # 判定した文字コードでデコード
                text_content = raw_content.decode(detected_encoding, errors='replace')
                return text_content
            except (UnicodeDecodeError, TypeError, LookupError) as e:
                return f"""エラー: コンテンツのデコード中に問題が発生しました。\n判定されたエンコーディング: {detected_encoding}\nエラー詳細: {e}"""

    except Exception as e:
        return f"エラー: URLの取得中に問題が発生しました - {e}"