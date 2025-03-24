# Outlookアカウント・フォルダ管理モデル

from datetime import datetime

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

    # MARK: Account
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
            store_id = account.DeliveryStore.StoreID

            # ログ用のアカウント情報を作成
            account_info = {
                "store_id": store_id,
                "display_name": account.DisplayName,
                "email_address": account.SmtpAddress,
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
                    SET displayname = ?, email_address = ?, last_sync = ?
                    WHERE store_id = ?
                    """,
                    (account.DisplayName, account.SmtpAddress, current_time, store_id),
                )
            else:
                # 新しいアカウントを挿入
                self.db.execute_update(
                    """
                    INSERT INTO accounts 
                    (store_id, displayname, email_address, last_sync)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        store_id,
                        account.DisplayName,
                        account.SmtpAddress,
                        current_time,
                    ),
                )

            self.logger.info(f"アカウント情報を保存しました: {account_info}")
            return True
        except Exception as e:
            self.logger.error(f"アカウント情報の保存に失敗しました: {str(e)}")
            return False

    # MARK: Folder
    def get_root_folders(self) -> list:
        """現在のアカウントのルートフォルダを取得する"""
        self.logger.info("アカウントのルートフォルダを取得します")
        try:
            # 現在のアカウントを取得
            account = self._service.get_account()
            root_folders = self._service.get_root_folders()

            # アカウントに紐づくフォルダのみをフィルタリング
            folder_list = [
                folder
                for folder in root_folders
                if hasattr(folder, "Store")
                and folder.Store.ExchangeStoreType
                == account.DeliveryStore.ExchangeStoreType
            ]

            # ログ用のフォルダ名リストを作成
            folder_names = (
                [f.Name for f in folder_list]
                if hasattr(folder_list[0], "Name")
                else ["unknown"]
            )
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
            for subfolder in subfolders:
                self._save_folder(account_id, subfolder)
                self._save_subfolders_recursively(account_id, subfolder)

            self.logger.info(f"フォルダ情報をデータベースに保存しました: {log_info}")
            return True
        except Exception as e:
            self.logger.error(f"フォルダ情報のデータベース保存に失敗しました: {str(e)}")
            return False

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
            folder_id = folder.EntryID
            current_time = self._get_timestamp()

            # 親フォルダIDを取得
            parent_folder_id = None
            if hasattr(folder, "Parent") and folder.Parent:
                parent_folder_id = folder.Parent.EntryID

            # フォルダ名とパスを取得
            folder_name = folder.Name if hasattr(folder, "Name") else "unknown"
            folder_path = (
                folder.FolderPath
                if hasattr(folder, "FolderPath")
                else "\\" + folder_name
            )

            # ログ用の情報を更新
            folder_info.update(
                {
                    "folder_id": folder_id,
                    "folder_name": folder_name,
                    "folder_path": folder_path,
                    "parent_folder_id": parent_folder_id,
                }
            )

            # フォルダが既に存在するか確認
            existing = self.db.execute_query(
                "SELECT id FROM outlook_folders WHERE account_id = ? AND folder_id = ?",
                (account_id, folder_id),
            )

            if existing:
                # 既存のフォルダを更新
                self.db.execute_update(
                    """
                    UPDATE outlook_folders 
                    SET name = ?, folder_path = ?, parent_folder_id = ?, last_sync = ?
                    WHERE account_id = ? AND folder_id = ?
                    """,
                    (
                        folder_name,
                        folder_path,
                        parent_folder_id,
                        current_time,
                        account_id,
                        folder_id,
                    ),
                )
            else:
                # 新しいフォルダを挿入
                self.db.execute_update(
                    """
                    INSERT INTO outlook_folders 
                    (account_id, folder_id, parent_folder_id, name, folder_path, last_sync, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        account_id,
                        folder_id,
                        parent_folder_id,
                        folder_name,
                        folder_path,
                        current_time,
                        current_time,
                    ),
                )
        except Exception as e:
            self.logger.error(
                f"フォルダの保存に失敗しました: {str(e)}, folder_info={folder_info}"
            )
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
            for subfolder in subfolders:
                self._save_folder(account_id, subfolder)
                # さらに深い階層のフォルダも保存
                self._save_subfolders_recursively(account_id, subfolder)
        except Exception as e:
            self.logger.error(f"サブフォルダの再帰的保存に失敗しました: {e}")

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
            account_id = account.DeliveryStore.StoreID

            # アカウントのルートフォルダを取得
            root_folders = self._service.get_root_folders()

            # アカウントに紐づくフォルダのみをフィルタリング
            folder_list = [
                folder
                for folder in root_folders
                if hasattr(folder, "Store")
                and folder.Store.ExchangeStoreType
                == account.DeliveryStore.ExchangeStoreType
            ]

            # 各フォルダとそのサブフォルダを保存
            for folder in folder_list:
                self._save_folder(account_id, folder)
                self._save_subfolders_recursively(account_id, folder)

            self.logger.info(
                f"アカウントのフォルダ情報をデータベースに保存しました: account_id={account_id}"
            )
            return True
        except Exception as e:
            self.logger.error(
                f"アカウントのフォルダ情報のデータベース保存に失敗しました: {e}"
            )
            return False

    def _get_timestamp(self) -> str:
        """SQLiteのタイムスタンプ形式に準拠した現在時刻を返す

        Returns:
            str: YYYY-MM-DD HH:MM:SS形式のタイムスタンプ
        """
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
