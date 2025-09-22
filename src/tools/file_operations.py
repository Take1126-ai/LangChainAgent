import os
import shutil
from langchain_core.tools import tool
from pathlib import Path
import fnmatch
import re

@tool
def list_directory_contents(path: str) -> str:
    """指定されたパスのディレクトリ内容を一覧表示します。"""
    if not os.path.exists(path):
        return f"エラー: パス '{path}' が見つかりません。"
    if not os.path.isdir(path):
        return f"エラー: パス '{path}' はディレクトリではありません。"

    try:
        contents = os.listdir(path)
        if not contents:
            return f"ディレクトリ '{path}' は空です。"
        
        return f"ディレクトリ '{path}' の内容:\n" + "\n".join(f"- {item}" for item in contents)
    except Exception as e:
        return f"ディレクトリ '{path}' の読み込み中にエラーが発生しました: {e}"

@tool
def read_file(path: str) -> str:
    """指定されたパスのファイル内容を読み込んで返します。"""
    if not os.path.exists(path):
        return f"エラー: パス '{path}' が見つかりません。"
    if not os.path.isfile(path):
        return f"エラー: パス '{path}' はファイルではありません。"

    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return f"ファイル '{path}' の内容:\n---\n{content}\n---"
    except Exception as e:
        return f"ファイル '{path}' の読み込み中にエラーが発生しました: {e}"

@tool
def write_file(path: str, content: str) -> str:
    """指定されたパスに内容を書き込みます（ファイルが存在する場合は上書きされます）。"""
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        return f"エラー: ディレクトリ '{directory}' が見つかりません。先にディレクトリを作成してください。"
    
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"ファイル '{path}' に内容を書き込みました。"
    except Exception as e:
        return f"ファイル '{path}' への書き込み中にエラーが発生しました: {e}"

@tool
def delete_file(path: str) -> str:
    """指定されたファイルを削除します。"""
    if not os.path.exists(path):
        return f"エラー: パス '{path}' が見つかりません。"
    if not os.path.isfile(path):
        return f"エラー: パス '{path}' はファイルではありません。"

    try:
        os.remove(path)
        return f"ファイル '{path}' を削除しました。"
    except Exception as e:
        return f"ファイル '{path}' の削除中にエラーが発生しました: {e}"

@tool
def create_directory(path: str) -> str:
    """指定されたパスにディレクトリを新規作成します。"""
    if os.path.exists(path):
        return f"エラー: パス '{path}' は既に存在します。"
    
    try:
        os.makedirs(path, exist_ok=False)
        return f"ディレクトリ '{path}' を作成しました。"
    except Exception as e:
        return f"ディレクトリ '{path}' の作成中にエラーが発生しました: {e}"

@tool
def delete_directory(path: str) -> str:
    """指定されたディレクトリを削除します（内容物があっても削除されます）。"""
    if not os.path.exists(path):
        return f"エラー: パス '{path}' が見つかりません。"
    if not os.path.isdir(path):
        return f"エラー: パス '{path}' はディレクトリではありません。"

    try:
        shutil.rmtree(path)
        return f"ディレクトリ '{path}' を削除しました。"
    except Exception as e:
        return f"ディレクトリ '{path}' の削除中にエラーが発生しました: {e}"

@tool
def move(source_path: str, destination_path: str) -> str:
    """ファイルまたはディレクトリを移動または名前変更します。"""
    if not os.path.exists(source_path):
        return f"エラー: 移動元パス '{source_path}' が見つかりません。"
    
    try:
        shutil.move(source_path, destination_path)
        return f"'{source_path}' を '{destination_path}' に移動しました。"
    except Exception as e:
        return f"'{source_path}' の移動中にエラーが発生しました: {e}"

@tool
def modify_file_content(path: str, old_text: str, new_text: str) -> str:
    """指定されたファイルの内容を読み込み、特定の文字列を別の文字列に置換して、その内容をファイルに書き戻します。"""
    try:
        # ファイルを読み込む
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 文字列を置換する
        modified_content = content.replace(old_text, new_text)
        
        # 修正した内容をファイルに書き戻す
        with open(path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
            
        return f"ファイル '{path}' の内容を修正しました。'{old_text}' を '{new_text}' に置換しました。"
    except FileNotFoundError:
        return f"エラー: ファイル '{path}' が見つかりません。"
    except Exception as e:
        return f"ファイル '{path}' の修正中にエラーが発生しました: {e}"

@tool
def read_many_files(paths: list[str], exclude: list[str] = None, include: list[str] = None, recursive: bool = True, useDefaultExcludes: bool = True) -> str:
    """
    複数のファイルやディレクトリの内容を読み込みます。globパターンもサポートします。
    テキストファイルのみを対象とし、バイナリファイルはスキップされます。

    Args:
        paths (list[str]): 読み込むファイルやディレクトリのパス、またはglobパターンのリスト。
        exclude (list[str], optional): 除外するファイルやディレクトリのglobパターン。
        include (list[str], optional): 追加で含めるglobパターン。
        recursive (bool, optional): ディレクトリを再帰的に検索するかどうか。デフォルトはTrue。
        useDefaultExcludes (bool, optional): デフォルトの除外パターンを適用するかどうか。デフォルトはTrue。

    Returns:
        str: 読み込んだファイルの内容を連結した文字列。各ファイルの内容は`--- {filePath} ---`で区切られます。
             エラーが発生した場合は、エラーメッセージを返します。
    """
    if exclude is None:
        exclude = []
    if include is None:
        include = []

    # デフォルトの除外パターン
    default_excludes = [
        "node_modules/", ".git/", "__pycache__/", "*.pyc", "*.log", "*.tmp",
        "*.zip", "*.tar.gz", "*.rar", "*.7z", "*.exe", "*.dll", "*.so", "*.dylib",
        "*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp", "*.ico", "*.mp3", "*.mp4",
        "*.avi", "*.mov", "*.flv", "*.wmv", "*.pdf", "*.doc", "*.docx", "*.xls",
        "*.xlsx", "*.ppt", "*.pptx", "*.sqlite3", "*.db", "*.DS_Store",
        "*.venv/", ".pytest_cache/", "uv.lock" # プロジェクト固有の除外
    ]
    if not useDefaultExcludes:
        default_excludes = []

    all_files_to_read = []
    for p in paths:
        base_path = Path(p)
        if base_path.is_file():
            all_files_to_read.append(base_path)
        elif base_path.is_dir():
            if recursive:
                for root, _, files in os.walk(base_path):
                    for file in files:
                        all_files_to_read.append(Path(root) / file)
            else:
                for item in os.listdir(base_path):
                    item_path = base_path / item
                    if item_path.is_file():
                        all_files_to_read.append(item_path)
        else: # globパターンとして扱う
            # glob.glob は再帰的なパターンをサポートしないため、Path.glob を使用
            # ただし、Path.glob はカレントディレクトリからの相対パスでしか機能しないため、
            # os.getcwd() を基準にするか、より汎用的な glob ライブラリを検討する必要がある。
            # ここでは簡易的に Path.glob を使用するが、必要に応じて修正する。
            # 現状の glob ツールと重複する部分もあるため、注意が必要。
            for f in Path('.').glob(p): # カレントディレクトリからのglob
                if f.is_file():
                    all_files_to_read.append(f)

    # フィルタリング
    filtered_files = []
    for file_path in all_files_to_read:
        file_str = str(file_path)
        # 除外パターンにマッチしないか確認
        if any(fnmatch.fnmatch(file_str, ex) for ex in exclude + default_excludes):
            continue
        # 含まれるパターンにマッチするか確認 (includeが指定されている場合のみ)
        if include and not any(fnmatch.fnmatch(file_str, inc) for inc in include):
            continue
        filtered_files.append(file_path)

    content_parts = []
    for file_path in sorted(filtered_files): # ソートして一貫性を保つ
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            content_parts.append(f"--- {file_path} ---\n{content}")
        except UnicodeDecodeError:
            # テキストファイルでない場合はスキップ
            content_parts.append(f"--- {file_path} (バイナリファイルまたは読み込みエラーのためスキップ) ---")
        except Exception as e:
            content_parts.append(f"--- {file_path} (読み込みエラー: {e}) ---")

    if not content_parts:
        return "指定された条件に一致するファイルは見つかりませんでした。"
    
    return "\n".join(content_parts) + "\n--- End of content ---"

@tool
def search_file_content(pattern: str, include: str = None, path: str = None) -> str:
    """
    指定されたディレクトリ内のファイル内容から正規表現パターンを検索します。
    マッチした行、ファイルパス、行番号を返します。

    Args:
        pattern (str): 検索する正規表現パターン。
        include (str, optional): 検索対象ファイルをフィルタリングするglobパターン（例: '*.py', 'src/**/*.js'）。
        path (str, optional): 検索対象ディレクトリの絶対パス。指定しない場合は現在の作業ディレクトリ。

    Returns:
        str: マッチした行、ファイルパス、行番号を含む文字列。
             検索結果がない場合は、その旨を伝えます。
    """
    search_path = Path(path) if path else Path.cwd()
    results = []
    compiled_pattern = re.compile(pattern)

    for root, _, files in os.walk(search_path):
        for file_name in files:
            file_path = Path(root) / file_name
            if include and not fnmatch.fnmatch(str(file_path), include):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if compiled_pattern.search(line):
                            results.append(f"{file_path}:{line_num}: {line.strip()}")
            except UnicodeDecodeError:
                # バイナリファイルはスキップ
                continue
            except Exception as e:
                results.append(f"エラー: ファイル {file_path} の読み込み中にエラーが発生しました: {e}")

    if not results:
        return f"パターン '{pattern}' に一致する内容はファイル内で見つかりませんでした。"
    
    return "\n".join(results)

# エージェントが利用するツールリスト
file_tools = [
    list_directory_contents,
    read_file,
    write_file,
    delete_file,
    create_directory,
    delete_directory,
    move,
    modify_file_content,
    read_many_files,
    search_file_content
]
