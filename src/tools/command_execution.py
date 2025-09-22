import subprocess
import os
from langchain_core.tools import tool

@tool
def run_shell_command(command: str, cwd: str = None) -> str:
    """
    指定されたシェルコマンドを実行し、その結果を返します。
    ファイルシステムやシステム状態を変更する可能性のあるコマンドを実行する前に、ユーザーの確認を求めます。

    Args:
        command (str): 実行するシェルコマンド文字列。
        cwd (str, optional): コマンドを実行するディレクトリ。指定しない場合は現在の作業ディレクトリで実行されます。

    Returns:
        str: コマンドの標準出力、標準エラー出力、および終了コードを含む結果文字列。
             エラーが発生した場合は、エラーメッセージを返します。
    """
    try:
        # subprocess.run を使用してコマンドを実行
        # shell=True を指定することで、シェルを介してコマンドを実行します。
        # capture_output=True で標準出力と標準エラー出力をキャプチャします。
        # text=True で出力をテキストとして扱います。
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            cwd=cwd, 
            check=False # エラーが発生しても例外を発生させない
        )

        output = f"Command: {command}\n"
        output += f"Directory: {cwd if cwd else os.getcwd()}\n"
        output += f"Stdout: {result.stdout if result.stdout else '(empty)'}\n"
        output += f"Stderr: {result.stderr if result.stderr else '(empty)'}\n"
        output += f"Exit Code: {result.returncode}\n"

        if result.returncode != 0:
            output += f"Error: Command exited with non-zero status {result.returncode}\n"
        else:
            output += f"Error: (none)\n"

        return output

    except FileNotFoundError:
        return f"エラー: コマンドが見つかりません: {command}"
    except Exception as e:
        return f"コマンド実行中に予期せぬエラーが発生しました: {e}"

# ツールリストに含める場合は、以下のようにリストに追加します。
# command_execution_tools = [run_shell_command]