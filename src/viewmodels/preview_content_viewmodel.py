"""
プレビューコンテンツのビューモデル
メールプレビュー画面のデータ処理を担当
"""

import logging
import os
import sqlite3
from typing import Any, Dict, List, Optional, Union

from src.core.database import DatabaseManager


class PreviewContentViewModel:
    """プレビューコンテンツのビューモデル"""

    def __init__(self, task_id: Optional[str] = None):
        """
        初期化

        Args:
            task_id: タスクID
        """
        self.task_id = task_id
        self.conn = None

        # task_idがNoneの場合はデータベース接続を行わない
        if task_id is not None:
            self.main_db_path = os.path.join("data", "archives", task_id, "items.db")
            self._connect_db()
        else:
            self.main_db_path = None

        # プレビュー用の一時データベース
        self.preview_db_path = os.path.join("data", "preview_cache.db")
        self.preview_db = DatabaseManager(self.preview_db_path)

        # 一時データベースの初期化
        self._initialize_preview_db()

        # 現在選択されているフォルダID
        self.current_folder_id = None

        # キャッシュされたメールリスト
        self.cached_mail_list = []

    def _connect_db(self):
        """データベースに接続"""
        try:
            if os.path.exists(self.main_db_path):
                self.conn = sqlite3.connect(self.main_db_path)
                self.conn.row_factory = sqlite3.Row
            else:
                logging.error(
                    f"データベースファイルが見つかりません: {self.main_db_path}"
                )
        except Exception as e:
            logging.error(f"データベース接続エラー: {e}")

    def get_task_info(self) -> Optional[Dict]:
        """タスク情報を取得"""
        if self.task_id is None:
            return None

        try:
            if self.conn:
                cursor = self.conn.cursor()
                cursor.execute(
                    """
                    SELECT DISTINCT task_id, task_name
                    FROM items
                    LIMIT 1
                    """
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "id": row["task_id"] or self.task_id,
                        "name": row["task_name"] or f"アーカイブタスク {self.task_id}",
                        "status": "completed",
                    }
        except Exception as e:
            logging.error(f"タスク情報取得エラー: {e}")

        # データベースから取得できない場合はダミーデータを返す
        return {
            "id": self.task_id,
            "name": f"アーカイブタスク {self.task_id}",
            "status": "completed",
        }

    def _initialize_preview_db(self) -> None:
        """プレビュー用の一時データベースを初期化する"""
        # この関数は使用しないため、空の実装にする
        pass

    def get_folders(self) -> List[Dict]:
        """フォルダ一覧を取得"""
        if self.conn is None:
            return []

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT DISTINCT folder_id as entry_id, folder_name as name
                FROM items
                ORDER BY name
                """
            )
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"フォルダ取得エラー: {e}")
            return []

    def load_folder_mails(self, folder_id: str) -> List[Dict]:
        """指定フォルダのメール一覧を取得"""
        if self.conn is None:
            return []

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT 
                    id as entry_id, 
                    sender, 
                    subject, 
                    substr(body, 1, 100) as preview, 
                    date, 
                    unread
                FROM items
                WHERE folder_id = ?
                ORDER BY date DESC
                """,
                (folder_id,),
            )
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"メール一覧取得エラー: {e}")
            return []

    def search_mails(self, search_term: str) -> List[Dict]:
        """メールを検索"""
        if self.conn is None:
            return []

        try:
            cursor = self.conn.cursor()
            search_pattern = f"%{search_term}%"
            cursor.execute(
                """
                SELECT 
                    id as entry_id, 
                    sender, 
                    subject, 
                    substr(body, 1, 100) as preview, 
                    date, 
                    unread
                FROM items
                WHERE 
                    subject LIKE ? OR 
                    sender LIKE ? OR 
                    body LIKE ?
                ORDER BY date DESC
                """,
                (search_pattern, search_pattern, search_pattern),
            )
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"メール検索エラー: {e}")
            return []

    def get_mail_content(self, entry_id: str) -> Optional[Dict]:
        """メールの内容を取得"""
        if self.conn is None:
            return None

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT 
                    id, 
                    sender, 
                    subject, 
                    body as content, 
                    date, 
                    unread
                FROM items
                WHERE id = ?
                """,
                (entry_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logging.error(f"メール内容取得エラー: {e}")
            return None

    def mark_as_read(self, entry_id: str) -> bool:
        """メールを既読にする"""
        if self.conn is None:
            return False

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                UPDATE items
                SET unread = 0
                WHERE id = ?
                """,
                (entry_id,),
            )
            self.conn.commit()
            return True
        except Exception as e:
            logging.error(f"既読設定エラー: {e}")
            return False

    def close(self):
        """データベース接続を閉じる"""
        if self.conn:
            self.conn.close()
        if self.preview_db:
            self.preview_db.disconnect()

            # 一時DBファイルを削除
            try:
                if os.path.exists(self.preview_db_path):
                    os.remove(self.preview_db_path)
            except Exception as e:
                logging.warning(f"一時DBファイル削除エラー: {str(e)}")
