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

            # 結果に応じてログを出力
            if result:
                self.logger.info(
                    "HomeContentViewModel: メール抽出開始成功", task_id=task_id
                )

                # メールの抽出処理中であることをダイアログに表示
                await self._progress_dialog.update_message_async(
                    "メールの抽出処理を実行中です。完了までお待ちください..."
                )

                # 抽出の完了を監視
                is_completed = False
                progress_check_count = 0

                while not is_completed:
                    # 抽出状態をチェック
                    status = self.check_snapshot_and_extraction_plan(task_id)

                    # データベースからも直接状態を確認（より確実に完了を検出するため）
                    extraction_completed, progress_info = (
                        await self._check_extraction_status_from_db(
                            task_id, with_progress=True
                        )
                    )

                    if status["extraction_completed"] or extraction_completed:
                        is_completed = True
                        self.logger.info(
                            "HomeContentViewModel: メール抽出が完了しました",
                            task_id=task_id,
                        )
                    else:
                        # 進捗情報を取得して表示
                        completed_count = progress_info.get("completed_count", 0)
                        total_count = progress_info.get("total_count", 0)

                        # 進捗メッセージを作成
                        progress_message = "メールの抽出処理を実行中です。"
                        if total_count > 0:
                            progress_message += (
                                f"\n処理済み: {completed_count}/{total_count} メール"
                            )
                            # プログレスバーを更新（completed_countがtotal_countより大きくならないように注意）
                            actual_completed = min(completed_count, total_count)
                            await self._progress_dialog.update_progress_async(
                                actual_completed, total_count
                            )
                        else:
                            progress_message += "\n準備中..."

                        # 定期的に処理状態も表示
                        progress_check_count += 1
                        if progress_check_count % 5 == 0:  # 5回ごとに詳細情報を表示
                            process_status = progress_info.get("process_details", "")
                            if process_status:
                                progress_message += f"\n{process_status}"

                        # 進捗状況をダイアログに表示
                        await self._progress_dialog.update_message_async(
                            progress_message
                        )

                        # 少し待機してから再チェック
                        await asyncio.sleep(1.0)

                # 抽出が完了したことをダイアログに表示
                await self._progress_dialog.update_message_async(
                    "メール抽出が完了しました。"
                )

                # 抽出完了ダイアログを表示する前に少し待機
                await asyncio.sleep(1.0)

                # ダイアログを閉じる
                await self._progress_dialog.close_async()

                # 抽出が完了したか確認（完了イベント通知のため）
                await self.check_extraction_completed(task_id)

                # 抽出結果の詳細を取得
                _, final_progress = await self._check_extraction_status_from_db(
                    task_id, with_progress=True
                )

                # 抽出結果サマリーを作成
                total_count = final_progress.get("total_count", 0)
                completed_count = final_progress.get("completed_count", 0)
                error_count = (
                    total_count - completed_count
                    if total_count > completed_count
                    else 0
                )

                result_message = "メール抽出が完了しました。\n\n"
                result_message += f"処理結果:\n"
                result_message += f"- 合計: {total_count} メール\n"
                result_message += f"- 成功: {completed_count} メール\n"

                if error_count > 0:
                    result_message += f"- エラー: {error_count} メール\n"

                # 添付ファイル情報がある場合は表示
                if (
                    "attachment_total" in final_progress
                    and final_progress["attachment_total"] > 0
                ):
                    att_total = final_progress.get("attachment_total", 0)
                    att_completed = final_progress.get("attachment_completed", 0)
                    result_message += f"- 添付ファイル: {att_completed}/{att_total}\n"

                # 完了メッセージとOKボタンを表示
                await self._progress_dialog.update_message_async(result_message)
                await self._progress_dialog.add_close_button_async("OK")

                # ユーザーがボタンをクリックするまで待機
                await self._progress_dialog.wait_for_close()

                # ダイアログが閉じられた後、通知を行う
                await self.check_extraction_completed(task_id)

                await asyncio.sleep(0.1)
                return True
            else:
                self.logger.error(
                    "HomeContentViewModel: メール抽出開始失敗", task_id=task_id
                )
                # 抽出開始失敗時はダイアログを閉じる
                await self._progress_dialog.close_async()
                return False

        except Exception as e:
            self.logger.error(
                "HomeContentViewModel: メール抽出処理中にエラー発生",
                task_id=task_id,
                error=str(e),
                stack=str(e.__traceback__),
            )
            try:
                # エラー発生時はダイアログのメッセージを更新して表示
                if self._progress_dialog.is_open:
                    error_message = (
                        f"メール抽出処理中にエラーが発生しました:\n\n{str(e)}"
                    )
                    await self._progress_dialog.update_message_async(error_message)

                    # OKボタンを表示してユーザーの確認を待つ
                    await self._progress_dialog.add_close_button_async("OK")
                    await self._progress_dialog.wait_for_close(
                        timeout=60.0
                    )  # 最大1分待機
            except Exception as dialog_ex:
                self.logger.error(
                    "HomeContentViewModel: エラー処理中に例外発生",
                    error=str(dialog_ex),
                )
                # どうしてもダイアログが閉じられない場合は無視
                pass

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

        # 抽出が完了している場合は、task_statusとtask_messageも取得
        if result["extraction_completed"]:
            try:
                # items.dbへのパスを設定
                items_db_path = os.path.join("data", "tasks", str(task_id), "items.db")

                if os.path.exists(items_db_path):
                    # DatabaseManagerを使用してデータベースに接続
                    items_db = DatabaseManager(items_db_path)

                    # task_progressテーブルから最新の状態を取得
                    progress_query = """
                    SELECT status, last_error FROM task_progress 
                    WHERE task_id = ? 
                    ORDER BY last_updated_at DESC LIMIT 1
                    """
                    progress_result = items_db.execute_query(progress_query, (task_id,))

                    if progress_result:
                        task_status = progress_result[0].get("status")
                        task_message = progress_result[0].get("last_error", "")

                        # task_statusとtask_messageを結果に追加
                        result["task_status"] = task_status
                        result["task_message"] = task_message

                        self.logger.debug(
                            "HomeContentViewModel: タスク状態情報を取得しました",
                            task_id=task_id,
                            status=task_status,
                        )

                    # データベース接続を閉じる
                    items_db.disconnect()
            except Exception as e:
                self.logger.error(
                    "HomeContentViewModel: タスク状態取得中にエラー発生",
                    task_id=task_id,
                    error=str(e),
                )
                # エラーが発生した場合はデフォルト値を設定
                result["task_status"] = "unknown"
                result["task_message"] = "状態取得エラー: " + str(e)

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
            self.logger.debug(
                "HomeContentViewModel: 抽出完了確認開始",
                task_id=task_id,
                has_status=status is not None,
                extraction_completed=status.get("extraction_completed", False),
            )

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
            self.logger.debug(
                "HomeContentViewModel: タスク状態取得",
                task_id=task_id,
                task_status=task_status,
                task_message=task_message,
            )

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
                    self.logger.debug(
                        "HomeContentViewModel: 抽出完了コールバックを呼び出します",
                        task_id=task_id,
                        status_info=str(status),
                    )
                    self.extraction_completed_callback(task_id, status)
                else:
                    self.logger.warning(
                        "HomeContentViewModel: 抽出完了コールバックが設定されていません",
                        task_id=task_id,
                    )

                return True

            self.logger.debug(
                "HomeContentViewModel: 抽出はまだ完了していません",
                task_id=task_id,
                task_status=task_status,
            )
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

    async def _check_extraction_status_from_db(
        self, task_id: str, with_progress: bool = False
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        データベースから抽出状態を確認する

        Args:
            task_id: タスクID
            with_progress: 進捗情報を含めて確認するかどうか

        Returns:
            Tuple[bool, Dict[str, Any]]: 抽出が完了しているかどうかと進捗情報
        """
        items_db = None
        try:
            # データベース接続が必要なため、モデルに処理を委譲
            items_db_path = os.path.join("data", "tasks", str(task_id), "items.db")

            if not os.path.exists(items_db_path):
                self.logger.warning(
                    "HomeContentViewModel: items.dbが見つかりません",
                    db_path=items_db_path,
                )
                return False, {}

            # DatabaseManagerを直接使用
            items_db = DatabaseManager(items_db_path)

            # 進捗情報を格納する辞書
            progress_info = {}

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
                return False, progress_info

            task_status = progress_result[0].get("status")
            task_message = progress_result[0].get("last_error", "")

            # 進捗情報を辞書に追加
            progress_info["task_status"] = task_status
            progress_info["task_message"] = task_message

            # with_progressが指定されている場合は進捗状況の詳細を取得
            if with_progress:
                # メールタスクの総数を取得
                total_query = """
                SELECT COUNT(*) as total FROM mail_tasks 
                WHERE task_id = ?
                """
                total_result = items_db.execute_query(total_query, (task_id,))
                total_count = total_result[0].get("total", 0) if total_result else 0

                # 完了したメールタスクの数を取得
                completed_query = """
                SELECT COUNT(*) as completed FROM mail_tasks 
                WHERE task_id = ? AND status IN ('completed', 'error')
                """
                completed_result = items_db.execute_query(completed_query, (task_id,))
                completed_count = (
                    completed_result[0].get("completed", 0) if completed_result else 0
                )

                # 添付ファイル処理状況
                attachment_query = """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN attachment_status = 'completed' THEN 1 ELSE 0 END) as completed
                FROM mail_tasks 
                WHERE task_id = ? AND has_attachments = 1
                """
                attachment_result = items_db.execute_query(attachment_query, (task_id,))

                # 進捗情報を辞書に追加
                progress_info["total_count"] = total_count
                progress_info["completed_count"] = completed_count
                if attachment_result:
                    progress_info["attachment_total"] = attachment_result[0].get(
                        "total", 0
                    )
                    progress_info["attachment_completed"] = attachment_result[0].get(
                        "completed", 0
                    )

                # 最近処理したメールの情報を取得（上位3つ）
                recent_query = """
                SELECT subject, status, last_updated_at 
                FROM mail_tasks 
                WHERE task_id = ? 
                ORDER BY last_updated_at DESC LIMIT 3
                """
                recent_result = items_db.execute_query(recent_query, (task_id,))
                if recent_result:
                    progress_info["recent_mails"] = recent_result

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
                progress_info["extraction_completed"] = True
                progress_info["extraction_in_progress"] = False
                progress_info["has_snapshot"] = True

                # 完了コールバックが設定されている場合は呼び出す
                if self.extraction_completed_callback and not with_progress:
                    self.extraction_completed_callback(task_id, progress_info)

                return True, progress_info

            # 完了していない場合も進捗情報を返す
            progress_info["extraction_completed"] = False
            progress_info["extraction_in_progress"] = task_status == "processing"

            return False, progress_info

        except Exception as e:
            self.logger.error(
                "HomeContentViewModel: 抽出完了確認中にエラー発生",
                task_id=task_id,
                error=str(e),
            )
            return False, {}
        finally:
            # データベース接続が閉じられていることを確認
            if items_db:
                items_db.disconnect()
