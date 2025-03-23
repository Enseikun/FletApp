from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from win32com.client import CDispatch

from src.core.logger import get_logger
from src.models.outlook.outlook_client import OutlookClient, OutlookConnection


@dataclass
class OutlookService:
    """Outlookサービス"""

    _client: OutlookClient = field(default_factory=OutlookClient)
    _connection: Optional[OutlookConnection] = field(init=False, default=None)
    _outlook: Optional[CDispatch] = field(init=False, default=None)
    _namespace: Optional[CDispatch] = field(init=False, default=None)
    _logger = get_logger()

    def __post_init__(self) -> None:
        """初期化後の処理"""
        self._logger.info("OutlookServiceを初期化します...")
        try:
            self._connect()
            self._logger.info("OutlookServiceを初期化しました")
        except Exception as e:
            self._logger.error("OutlookServiceの初期化に失敗しました", error=str(e))
            raise

    def _connect(self) -> None:
        """Outlook接続を確立する"""
        if not self._connection or not self._client._is_connected():
            self._logger.info("Outlook接続を確立します...")
            self._connection = self._client._get_connection()
            self._outlook = self._connection.outlook
            self._namespace = self._connection.namespace
            self._logger.info("Outlook接続を確立しました")

    def get_account(self) -> CDispatch:
        """ログイン済みのデフォルトアカウントを取得する"""
        self._logger.debug("Outlookデフォルトアカウントを取得します...")
        try:
            self._connect()
            # デフォルトプロファイル情報を取得
            profile = self._namespace.CurrentUser
            if profile:
                self._logger.info("デフォルトアカウントの取得に成功しました")
                return profile
            else:
                raise RuntimeError("デフォルトアカウントの取得に失敗しました")
        except Exception as e:
            self._logger.error(
                "Outlookデフォルトアカウントの取得に失敗しました", error=str(e)
            )
            raise

    def get_root_folder(self) -> CDispatch:
        """ルートフォルダを取得する"""
        self._logger.debug("ルートフォルダを取得します...")
        try:
            self._connect()
            root_folder = self._namespace.Folders
            self._logger.info("ルートフォルダを取得しました", count=len(root_folder))
            return root_folder
        except Exception as e:
            self._logger.error("ルートフォルダの取得に失敗しました", error=str(e))
            raise

    def get_folders(self, root_folder: CDispatch) -> List[CDispatch]:
        """指定されたフォルダ配下のフォルダを取得する"""
        self._logger.debug(
            "指定されたフォルダのサブフォルダを取得します...", root_folder=root_folder
        )
        try:
            self._connect()
            folders = [f for f in root_folder.Folders if f.DefaultItemType == 0]
            self._logger.info(
                "指定されたフォルダのサブフォルダを取得しました", count=len(folders)
            )
            return folders
        except Exception as e:
            self._logger.error(
                "指定されたフォルダのサブフォルダの取得に失敗しました", error=str(e)
            )
            raise

    def get_folder_by_id(self, folder_EntryID: str) -> CDispatch:
        """指定されたEntryIDのフォルダを取得する"""
        self._logger.debug(
            "指定されたEntryIDのフォルダを取得します...", folder_EntryID=folder_EntryID
        )
        try:
            self._connect()

            folder = self._namespace.GetFolderFromID(folder_EntryID)
            self._logger.info(
                "指定されたEntryIDのフォルダを取得しました", folder=folder
            )
            return folder
        except Exception as e:
            self._logger.error(
                "指定されたEntryIDのフォルダの取得に失敗しました", error=str(e)
            )
            raise

    def get_item_by_id(self, item_EntryID: str) -> CDispatch:
        """指定されたEntryIDのアイテムを取得する"""
        self._logger.debug(
            "指定されたEntryIDのアイテムを取得します...", item_EntryID=item_EntryID
        )
        try:
            self._connect()

            item = self._connection.namespace.GetItemFromID(item_EntryID)
            self._logger.info("指定されたEntryIDのアイテムを取得しました", item=item)
            return item
        except Exception as e:
            self._logger.error(
                "指定されたEntryIDのアイテムの取得に失敗しました", error=str(e)
            )
            raise

    def get_item_from_msg(self, item_path: str) -> CDispatch:
        """MSG形式のファイルをメールアイテムとして取得する"""
        self._logger.debug(
            "MSG形式のファイルをメールアイテムとして取得します...", item_path=item_path
        )
        try:
            self._connect()

            item = self._connection.namespace.Session.OpenSharedItem(item_path)
            self._logger.info(
                "MSG形式のファイルをメールアイテムとして取得しました", item=item
            )
            return item
        except Exception as e:
            self._logger.error(
                "MSG形式のファイルをメールアイテムとして取得に失敗しました",
                error=str(e),
            )
            raise

    def move_item(self, item_entryid: str, folder_entryid: str) -> bool:
        """メールアイテムを指定されたフォルダに移動する"""
        self._logger.debug(
            "メールアイテムを指定されたフォルダに移動します...",
            item_entryid=item_entryid,
            folder_entryid=folder_entryid,
        )
        try:
            self._connect()

            mail_item = self.get_item_by_id(item_entryid)
            if not mail_item:
                self._logger.error(
                    "指定されたEntryIDのメールアイテムが見つかりませんでした",
                    item_entryid=item_entryid,
                )
                return False

            target_folder = self.get_folder_by_id(folder_entryid)
            if not target_folder:
                self._logger.error(
                    "指定されたEntryIDのフォルダが見つかりませんでした",
                    folder_entryid=folder_entryid,
                )
                return False

            mail_item.Move(target_folder)
            self._logger.info(
                "メールアイテムを指定されたフォルダに移動しました",
                item_entryid=item_entryid,
                folder_entryid=folder_entryid,
            )
            return True
        except Exception as e:
            self._logger.error(
                "メールアイテムを指定されたフォルダに移動に失敗しました", error=str(e)
            )
            raise

    def set_flag(self, item_entryid: str, flag: int, flag_status: int) -> bool:
        """メールアイテムにフラグを設定する"""
        self._logger.debug(
            "メールアイテムにフラグを設定します...",
            item_entryid=item_entryid,
            flag=flag,
        )
        try:
            self._connect()

            mail_item = self.get_item_by_id(item_entryid)

            if not mail_item:
                self._logger.error(
                    "指定されたEntryIDのメールアイテムが見つかりませんでした",
                    item_entryid=item_entryid,
                )
                return False

            mail_item.FlagStatus = flag_status
            mail_item.Save()
            self._logger.info(
                "メールアイテムにフラグを設定しました",
                item_entryid=item_entryid,
                flag=flag,
            )
            return True
        except Exception as e:
            self._logger.error(
                "メールアイテムにフラグを設定に失敗しました", error=str(e)
            )
            raise
