import logging
import os
import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Union


class DatabaseManager:
    """SQLiteデータベースとの接続や操作を担うクラス"""

    def __init__(self, db_path: str):
        """
        DatabaseManagerのコンストラクタ

        Args:
            db_path: データベースファイルのパス
        """
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        self._initialize_db()

    def _initialize_db(self) -> None:
        """データベースの初期化を行う"""
        try:
            # データベースディレクトリが存在しない場合は作成
            db_dir = os.path.dirname(self.db_path)
            if not os.path.exists(db_dir):
                os.makedirs(db_dir)

            # データベースに接続
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()

            # SQLスクリプトを実行してテーブルを作成
            self._execute_sql_scripts()

            logging.info(f"データベース初期化完了: {self.db_path}")
        except Exception as e:
            logging.error(f"データベース初期化エラー: {str(e)}")
            raise

    def _execute_sql_scripts(self) -> None:
        """SQLスクリプトファイルを実行してテーブルを作成する"""
        # データベースファイル名からベース名を取得
        db_basename = os.path.basename(self.db_path)
        db_name = os.path.splitext(db_basename)[0]  # 拡張子を除いたファイル名

        # データベース名に対応するSQLファイルを選択
        if db_name == "outlook":
            script_files = ["data/outlook.sql"]
        elif db_name == "tasks":
            script_files = ["data/tasks.sql"]
        elif db_name == "items":
            script_files = ["data/items.sql"]
        else:
            # デフォルトの場合は何も実行しない
            logging.warning(f"対応するSQLファイルが見つかりません: {db_name}")
            return

        for script_file in script_files:
            try:
                with open(script_file, "r", encoding="utf-8") as f:
                    sql_script = f.read()
                    self.cursor.executescript(sql_script)
                self.connection.commit()
                logging.info(f"SQLスクリプト実行完了: {script_file}")
            except Exception as e:
                logging.error(f"SQLスクリプト実行エラー ({script_file}): {str(e)}")
                raise

    def connect(self) -> None:
        """データベースに接続する"""
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()

    def disconnect(self) -> None:
        """データベース接続を閉じる"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        SELECT クエリを実行し、結果を辞書のリストとして返す

        Args:
            query: 実行するSQLクエリ
            params: クエリパラメータ

        Returns:
            クエリ結果の辞書リスト
        """
        try:
            self.connect()
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logging.error(
                f"クエリ実行エラー: {query}, パラメータ: {params}, エラー: {str(e)}"
            )
            raise

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """
        INSERT, UPDATE, DELETE クエリを実行し、影響を受けた行数を返す

        Args:
            query: 実行するSQLクエリ
            params: クエリパラメータ

        Returns:
            影響を受けた行数
        """
        try:
            self.connect()
            self.cursor.execute(query, params)
            self.connection.commit()
            return self.cursor.rowcount
        except Exception as e:
            self.connection.rollback()
            logging.error(
                f"更新クエリ実行エラー: {query}, パラメータ: {params}, エラー: {str(e)}"
            )
            raise

    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """
        複数のパラメータセットで同じクエリを実行する

        Args:
            query: 実行するSQLクエリ
            params_list: パラメータのリスト

        Returns:
            影響を受けた行数
        """
        try:
            self.connect()
            self.cursor.executemany(query, params_list)
            self.connection.commit()
            return self.cursor.rowcount
        except Exception as e:
            self.connection.rollback()
            logging.error(
                f"一括クエリ実行エラー: {query}, パラメータ数: {len(params_list)}, エラー: {str(e)}"
            )
            raise

    def insert_and_get_id(self, query: str, params: tuple = ()) -> int:
        """
        INSERT クエリを実行し、生成された行のIDを返す

        Args:
            query: 実行するSQLクエリ
            params: クエリパラメータ

        Returns:
            挿入された行のID
        """
        try:
            self.connect()
            self.cursor.execute(query, params)
            self.connection.commit()
            return self.cursor.lastrowid
        except Exception as e:
            self.connection.rollback()
            logging.error(
                f"挿入クエリ実行エラー: {query}, パラメータ: {params}, エラー: {str(e)}"
            )
            raise

    def get_single_value(self, query: str, params: tuple = ()) -> Optional[Any]:
        """
        単一の値を返すクエリを実行する

        Args:
            query: 実行するSQLクエリ
            params: クエリパラメータ

        Returns:
            クエリ結果の単一の値、または結果がない場合はNone
        """
        try:
            self.connect()
            self.cursor.execute(query, params)
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            logging.error(
                f"単一値クエリ実行エラー: {query}, パラメータ: {params}, エラー: {str(e)}"
            )
            raise

    def begin_transaction(self) -> None:
        """トランザクションを開始する"""
        self.connect()
        self.connection.execute("BEGIN TRANSACTION")

    def commit(self) -> None:
        """トランザクションをコミットする"""
        if self.connection:
            self.connection.commit()

    def rollback(self) -> None:
        """トランザクションをロールバックする"""
        if self.connection:
            self.connection.rollback()

    def table_exists(self, table_name: str) -> bool:
        """
        指定したテーブルが存在するかチェックする

        Args:
            table_name: チェックするテーブル名

        Returns:
            テーブルが存在する場合はTrue、そうでない場合はFalse
        """
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        result = self.get_single_value(query, (table_name,))
        return result is not None

    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """
        テーブルの構造情報を取得する

        Args:
            table_name: 情報を取得するテーブル名

        Returns:
            テーブル構造情報の辞書リスト
        """
        query = f"PRAGMA table_info({table_name})"
        return self.execute_query(query)

    def backup_database(self, backup_path: str) -> bool:
        """
        データベースのバックアップを作成する

        Args:
            backup_path: バックアップファイルのパス

        Returns:
            バックアップが成功した場合はTrue
        """
        try:
            # バックアップディレクトリが存在しない場合は作成
            backup_dir = os.path.dirname(backup_path)
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)

            # 現在の接続を閉じる
            self.disconnect()

            # データベースファイルをコピー
            source_conn = sqlite3.connect(self.db_path)
            dest_conn = sqlite3.connect(backup_path)

            source_conn.backup(dest_conn)

            source_conn.close()
            dest_conn.close()

            # 再接続
            self.connect()

            logging.info(f"データベースバックアップ完了: {backup_path}")
            return True
        except Exception as e:
            logging.error(f"データベースバックアップエラー: {str(e)}")
            # エラー後に再接続を試みる
            try:
                self.connect()
            except:
                pass
            return False
