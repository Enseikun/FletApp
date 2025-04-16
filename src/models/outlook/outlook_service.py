"""
Outlook操作サービス

責務:
- Outlook操作の高レベルインターフェース提供
- フォルダ操作の抽象化
- メール操作の抽象化
- エラーハンドリングの統一

主なメソッド:
- get_folder_by_id: フォルダ情報の取得
- get_mail_by_id: メールデータの取得
- get_folder_items: フォルダ内アイテムの取得
- search_items: アイテムの検索

連携:
上流:
- OutlookBaseModel: 共通機能の提供
- OutlookItemModel: メールデータの操作要求

下流:
- OutlookClient: 低レベルなAPI通信
  - メールデータの取得
  - フォルダ情報の取得
  - アイテムの移動
  - フラグの設定
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from win32com.client import CDispatch

from src.core.logger import get_logger
from src.models.outlook.outlook_client import OutlookClient, OutlookConnection
from src.util.object_util import debug_print_mail_item, debug_print_mail_methods


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
            # アカウントコレクションから最初のアカウントを取得
            accounts = self._namespace.Accounts
            if accounts.Count > 0:
                account = accounts.Item(1)  # 最初のアカウントを取得
                self._logger.info("デフォルトアカウントの取得に成功しました")
                return account
            else:
                raise RuntimeError("アカウントが見つかりません")
        except Exception as e:
            self._logger.error(
                "Outlookデフォルトアカウントの取得に失敗しました", error=str(e)
            )
            raise

    def get_root_folders(self) -> CDispatch:
        """ルートフォルダのコレクションを取得する"""
        self._logger.debug("ルートフォルダのコレクションを取得します...")
        try:
            self._connect()
            root_folders = self._namespace.Folders
            self._logger.info(
                "ルートフォルダのコレクションを取得しました", count=len(root_folders)
            )
            return root_folders
        except Exception as e:
            self._logger.error(
                "ルートフォルダのコレクションの取得に失敗しました", error=str(e)
            )
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

    def debug_mail_item(self, mail_item: CDispatch, title: str = None) -> None:
        """メールアイテムの詳細情報をデバッグ出力する

        Args:
            mail_item (CDispatch): デバッグ対象のメールアイテム
            title (str, optional): デバッグ出力のタイトル. Defaults to None.
        """
        if title is None:
            title = "メールアイテムのデバッグ情報"

        self._logger.debug(f"メールアイテムのデバッグ情報を出力します: {title}")

        try:
            # プロパティ情報の出力
            debug_print_mail_item(mail_item, title)

            # 続けてメソッド情報も出力
            debug_print_mail_methods(mail_item, f"{title} - メソッド情報")

            self._logger.debug("メールアイテムのデバッグ情報出力が完了しました")
        except Exception as e:
            self._logger.error(
                "メールアイテムのデバッグ情報出力に失敗しました", error=str(e)
            )

    def debug_msg_item(self, msg_path: str, title: str = None) -> None:
        """MSGファイルから復元したメールアイテムの詳細情報をデバッグ出力する

        Args:
            msg_path (str): MSGファイルのパス
            title (str, optional): デバッグ出力のタイトル. Defaults to None.
        """
        if title is None:
            title = f"MSGファイルのデバッグ情報: {msg_path}"

        self._logger.debug(f"MSGファイルのデバッグ情報を出力します: {msg_path}")

        try:
            # MSGファイルからメールアイテムを取得
            mail_item = self.get_item_from_msg(msg_path)

            if mail_item:
                # メールアイテムのデバッグ情報を出力
                self.debug_mail_item(mail_item, title)
            else:
                self._logger.warning(
                    f"MSGファイルからメールアイテムを取得できませんでした: {msg_path}"
                )

            self._logger.debug("MSGファイルのデバッグ情報出力が完了しました")
        except Exception as e:
            self._logger.error(
                "MSGファイルのデバッグ情報出力に失敗しました",
                error=str(e),
                msg_path=msg_path,
            )
