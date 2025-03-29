"""
メール処理フローを管理するクラス

責務:
- メールと関連情報（添付ファイル、参加者など）の処理
- チャンク単位での一括処理
- 処理結果の返却
"""

from typing import Any, Dict, List, Tuple

from src.core.logger import get_logger
from src.models.outlook.outlook_item_model import OutlookItemModel
from src.util.object_util import get_safe


class MailProcessingManager:
    """メール処理フローを管理するクラス"""

    def __init__(self, outlook_model: OutlookItemModel):
        self.outlook_model = outlook_model
        self.logger = get_logger()

    def process_chunk(
        self, chunk: List[Dict[str, Any]], db_connection
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        チャンク単位でメールと関連情報を処理する

        Args:
            chunk: 処理するメールアイテムのリスト
            db_connection: データベース接続

        Returns:
            Tuple[bool, List[Dict[str, Any]]]: (処理成功フラグ, 処理結果のリスト)
        """
        try:
            results = []
            for item in chunk:
                # 1. メール情報の処理
                mail_id = self._process_mail_info(db_connection, item)
                if not mail_id:
                    continue

                # 2. 添付ファイルの処理
                attachment_results = []
                if item.get("HasAttachments"):
                    attachment_results = self._process_attachments(mail_id, item)

                # 3. 参加者情報の処理
                participant_results = self._process_participants(mail_id, item)

                # 4. 処理結果の集約
                results.append(
                    {
                        "mail_id": mail_id,
                        "mail_info": {
                            "subject": get_safe(item, "Subject"),
                            "received_time": get_safe(item, "ReceivedTime"),
                            "sender_name": get_safe(item, "SenderName"),
                            "unread": get_safe(item, "UnRead", False),
                            "has_attachments": get_safe(item, "HasAttachments", False),
                            "size": get_safe(item, "Size", 0),
                            "categories": get_safe(item, "Categories", ""),
                        },
                        "attachments": attachment_results,
                        "participants": participant_results,
                    }
                )

            return True, results

        except Exception as e:
            self.logger.error(f"チャンク処理エラー: {e}")
            return False, []

    def _process_mail_info(self, conn, item: Dict[str, Any]) -> str:
        """
        メール情報の処理

        Args:
            conn: データベース接続
            item: メールアイテム

        Returns:
            str: メールID
        """
        try:
            mail_id = get_safe(item, "EntryID")
            if not mail_id:
                return None

            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO mail_items (
                    entry_id, subject, received_time, sender_name,
                    unread, has_attachments, size, categories
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mail_id,
                    get_safe(item, "Subject"),
                    get_safe(item, "ReceivedTime"),
                    get_safe(item, "SenderName"),
                    get_safe(item, "UnRead", False),
                    get_safe(item, "HasAttachments", False),
                    get_safe(item, "Size", 0),
                    get_safe(item, "Categories", ""),
                ),
            )

            return mail_id

        except Exception as e:
            self.logger.error(f"メール情報処理エラー: {e}")
            return None

    def _process_attachments(
        self, mail_id: str, item: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        添付ファイルの処理

        Args:
            mail_id: メールID
            item: メールアイテム

        Returns:
            List[Dict[str, Any]]: 処理結果のリスト
        """
        try:
            attachments = self.outlook_model.get_attachments(mail_id)
            results = []

            for attachment in attachments:
                # 添付ファイルの保存
                if self.outlook_model.save_attachment(attachment, "data/attachments"):
                    results.append(
                        {
                            "file_name": get_safe(attachment, "FileName"),
                            "file_size": get_safe(attachment, "Size"),
                            "file_path": get_safe(attachment, "FilePath"),
                        }
                    )
                else:
                    self.logger.warning(
                        f"添付ファイルの保存に失敗: {get_safe(attachment, 'FileName')}"
                    )

            return results

        except Exception as e:
            self.logger.error(f"添付ファイル処理エラー: {e}")
            return []

    def _process_participants(
        self, mail_id: str, item: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        参加者情報の処理

        Args:
            mail_id: メールID
            item: メールアイテム

        Returns:
            List[Dict[str, Any]]: 処理結果のリスト
        """
        try:
            participants = self.outlook_model.get_participants(mail_id)
            return [
                {
                    "email_address": get_safe(participant, "EmailAddress"),
                    "display_name": get_safe(participant, "DisplayName"),
                    "participant_type": get_safe(participant, "Type"),
                }
                for participant in participants
            ]

        except Exception as e:
            self.logger.error(f"参加者情報処理エラー: {e}")
            return []
