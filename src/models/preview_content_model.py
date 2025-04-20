"""
プレビューコンテンツのモデル
メールプレビュー画面のデータアクセスを担当
"""

import json
import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from src.core.database import DatabaseManager


class PreviewContentModel:
    """プレビューコンテンツのモデル"""

    def __init__(self, task_id: Optional[str] = None):
        """
        初期化

        Args:
            task_id: タスクID
        """
        self.task_id = task_id
        self.db_manager = None

        # task_idがNoneの場合はデータベース接続を行わない
        if task_id is not None:
            self.main_db_path = os.path.join("data", "tasks", task_id, "items.db")
            self._connect_db()
        else:
            self.main_db_path = None

        # プレビュー用の一時データベース
        self.preview_db_path = os.path.join("data", "preview_cache.db")
        self._initialize_preview_db()

    def _connect_db(self) -> bool:
        """
        データベースに接続

        Returns:
            bool: 接続に成功したかどうか
        """
        try:
            if os.path.exists(self.main_db_path):
                self.db_manager = DatabaseManager(self.main_db_path)

                # flaggedカラムが存在しない場合は追加する
                self._add_flagged_column_if_not_exists()

                return True
            else:
                logging.error(
                    f"データベースファイルが見つかりません: {self.main_db_path}"
                )
                return False
        except Exception as e:
            logging.error(f"データベース接続エラー: {e}")
            return False

    def _initialize_preview_db(self) -> None:
        """プレビュー用の一時データベースを初期化する"""
        # この関数は使用しないため、空の実装にする
        pass

    def _is_db_connected(self) -> bool:
        """
        データベース接続が有効かどうかを確認

        Returns:
            bool: データベース接続が有効かどうか
        """
        return self.db_manager is not None

    def get_task_info(self) -> Optional[Dict]:
        """
        タスク情報を取得

        Returns:
            Optional[Dict]: タスク情報、取得できない場合はNone
        """
        if self.task_id is None:
            return None

        try:
            if self._is_db_connected():
                query = """
                    SELECT DISTINCT task_id
                    FROM mail_items
                    LIMIT 1
                    """
                results = self.db_manager.execute_query(query)
                if results:
                    row = results[0]
                    return {
                        "id": row.get("task_id") or self.task_id,
                        "name": f"アーカイブタスク {self.task_id}",
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

    def get_folders(self) -> List[Dict]:
        """
        フォルダ一覧を取得

        Returns:
            List[Dict]: フォルダ情報のリスト
        """
        if not self._is_db_connected():
            return []

        try:
            query = """
                SELECT DISTINCT folder_id as entry_id, folder_name as name
                FROM mail_items
                ORDER BY name
                """
            return self.db_manager.execute_query(query)
        except Exception as e:
            logging.error(f"フォルダ取得エラー: {e}")
            return []

    def load_folder_mails(self, folder_id: str) -> List[Dict]:
        """
        指定フォルダのメール一覧を取得

        Args:
            folder_id: フォルダID

        Returns:
            List[Dict]: メール情報のリスト
        """
        if not self._is_db_connected():
            return []

        try:
            query = """
                SELECT 
                    entry_id, 
                    '' as sender, 
                    subject, 
                    substr(body, 1, 100) as preview, 
                    sent_time as date, 
                    unread
                FROM mail_items
                WHERE (folder_id = ?) AND (message_type IS NULL OR message_type != 'guardian')
                ORDER BY sent_time DESC
                """
            return self.db_manager.execute_query(query, (folder_id,))
        except Exception as e:
            logging.error(f"メール一覧取得エラー: {e}")
            return []

    def _get_mail_participants(self, mail_id: str) -> Dict[str, str]:
        """
        メールの送信者と受信者情報を取得する

        Args:
            mail_id: メールID

        Returns:
            Dict[str, str]: 送信者と受信者情報を含む辞書
        """
        default_result = {
            "sender": "不明 <unknown@example.com>",
            "recipient": "不明 <unknown@example.com>",
        }

        if not self._is_db_connected():
            return default_result

        try:
            # 送信者情報を取得
            sender_query = """
                SELECT 
                    u.name, 
                    u.email, 
                    u.display_name 
                FROM participants p
                JOIN users u ON p.user_id = u.id
                WHERE p.mail_id = ? AND p.participant_type = 'sender'
                LIMIT 1
            """
            sender_results = self.db_manager.execute_query(sender_query, (mail_id,))

            # 受信者情報を取得（to参加者のみ）
            recipient_query = """
                SELECT 
                    u.name, 
                    u.email, 
                    u.display_name 
                FROM participants p
                JOIN users u ON p.user_id = u.id
                WHERE p.mail_id = ? AND p.participant_type = 'to'
                LIMIT 1
            """
            recipient_results = self.db_manager.execute_query(
                recipient_query, (mail_id,)
            )

            # 送信者情報の処理
            sender = "不明 <unknown@example.com>"
            if sender_results:
                sender_info = sender_results[0]
                sender_name = (
                    sender_info.get("display_name") or sender_info.get("name") or ""
                )
                sender_email = sender_info.get("email") or "unknown@example.com"
                sender = f"{sender_name} <{sender_email}>"

            # 受信者情報の処理
            recipient = "不明 <unknown@example.com>"
            if recipient_results:
                recipient_info = recipient_results[0]
                recipient_name = (
                    recipient_info.get("display_name")
                    or recipient_info.get("name")
                    or ""
                )
                recipient_email = recipient_info.get("email") or "unknown@example.com"
                recipient = f"{recipient_name} <{recipient_email}>"

            return {"sender": sender, "recipient": recipient}
        except Exception as e:
            logging.error(f"参加者情報取得エラー: {e}")
            return default_result

    def _get_all_participants(self, mail_id: str) -> Dict[str, List[Dict]]:
        """
        メールの全参加者情報を取得する（sender, to, cc, bcc）

        Args:
            mail_id: メールID

        Returns:
            Dict[str, List[Dict]]: 参加者タイプ別の情報を含む辞書
        """
        default_result = {"sender": [], "to": [], "cc": [], "bcc": []}

        if not self._is_db_connected():
            return default_result

        try:
            # 全参加者情報を取得
            query = """
                SELECT 
                    u.id,
                    u.name, 
                    u.email, 
                    u.display_name,
                    u.company,
                    p.participant_type
                FROM participants p
                JOIN users u ON p.user_id = u.id
                WHERE p.mail_id = ?
                ORDER BY p.participant_type, u.name
            """
            results = self.db_manager.execute_query(query, (mail_id,))

            # 参加者タイプ別に整理
            participants = {"sender": [], "to": [], "cc": [], "bcc": []}

            for participant in results:
                participant_type = participant.get("participant_type", "to")

                if participant_type not in participants:
                    participants[participant_type] = []

                participants[participant_type].append(
                    {
                        "id": participant.get("id"),
                        "name": participant.get("name", ""),
                        "email": participant.get("email", ""),
                        "display_name": participant.get("display_name", ""),
                        "company": participant.get("company", ""),
                    }
                )

            return participants
        except Exception as e:
            logging.error(f"全参加者情報取得エラー: {e}")
            return default_result

    def search_mails(self, search_term: str) -> List[Dict]:
        """
        メールを検索

        Args:
            search_term: 検索キーワード

        Returns:
            List[Dict]: 検索結果のメールリスト
        """
        if not self._is_db_connected():
            return []

        try:
            search_pattern = f"%{search_term}%"
            query = """
                SELECT 
                    entry_id as id, 
                    subject, 
                    body as content,
                    substr(body, 1, 100) as preview, 
                    sent_time as date, 
                    unread,
                    folder_id,
                    has_attachments,
                    flagged
                FROM mail_items
                WHERE 
                    (subject LIKE ? OR body LIKE ?) AND
                    (message_type IS NULL OR message_type != 'guardian')
                ORDER BY sent_time DESC
                """
            results = self.db_manager.execute_query(
                query, (search_pattern, search_pattern)
            )

            # データがなければ空リストを返す
            if not results:
                return []

            # 結果を整形
            formatted_mails = []
            for mail in results:
                # 送信者と受信者情報を取得
                participant_info = self._get_mail_participants(mail["id"])
                mail["sender"] = participant_info["sender"]
                mail["recipient"] = participant_info["recipient"]

                # フラグ状態
                mail["flagged"] = bool(mail.get("flagged", 0))

                # 添付ファイル情報を取得（has_attachmentsが1の場合のみ）
                attachments = []
                if mail.get("has_attachments", 0) == 1:
                    attachment_query = """
                        SELECT id, name, path
                        FROM attachments
                        WHERE mail_id = ?
                        """
                    attachment_results = self.db_manager.execute_query(
                        attachment_query, (mail["id"],)
                    )
                    attachments = attachment_results if attachment_results else []

                # 添付ファイル情報を設定
                mail["attachments"] = attachments
                formatted_mails.append(mail)

            return formatted_mails
        except Exception as e:
            logging.error(f"メール検索エラー: {e}")
            return []

    def get_ai_review_for_thread(self, thread_id: str) -> Optional[Dict]:
        """
        会話グループのAIレビュー結果を取得

        Args:
            thread_id: 会話ID

        Returns:
            Optional[Dict]: AIレビュー結果を含む辞書（ない場合はNone）
        """
        if not self._is_db_connected() or not thread_id:
            return None

        try:
            query = """
                SELECT result
                FROM ai_reviews
                WHERE thread_id = ?
                """
            results = self.db_manager.execute_query(query, (thread_id,))

            if not results or not results[0].get("result"):
                return None

            # JSON文字列をPythonオブジェクトに変換
            try:
                result_json = results[0].get("result")
                if isinstance(result_json, str):
                    return json.loads(result_json)
                return result_json
            except json.JSONDecodeError as e:
                logging.error(f"AIレビュー結果のJSON解析エラー: {e}")
                return None
        except Exception as e:
            logging.error(f"AIレビュー取得エラー: {e}")
            return None

    def get_mail_content(self, entry_id: str) -> Optional[Dict]:
        """
        メールの内容を取得

        Args:
            entry_id: メールID

        Returns:
            Optional[Dict]: メール情報、取得できない場合はNone
        """
        if not self._is_db_connected():
            return None

        try:
            # メール基本情報を取得
            query = """
                SELECT 
                    entry_id as id, 
                    subject, 
                    body as content, 
                    sent_time as date, 
                    unread,
                    has_attachments,
                    thread_id,
                    flagged
                FROM mail_items
                WHERE (entry_id = ?) AND (message_type IS NULL OR message_type != 'guardian')
                """
            results = self.db_manager.execute_query(query, (entry_id,))
            if not results:
                return None

            mail = results[0]

            # Markdownフラグを常にFalseに設定
            mail["is_markdown"] = False

            # 送信者と受信者情報を取得
            participant_info = self._get_mail_participants(entry_id)
            mail["sender"] = participant_info["sender"]
            mail["recipient"] = participant_info["recipient"]

            # 全参加者情報を取得
            mail["participants"] = self._get_all_participants(entry_id)

            # フラグ状態（DBに値がなければデフォルトでFalse）
            mail["flagged"] = bool(mail.get("flagged", 0))

            # 添付ファイル情報を取得（has_attachmentsが1の場合のみ）
            attachments = []
            if mail.get("has_attachments", 0) == 1:
                attachment_query = """
                    SELECT id, name, path
                    FROM attachments
                    WHERE mail_id = ?
                    """
                attachment_results = self.db_manager.execute_query(
                    attachment_query, (entry_id,)
                )
                attachments = attachment_results if attachment_results else []

            # 添付ファイル情報を設定
            mail["attachments"] = attachments

            # 会話IDがあれば、AIレビュー結果を取得
            if mail.get("thread_id"):
                mail["ai_review"] = self.get_ai_review_for_thread(mail["thread_id"])

            return mail
        except Exception as e:
            logging.error(f"メール内容取得エラー: {e}")
            return None

    def mark_as_read(self, entry_id: str) -> Tuple[bool, str]:
        """
        メールを既読にする

        Args:
            entry_id: メールID

        Returns:
            Tuple[bool, str]: 成功したかどうかとメッセージのタプル
        """
        if not self._is_db_connected():
            return False, "データベース接続がありません"

        try:
            query = """
                UPDATE mail_items
                SET unread = 0
                WHERE entry_id = ?
                """
            self.db_manager.execute_update(query, (entry_id,))
            return True, "メールを既読に設定しました"
        except Exception as e:
            error_msg = f"既読設定エラー: {e}"
            logging.error(error_msg)
            return False, error_msg

    def get_all_mails(self) -> List[Dict]:
        """
        すべてのメールを取得

        Returns:
            List[Dict]: 全メール情報のリスト
        """
        if not self._is_db_connected():
            return []

        try:
            # メール一覧情報を取得
            query = """
                SELECT 
                    entry_id as id, 
                    subject,
                    body as content,
                    substr(body, 1, 100) as preview, 
                    sent_time as date,
                    unread,
                    folder_id,
                    has_attachments,
                    thread_id,
                    flagged
                FROM mail_items
                WHERE (message_type IS NULL OR message_type != 'guardian')
                ORDER BY sent_time DESC
                """
            results = self.db_manager.execute_query(query)

            # データがなければ空リストを返す
            if not results:
                return []

            # 会話IDをキーにしてAIレビュー結果をまとめて取得
            thread_ids = set()
            for mail in results:
                if mail.get("thread_id"):
                    thread_ids.add(mail["thread_id"])

            ai_reviews = self._get_ai_reviews_by_thread_ids(thread_ids)

            # 結果を整形
            formatted_mails = []
            for mail in results:
                # 送信者と受信者情報を取得
                participant_info = self._get_mail_participants(mail["id"])
                mail["sender"] = participant_info["sender"]
                mail["recipient"] = participant_info["recipient"]

                # フラグ状態（DBに値がなければデフォルトでFalse）
                mail["flagged"] = bool(mail.get("flagged", 0))

                # 添付ファイル情報を取得
                mail["attachments"] = self._get_attachments_for_mail(mail)

                # AIレビュー結果を設定
                if mail.get("thread_id") and mail["thread_id"] in ai_reviews:
                    mail["ai_review"] = ai_reviews[mail["thread_id"]]

                formatted_mails.append(mail)

            return formatted_mails
        except Exception as e:
            logging.error(f"すべてのメール取得エラー: {e}")
            return []

    def _get_ai_reviews_by_thread_ids(self, thread_ids: set) -> Dict[str, Any]:
        """AIレビュー結果をまとめて取得する"""
        ai_reviews = {}
        if not thread_ids or not self._is_db_connected():
            return ai_reviews

        try:
            placeholders = ", ".join(["?"] * len(thread_ids))
            ai_review_query = f"""
                SELECT thread_id, result
                FROM ai_reviews
                WHERE thread_id IN ({placeholders})
                """
            ai_review_results = self.db_manager.execute_query(
                ai_review_query, tuple(thread_ids)
            )

            for review in ai_review_results:
                conv_id = review.get("thread_id")
                result = review.get("result")
                if conv_id and result:
                    try:
                        if isinstance(result, str):
                            ai_reviews[conv_id] = json.loads(result)
                        else:
                            ai_reviews[conv_id] = result
                    except json.JSONDecodeError:
                        logging.warning(f"AIレビュー結果のJSON解析エラー: {conv_id}")
        except Exception as e:
            logging.error(f"AIレビュー一括取得エラー: {e}")

        return ai_reviews

    def _get_attachments_for_mail(self, mail: Dict) -> List[Dict]:
        """メールの添付ファイル情報を取得"""
        attachments = []
        if not mail.get("has_attachments", 0) == 1 or not self._is_db_connected():
            return attachments

        try:
            attachment_query = """
                SELECT id, name, path
                FROM attachments
                WHERE mail_id = ?
                """
            attachment_results = self.db_manager.execute_query(
                attachment_query, (mail["id"],)
            )
            attachments = attachment_results if attachment_results else []
        except Exception as e:
            logging.error(
                f"添付ファイル情報取得エラー - メールID: {mail['id']}, エラー: {e}"
            )

        return attachments

    def download_attachment(self, file_id: str) -> Tuple[bool, str, Optional[str]]:
        """
        添付ファイルをダウンロード

        Args:
            file_id: 添付ファイルのID

        Returns:
            Tuple[bool, str, Optional[str]]: (成功したかどうか, メッセージ, 保存されたパス)
        """
        if not self._is_db_connected():
            return False, "データベース接続がありません", None

        try:
            # 添付ファイル情報を取得
            attachment_info = self._get_attachment_info(file_id)
            if not attachment_info:
                return False, f"添付ファイルが見つかりません: {file_id}", None

            source_path = attachment_info.get("path")
            mail_id = attachment_info.get("mail_id")
            file_name = attachment_info.get("name")

            # パスの検証
            if not self._validate_attachment_path(source_path, file_id):
                return False, f"添付ファイルのパスが無効です: {source_path}", None

            if not mail_id:
                return (
                    False,
                    f"添付ファイルに関連するメールIDが見つかりません: {file_id}",
                    None,
                )

            # ダウンロード先ディレクトリを作成
            download_dir = os.path.join("data", "tasks", self.task_id, mail_id)
            downloads_path = Path(download_dir)

            if not self._ensure_download_directory(downloads_path):
                return (
                    False,
                    f"ダウンロードディレクトリの作成に失敗しました: {download_dir}",
                    None,
                )

            # ファイル名の競合を解決して保存
            target_path = self._resolve_file_name_conflict(download_dir, file_name)

            # ファイルをコピー
            try:
                shutil.copy2(source_path, target_path)

                # コピーが成功したか確認
                if os.path.exists(target_path):
                    # 保存したパスをDBに更新
                    self._update_attachment_path(file_id, target_path)
                    return (
                        True,
                        f"添付ファイルをダウンロードしました: {os.path.basename(target_path)}",
                        target_path,
                    )
                else:
                    return False, f"添付ファイルのコピーに失敗しました", None
            except Exception as e:
                return False, f"ファイルコピーエラー: {str(e)}", None

        except Exception as e:
            error_msg = f"添付ファイルのダウンロードに失敗: {str(e)}"
            logging.error(error_msg)
            return False, error_msg, None

    def _get_attachment_info(self, file_id: str) -> Optional[Dict]:
        """添付ファイル情報を取得"""
        if not self._is_db_connected():
            return None

        try:
            query = """
                SELECT a.id, a.name, a.path, a.mail_id
                FROM attachments a
                WHERE a.id = ?
                """
            results = self.db_manager.execute_query(query, (file_id,))
            return results[0] if results else None
        except Exception as e:
            logging.error(f"添付ファイル情報取得エラー: {e}")
            return None

    def _validate_attachment_path(
        self, source_path: Optional[str], file_id: str
    ) -> bool:
        """添付ファイルのパスを検証"""
        if not source_path:
            logging.error(f"添付ファイルのパスが設定されていません: {file_id}")
            return False

        if not os.path.exists(source_path):
            logging.error(f"添付ファイルのパスが無効です: {source_path}")
            return False

        return True

    def _ensure_download_directory(self, downloads_path: Path) -> bool:
        """ダウンロードディレクトリの存在を確認し、なければ作成"""
        try:
            if not downloads_path.exists():
                os.makedirs(downloads_path, exist_ok=True)
            return True
        except Exception as e:
            logging.error(f"ディレクトリ作成エラー: {str(e)}")
            return False

    def _resolve_file_name_conflict(self, download_dir: str, file_name: str) -> str:
        """ファイル名の競合を解決"""
        target_path = os.path.join(download_dir, file_name)
        try:
            if os.path.exists(target_path):
                base_name, ext = os.path.splitext(file_name)
                counter = 1
                while os.path.exists(target_path):
                    new_file_name = f"{base_name}_{counter}{ext}"
                    target_path = os.path.join(download_dir, new_file_name)
                    counter += 1
        except Exception as e:
            logging.error(f"ファイル名競合処理エラー: {str(e)}")

        return target_path

    def _update_attachment_path(self, file_id: str, target_path: str) -> bool:
        """添付ファイルの保存パスをDBに更新"""
        if not self._is_db_connected():
            return False

        try:
            update_query = """
                UPDATE attachments
                SET path = ?
                WHERE id = ?
            """
            self.db_manager.execute_update(update_query, (target_path, file_id))
            return True
        except Exception as e:
            logging.error(f"DB更新エラー: {str(e)}")
            return False

    def close(self) -> bool:
        """
        データベース接続を閉じる

        Returns:
            bool: 成功したかどうか
        """
        try:
            # データベース接続が存在する場合
            if self.db_manager:
                try:
                    # リソース解放用のSQLコマンドを実行
                    self.db_manager.execute_update("PRAGMA optimize")
                    self.db_manager.execute_update("PRAGMA wal_checkpoint(FULL)")
                    self.db_manager.execute_update("VACUUM")
                    # DB解放前に同期を強制
                    self.db_manager.execute_update("PRAGMA synchronous = OFF")
                    self.db_manager.commit()
                    # 接続を閉じる
                    self.db_manager.disconnect()
                    logging.info("データベース接続を閉じました")
                except Exception as e:
                    logging.error(f"データベース接続を閉じる際にエラー: {str(e)}")
                finally:
                    # 参照を確実に解放
                    self.db_manager = None

            # 一時DBファイルを削除
            self._clean_up_temp_files()

            # タスクIDをクリア
            self.task_id = None

            # 明示的にガベージコレクションを実行
            import gc

            gc.collect()

            return True

        except Exception as e:
            logging.error(f"リソース解放中に予期せぬエラー: {str(e)}")
            # 最終的に参照を確実に解放
            self.db_manager = None
            return False

    def _clean_up_temp_files(self) -> None:
        """一時ファイルの削除"""
        try:
            if (
                hasattr(self, "preview_db_path")
                and self.preview_db_path
                and os.path.exists(self.preview_db_path)
            ):
                os.remove(self.preview_db_path)
                logging.info(f"一時DBファイルを削除しました: {self.preview_db_path}")
        except Exception as e:
            logging.warning(f"一時ファイル削除エラー: {str(e)}")

    def _add_flagged_column_if_not_exists(self) -> None:
        """mail_itemsテーブルにflaggedカラムがなければ追加する"""
        if not self.db_manager:
            return

        try:
            # mail_itemsテーブルの構造を確認
            columns = self.db_manager.get_table_info("mail_items")
            column_names = [col["name"] for col in columns]

            # flaggedカラムが存在しない場合は追加
            if "flagged" not in column_names:
                query = """
                ALTER TABLE mail_items
                ADD COLUMN flagged INTEGER DEFAULT 0
                """
                self.db_manager.execute_update(query)
                logging.info("mail_itemsテーブルにflaggedカラムを追加しました")
        except Exception as e:
            logging.error(f"flaggedカラム追加エラー: {e}")

    def toggle_flag(
        self, entry_id: str, target_state: Optional[bool] = None
    ) -> Tuple[bool, str, bool]:
        """
        メールのフラグ状態を切り替える、または指定された状態に設定する

        Args:
            entry_id: メールID
            target_state: 目標とするフラグ状態（指定がなければ現在の状態を反転）

        Returns:
            Tuple[bool, str, bool]: (成功したかどうか, メッセージ, 新しいフラグ状態)
        """
        if not self._is_db_connected():
            return False, "データベース接続がありません", False

        try:
            # 現在のフラグ状態を取得
            query = """
                SELECT flagged
                FROM mail_items
                WHERE entry_id = ?
                """
            results = self.db_manager.execute_query(query, (entry_id,))

            if not results:
                return False, f"メールが見つかりません: {entry_id}", False

            current_flag = results[0].get("flagged", 0)

            # 新しいフラグ状態を決定
            if target_state is None:
                # target_stateが指定されていない場合は現在の状態を反転
                new_flag = 1 if current_flag == 0 else 0
            else:
                # target_stateが指定されている場合はその値を使用
                new_flag = 1 if target_state else 0

                # 現在の状態と同じなら変更なし
                if (current_flag == 1 and new_flag == 1) or (
                    current_flag == 0 and new_flag == 0
                ):
                    flag_status = "オン" if new_flag == 1 else "オフ"
                    return True, f"フラグ状態は既に{flag_status}です", new_flag == 1

            # フラグ状態を更新
            update_query = """
                UPDATE mail_items
                SET flagged = ?
                WHERE entry_id = ?
                """
            self.db_manager.execute_update(update_query, (new_flag, entry_id))

            flag_status = "追加" if new_flag == 1 else "解除"
            return True, f"フラグを{flag_status}しました", new_flag == 1
        except Exception as e:
            error_msg = f"フラグ設定エラー: {e}"
            logging.error(error_msg)
            return False, error_msg, False

    def batch_update_flags(self, flag_updates: Dict[str, bool]) -> bool:
        """
        複数のメールのフラグ状態を一括で更新する

        Args:
            flag_updates: メールIDとフラグ状態のマッピング辞書

        Returns:
            bool: すべての更新が成功したかどうか
        """
        if not self._is_db_connected() or not flag_updates:
            return False

        logging.info(f"一括フラグ更新: {len(flag_updates)}件")

        try:
            # トランザクション開始
            self.db_manager.begin_transaction()

            # 各メールのフラグ状態を更新
            update_query = """
                UPDATE mail_items
                SET flagged = ?
                WHERE entry_id = ?
            """

            success_count = 0
            for mail_id, flag_state in flag_updates.items():
                try:
                    flag_value = 1 if flag_state else 0
                    self.db_manager.execute_update(update_query, (flag_value, mail_id))
                    success_count += 1
                except Exception as e:
                    logging.error(f"メール {mail_id} のフラグ更新に失敗: {e}")

            # トランザクション終了（コミット）
            self.db_manager.commit()

            logging.info(
                f"一括フラグ更新完了: {success_count}/{len(flag_updates)}件成功"
            )
            return success_count == len(flag_updates)

        except Exception as e:
            # エラー発生時はロールバック
            self.db_manager.rollback()
            logging.error(f"一括フラグ更新エラー: {e}")
            return False
