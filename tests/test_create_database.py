import datetime
import os
from pathlib import Path

from src.core.database import DatabaseManager

# プロジェクトのルートディレクトリを取得
ROOT_DIR = Path(__file__).parent.parent


def test_create_outlook_database():
    """outlook.sqlからoutlook.dbを作成するテスト"""
    db_file = ROOT_DIR / "data" / "outlook.db"
    sql_file = ROOT_DIR / "data" / "outlook.sql"

    # 既存のDBファイルがあれば削除（テスト用）
    if os.path.exists(db_file):
        os.remove(db_file)

    # SQLファイルが存在することを確認
    assert os.path.exists(sql_file), f"SQLファイルが見つかりません: {sql_file}"

    # DatabaseManagerを使用してデータベースを作成
    db_manager = DatabaseManager(str(db_file))

    # データベースが作成されたことを確認
    assert os.path.exists(db_file)

    # テーブルが存在することを確認
    tables = db_manager.execute_query(
        "SELECT name FROM sqlite_master WHERE type='table';"
    )

    # 少なくとも1つのテーブルが存在することを確認
    assert len(tables) > 0

    # 接続を閉じる
    db_manager.disconnect()


def test_create_tasks_database():
    """tasks.sqlからtasks.dbを作成するテスト"""
    db_file = ROOT_DIR / "data" / "tasks.db"

    # 既存のDBファイルがあれば削除（テスト用）
    if os.path.exists(db_file):
        os.remove(db_file)

    # DatabaseManagerを使用してデータベースを作成
    db_manager = DatabaseManager(str(db_file))

    # データベースが作成されたことを確認
    assert os.path.exists(db_file)

    # テーブルが存在することを確認
    tables = db_manager.execute_query(
        "SELECT name FROM sqlite_master WHERE type='table';"
    )

    # 少なくとも1つのテーブルが存在することを確認
    assert len(tables) > 0

    # 接続を閉じる
    db_manager.disconnect()


def test_create_items_database():
    """items.sqlからアーカイブディレクトリにitems.dbを作成するテスト"""
    # 現在のタイムスタンプをディレクトリ名として使用
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    archive_dir = ROOT_DIR / "data" / "archives" / timestamp
    db_file = archive_dir / "items.db"
    sql_file = ROOT_DIR / "data" / "items.sql"

    # ディレクトリが存在しない場合は作成
    os.makedirs(archive_dir, exist_ok=True)

    # 既存のDBファイルがあれば削除（テスト用）
    if os.path.exists(db_file):
        os.remove(db_file)

    # SQLファイルの内容を確認（デバッグ用）
    try:
        with open(sql_file, "r", encoding="utf-8") as f:
            sql_content = f.read()
            print(f"SQLファイルの内容:\n{sql_content}")
    except Exception as e:
        print(f"SQLファイル読み込みエラー: {e}")

    try:
        # DatabaseManagerを使用してデータベースを作成
        db_manager = DatabaseManager(str(db_file))

        # データベースが作成されたことを確認
        assert os.path.exists(db_file)

        # テーブルが存在することを確認
        tables = db_manager.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table';"
        )

        # 少なくとも1つのテーブルが存在することを確認
        assert len(tables) > 0

        # 接続を閉じる
        db_manager.disconnect()
    except Exception as e:
        print(f"データベース作成エラー: {e}")
        raise

    # テスト後にクリーンアップ
    if os.path.exists(db_file):
        os.remove(db_file)
    os.rmdir(archive_dir)


# 手動実行用のヘルパー関数
def run_tests():
    # テスト関数を直接実行
    test_create_outlook_database()
    test_create_tasks_database()
    test_create_items_database()


if __name__ == "__main__":
    # 手動実行用
    run_tests()
    print("すべてのデータベース作成テストが完了しました。")
