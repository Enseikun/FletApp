import flet as ft

from src.core.logger import get_logger
from src.viewmodels.home_content_viewmodel import HomeContentViewModel
from src.viewmodels.home_viewmodel import HomeViewModel
from src.views.components.add_button import AddButton
from src.views.components.text_with_subtitle_with_delete_icon import (
    TextWithSubtitleWithDeleteIcon,
)
from src.views.styles.style import AppTheme


class HomeContent(ft.Container):
    """
    ホーム画面のコンテンツ
    TextWithSubtitleWithDeleteIconコンポーネントを使用したリストを表示
    """

    def __init__(self, contents_viewmodel):
        """初期化"""

        super().__init__()
        # HomeContentViewModelのインスタンスを作成
        self.contents_viewmodel = HomeContentViewModel()
        self.logger = get_logger()
        self.logger.info("HomeContent: 初期化開始")

        # ダイアログ管理用の変数
        self._current_dialog = None
        self._is_dialog_open = False

        # MainViewModelへの参照を取得
        self.main_viewmodel = None
        if (
            hasattr(contents_viewmodel, "main_viewmodel")
            and contents_viewmodel.main_viewmodel
        ):
            self.main_viewmodel = contents_viewmodel.main_viewmodel
            self.logger.info("HomeContent: MainViewModelを取得しました")
            # HomeContentViewModelにMainViewModelを設定
            self.contents_viewmodel.main_viewmodel = self.main_viewmodel

        # 抽出確認コールバックの設定は不要（直接抽出メソッドが使用されるため）
        self.logger.info(
            "HomeContent: 抽出確認コールバックは設定しません（レガシー機能）"
        )

        # 抽出完了コールバックを設定
        self.contents_viewmodel.set_extraction_completed_callback(
            self.show_extraction_completed_dialog
        )
        self.logger.info("HomeContent: 抽出完了コールバックを設定しました")

        # HomeViewModelのインスタンスを作成（MainViewModelを渡す）
        self.home_viewmodel = HomeViewModel(
            self.main_viewmodel or self.contents_viewmodel
        )

        # タスクリストを表示するコントロールを作成
        self.task_items_column = ft.Column(
            scroll=ft.ScrollMode.AUTO, spacing=10, expand=True
        )

        # 新規タスク追加ボタン
        self.add_button = AddButton(
            on_click=self.on_add_task_click,
            tooltip="新しいタスクを追加",
            size=50,
        )

        # 追加ボタン用のコンテナ（中央揃え）
        self.add_button_container = ft.Container(
            content=self.add_button,
            alignment=ft.alignment.center,
            padding=ft.padding.only(top=10, bottom=10),
        )

        # タスクリストを取得
        tasks = self.home_viewmodel.load_tasks()
        self.logger.debug("HomeContent: タスクリスト取得", task_count=len(tasks))

        # タスクリストを作成（update()を呼び出さない）
        self._create_task_list(tasks)

        # メインコンテンツ
        self.content = ft.Column(
            controls=[
                ft.Text("タスク一覧", size=24, weight="bold"),
                ft.Divider(),
                self.task_items_column,
            ],
            spacing=10,
            expand=True,
        )
        self.padding = 20
        self.expand = True
        self.logger.info("HomeContent: 初期化完了")

    def _create_task_list(self, tasks):
        """タスクリストを作成する"""
        self.logger.debug("HomeContent: タスクリスト作成開始", task_count=len(tasks))
        self.task_items_column.controls.clear()

        for task in tasks:
            try:
                # タスクデータの内容をログ出力
                self.logger.debug(
                    "HomeContent: タスクデータ処理開始",
                    task_id=task.get("id"),
                    task_data=task,
                )

                # TextWithSubtitleWithDeleteIconを使用してタスクアイテムを作成
                task_item = TextWithSubtitleWithDeleteIcon(
                    text=f"タスクID: {task.get('id', '')}",
                    subtitle=task.get("from_folder_name", "未設定"),
                    on_click=lambda e, task_id=task.get("id"): self.on_task_selected(
                        task_id
                    ),
                    on_delete=lambda e, task_id=task.get("id"): self.on_task_delete(
                        task_id, e
                    ),
                )

                self.task_items_column.controls.append(task_item)
                self.logger.debug(
                    "HomeContent: タスクアイテム追加完了", task_id=task.get("id")
                )
            except Exception as e:
                self.logger.error(
                    "HomeContent: タスクアイテムの作成中にエラー発生",
                    task_id=task.get("id", "unknown"),
                    error=str(e),
                    task_data=task,
                )
                continue

        self.task_items_column.controls.append(self.add_button_container)
        self.logger.debug(
            "HomeContent: タスクリスト作成完了",
            total_items=len(self.task_items_column.controls),
        )

    def update_task_list(self, tasks):
        """タスクリストを更新する（ページに追加された後に呼び出す）"""
        self.logger.info("HomeContent: タスクリスト更新開始", task_count=len(tasks))
        self._create_task_list(tasks)

        # ページに追加されている場合のみupdateを呼び出す
        if hasattr(self, "page") and self.page:
            self.update()
            self.logger.debug("HomeContent: UI更新完了")

    def _show_dialog(self, dialog):
        """ダイアログを表示する共通メソッド"""
        if hasattr(self, "page") and self.page:
            # 前のダイアログが開いていれば閉じる
            self._close_current_dialog()
            # 新しいダイアログを表示
            self._current_dialog = dialog
            self._is_dialog_open = True
            self.page.open(dialog)
            self.page.update()

    def _close_current_dialog(self):
        """現在開いているダイアログを閉じる"""
        if self._current_dialog is not None and self._is_dialog_open:
            self.page.close(self._current_dialog)
            self._current_dialog = None
            self._is_dialog_open = False
            self.page.update()

    def _close_dialog(self, e):
        """ダイアログを閉じるコールバック関数"""
        self._close_current_dialog()

    def show_extraction_completed_dialog(self, task_id, status):
        """
        メール抽出完了ダイアログを表示する

        Args:
            task_id: タスクID
            status: スナップショットと抽出計画の状態
        """
        self.logger.info(
            "HomeContent: メール抽出完了ダイアログを表示します",
            task_id=task_id,
            status=status,
        )

        # タスクの状態を取得
        task_status = status.get("task_status", "unknown")
        task_message = status.get("task_message", "情報がありません")

        # ステータス情報を詳細にログ出力
        self.logger.debug(
            "HomeContent: タスク状態情報",
            task_id=task_id,
            task_status=task_status,
            task_message=task_message,
            status_dict=str(status),
        )

        # 状態に応じたメッセージとタイトルを設定
        if task_status == "completed":
            title = "メール抽出完了"
            message = "メールの抽出処理が完了しました。"
        elif task_status == "error":
            title = "メール抽出エラー"
            message = f"メール抽出中にエラーが発生しました。\n{task_message}"
        else:
            title = "メール抽出状態"
            message = f"メール抽出の状態: {task_status}\n{task_message}"

        def close_extraction_dialog(e):
            # ダイアログを閉じる
            self._close_current_dialog()

            # 完了の場合のみプレビュー画面に移動
            if task_status == "completed":
                self.navigate_to_preview(task_id, task_status)
            else:
                # 完了以外の場合はメッセージ表示
                if hasattr(self, "page") and self.page:
                    incomplete_dialog = ft.AlertDialog(
                        modal=True,
                        title=ft.Text("抽出未完了"),
                        content=ft.Text(
                            "メール抽出処理が完了していないため、プレビュー画面に移動できません。"
                        ),
                        actions=[
                            ft.TextButton("OK", on_click=self._close_dialog),
                        ],
                        actions_alignment=ft.MainAxisAlignment.END,
                        shape=ft.RoundedRectangleBorder(
                            radius=AppTheme.CONTAINER_BORDER_RADIUS
                        ),
                    )
                    self._show_dialog(incomplete_dialog)

        # 確認ダイアログを作成
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Column(
                [
                    ft.Text(message),
                ],
                spacing=10,
                tight=True,
            ),
            actions=[
                ft.TextButton("OK", on_click=close_extraction_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=AppTheme.CONTAINER_BORDER_RADIUS),
        )

        # ダイアログを表示
        self._show_dialog(dialog)
        self.logger.debug(
            "HomeContent: メール抽出完了ダイアログ表示完了", task_id=task_id
        )

    def navigate_to_preview(self, task_id, task_status):
        """プレビュー画面に遷移する"""
        self.logger.info(
            f"HomeContent: プレビュー画面への遷移開始 - {task_id}, ステータス: {task_status}"
        )
        # エラーでない場合のみ画面遷移
        if task_status != "error":
            try:
                if self.main_viewmodel:
                    self.main_viewmodel.set_current_task_id(task_id)
                    self.main_viewmodel.set_destination("preview")
                    self.logger.info(
                        f"HomeContent: MainViewModelを使用して画面遷移 - {task_id}"
                    )
                    # 確実に更新されるようにページ更新を追加
                    if hasattr(self, "page") and self.page:
                        self.page.update()
                else:
                    # HomeViewModelのselect_taskメソッドを使用（非同期版）
                    if hasattr(self, "page") and self.page:

                        async def run_select_task():
                            await self._handle_home_viewmodel_select_task(task_id)

                        self.page.run_task(run_select_task)
                        self.logger.info(
                            f"HomeContent: HomeViewModelを使用して画面遷移タスク開始 - {task_id}"
                        )
            except Exception as e:
                self.logger.error(
                    "HomeContent: プレビュー画面への遷移でエラー発生",
                    task_id=task_id,
                    error=str(e),
                )
                # エラーメッセージを表示
                if hasattr(self, "page") and self.page:
                    # ダイアログを作成
                    dialog = ft.AlertDialog(
                        modal=True,
                        title=ft.Text("エラー"),
                        content=ft.Text(
                            "プレビュー画面への遷移中にエラーが発生しました。"
                        ),
                        actions=[
                            ft.TextButton("OK", on_click=self._close_dialog),
                        ],
                        actions_alignment=ft.MainAxisAlignment.END,
                        shape=ft.RoundedRectangleBorder(
                            radius=AppTheme.CONTAINER_BORDER_RADIUS
                        ),
                    )
                    self._show_dialog(dialog)

    def on_task_selected(self, task_id):
        """タスク選択時の処理"""
        self.logger.info(f"HomeContent: タスク選択 - {task_id}")
        self.logger.debug(
            "HomeContent: contents_viewmodelの状態確認",
            has_contents_viewmodel=self.contents_viewmodel is not None,
        )

        # 非同期処理を実行するために、page.run_taskを使用
        if hasattr(self, "page") and self.page:
            # コルーチンオブジェクトをasyncio.run_coroutineでラップする
            async def run_task():
                await self._handle_task_selection(task_id)

            self.page.run_task(run_task)
            self.logger.info(f"HomeContent: 非同期タスク実行開始 - {task_id}")

    async def _handle_task_selection(self, task_id):
        """タスク選択の非同期処理"""
        # タスクIDを設定
        try:
            self.logger.debug(
                "HomeContent: 非同期処理開始",
                task_id=task_id,
                has_main_viewmodel=self.main_viewmodel is not None,
            )

            # タスクの状態を確認
            status = self.contents_viewmodel.check_snapshot_and_extraction_plan(task_id)
            self.logger.debug(f"HomeContent: タスク状態確認 - {status}")

            # 抽出が完了している場合は、直接プレビュー画面に遷移
            if status["extraction_completed"]:
                self.logger.info(
                    "HomeContent: 抽出は完了しています。プレビュー画面に遷移します"
                )
                self.navigate_to_preview(
                    task_id, status.get("task_status", "completed")
                )
                return

            # 抽出が進行中の場合は、進捗ダイアログを表示してプレビュー画面に遷移
            if status["extraction_in_progress"]:
                self.logger.info(
                    "HomeContent: 抽出は進行中です。プレビュー画面に遷移します"
                )
                # ここでは確認なしで直接プレビュー画面に遷移
                if self.main_viewmodel:
                    self.main_viewmodel.set_current_task_id(task_id)
                    self.main_viewmodel.set_destination("preview")
                else:
                    await self._handle_home_viewmodel_select_task(task_id)
                return

            # 抽出が進行中でも完了でもない場合は、抽出確認ダイアログを表示せずに直接抽出開始
            self.logger.info("HomeContent: 抽出を開始します")

            # タスクID設定
            result = await self.contents_viewmodel.set_current_task_id(task_id)

            if not result:
                self.logger.error(f"HomeContent: タスクID設定に失敗 - {task_id}")
                if hasattr(self, "page") and self.page:
                    # ダイアログを作成
                    dialog = ft.AlertDialog(
                        modal=True,
                        title=ft.Text("エラー"),
                        content=ft.Text("タスクの処理中にエラーが発生しました。"),
                        actions=[
                            ft.TextButton("OK", on_click=self._close_dialog),
                        ],
                        actions_alignment=ft.MainAxisAlignment.END,
                        shape=ft.RoundedRectangleBorder(
                            radius=AppTheme.CONTAINER_BORDER_RADIUS
                        ),
                    )
                    self._show_dialog(dialog)
                return

            # 直接抽出を開始 - ProgressDialogを表示し、完了を待機
            success = (
                await self.contents_viewmodel._start_extraction_without_confirmation(
                    task_id
                )
            )

            if success:
                # 抽出が成功したらプレビュー画面に遷移
                if self.main_viewmodel:
                    self.main_viewmodel.set_current_task_id(task_id)
                    self.main_viewmodel.set_destination("preview")
                else:
                    await self._handle_home_viewmodel_select_task(task_id)
            else:
                self.logger.error(f"HomeContent: メール抽出に失敗 - {task_id}")
                # エラーメッセージはProgressDialogで既に表示されているので、ここでは何もしない

        except Exception as e:
            self.logger.error(
                "HomeContent: タスクID設定または画面遷移でエラー発生", error=str(e)
            )

    async def _handle_home_viewmodel_select_task(self, task_id):
        """HomeViewModelのselect_taskメソッドを非同期で呼び出す"""
        try:
            self.logger.debug(f"HomeContent: select_task開始 - {task_id}")
            # HomeViewModelのselect_taskメソッドを非同期で呼び出す
            result = await self.home_viewmodel.select_task(task_id)
            self.logger.info(
                f"HomeContent: HomeViewModelのselect_task完了 - {task_id}, 結果: {result}"
            )
            return result
        except Exception as e:
            self.logger.error(
                "HomeContent: HomeViewModelのselect_task呼び出しでエラー発生",
                task_id=task_id,
                error=str(e),
            )
            return False

    def on_task_delete(self, task_id, e):
        """タスク削除時の処理"""
        self.logger.info("HomeContent: タスク削除処理開始", task_id=task_id)

        # 削除確認ダイアログを表示
        def confirm_delete(e):
            # まずダイアログを閉じる
            self._close_current_dialog()

            if e.control.data == "yes":
                self.logger.info("HomeContent: タスク削除確認", task_id=task_id)
                try:
                    # タスクを削除
                    success = self.home_viewmodel.delete_task(task_id)
                    if success:
                        # 削除したタスクが現在表示中のタスクの場合は、current_task_idをクリアする
                        if self.main_viewmodel:
                            current_task_id = self.main_viewmodel.get_current_task_id()
                            if current_task_id == task_id:
                                # 現在のタスクIDをクリア
                                self.main_viewmodel.set_current_task_id(None)
                                # ホーム画面に戻す（プレビュー画面を初期化するため）
                                self.main_viewmodel.set_destination("home")
                                self.logger.info(
                                    "HomeContent: 現在表示中のタスクを削除したため、ホーム画面に戻します",
                                    task_id=task_id,
                                )

                        # タスクリストを再取得して更新
                        tasks = self.home_viewmodel.load_tasks()
                        self.update_task_list(tasks)
                        # 成功メッセージを表示
                        delete_success_dialog = ft.AlertDialog(
                            modal=True,
                            title=ft.Text("削除成功"),
                            content=ft.Text(f"タスクID: {task_id} が削除されました"),
                            actions=[
                                ft.TextButton(
                                    "OK",
                                    on_click=self._close_dialog,
                                ),
                            ],
                            actions_alignment=ft.MainAxisAlignment.END,
                            shape=ft.RoundedRectangleBorder(
                                radius=AppTheme.CONTAINER_BORDER_RADIUS
                            ),
                        )
                        self._show_dialog(delete_success_dialog)
                        self.logger.info("HomeContent: タスク削除成功", task_id=task_id)
                    else:
                        # エラーメッセージを表示
                        delete_error_dialog = ft.AlertDialog(
                            modal=True,
                            title=ft.Text("削除エラー"),
                            content=ft.Text(
                                f"タスクID: {task_id} の削除に失敗しました。ファイルが使用中または権限が不足している可能性があります。"
                            ),
                            actions=[
                                ft.TextButton(
                                    "OK",
                                    on_click=self._close_dialog,
                                ),
                            ],
                            actions_alignment=ft.MainAxisAlignment.END,
                            shape=ft.RoundedRectangleBorder(
                                radius=AppTheme.CONTAINER_BORDER_RADIUS
                            ),
                        )
                        self._show_dialog(delete_error_dialog)
                        self.logger.error(
                            "HomeContent: タスク削除失敗", task_id=task_id
                        )
                except Exception as ex:
                    # 予期せぬエラーメッセージを表示
                    delete_exception_dialog = ft.AlertDialog(
                        modal=True,
                        title=ft.Text("削除エラー"),
                        content=ft.Text(
                            f"タスクID: {task_id} の削除中にエラーが発生しました: {str(ex)}"
                        ),
                        actions=[
                            ft.TextButton(
                                "OK",
                                on_click=self._close_dialog,
                            ),
                        ],
                        actions_alignment=ft.MainAxisAlignment.END,
                        shape=ft.RoundedRectangleBorder(
                            radius=AppTheme.CONTAINER_BORDER_RADIUS
                        ),
                    )
                    self._show_dialog(delete_exception_dialog)
                    self.logger.error(
                        "HomeContent: タスク削除中にエラー発生",
                        task_id=task_id,
                        error=str(ex),
                    )
            else:
                self.logger.info("HomeContent: タスク削除キャンセル", task_id=task_id)

        # 確認ダイアログを作成
        dialog = ft.AlertDialog(
            modal=True,  # モーダルダイアログとして表示
            title=ft.Text("タスク削除の確認"),
            content=ft.Text(f"タスクID: {task_id} を削除してもよろしいですか？"),
            actions=[
                ft.TextButton("いいえ", on_click=confirm_delete, data="no"),
                ft.TextButton(
                    "はい",
                    on_click=confirm_delete,
                    data="yes",
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=AppTheme.CONTAINER_BORDER_RADIUS),
        )

        # ダイアログを表示
        self._show_dialog(dialog)
        self.logger.debug("HomeContent: 削除確認ダイアログ表示", task_id=task_id)

    def on_add_task_click(self, e):
        """新規タスク追加ボタンクリック時の処理"""
        self.logger.info("HomeContent: 新規タスク追加ボタンクリック")
        # タスク設定画面に遷移
        if self.main_viewmodel:
            self.main_viewmodel.set_destination("task")
        else:
            self.home_viewmodel.set_destination("task")
