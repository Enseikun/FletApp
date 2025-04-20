import os
import sqlite3
import threading
from typing import Any, Dict, List, Optional, Tuple, Union

from src.core.logger import get_logger


class DatabaseManager:
    """SQLiteデータベースとの接続や操作を担うクラス"""

    def __init__(self, db_path: str):
        """
        DatabaseManagerのコンストラクタ

        Args:
            db_path: データベースファイルのパス
        """
        self.db_path = db_path
        self._local = threading.local()
        self.logger = get_logger()
        self._initialize_db()

    def _get_connection(self) -> sqlite3.Connection:
        """スレッドローカルなデータベース接続を取得する"""
        if not hasattr(self._local, "connection"):
            self._local.connection = sqlite3.connect(self.db_path)
            self._local.connection.row_factory = sqlite3.Row
            self._local.cursor = self._local.connection.cursor()
        return self._local.connection

    def _get_cursor(self) -> sqlite3.Cursor:
        """スレッドローカルなカーソルを取得する"""
        if not hasattr(self._local, "cursor"):
            self._get_connection()
        return self._local.cursor

    def _initialize_db(self) -> None:
        """データベースの初期化を行う"""
        try:
            # データベースディレクトリが存在しない場合は作成
            db_dir = os.path.dirname(self.db_path)
            if not os.path.exists(db_dir):
                os.makedirs(db_dir)

            # 初期接続を作成
            self._get_connection()

            # SQLスクリプトを実行してテーブルを作成
            self._execute_sql_scripts()

            self.logger.info(f"データベース初期化完了: {self.db_path}")
        except Exception as e:
            self.logger.error(f"データベース初期化エラー: {str(e)}")
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
            self.logger.warning(f"対応するSQLファイルが見つかりません: {db_name}")
            return

        for script_file in script_files:
            try:
                with open(script_file, "r", encoding="utf-8") as f:
                    sql_script = f.read()
                    self._get_cursor().executescript(sql_script)
                self._get_connection().commit()
                self.logger.info(f"SQLスクリプト実行完了: {script_file}")
            except Exception as e:
                self.logger.error(f"SQLスクリプト実行エラー ({script_file}): {str(e)}")
                raise

    def connect(self) -> bool:
        """
        データベースに接続する

        Returns:
            bool: 接続に成功したかどうか
        """
        try:
            self._get_connection()
            return True
        except Exception as e:
            self.logger.error(f"データベース接続エラー: {e}")
            return False

    def disconnect(self) -> bool:
        """
        データベース接続を閉じる

        Returns:
            bool: 切断に成功したかどうか
        """
        try:
            if hasattr(self._local, "connection"):
                self._local.connection.close()
                del self._local.connection
                del self._local.cursor
            return True
        except Exception as e:
            self.logger.error(f"データベース切断エラー: {e}")
            return False

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
            self._get_cursor().execute(query, params)
            rows = self._get_cursor().fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(
                f"クエリ実行エラー: {query}, パラメータ: {params}, エラー: {str(e)}"
            )
            return []  # エラー時に空のリストを返す

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
            self._get_cursor().execute(query, params)
            self._get_connection().commit()
            return self._get_cursor().rowcount
        except Exception as e:
            self._get_connection().rollback()
            self.logger.error(
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
            self._get_cursor().executemany(query, params_list)
            self._get_connection().commit()
            return self._get_cursor().rowcount
        except Exception as e:
            self._get_connection().rollback()
            self.logger.error(
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
            self._get_cursor().execute(query, params)
            self._get_connection().commit()
            return self._get_cursor().lastrowid
        except Exception as e:
            self._get_connection().rollback()
            self.logger.error(
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
            self._get_cursor().execute(query, params)
            result = self._get_cursor().fetchone()
            return result[0] if result else None
        except Exception as e:
            self.logger.error(
                f"単一値クエリ実行エラー: {query}, パラメータ: {params}, エラー: {str(e)}"
            )
            raise

    def begin_transaction(self) -> bool:
        """
        トランザクションを開始する

        Returns:
            bool: トランザクション開始に成功したかどうか
        """
        try:
            self.connect()
            self._get_connection().execute("BEGIN TRANSACTION")
            return True
        except Exception as e:
            self.logger.error(f"トランザクション開始エラー: {e}")
            return False

    def commit(self) -> bool:
        """
        トランザクションをコミットする

        Returns:
            bool: コミットに成功したかどうか
        """
        try:
            if hasattr(self._local, "connection"):
                self._get_connection().commit()
            return True
        except Exception as e:
            self.logger.error(f"コミットエラー: {e}")
            return False

    def rollback(self) -> bool:
        """
        トランザクションをロールバックする

        Returns:
            bool: ロールバックに成功したかどうか
        """
        try:
            if hasattr(self._local, "connection"):
                self._get_connection().rollback()
            return True
        except Exception as e:
            self.logger.error(f"ロールバックエラー: {e}")
            return False

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

            self.logger.info(f"データベースバックアップ完了: {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"データベースバックアップエラー: {str(e)}")
            # エラー後に再接続を試みる
            try:
                self.connect()
            except:
                pass
            return False
