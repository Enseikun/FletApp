# Outlookアカウント・フォルダ管理モデル

from datetime import datetime
from typing import Any

from win32com.client import CDispatch

from src.core.database import DatabaseManager
from src.models.outlook.outlook_base_model import OutlookBaseModel


class OutlookAccountModel(OutlookBaseModel):
    """
    Outlookアカウント・フォルダ管理モデル
    data/outlook.dbと連携
    """

    def __init__(self):
        super().__init__()
        self.db = DatabaseManager("data/outlook.db")

    def get_safe(
        self, obj: CDispatch, property_name: str, default_value: any = None
    ) -> any:
        """
        Outlookオブジェクトのプロパティを安全に取得する

        Args:
            obj (CDispatch): Outlookオブジェクト
            property_name (str): 取得するプロパティ名
            default_value (any, optional): プロパティが存在しない場合のデフォルト値. Defaults to None.

        Returns:
            any: プロパティの値。存在しない場合はデフォルト値
        """
        try:
            if not hasattr(obj, property_name):
                return default_value

            value = getattr(obj, property_name)
            return value if value is not None else default_value
        except Exception as e:
            self.logger.warning(
                f"プロパティ '{property_name}' の取得に失敗しました: {str(e)}"
            )
            return default_value

    # MARK: - Private Methods
    def _get_timestamp(self) -> str:
        """SQLiteのタイムスタンプ形式に準拠した現在時刻を返す

        Returns:
            str: YYYY-MM-DD HH:MM:SS形式のタイムスタンプ
        """
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _save_folder(
        self,
        account_id: str,
        folder,
    ) -> None:
        """
        単一のフォルダ情報をデータベースに保存する

        Args:
            account_id: アカウントID
            folder: フォルダオブジェクト
        """
        # ログ用の情報を初期化
        folder_info = {
            "account_id": account_id,
            "folder_id": "unknown",
            "folder_name": "unknown",
            "folder_path": "unknown",
            "parent_folder_id": None,
        }

        try:
            folder_id = self.get_safe(folder, "EntryID")
            current_time = self._get_timestamp()

            # 親フォルダIDを取得
            parent_folder_id = None
            parent = self.get_safe(folder, "Parent")
            if parent:
                parent_folder_id = self.get_safe(parent, "EntryID")

            # フォルダ名とパスを取得
            folder_name = self.get_safe(folder, "Name", "unknown")
            folder_path = self.get_safe(folder, "FolderPath", "\\" + folder_name)
            item_count = self.get_safe(folder, "Items", {}).Count
            unread_count = self.get_safe(folder, "UnReadItemCount", 0)

            # ログ用の情報を更新
            folder_info.update(
                {
                    "folder_id": folder_id,
                    "folder_name": folder_name,
                    "folder_path": folder_path,
                    "parent_folder_id": parent_folder_id,
                    "item_count": item_count,
                    "unread_count": unread_count,
                }
            )

            # フォルダが既に存在するか確認
            existing = self.db.execute_query(
                "SELECT entry_id FROM folders WHERE store_id = ? AND entry_id = ?",
                (account_id, folder_id),
            )

            if existing:
                # 既存のフォルダを更新
                self.db.execute_update(
                    """
                    UPDATE folders 
                    SET name = ?, path = ?, parent_folder_id = ?, item_count = ?, unread_count = ?, last_sync = ?, updated_at = ?
                    WHERE store_id = ? AND entry_id = ?
                    """,
                    (
                        folder_name,
                        folder_path,
                        parent_folder_id,
                        item_count,
                        unread_count,
                        current_time,
                        current_time,
                        account_id,
                        folder_id,
                    ),
                )
            else:
                # 新しいフォルダを挿入
                self.db.execute_update(
                    """
                    INSERT INTO folders 
                    (entry_id, store_id, name, path, parent_folder_id, item_count, unread_count, last_sync, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        folder_id,
                        account_id,
                        folder_name,
                        folder_path,
                        parent_folder_id,
                        item_count,
                        unread_count,
                        current_time,
                        current_time,
                        current_time,
                    ),
                )
        except Exception as e:
            # エラー情報を文字列に変換して記録
            error_info = {
                "error": str(e),
                "folder_info": folder_info,
            }
            self.logger.error(f"フォルダの保存に失敗しました: {error_info}")
            raise

    def _save_subfolders_recursively(self, account_id: str, parent_folder) -> None:
        """
        サブフォルダを再帰的に保存する

        Args:
            account_id: アカウントID
            parent_folder: 親フォルダオブジェクト
        """
        try:
            subfolders = self._service.get_folders(parent_folder)
            # EntryIDを持つフォルダのみをフィルタリング
            valid_subfolders = [
                folder for folder in subfolders if self.get_safe(folder, "EntryID")
            ]
            for subfolder in valid_subfolders:
                self._save_folder(account_id, subfolder)
                # さらに深い階層のフォルダも保存
                self._save_subfolders_recursively(account_id, subfolder)
        except Exception as e:
            self.logger.error(f"サブフォルダの再帰的保存に失敗しました: {str(e)}")

    # MARK: - Account Methods
    def get_account(self) -> CDispatch:
        """Outlookのデフォルトアカウントを取得する"""
        return self._service.get_account()

    def save_account(self, account: CDispatch) -> bool:
        """アカウント情報をデータベースに保存する

        Args:
            account: Outlookアカウントオブジェクト

        Returns:
            bool: 保存が成功した場合はTrue
        """
        try:
            current_time = self._get_timestamp()

            # StoreIDを主キーとして使用
            delivery_store = self.get_safe(account, "DeliveryStore")
            store_id = self.get_safe(delivery_store, "StoreID")

            # ログ用のアカウント情報を作成（文字列値のみ）
            account_info = {
                "store_id": store_id,
                "display_name": self.get_safe(account, "DisplayName"),
                "email_address": self.get_safe(account, "SmtpAddress"),
            }

            self.logger.info(f"アカウント情報を保存します: {account_info}")

            existing = self.db.execute_query(
                "SELECT store_id FROM accounts WHERE store_id = ?",
                (store_id,),
            )

            if existing:
                # 既存のアカウントを更新
                self.db.execute_update(
                    """
                    UPDATE accounts 
                    SET displayname = ?, email_address = ?, last_sync = ?, updated_at = ?
                    WHERE store_id = ?
                    """,
                    (
                        self.get_safe(account, "DisplayName"),
                        self.get_safe(account, "SmtpAddress"),
                        current_time,
                        current_time,
                        store_id,
                    ),
                )
            else:
                # 新しいアカウントを挿入
                self.db.execute_update(
                    """
                    INSERT INTO accounts 
                    (store_id, displayname, email_address, last_sync, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        store_id,
                        self.get_safe(account, "DisplayName"),
                        self.get_safe(account, "SmtpAddress"),
                        current_time,
                        current_time,
                        current_time,
                    ),
                )

            self.logger.info(f"アカウント情報を保存しました: {account_info}")
            return True
        except Exception as e:
            self.logger.error(f"アカウント情報の保存に失敗しました: {str(e)}")
            return False

    # MARK: - Folder Methods
    def get_root_folders(self) -> list:
        """現在のアカウントのルートフォルダを取得する"""
        self.logger.info("アカウントのルートフォルダを取得します")
        try:
            # 現在のアカウントを取得
            account = self._service.get_account()
            root_folders = self._service.get_root_folders()

            if not root_folders:
                self.logger.error("ルートフォルダの取得に失敗しました")
                return False

            # アカウントに紐づくフォルダのみをフィルタリング
            folder_list = [
                folder
                for folder in root_folders
                if self.get_safe(folder, "EntryID")  # EntryIDの存在のみをチェック
            ]

            if not folder_list:
                self.logger.error("アカウントに紐づくフォルダが見つかりませんでした")
                return False

            # ログ用のフォルダ名リストを作成（文字列値のみ）
            folder_names = [self.get_safe(f, "Name", "unknown") for f in folder_list]
            self.logger.info(
                f"アカウントのルートフォルダを取得しました: {folder_names}"
            )
            return folder_list
        except Exception as e:
            self.logger.error(
                f"アカウントのルートフォルダの取得に失敗しました: {str(e)}"
            )
            raise

    def save_folders_to_db(
        self,
        account_id: str,
        folder_id: str,
    ) -> bool:
        """
        指定したフォルダID以下のすべてのフォルダ情報をデータベースに保存する

        Args:
            account_id: アカウントID
            folder_id: フォルダID

        Returns:
            保存が成功した場合はTrue
        """
        # ログ用の情報を作成
        log_info = {"account_id": account_id, "folder_id": folder_id}
        self.logger.info(f"フォルダ情報をデータベースに保存します: {log_info}")

        try:
            # フォルダを取得
            folder = self._service.get_folder_by_id(folder_id)
            if not folder:
                self.logger.error(
                    f"指定されたフォルダが見つかりませんでした: {folder_id}"
                )
                return False

            # フォルダ情報をデータベースに保存
            self._save_folder(account_id, folder)

            # サブフォルダを取得して再帰的に保存
            subfolders = self._service.get_folders(folder)
            # EntryIDを持つフォルダのみをフィルタリング
            valid_subfolders = [
                subfolder for subfolder in subfolders if hasattr(subfolder, "EntryID")
            ]
            for subfolder in valid_subfolders:
                self._save_folder(account_id, subfolder)
                self._save_subfolders_recursively(account_id, subfolder)

            self.logger.info(f"フォルダ情報をデータベースに保存しました: {log_info}")
            return True
        except Exception as e:
            self.logger.error(f"フォルダ情報のデータベース保存に失敗しました: {str(e)}")
            return False

    def save_account_folders(self) -> bool:
        """
        現在ログインしているアカウントのすべてのフォルダ情報をデータベースに保存する

        Returns:
            bool: 保存が成功した場合はTrue
        """
        self.logger.info("アカウントのフォルダ情報をデータベースに保存します")
        try:
            # 現在のアカウントを取得
            account = self._service.get_account()
            if not account:
                self.logger.error("アカウントの取得に失敗しました")
                return False

            # アカウント情報を保存
            if not self.save_account(account):
                self.logger.error("アカウント情報の保存に失敗しました")
                return False

            account_id = self.get_safe(
                self.get_safe(account, "DeliveryStore"), "StoreID"
            )

            # アカウントのルートフォルダを取得
            root_folders = self._service.get_root_folders()
            if not root_folders:
                self.logger.error("ルートフォルダの取得に失敗しました")
                return False

            # アカウントに紐づくフォルダのみをフィルタリング
            folder_list = [
                folder
                for folder in root_folders
                if self.get_safe(folder, "EntryID")  # EntryIDの存在のみをチェック
            ]

            if not folder_list:
                self.logger.error("アカウントに紐づくフォルダが見つかりませんでした")
                return False

            # 各フォルダとそのサブフォルダを保存
            for folder in folder_list:
                try:
                    self._save_folder(account_id, folder)
                    self._save_subfolders_recursively(account_id, folder)
                except Exception as e:
                    self.logger.error(
                        f"フォルダの保存中にエラーが発生しました: {str(e)}"
                    )
                    continue

            self.logger.info(
                f"アカウントのフォルダ情報をデータベースに保存しました: account_id={account_id}"
            )
            return True
        except Exception as e:
            self.logger.error(
                f"アカウントのフォルダ情報のデータベース保存に失敗しました: {e}"
            )
            return False

    def get_folder_paths(self) -> list[str]:
        """
        データベースに保存されているすべてのフォルダパスを取得する

        Returns:
            list[str]: フォルダパスのリスト
        """
        try:
            # フォルダパスを取得するクエリを実行
            query = "SELECT path FROM folders ORDER BY path"
            results = self.db.execute_query(query)

            # パスのみをリストに抽出
            paths = [row["path"] for row in results]

            self.logger.info(f"フォルダパスを取得しました: {len(paths)}件")
            return paths
        except Exception as e:
            self.logger.error(f"フォルダパスの取得に失敗しました: {str(e)}")
            return []

    def get_folder_info(self) -> list[dict[str, Any]]:
        """
        データベースに保存されているすべてのフォルダ情報を取得する

        Returns:
            list[dict[str, Any]]: フォルダ情報のリスト
        """
        try:
            # フォルダ情報を取得するクエリを実行
            query = """
            SELECT 
                entry_id,
                store_id,
                name,
                path,
                item_count,
                unread_count,
                parent_folder_id
            FROM folders 
            ORDER BY path
            """
            results = self.db.execute_query(query)

            self.logger.info(f"フォルダ情報を取得しました: {len(results)}件")
            return results
        except Exception as e:
            self.logger.error(f"フォルダ情報の取得に失敗しました: {str(e)}")
            return []
