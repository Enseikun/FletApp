# Outlookアカウント・フォルダ管理モデル

from datetime import datetime

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
    def get_account(self) -> str:
        """デフォルトアカウントを取得する"""
        self.logger.info("デフォルトアカウントを取得します")
        try:
            account = self._service.get_account()

            # アカウントオブジェクトの検証を追加
            if not account:
                raise ValueError("アカウントオブジェクトが取得できません")

            # DisplayName属性の存在確認を追加
            if not hasattr(account, "DisplayName"):
                self.logger.error("アカウントオブジェクトにDisplayName属性がありません")
                self.logger.debug(f"利用可能なプロパティ: {dir(account)}")
                raise AttributeError("DisplayName属性が見つかりません")

            account_name = account.DisplayName
            self.logger.info(f"デフォルトアカウントを取得しました: {account_name}")
            return account_name
        except Exception as e:
            self.logger.error(f"デフォルトアカウントの取得に失敗しました: {e}")
            raise

    def get_root_folders(self) -> list[str]:
        """現在のアカウントのルートフォルダを取得する"""
        self.logger.info("アカウントのルートフォルダを取得します")
        try:
            # 現在のアカウントを取得
            account = self._service.get_account()
            root_folders = self._service.get_root_folder()

            # アカウントに紐づくフォルダのみをフィルタリング
            folder_list = [
                folder.EntryID
                for folder in root_folders
                if hasattr(folder, "Store")
                and folder.Store.ExchangeStoreType
                == account.DeliveryStore.ExchangeStoreType
            ]

            self.logger.info(f"アカウントのルートフォルダを取得しました: {folder_list}")
            return folder_list
        except Exception as e:
            self.logger.error(f"アカウントのルートフォルダの取得に失敗しました: {e}")
            raise

    def get_folders(self, folder_id: str) -> list[str]:
        """フォルダを取得する"""
        return self._service.get_folders(folder_id)

    def save_folders_to_db(
        self,
        account_id: str,
        folder_id: str,
        is_default_inbox: bool = False,
        is_default_sent: bool = False,
    ) -> bool:
        """
        指定したフォルダID以下のすべてのフォルダ情報をデータベースに保存する

        Args:
            account_id: アカウントID
            folder_id: フォルダID
            is_default_inbox: 受信トレイのデフォルトフォルダかどうか
            is_default_sent: 送信済みアイテムのデフォルトフォルダかどうか

        Returns:
            保存が成功した場合はTrue
        """
        self.logger.info(
            f"フォルダ情報をデータベースに保存します: account_id={account_id}, folder_id={folder_id}"
        )
        try:
            # フォルダを取得
            folder = self._service.get_folder_by_id(folder_id)
            if not folder:
                self.logger.error(
                    f"指定されたフォルダが見つかりませんでした: {folder_id}"
                )
                return False

            # フォルダ情報をデータベースに保存
            self._save_folder(account_id, folder, is_default_inbox, is_default_sent)

            # サブフォルダを取得して再帰的に保存
            subfolders = self._service.get_folders(folder)
            for subfolder in subfolders:
                self._save_folder(account_id, subfolder)
                # さらに深い階層のフォルダも保存
                self._save_subfolders_recursively(account_id, subfolder)

            self.logger.info(
                f"フォルダ情報をデータベースに保存しました: account_id={account_id}"
            )
            return True
        except Exception as e:
            self.logger.error(f"フォルダ情報のデータベース保存に失敗しました: {e}")
            return False

    def _save_folder(
        self,
        account_id: str,
        folder,
        is_default_inbox: bool = False,
        is_default_sent: bool = False,
    ) -> None:
        """
        単一のフォルダ情報をデータベースに保存する

        Args:
            account_id: アカウントID
            folder: フォルダオブジェクト
            is_default_inbox: 受信トレイのデフォルトフォルダかどうか
            is_default_sent: 送信済みアイテムのデフォルトフォルダかどうか
        """
        try:
            folder_id = folder.EntryID

            # フォルダが既に存在するか確認
            existing = self.db.execute_query(
                "SELECT id FROM outlook_folders WHERE account_id = ? AND folder_id = ?",
                (account_id, folder_id),
            )

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if existing:
                # 既存のフォルダを更新
                self.db.execute_update(
                    """
                    UPDATE outlook_folders 
                    SET is_default_inbox = ?, is_default_sent = ?, last_sync = ?
                    WHERE account_id = ? AND folder_id = ?
                    """,
                    (
                        is_default_inbox,
                        is_default_sent,
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
                    (account_id, folder_id, is_default_inbox, is_default_sent, last_sync)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        account_id,
                        folder_id,
                        is_default_inbox,
                        is_default_sent,
                        current_time,
                    ),
                )
        except Exception as e:
            self.logger.error(
                f"フォルダの保存に失敗しました: {e}, folder_name={folder.Name if hasattr(folder, 'Name') else 'unknown'}"
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

    def save_account_folders(self, account_id: str) -> bool:
        """
        アカウントのすべてのフォルダ情報をデータベースに保存する

        Args:
            account_id: アカウントID

        Returns:
            保存が成功した場合はTrue
        """
        self.logger.info(
            f"アカウントのフォルダ情報をデータベースに保存します: account_id={account_id}"
        )
        try:
            # アカウントのルートフォルダを取得
            account = None
            accounts = self._service.get_accounts()
            for acc in accounts:
                if acc.EntryID == account_id:
                    account = acc
                    break

            if not account:
                self.logger.error(
                    f"指定されたアカウントが見つかりませんでした: {account_id}"
                )
                return False

            # アカウントのルートフォルダを取得
            root_folder = self._service.get_root_folder()

            # アカウントのフォルダを保存
            for folder in root_folder:
                if hasattr(folder, "StoreID") and folder.StoreID == account.StoreID:
                    # デフォルトフォルダを判定
                    is_default_inbox = (
                        folder.DefaultItemType == 0 and "受信" in folder.Name
                    )
                    is_default_sent = (
                        folder.DefaultItemType == 0 and "送信済" in folder.Name
                    )

                    # フォルダとサブフォルダを保存
                    self._save_folder(
                        account_id, folder, is_default_inbox, is_default_sent
                    )
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

    def get_account_by_id(self, account_id: str):
        """
        指定したIDのアカウント情報を取得する

        Args:
            account_id: アカウントID

        Returns:
            アカウント情報
        """
        # 未実装
        pass

    def get_folder_by_id(self, folder_id: str):
        """
        指定したIDのフォルダ情報をデータベースから取得する

        Args:
            folder_id: フォルダID

        Returns:
            フォルダ情報
        """
        # 未実装
        pass
