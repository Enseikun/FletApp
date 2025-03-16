import os
import sqlite3


def insert_dummy_data(db_path, sql_file_path):
    """
    指定されたSQLiteデータベースにダミーデータを挿入します
    """
    # データベースに接続
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # ダミーデータのSQLファイルを読み込む
        with open(sql_file_path, "r", encoding="utf-8") as f:
            sql_script = f.read()

        # SQLスクリプトを実行
        cursor.executescript(sql_script)

        # 変更をコミット
        conn.commit()
        print(
            f"{os.path.basename(sql_file_path)}からのダミーデータが正常に挿入されました"
        )

    except sqlite3.Error as e:
        print(f"エラーが発生しました: {e}")
        conn.rollback()

    finally:
        # 接続を閉じる
        conn.close()


if __name__ == "__main__":
    # タスク情報のダミーデータを挿入
    insert_dummy_data("data/tasks.db", "data/dummy_task_data.sql")

    # アイテム情報のダミーデータを挿入
    insert_dummy_data(
        "data/archives/20250315172449/items.db", "data/dummy_items_data.sql"
    )

    # Outlookアカウント情報のダミーデータを挿入
    insert_dummy_data("data/outlook.db", "data/dummy_outlook_data.sql")
