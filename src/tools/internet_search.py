import os
from langchain_core.tools import tool
from tavily import TavilyClient

# Tavily APIキーは環境変数から読み込まれることを想定
# .env ファイルに TAVILY_API_KEY=YOUR_API_KEY を設定してください
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY is not set in environment variables.")

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

@tool
def internet_search(query: str) -> str:
    """
    インターネットで情報を検索し、結果の要約または関連スニペットを返します。
    特に、最新の情報や特定のウェブサイトからの情報を取得するのに役立ちます。

    Args:
        query (str): 検索するクエリ文字列。

    Returns:
        str: 検索結果の要約または関連スニペット。
             検索結果がない場合は、その旨を伝えます。
    """
    try:
        # Tavily API を使用して検索を実行
        # max_results は取得する検索結果の数を指定します。
        # include_raw_content=False で、コンテンツ全体ではなくスニペットのみを取得します。
        response = tavily_client.search(query=query, max_results=5, include_raw_content=False)

        if not response['results']:
            return "指定されたクエリに対する検索結果は見つかりませんでした。"

        # 検索結果を整形して返す
        formatted_results = []
        for i, result in enumerate(response['results']):
            formatted_results.append(f"Result {i+1}:")
            formatted_results.append(f"  Title: {result['title']}")
            formatted_results.append(f"  URL: {result['url']}")
            formatted_results.append(f"  Snippet: {result['content']}")
            formatted_results.append("") # 空行で区切り

        return "\n".join(formatted_results)

    except Exception as e:
        return f"インターネット検索中にエラーが発生しました: {e}"

# ツールリストに含める場合は、以下のようにリストに追加します。
# internet_search_tools = [internet_search]

