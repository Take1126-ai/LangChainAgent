
import sys
import os
from pathlib import Path
import pytest

# Add project root to sys.path to allow importing from src
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.tools.command_execution import run_shell_command


def test_run_shell_command_success():
    """単純な成功するコマンドをテストします。"""
    command = "echo 'hello world'"
    result = run_shell_command.invoke({"command": command})

    assert f"Command: {command}" in result
    assert "Stdout: hello world" in result
    assert "Stderr: (empty)" in result
    assert "Exit Code: 0" in result
    assert "Error: (none)" in result

def test_run_shell_command_error():
    """エラーを生成するコマンドをテストします。"""
    command = "ls no_such_dir_exists_here"
    result = run_shell_command.invoke({"command": command})

    assert f"Command: {command}" in result
    assert "Stdout: (empty)" in result
    assert "Stderr: " in result # Stderr should not be empty
    assert "No such file or directory" in result # The specific error message
    assert "Exit Code: " in result
    assert "Error: Command exited with non-zero status" in result

def test_run_shell_command_with_cwd(tmp_path):
    """`cwd` パラメータを使用して異なるディレクトリでコマンドを実行するのをテストします。"""
    # 一時ディレクトリ内に新しいサブディレクトリを作成
    sub_dir = tmp_path / "sub"
    sub_dir.mkdir()

    command = "pwd"
    result = run_shell_command.invoke({"command": command, "cwd": str(sub_dir)})

    assert f"Command: {command}" in result
    assert f"Directory: {sub_dir}" in result
    assert str(sub_dir) in result # pwdの出力にサブディレクトリのパスが含まれているはず
    assert "Exit Code: 0" in result
