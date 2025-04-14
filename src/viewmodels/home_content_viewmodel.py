import asyncio
import os
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.core.database import DatabaseManager
from src.core.logger import get_logger
from src.models.home_content_model import HomeContentModel
from src.views.components.progress_dialog import ProgressDialog


class HomeContentViewModel:
    """
    ホーム画面のコンテンツ用ViewModel
    tasks.dbからデータを取得して提供する
    """

    def __init__(self, db_path: str = None):
        """初期化"""
        self.logger = get_logger()
        self.logger.info("HomeContentViewModel: 初期化開始", db_path=db_path)
        self.model = HomeContentModel(db_path)
        self.current_task_id = None
        self.main_viewmodel = None  # MainViewModelへの参照を保持するためのプロパティ
        self.extraction_confirmation_callback = None  # 抽出確認コールバック
        self.extraction_completed_callback = None  # 抽出完了コールバック

        # ProgressDialogのインスタンスを取得
        self._progress_dialog = ProgressDialog()

        self.logger.info("HomeContentViewModel: 初期化完了")

    def get_tasks_data(self) -> List[Tuple[int, str]]:
        """
        tasks.dbからタスクデータを取得する

        Returns:
            List[Tuple[int, str]]: (id, from_folder_name)のリスト
        """
        self.logger.debug("HomeContentViewModel: タスクデータ取得開始")
        result = self.model.get_tasks_data()
        self.logger.debug(
            "HomeContentViewModel: タスクデータ取得完了", task_count=len(result)
        )
        return result

    def delete_task(self, task_id: str) -> bool:
        """
        指定されたIDのタスクを削除する

        Args:
            task_id: 削除するタスクのID

        Returns:
            bool: 削除が成功したかどうか
        """
        self.logger.info("HomeContentViewModel: タスク削除開始", task_id=task_id)
        result = self.model.delete_task(task_id)
        if result:
            self.logger.info("HomeContentViewModel: タスク削除成功", task_id=task_id)
        else:
            self.logger.error("HomeContentViewModel: タスク削除失敗", task_id=task_id)
        return result

    def set_extraction_confirmation_callback(
        self, callback: Callable[[str, Dict[str, bool]], None]
    ) -> None:
        """
        メール抽出確認ダイアログを表示するためのコールバックを設定する

        Args:
            callback: タスクIDとステータス情報を引数に取るコールバック関数
        """
        self.extraction_confirmation_callback = callback
        self.logger.info("HomeContentViewModel: 抽出確認コールバックを設定しました")

    def set_extraction_completed_callback(
        self, callback: Callable[[str, Dict[str, bool]], None]
    ) -> None:
        """
        メール抽出完了ダイアログを表示するためのコールバックを設定する

        Args:
            callback: タスクIDとステータス情報を引数に取るコールバック関数
        """
        self.extraction_completed_callback = callback
        self.logger.info("HomeContentViewModel: 抽出完了コールバックを設定しました")

    async def set_current_task_id(self, task_id: str) -> bool:
        """
        現在選択されているタスクIDを設定する

        Args:
            task_id: 設定するタスクID

        Returns:
            bool: 処理が成功したかどうか
        """
        # タスクIDが同じ場合は処理をスキップ
        if self.current_task_id == task_id:
            self.logger.info(
                "HomeContentViewModel: 同じタスクIDが選択されました。処理をスキップします",
                task_id=task_id,
            )
            return True

        self.current_task_id = task_id
        self.logger.info("HomeContentViewModel: 現在のタスクIDを設定", task_id=task_id)

        success = True

        # 抽出状態を確認
        if task_id:
            # スナップショットと抽出計画の状態を確認
            status = self.check_snapshot_and_extraction_plan(task_id)

            # 抽出が進行中または完了している場合はスキップ
            if status["extraction_in_progress"]:
                self.logger.info(
                    f"HomeContentViewModel: メール抽出は既に進行中です - {task_id}"
                )
            elif status["extraction_completed"]:
                self.logger.info(
                    f"HomeContentViewModel: メール抽出は既に完了しています - {task_id}"
                )
            else:
                # 抽出が進行中でも完了でもない場合は確認ダイアログを表示
                self.logger.info(
                    f"HomeContentViewModel: メール抽出確認ダイアログを表示します - {task_id}"
                )

                # 確認コールバックが設定されている場合は呼び出す
                if self.extraction_confirmation_callback:
                    self.extraction_confirmation_callback(task_id, status)
                else:
                    # コールバックが設定されていない場合は直接抽出を開始
                    await self._start_extraction_without_confirmation(task_id)

        # MainViewModelが設定されている場合通知
        if self.main_viewmodel and success:
            self.main_viewmodel.set_current_task_id(task_id)
            self.logger.debug(
                "HomeContentViewModel: MainViewModelにタスクIDを設定", task_id=task_id
            )

        return success

    async def _start_extraction_without_confirmation(self, task_id: str) -> bool:
        """
        確認なしでメール抽出を開始する（内部メソッド）

        Args:
            task_id: タスクID

        Returns:
            bool: 開始が成功したかどうか
        """
        try:
            # メール抽出の開始時にProgressDialogを表示
            await self._progress_dialog.show_async(
                "メール抽出中",
                "メール抽出の準備をしています...",
                0,
                None,
            )

            await asyncio.sleep(0.1)

            # スナップショットと抽出計画の状態を確認
            status = self.check_snapshot_and_extraction_plan(task_id)

            # スナップショットが存在しない場合は作成
            if not status["has_snapshot"]:
                self.logger.info(
                    f"HomeContentViewModel: スナップショットが存在しないため作成します - {task_id}"
                )
                await self._progress_dialog.update_message_async(
                    "Outlookフォルダのスナップショットを作成しています..."
                )

                await asyncio.sleep(0.1)

                # スナップショットを作成
                snapshot_success = self.model.create_outlook_snapshot(task_id)
                if not snapshot_success:
                    self.logger.error(
                        "HomeContentViewModel: スナップショットの作成に失敗しました",
                        task_id=task_id,
                    )
                    await self._progress_dialog.close_async()
                    await asyncio.sleep(0.1)
                    return False

                self.logger.info(
                    "HomeContentViewModel: Outlookスナップショット作成成功",
                    task_id=task_id,
                )

            # メール抽出の準備
            await self._progress_dialog.update_message_async(
                "メールの抽出処理を実行しています..."
            )

            await asyncio.sleep(0.1)

            # メール抽出を開始
            result = self.model.start_mail_extraction(task_id)

            # ProgressDialogを閉じる（抽出は非同期で進行中）
            await self._progress_dialog.close_async()

            await asyncio.sleep(0.1)
            # 結果に応じてログを出力
            if result:
                self.logger.info(
                    "HomeContentViewModel: メール抽出開始成功", task_id=task_id
                )

                # 抽出が完了したか確認（すぐに完了する場合もあるため）
                await self.check_extraction_completed(task_id)

                await asyncio.sleep(0.1)
                return True
            else:
                self.logger.error(
                    "HomeContentViewModel: メール抽出開始失敗", task_id=task_id
                )
                return False

        except Exception as e:
            self.logger.error(
                "HomeContentViewModel: メール抽出処理中にエラー発生",
                task_id=task_id,
                error=str(e),
            )
            # エラー発生時はダイアログを確実に閉じる
            if self._progress_dialog.is_open:
                await self._progress_dialog.close_async()

            await asyncio.sleep(0.1)
            return False

    async def handle_extraction_confirmation(
        self, task_id: str, confirmed: bool
    ) -> bool:
        """
        メール抽出確認ダイアログの結果を処理する

        Args:
            task_id: タスクID
            confirmed: ユーザーが確認したかどうか

        Returns:
            bool: 処理が成功したかどうか
        """
        if confirmed:
            self.logger.info(
                "HomeContentViewModel: ユーザーがメール抽出を承認しました",
                task_id=task_id,
            )

            # 抽出開始前に現在の状態を確認
            current_status = self.check_snapshot_and_extraction_plan(task_id)

            # 既に抽出が進行中または完了している場合はスキップ
            if current_status["extraction_in_progress"]:
                self.logger.info(
                    "HomeContentViewModel: 抽出は既に進行中です。新たな抽出は開始しません。",
                    task_id=task_id,
                )
                return True

            if current_status["extraction_completed"]:
                self.logger.info(
                    "HomeContentViewModel: 抽出は既に完了しています。新たな抽出は開始しません。",
                    task_id=task_id,
                )
                return True

            # 抽出が進行中でも完了でもない場合に抽出を開始
            return await self._start_extraction_without_confirmation(task_id)
        else:
            self.logger.info(
                "HomeContentViewModel: ユーザーがメール抽出をキャンセルしました",
                task_id=task_id,
            )
            return True  # キャンセルは成功扱い

    def get_current_task_id(self) -> str:
        """
        現在選択されているタスクIDを取得する

        Returns:
            str: 現在のタスクID
        """
        self.logger.debug(
            "HomeContentViewModel: 現在のタスクIDを取得", task_id=self.current_task_id
        )
        return self.current_task_id

    def create_task_directory_and_database(self, task_id: str) -> bool:
        """
        タスクフォルダとデータベースを作成する

        Args:
            task_id: タスクID

        Returns:
            bool: 作成が成功したかどうか
        """
        self.logger.info(
            "HomeContentViewModel: タスクフォルダとデータベースの作成開始",
            task_id=task_id,
        )
        result = self.model.create_task_directory_and_database(task_id)
        if result:
            self.logger.info(
                "HomeContentViewModel: タスクフォルダとデータベースの作成成功",
                task_id=task_id,
            )
        else:
            self.logger.error(
                "HomeContentViewModel: タスクフォルダとデータベースの作成失敗",
                task_id=task_id,
            )
        return result

    def check_snapshot_and_extraction_plan(self, task_id: str) -> Dict[str, bool]:
        """
        スナップショットと抽出計画の存在を確認する

        Args:
            task_id: タスクID

        Returns:
            Dict[str, bool]: スナップショットと抽出計画の存在状況
        """
        self.logger.info(
            "HomeContentViewModel: スナップショットと抽出計画の確認開始",
            task_id=task_id,
        )
        result = self.model.check_snapshot_and_extraction_plan(task_id)
        self.logger.info(
            "HomeContentViewModel: スナップショットと抽出計画の確認完了",
            task_id=task_id,
            result=result,
        )
        return result

    async def check_extraction_completed(self, task_id: str) -> bool:
        """
        メール抽出が完了したかどうかを確認し、完了していれば完了コールバックを呼び出す

        Args:
            task_id: タスクID

        Returns:
            bool: 抽出が完了しているかどうか
        """
        items_db = None
        try:
            # 抽出状態を確認
            status = self.check_snapshot_and_extraction_plan(task_id)

            # データベース接続が必要なため、モデルに処理を委譲
            items_db_path = os.path.join("data", "tasks", str(task_id), "items.db")

            if not os.path.exists(items_db_path):
                self.logger.warning(
                    "HomeContentViewModel: items.dbが見つかりません",
                    db_path=items_db_path,
                )
                return False

            # DatabaseManagerを直接使用
            items_db = DatabaseManager(items_db_path)

            # task_progressテーブルから最新の状態を取得
            progress_query = """
            SELECT status, last_error FROM task_progress 
            WHERE task_id = ? 
            ORDER BY last_updated_at DESC LIMIT 1
            """
            progress_result = items_db.execute_query(progress_query, (task_id,))

            if not progress_result:
                self.logger.warning(
                    "HomeContentViewModel: task_progressテーブルに情報がありません",
                    task_id=task_id,
                )
                return False

            task_status = progress_result[0].get("status")
            task_message = progress_result[0].get("last_error", "")

            # 処理が完了またはエラーの場合
            is_completed = task_status in ["completed", "error"]

            if is_completed:
                self.logger.info(
                    "HomeContentViewModel: メール抽出が完了しています",
                    task_id=task_id,
                    status=task_status,
                    error_message=task_message,
                )

                # ステータス情報を更新
                status["task_status"] = task_status
                status["task_message"] = task_message

                # 完了コールバックが設定されている場合は呼び出す
                if self.extraction_completed_callback:
                    self.extraction_completed_callback(task_id, status)

                return True

            return False

        except Exception as e:
            self.logger.error(
                "HomeContentViewModel: 抽出完了確認中にエラー発生",
                task_id=task_id,
                error=str(e),
            )
            return False
        finally:
            # データベース接続が閉じられていることを確認
            if items_db:
                items_db.disconnect()
