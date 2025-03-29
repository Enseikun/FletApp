"""
Outlook APIクライアント

責務:
- Outlook APIとの直接通信
- メールデータの取得
- フォルダ情報の取得
- 認証管理

主なメソッド:
- get_folder: フォルダ情報の取得
- get_mail: メールデータの取得
- get_attachments: 添付ファイルの取得
- authenticate: 認証処理

連携:
上流:
- OutlookService: 高レベルなOutlook操作の提供
- OutlookExtractionService: メールデータの取得要求

下流:
- Outlook API: Microsoft Graph API
  - メールデータの取得
  - フォルダ情報の取得
  - 認証処理
"""

import time
from dataclasses import dataclass
from typing import Any

import pythoncom
import win32com.client

from src.core.logger import get_logger


@dataclass
class OutlookConnection:
    outlook: Any
    namespace: Any


class OutlookClient:
    def __init__(self):
        self._logger = get_logger()
        self._outlook = None
        self._namespace = None
        self._max_wait_time = 30
        self._initial_retry_delay = 1
        self._is_initialized = False

        self._logger.info(
            "OutlookClientを初期化します...",
            max_wait_time=self._max_wait_time,
            initial_retry_delay=self._initial_retry_delay,
        )

        self._initialize_com()

    def _initialize_com(self):
        """Outlookの初期化を試みる"""
        if not self._is_initialized:
            try:
                pythoncom.CoInitialize()
                self._is_initialized = True
                self._logger.info("Outlook接続の初期化に成功しました")
            except Exception as e:
                self._logger.error(
                    "Outlook接続の初期化に失敗しました",
                    error=str(e),
                )
                raise

    def __del__(self):
        """クライアント破棄時にCOMオブジェクトを解放する"""
        if self._is_initialized:
            try:
                pythoncom.CoUninitialize()
                self._is_initialized = False
                self._logger.info("Outlook接続を破棄しました")
            except Exception as e:
                self._logger.error(
                    "Outlook接続の破棄に失敗しました",
                    error=str(e),
                )

    def get_active_outlook_instance(self) -> bool:
        """Outlookのインスタンスが存在するか確認する"""
        try:
            self._outlook = win32com.client.Dispatch("Outlook.Application")
            self._namespace = self._outlook.GetNamespace("MAPI")
            self._logger.info("アクティブなOutlookインスタンスを取得しました")
            return True
        except pythoncom.com_error as e:
            self._logger.error(
                "アクティブなOutlookインスタンスの取得に失敗しました",
                error_code=e.hresult,
                error=str(e),
            )
            return False

    def _wait_for_outlook_initialization(self, timeout: int = 10):
        """Outlookの初期化を待つ"""
        self._logger.info("Outlookの初期化を待ちます...", timeout=timeout)
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if isinstance(self._outlook, win32com.client.CDispatch):
                    self._namespace = self._outlook.GetNamespace("MAPI")
                    if self._namespace:
                        _ = self._namespace.GetDefaultFolder(6)
                        self._logger.info("Outlookの初期化が完了しました")
                        return True
            except pythoncom.com_error as e:
                self._logger.debug(
                    "初期化待機中",
                    error_code=e.hresult,
                    elapsed_time=f"{time.time() - start_time:.2f}秒",
                )
            except Exception as e:
                self._logger.error(
                    "初期化待機中に予期せぬエラーが発生しました",
                    error=str(e),
                )
            time.sleep(1)

        self._logger.error("Outlookの初期化が完了しませんでした")
        return False

    def _get_connection(self) -> OutlookConnection:
        """Outlook接続を確立する"""
        self._logger.debug("Outlook接続を確立します...")
        if not self._is_connected():
            self._logger.error("Outlook接続が確立されていません")

            retry_delay = self._initial_retry_delay
            start_time = time.time()

            while time.time() - start_time < self._max_wait_time:
                try:
                    if self.get_active_outlook_instance():
                        break
                    else:
                        self._logger.info("新しいOutlookインスタンスを作成します...")
                        self._outlook = win32com.client.Dispatch("Outlook.Application")

                        if self._wait_for_outlook_initialization():
                            break
                except Exception as e:
                    if time.time() - start_time + retry_delay >= self._max_wait_time:
                        self._logger.error(
                            "Outlook接続の確立に失敗しました",
                            error=str(e),
                            total_time=f"{time.time() - start_time:.2f}秒",
                        )
                        raise RuntimeError("Outlook接続の確立に失敗しました")

                    self._logger.warning(
                        "Outlook接続の確立を再試行中...",
                        retry_delay=f"{retry_delay:.2f}秒",
                        elapsed_time=f"{time.time() - start_time:.2f}秒",
                        remaining_time=f"{self._max_wait_time - (time.time() - start_time):.2f}秒",
                    )
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 5)
            else:
                self._logger.error(
                    "Outlook接続の確立に失敗しました",
                    total_time=f"{time.time() - start_time:.2f}秒",
                )
                raise RuntimeError("Outlook接続の確立に失敗しました")

        self._logger.info("Outlook接続を確立しました")
        return OutlookConnection(
            outlook=self._outlook,
            namespace=self._namespace,
        )

    def _is_connected(self) -> bool:
        """Outlook接続が確立されているか確認する"""
        if not self._outlook or not self._namespace:
            self._logger.error("Outlook接続が確立されていません")
            return False

        try:
            _ = self._namespace.GetDefaultFolder(6)
            self._logger.info("Outlook接続が確立されています")
            return True
        except Exception as e:
            self._logger.error(
                "Outlook接続の確認に失敗しました",
                error=str(e),
            )
            return False

    @property
    def outlook(self):
        if not self._outlook:
            self._logger.error("Outlook接続が確立されていません")
            raise RuntimeError("Outlook接続が確立されていません")
        return self._outlook

    @property
    def namespace(self):
        if not self._namespace:
            self._logger.error("Outlook接続が確立されていません")
            raise RuntimeError("Outlook接続が確立されていません")
        return self._namespace
