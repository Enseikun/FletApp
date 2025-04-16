"""
Outlookメールアイテム管理モデル

責務:
- メールアイテムのデータ取得
- 添付ファイルの取得と保存
- 参加者情報の取得
- メールアイテムの基本的な操作

主なメソッド:
- get_mail_items: メールアイテムの取得
- get_attachments: 添付ファイル情報の取得
- save_attachment: 添付ファイルの保存
- get_participants: 参加者情報の取得
"""

from typing import Any, Dict, Generator, List, Optional

from src.models.outlook.outlook_base_model import OutlookBaseModel
from src.models.outlook.outlook_service import OutlookService
from src.util.object_util import debug_print_mail_item, get_safe


class OutlookItemModel(OutlookBaseModel):
    """Outlookメールアイテム管理モデル"""

    def __init__(self):
        super().__init__()
        self.service = OutlookService()
        self._chunk_size = None  # 計算済みのチャンクサイズを保持

    def get_mail_items(
        self,
        folder_id: str,
        filter_criteria: Optional[str] = None,
        chunk_size: Optional[int] = None,
    ) -> Generator[List[Dict[str, Any]], None, None]:
        """
        指定したフォルダのメールアイテムを取得する

        Args:
            folder_id: フォルダID
            filter_criteria: フィルタ条件
            chunk_size: バッチ処理のチャンクサイズ（指定がない場合は自動計算）

        Yields:
            List[Dict[str, Any]]: メールアイテムのリスト（チャンク単位）
        """
        # チャンクサイズの決定
        if chunk_size is None:
            if self._chunk_size is None:
                # self._chunk_size = self._calculate_chunk_size()
                self._chunk_size = 20
            chunk_size = self._chunk_size

        self.logger.info(
            "メールアイテムを取得します",
            folder_id=folder_id,
            filter_criteria=filter_criteria,
            chunk_size=chunk_size,
        )

        try:
            folder = self.service.get_folder_by_id(folder_id)
            if not folder:
                self.logger.error(f"フォルダが見つかりません: {folder_id}")
                return

            # フォルダ内のメールアイテムを取得
            mail_items = folder.Items
            if filter_criteria:
                mail_items = mail_items.Restrict(filter_criteria)

            # メールアイテムをチャンクごとに処理
            current_chunk = []
            total_processed = 0

            for item in mail_items:
                mail_data = {
                    "EntryID": get_safe(item, "EntryID"),
                    "Subject": get_safe(item, "Subject"),
                    "ReceivedTime": get_safe(item, "ReceivedTime"),
                    "SenderName": get_safe(item, "SenderName"),
                    "UnRead": get_safe(item, "UnRead", False),
                    "HasAttachments": get_safe(item, "HasAttachments", False),
                    "Size": get_safe(item, "Size", 0),
                    "Categories": get_safe(item, "Categories", ""),
                }
                current_chunk.append(mail_data)

                # チャンクサイズに達したらyield
                if len(current_chunk) >= chunk_size:
                    total_processed += len(current_chunk)
                    self.logger.info(
                        f"チャンクを取得しました: {len(current_chunk)}件 (合計: {total_processed}件)"
                    )
                    yield current_chunk
                    current_chunk = []

            # 残りのアイテムをyield
            if current_chunk:
                total_processed += len(current_chunk)
                self.logger.info(
                    f"最後のチャンクを取得しました: {len(current_chunk)}件 (合計: {total_processed}件)"
                )
                yield current_chunk

            self.logger.info(f"メールアイテムの取得が完了しました: {total_processed}件")

        except Exception as e:
            self.logger.error(f"メールアイテムの取得に失敗しました: {e}")
            return

    def get_attachments(self, mail_id: str) -> List[Dict[str, Any]]:
        """
        指定したメールの添付ファイル情報を取得する

        Args:
            mail_id: メールID

        Returns:
            List[Dict[str, Any]]: 添付ファイル情報のリスト
        """
        try:
            mail_item = self.service.get_mail_by_id(mail_id)
            if not mail_item:
                return []

            attachments = []
            for attachment in mail_item.Attachments:
                attachment_info = {
                    "FileName": get_safe(attachment, "FileName"),
                    "Size": get_safe(attachment, "Size"),
                    "FilePath": None,  # 保存時に設定
                }
                attachments.append(attachment_info)

            return attachments

        except Exception as e:
            self.logger.error(f"添付ファイル情報の取得に失敗しました: {e}")
            return []

    def save_attachment(self, attachment: Dict[str, Any], save_path: str) -> bool:
        """
        添付ファイルを保存する

        Args:
            attachment: 添付ファイル情報
            save_path: 保存先パス

        Returns:
            bool: 保存が成功したかどうか
        """
        try:
            mail_item = self.service.get_mail_by_id(attachment["MailID"])
            if not mail_item:
                return False

            for outlook_attachment in mail_item.Attachments:
                if outlook_attachment.FileName == attachment["FileName"]:
                    file_path = f"{save_path}/{attachment['FileName']}"
                    outlook_attachment.SaveAsFile(file_path)
                    attachment["FilePath"] = file_path
                    return True

            return False

        except Exception as e:
            self.logger.error(f"添付ファイルの保存に失敗しました: {e}")
            return False

    def get_participants(self, mail_id: str) -> List[Dict[str, Any]]:
        """
        指定したメールの参加者情報を取得する

        Args:
            mail_id: メールID

        Returns:
            List[Dict[str, Any]]: 参加者情報のリスト
        """
        try:
            mail_item = self.service.get_mail_by_id(mail_id)
            if not mail_item:
                return []

            participants = []

            # 送信者
            if mail_item.Sender:
                participants.append(
                    {
                        "EmailAddress": get_safe(mail_item.Sender, "Address"),
                        "DisplayName": get_safe(mail_item.Sender, "Name"),
                        "Type": "sender",
                    }
                )

            # 受信者
            for recipient in mail_item.Recipients:
                participants.append(
                    {
                        "EmailAddress": get_safe(recipient, "Address"),
                        "DisplayName": get_safe(recipient, "Name"),
                        "Type": "recipient",
                    }
                )

            return participants

        except Exception as e:
            self.logger.error(f"参加者情報の取得に失敗しました: {e}")
            return []

    def _calculate_chunk_size(self) -> int:
        """
        システムリソースとメールデータの特性に基づいて最適なチャンクサイズを計算する

        Returns:
            int: 計算されたチャンクサイズ
        """
        try:
            import sys

            import psutil

            # システムリソースの取得
            available_memory = psutil.virtual_memory().available  # バイト単位
            cpu_count = psutil.cpu_count()

            # メールデータの推定サイズ（バイト単位）
            # ヘッダー情報: 2KB, 本文: 20KB, 添付ファイル情報: 1KB
            MAIL_DATA_SIZE = 23 * 1024  # 23KB

            # 安全係数（メモリ使用率の制限）
            SAFETY_FACTOR = 0.3  # 利用可能メモリの30%まで使用

            # データベースのバッファサイズ（経験則）
            DB_BUFFER_SIZE = 10 * 1024 * 1024  # 10MB

            # 最小・最大チャンクサイズ
            MIN_CHUNK_SIZE = 50
            MAX_CHUNK_SIZE = 1000

            # メモリ量に応じて安全係数とバッファサイズを調整
            memory_gb = available_memory / (1024 * 1024 * 1024)  # GBに変換
            if memory_gb < 2:  # 2GB未満の場合
                SAFETY_FACTOR = 0.1  # 安全係数を下げる
                DB_BUFFER_SIZE = 2 * 1024 * 1024  # バッファサイズを2MBに下げる
            elif memory_gb < 4:  # 4GB未満の場合
                SAFETY_FACTOR = 0.2  # 安全係数を少し下げる
                DB_BUFFER_SIZE = 5 * 1024 * 1024  # バッファサイズを5MBに下げる

            memory_based_size = int(
                (available_memory * SAFETY_FACTOR) / (MAIL_DATA_SIZE * cpu_count * 2)
            )

            # データベースバッファベースの計算
            db_based_size = int(DB_BUFFER_SIZE / MAIL_DATA_SIZE)

            # 最終的なチャンクサイズの決定
            chunk_size = min(memory_based_size, db_based_size)

            # 最小・最大値の制限を適用
            chunk_size = max(MIN_CHUNK_SIZE, min(chunk_size, MAX_CHUNK_SIZE))

            self.logger.info(
                "チャンクサイズを計算しました",
                available_memory=available_memory,
                cpu_count=cpu_count,
                calculated_size=chunk_size,
                memory_gb=memory_gb,
                safety_factor=SAFETY_FACTOR,
                db_buffer_size=DB_BUFFER_SIZE,
            )

            return chunk_size

        except Exception as e:
            self.logger.error(f"チャンクサイズの計算に失敗しました: {e}")
            # エラー時は安全なデフォルト値を返す
            return 25

    def process_attachments(
        self, mail_id: str, item: Dict[str, Any], save_path: str
    ) -> bool:
        """
        添付ファイルを処理する

        Args:
            mail_id: メールID
            item: メールアイテム
            save_path: 保存先パス

        Returns:
            bool: 処理が成功したかどうか
        """
        try:
            if not get_safe(item, "HasAttachments", False):
                self.logger.info(f"添付ファイルなし: {mail_id}")
                return True

            # ディレクトリを作成
            import os

            # 確実にフルパスが作成されていることを確認
            try:
                save_path = os.path.abspath(save_path)
                os.makedirs(save_path, exist_ok=True)
                self.logger.info(f"添付ファイル保存先ディレクトリを作成: {save_path}")
            except Exception as e:
                self.logger.error(
                    f"ディレクトリ作成エラー: {save_path}, 詳細: {str(e)}"
                )
                return False

            # メールアイテムの取得
            mail_item = self.service.get_mail_by_id(mail_id)
            if not mail_item:
                self.logger.error(f"メールアイテムの取得に失敗しました: {mail_id}")
                return False

            # 添付ファイルが実際に存在するか再確認
            try:
                attachments = mail_item.Attachments
                if not attachments or attachments.Count == 0:
                    self.logger.info(f"添付ファイルが見つかりませんでした: {mail_id}")
                    return True
            except Exception as e:
                self.logger.error(
                    f"添付ファイルの取得エラー: {mail_id}, 詳細: {str(e)}"
                )
                return False

            # 添付ファイルの総数をログに記録
            self.logger.info(
                f"添付ファイル処理開始: {mail_id}, 添付ファイル数: {attachments.Count}"
            )

            saved_count = 0
            for i in range(1, attachments.Count + 1):  # Outlookのインデックスは1始まり
                try:
                    attachment = attachments.Item(i)
                    file_name = attachment.FileName
                    self.logger.info(
                        f"添付ファイル処理中: {file_name}, インデックス: {i}/{attachments.Count}"
                    )

                    file_path = os.path.join(save_path, file_name)

                    # ファイルの上書き確認
                    if os.path.exists(file_path):
                        # 既に存在する場合は、新しいファイル名を生成
                        base_name, ext = os.path.splitext(file_name)
                        counter = 1
                        while os.path.exists(file_path):
                            new_file_name = f"{base_name}_{counter}{ext}"
                            file_path = os.path.join(save_path, new_file_name)
                            counter += 1
                        self.logger.info(
                            f"ファイル名競合回避: {file_name} -> {os.path.basename(file_path)}"
                        )

                    # 添付ファイルを保存
                    self.logger.info(f"添付ファイルを保存します: {file_path}")
                    attachment.SaveAsFile(file_path)

                    # ファイルが実際に作成されたか確認
                    if not os.path.exists(file_path):
                        self.logger.error(
                            f"添付ファイルの保存に失敗しました: {file_path} - ファイルが作成されませんでした"
                        )
                        continue

                    # ファイルサイズが0でないか確認
                    file_size = os.path.getsize(file_path)
                    if file_size == 0:
                        self.logger.warning(f"添付ファイルのサイズが0です: {file_path}")

                    saved_count += 1
                    self.logger.info(
                        f"添付ファイルを保存しました: {file_path}, サイズ: {file_size}バイト"
                    )

                except Exception as e:
                    self.logger.error(
                        f"添付ファイルの保存に失敗: {i}番目の添付ファイル, エラー: {str(e)}"
                    )
                    # 個別の添付ファイルのエラーはスキップし、次の添付ファイル処理を続行

            self.logger.info(
                f"添付ファイル処理完了: {mail_id}, {saved_count}/{attachments.Count}個のファイルを保存"
            )

            # 少なくとも1つのファイルが保存できたか、または添付ファイルが0だった場合は成功
            return saved_count > 0 or attachments.Count == 0

        except Exception as e:
            self.logger.error(
                f"添付ファイルの処理に失敗しました: {mail_id}, エラー: {str(e)}"
            )
            return False

    def save_participants(self, mail_id: str, item: Dict[str, Any]) -> bool:
        """
        参加者情報を保存する

        Args:
            mail_id: メールID
            item: メールアイテム

        Returns:
            bool: 保存が成功したかどうか
        """
        try:
            participants = self.get_participants(mail_id)
            if not participants:
                self.logger.warning(f"参加者情報が見つかりませんでした: {mail_id}")
                return True

            self.logger.info(
                f"参加者情報を取得しました: {len(participants)}件", mail_id=mail_id
            )
            return True
        except Exception as e:
            self.logger.error(f"参加者情報の保存に失敗しました: {e}")
            return False
