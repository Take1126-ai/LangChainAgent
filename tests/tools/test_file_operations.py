
import sys
import os
from pathlib import Path
import pytest

# Add project root to sys.path to allow importing from src
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.tools.file_operations import (
    write_file,
    read_file,
    create_directory,
    list_directory_contents,
    delete_file,
    delete_directory,
    move,
    modify_file_content
)

# --- Test Fixtures ---
@pytest.fixture
def temp_dir(tmp_path):
    """一時的なディレクトリを作成し、テスト中にそのパスをカレントディレクトリとして使用します。"""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original_cwd)

# --- Test Cases ---

def test_write_and_read_file(temp_dir):
    """write_file と read_file の基本的な動作をテストします。"""
    file_path = "test_file.txt"
    content = "こんにちは、世界！\nテストです。"

    # ファイルに書き込む
    write_result = write_file.invoke({"path": file_path, "content": content})
    assert f"ファイル '{file_path}' に内容を書き込みました。" in write_result
    assert os.path.exists(file_path)

    # ファイルを読み込む
    read_result = read_file.invoke({"path": file_path})
    assert content in read_result

def test_read_file_not_found():
    """存在しないファイルを読み込もうとした場合のエラーをテストします。"""
    result = read_file.invoke({"path": "non_existent_file.txt"})
    assert "エラー: パス 'non_existent_file.txt' が見つかりません。" in result

def test_create_and_list_directory(temp_dir):
    """create_directory と list_directory_contents の動作をテストします。"""
    dir_path = "test_dir"

    # ディレクトリを作成
    create_result = create_directory.invoke({"path": dir_path})
    assert f"ディレクトリ '{dir_path}' を作成しました。" in create_result
    assert os.path.isdir(dir_path)

    # ファイルを内部に作成してリスト表示をテスト
    (Path(dir_path) / "file1.txt").touch()
    (Path(dir_path) / "file2.log").touch()

    # ディレクトリの内容をリスト表示
    list_result = list_directory_contents.invoke({"path": dir_path})
    assert "file1.txt" in list_result
    assert "file2.log" in list_result

def test_create_directory_already_exists(temp_dir):
    """既に存在するディレクトリを作成しようとした場合のエラーをテストします。"""
    dir_path = "existing_dir"
    os.makedirs(dir_path)

    result = create_directory.invoke({"path": dir_path})
    assert f"エラー: パス '{dir_path}' は既に存在します。" in result

def test_delete_file(temp_dir):
    """delete_file の基本的な動作をテストします。"""
    file_path = "file_to_delete.txt"
    Path(file_path).touch()
    assert os.path.exists(file_path)

    # ファイルを削除
    delete_result = delete_file.invoke({"path": file_path})
    assert f"ファイル '{file_path}' を削除しました。" in delete_result
    assert not os.path.exists(file_path)


def test_delete_directory(temp_dir):
    """delete_directory の基本的な動作をテストします。"""
    dir_path = "dir_to_delete"
    os.makedirs(dir_path)
    (Path(dir_path) / "some_file.txt").touch()
    assert os.path.isdir(dir_path)

    # ディレクトリを削除
    delete_result = delete_directory.invoke({"path": dir_path})
    assert f"ディレクトリ '{dir_path}' を削除しました。" in delete_result
    assert not os.path.exists(dir_path)

def test_move_file(temp_dir):
    """move ツールのファイル移動の動作をテストします。"""
    src_file = "source.txt"
    dest_file = "destination.txt"
    Path(src_file).write_text("move test")

    # ファイルを移動
    move_result = move.invoke({"source_path": src_file, "destination_path": dest_file})
    assert f"'{src_file}' を '{dest_file}' に移動しました。" in move_result
    assert not os.path.exists(src_file)
    assert os.path.exists(dest_file)
    assert Path(dest_file).read_text() == "move test"

def test_rename_directory(temp_dir):
    """move ツールのディレクトリ名変更の動作をテストします。"""
    src_dir = "source_dir"
    dest_dir = "renamed_dir"
    os.makedirs(src_dir)
    (Path(src_dir) / "a.txt").touch()

    # ディレクトリ名を変更
    move_result = move.invoke({"source_path": src_dir, "destination_path": dest_dir})
    assert f"'{src_dir}' を '{dest_dir}' に移動しました。" in move_result
    assert not os.path.exists(src_dir)
    assert os.path.exists(dest_dir)
    assert os.path.exists(Path(dest_dir) / "a.txt")


def test_modify_file_content(temp_dir):
    """modify_file_content の基本的な動作をテストします。"""
    file_path = "modify_me.txt"
    original_content = "This is the old line of text."
    Path(file_path).write_text(original_content, encoding='utf-8')

    # 内容を修正
    old_text = "old line"
    new_text = "new line"
    modify_result = modify_file_content.invoke({
        "path": file_path, 
        "old_text": old_text, 
        "new_text": new_text
    })
    
    assert f"'{old_text}' を '{new_text}' に置換しました。" in modify_result

    # 内容を確認
    modified_content = Path(file_path).read_text(encoding='utf-8')
    expected_content = "This is the new line of text."
    assert modified_content == expected_content
