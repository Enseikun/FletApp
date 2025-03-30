"""
プレビューコンテンツのモデル
メールプレビュー画面のデータアクセスを担当
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

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

    def _connect_db(self):
        """データベースに接続"""
        try:
            if os.path.exists(self.main_db_path):
                self.db_manager = DatabaseManager(self.main_db_path)
            else:
                logging.error(
                    f"データベースファイルが見つかりません: {self.main_db_path}"
                )
        except Exception as e:
            logging.error(f"データベース接続エラー: {e}")

    def _initialize_preview_db(self) -> None:
        """プレビュー用の一時データベースを初期化する"""
        # この関数は使用しないため、空の実装にする
        pass

    def get_task_info(self) -> Optional[Dict]:
        """タスク情報を取得"""
        if self.task_id is None:
            return None

        try:
            if self.db_manager:
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
        """フォルダ一覧を取得"""
        if self.db_manager is None:
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
        """指定フォルダのメール一覧を取得"""
        if self.db_manager is None:
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
                WHERE folder_id = ?
                ORDER BY sent_time DESC
                """
            return self.db_manager.execute_query(query, (folder_id,))
        except Exception as e:
            logging.error(f"メール一覧取得エラー: {e}")
            return []

    def _get_mail_participants(self, mail_id: str) -> Dict[str, str]:
        """メールの送信者と受信者情報を取得する

        Args:
            mail_id: メールID

        Returns:
            送信者と受信者情報を含む辞書
        """
        if self.db_manager is None:
            return {
                "sender": "不明 <unknown@example.com>",
                "recipient": "不明 <unknown@example.com>",
            }

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
            return {
                "sender": "不明 <unknown@example.com>",
                "recipient": "不明 <unknown@example.com>",
            }

    def _get_all_participants(self, mail_id: str) -> Dict[str, List[Dict]]:
        """メールの全参加者情報を取得する（sender, to, cc, bcc）

        Args:
            mail_id: メールID

        Returns:
            参加者タイプ別の情報を含む辞書
        """
        if self.db_manager is None:
            return {"sender": [], "to": [], "cc": [], "bcc": []}

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
            return {"sender": [], "to": [], "cc": [], "bcc": []}

    def search_mails(self, search_term: str) -> List[Dict]:
        """メールを検索"""
        if self.db_manager is None:
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
                    has_attachments
                FROM mail_items
                WHERE 
                    subject LIKE ? OR 
                    body LIKE ?
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
                mail["flagged"] = False

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

    def get_ai_review_for_conversation(self, conversation_id: str) -> Optional[Dict]:
        """会話グループのAIレビュー結果を取得

        Args:
            conversation_id: 会話ID

        Returns:
            AIレビュー結果を含む辞書（ない場合はNone）
        """
        if self.db_manager is None or not conversation_id:
            return None

        try:
            query = """
                SELECT result
                FROM ai_reviews
                WHERE conversation_id = ?
                """
            results = self.db_manager.execute_query(query, (conversation_id,))

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
        """メールの内容を取得"""
        if self.db_manager is None:
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
                    conversation_id
                FROM mail_items
                WHERE entry_id = ?
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

            # フラグ状態
            mail["flagged"] = False

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
            if mail.get("conversation_id"):
                mail["ai_review"] = self.get_ai_review_for_conversation(
                    mail["conversation_id"]
                )

            return mail
        except Exception as e:
            logging.error(f"メール内容取得エラー: {e}")
            return None

    def mark_as_read(self, entry_id: str) -> bool:
        """メールを既読にする"""
        if self.db_manager is None:
            return False

        try:
            query = """
                UPDATE mail_items
                SET unread = 0
                WHERE entry_id = ?
                """
            self.db_manager.execute_update(query, (entry_id,))
            return True
        except Exception as e:
            logging.error(f"既読設定エラー: {e}")
            return False

    def get_all_mails(self) -> List[Dict]:
        """すべてのメールを取得"""
        if self.db_manager is None:
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
                    conversation_id
                FROM mail_items
                ORDER BY sent_time DESC
                """
            results = self.db_manager.execute_query(query)

            # データがなければ空リストを返す
            if not results:
                return []

            # 会話IDをキーにしてAIレビュー結果をまとめて取得
            conversation_ids = set()
            for mail in results:
                if mail.get("conversation_id"):
                    conversation_ids.add(mail["conversation_id"])

            ai_reviews = {}
            if conversation_ids:
                placeholders = ", ".join(["?"] * len(conversation_ids))
                ai_review_query = f"""
                    SELECT conversation_id, result
                    FROM ai_reviews
                    WHERE conversation_id IN ({placeholders})
                    """
                ai_review_results = self.db_manager.execute_query(
                    ai_review_query, tuple(conversation_ids)
                )

                for review in ai_review_results:
                    conv_id = review.get("conversation_id")
                    result = review.get("result")
                    if conv_id and result:
                        try:
                            if isinstance(result, str):
                                ai_reviews[conv_id] = json.loads(result)
                            else:
                                ai_reviews[conv_id] = result
                        except json.JSONDecodeError:
                            logging.warning(
                                f"AIレビュー結果のJSON解析エラー: {conv_id}"
                            )

            # 結果を整形
            formatted_mails = []
            for mail in results:
                # 送信者と受信者情報を取得
                participant_info = self._get_mail_participants(mail["id"])
                mail["sender"] = participant_info["sender"]
                mail["recipient"] = participant_info["recipient"]

                # フラグ状態
                mail["flagged"] = False

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

                # AIレビュー結果を設定
                if (
                    mail.get("conversation_id")
                    and mail["conversation_id"] in ai_reviews
                ):
                    mail["ai_review"] = ai_reviews[mail["conversation_id"]]

                formatted_mails.append(mail)

            return formatted_mails
        except Exception as e:
            logging.error(f"すべてのメール取得エラー: {e}")
            return []

    def close(self):
        """データベース接続を閉じる"""
        if self.db_manager:
            self.db_manager.disconnect()

        # 一時DBファイルを削除
        try:
            if os.path.exists(self.preview_db_path):
                os.remove(self.preview_db_path)
        except Exception as e:
            logging.warning(f"一時DBファイル削除エラー: {str(e)}")

    def download_attachment(self, file_id: str) -> bool:
        """添付ファイルをダウンロード

        Args:
            file_id: 添付ファイルのID

        Returns:
            bool: ダウンロードが成功したかどうか
        """
        if self.db_manager is None:
            logging.error("データベース接続がありません")
            return False

        try:
            logging.info(
                f"===== 添付ファイルダウンロード開始 - ファイルID: {file_id} ====="
            )
            logging.info(f"タスクID: {self.task_id}")

            # 添付ファイル情報を取得
            query = """
                SELECT a.id, a.name, a.path, a.mail_id
                FROM attachments a
                WHERE a.id = ?
                """
            logging.info(f"クエリ実行: {query} - パラメータ: {file_id}")
            results = self.db_manager.execute_query(query, (file_id,))
            logging.info(f"クエリ結果: {results}")

            if not results:
                logging.error(f"添付ファイルが見つかりません: {file_id}")
                return False

            attachment = results[0]
            source_path = attachment.get("path")
            mail_id = attachment.get("mail_id")
            file_name = attachment.get("name")

            logging.info(f"取得した添付ファイル情報:")
            logging.info(f"  ID: {attachment.get('id')}")
            logging.info(f"  名前: {file_name}")
            logging.info(f"  パス: {source_path}")
            logging.info(f"  メールID: {mail_id}")

            # ソースパスの検証
            if not source_path:
                logging.error(f"添付ファイルのパスが設定されていません: {file_id}")
                return False

            if not os.path.exists(source_path):
                logging.error(f"添付ファイルのパスが無効です: {source_path}")
                # ファイルの存在確認
                if os.path.isdir(os.path.dirname(source_path)):
                    logging.info(
                        f"ディレクトリは存在します: {os.path.dirname(source_path)}"
                    )
                    dir_contents = os.listdir(os.path.dirname(source_path))
                    logging.info(f"ディレクトリ内容: {dir_contents}")
                else:
                    logging.error(
                        f"ディレクトリが存在しません: {os.path.dirname(source_path)}"
                    )
                return False

            if not mail_id:
                logging.error(
                    f"添付ファイルに関連するメールIDが見つかりません: {file_id}"
                )
                return False

            # ダウンロード先ディレクトリを作成
            import shutil
            from pathlib import Path

            # 指定されたディレクトリ構造に保存
            download_dir = os.path.join("data", "tasks", self.task_id, mail_id)
            downloads_path = Path(download_dir)
            logging.info(f"保存先ディレクトリ: {download_dir}")
            logging.info(f"絶対パス: {os.path.abspath(download_dir)}")

            # ダウンロードディレクトリの存在確認、なければ作成
            try:
                if not downloads_path.exists():
                    os.makedirs(download_dir, exist_ok=True)
                    logging.info(
                        f"ダウンロードディレクトリを作成しました: {download_dir}"
                    )
                else:
                    logging.info(
                        f"ダウンロードディレクトリは既に存在します: {download_dir}"
                    )

                # ディレクトリの権限を確認
                logging.info(
                    f"ディレクトリの権限: {oct(os.stat(download_dir).st_mode)[-3:]}"
                )
            except Exception as e:
                logging.error(f"ディレクトリ作成エラー: {str(e)}")
                return False

            # ファイル名を取得
            target_path = os.path.join(download_dir, file_name)
            logging.info(f"保存先ファイルパス: {target_path}")

            # ファイルが既に存在する場合は別名で保存
            try:
                if os.path.exists(target_path):
                    base_name, ext = os.path.splitext(file_name)
                    counter = 1
                    while os.path.exists(target_path):
                        new_file_name = f"{base_name}_{counter}{ext}"
                        target_path = os.path.join(download_dir, new_file_name)
                        counter += 1
                    logging.info(
                        f"ファイル名競合回避: {file_name} -> {os.path.basename(target_path)}"
                    )
            except Exception as e:
                logging.error(f"ファイル名競合処理エラー: {str(e)}")
                return False

            # ファイルをコピー
            try:
                logging.info(f"ファイルコピー開始: {source_path} -> {target_path}")
                shutil.copy2(source_path, target_path)
                logging.info(f"ファイルコピー完了")
            except Exception as e:
                logging.error(f"ファイルコピーエラー: {str(e)}")
                return False

            # コピー成功を確認
            if os.path.exists(target_path):
                file_size = os.path.getsize(target_path)
                logging.info(
                    f"添付ファイルをダウンロードしました: {target_path} (サイズ: {file_size} バイト)"
                )

                # 保存したパスをDBに更新
                try:
                    update_query = """
                        UPDATE attachments
                        SET path = ?
                        WHERE id = ?
                    """
                    logging.info(
                        f"DB更新クエリ: {update_query} - パラメータ: {target_path}, {file_id}"
                    )
                    self.db_manager.execute_update(update_query, (target_path, file_id))
                    logging.info(
                        f"添付ファイルの保存パスをDBに更新しました: {target_path}"
                    )
                except Exception as e:
                    logging.error(f"DB更新エラー: {str(e)}")
                    return False

                logging.info(
                    f"===== 添付ファイルダウンロード完了 - ファイルID: {file_id} ====="
                )
                return True
            else:
                logging.error(
                    f"添付ファイルのコピーに失敗しました: {source_path} -> {target_path}"
                )
                return False

        except Exception as e:
            import traceback

            logging.error(f"添付ファイルのダウンロードに失敗: {str(e)}")
            logging.error(traceback.format_exc())
            return False
