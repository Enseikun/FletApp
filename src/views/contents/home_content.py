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
    MVVMパターンのView部分を担当
    """

    def __init__(self, contents_viewmodel):
        """初期化"""

        super().__init__()
        self.logger = get_logger()
        self.logger.info("HomeContent: 初期化開始")

        # ダイアログ管理用の変数（UI表示に関わる部分なのでViewが管理）
        self._current_dialog = None
        self._is_dialog_open = False

        # ViewModelの取得または作成（依存性注入パターン）
        self.contents_viewmodel = (
            contents_viewmodel if contents_viewmodel else HomeContentViewModel()
        )

        # MainViewModelへの参照を取得
        self.main_viewmodel = None
        if (
            hasattr(self.contents_viewmodel, "main_viewmodel")
            and self.contents_viewmodel.main_viewmodel
        ):
            self.main_viewmodel = self.contents_viewmodel.main_viewmodel
            self.logger.info("HomeContent: MainViewModelを取得しました")

        # 抽出完了時のUIコールバックを設定（HomeContentViewModelの場合のみ）
        if hasattr(self.contents_viewmodel, "set_extraction_completed_callback"):
            self.contents_viewmodel.set_extraction_completed_callback(
                self._show_extraction_completed_dialog
            )
            self.logger.info("HomeContent: 抽出完了コールバックを設定しました")
        else:
            self.logger.info(
                "HomeContent: 抽出完了コールバックはサポートされていません"
            )

        # HomeViewModelのインスタンスを取得または作成
        self.home_viewmodel = HomeViewModel(
            self.main_viewmodel or self.contents_viewmodel
        )

        # タスクリストを表示するコントロールを作成
        self.task_items_column = ft.Column(
            scroll=ft.ScrollMode.AUTO, spacing=10, expand=True
        )

        # 新規タスク追加ボタン
        self.add_button = AddButton(
            on_click=self._on_add_task_click,
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
        self.logger.debug(
            f"HomeContent: タスクリスト作成開始 - task_count: {len(tasks)}"
        )
        self.task_items_column.controls.clear()

        for task in tasks:
            try:
                # タスクデータの内容をログ出力
                self.logger.debug(
                    f"HomeContent: タスクデータ処理開始 - task_id: {task.get('id')}"
                )

                # TextWithSubtitleWithDeleteIconを使用してタスクアイテムを作成
                task_item = TextWithSubtitleWithDeleteIcon(
                    text=f"タスクID: {task.get('id', '')}",
                    subtitle=task.get("from_folder_name", "未設定"),
                    on_click=lambda e, task_id=task.get("id"): self._on_task_selected(
                        task_id
                    ),
                    on_delete=lambda e, task_id=task.get("id"): self._on_task_delete(
                        task_id, e
                    ),
                )

                self.task_items_column.controls.append(task_item)
                self.logger.debug(
                    f"HomeContent: タスクアイテム追加完了 - task_id: {task.get('id')}"
                )
            except Exception as e:
                error_msg = f"HomeContent: タスクアイテムの作成中にエラー発生 - task_id: {task.get('id', 'unknown')}, error: {str(e)}"
                self.logger.error(error_msg)
                continue

        self.task_items_column.controls.append(self.add_button_container)
        self.logger.debug(
            f"HomeContent: タスクリスト作成完了 - total_items: {len(self.task_items_column.controls)}"
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

    def _show_extraction_completed_dialog(self, task_id, status):
        """
        メール抽出完了ダイアログを表示する（ViewModelからのコールバック）

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
                ft.TextButton(
                    "OK",
                    on_click=lambda e: self._on_extraction_dialog_closed(
                        e, task_id, task_status
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=AppTheme.CONTAINER_BORDER_RADIUS),
        )

        # ダイアログを表示
        self._show_dialog(dialog)
        self.logger.debug(
            "HomeContent: メール抽出完了ダイアログ表示完了", task_id=task_id
        )

    def _on_extraction_dialog_closed(self, e, task_id, task_status):
        """抽出完了ダイアログが閉じられたときの処理"""
        # ダイアログを閉じる
        self._close_current_dialog()

        # ViewModelに抽出完了後の処理を委譲（完了ステータスに基づいて画面遷移を判断）
        if hasattr(self, "page") and self.page:

            async def handle_extraction_completion():
                # ViewModelがハンドラーメソッドを持っているか確認
                should_navigate = False
                if hasattr(self.contents_viewmodel, "handle_extraction_completion"):
                    should_navigate = (
                        await self.contents_viewmodel.handle_extraction_completion(
                            task_id, task_status
                        )
                    )
                else:
                    # ViewModel側に実装がない場合はデフォルトとして完了のみナビゲーション
                    should_navigate = task_status == "completed"

                if should_navigate:
                    self._navigate_to_preview(task_id)
                else:
                    # 完了以外の場合はメッセージ表示
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

            self.page.run_task(handle_extraction_completion)

    def _navigate_to_preview(self, task_id):
        """プレビュー画面に遷移する（単純な画面遷移処理のみ）"""
        self.logger.info(f"HomeContent: プレビュー画面への遷移開始 - {task_id}")

        try:
            # MainViewModelがある場合はそれを使用
            if self.main_viewmodel:
                # タスクIDを先に設定してから遷移
                self.main_viewmodel.set_current_task_id(task_id)
                # 少し待機してタスクIDの設定が確実に反映されるようにする
                if hasattr(self, "page") and self.page:
                    # 画面遷移
                    self.main_viewmodel.set_destination("preview")
                    self.logger.info(
                        f"HomeContent: MainViewModelを使用して画面遷移 - {task_id}"
                    )
                    # 確実に更新されるようにページ更新を追加
                    self.page.update()
            # MainViewModelがない場合はHomeViewModelを使用
            elif hasattr(self, "page") and self.page:

                async def run_select_task():
                    result = await self._handle_home_viewmodel_select_task(task_id)
                    # 結果をログに記録
                    self.logger.info(f"HomeContent: select_task実行結果 - {result}")

                self.page.run_task(run_select_task)
                self.logger.info(
                    f"HomeContent: HomeViewModelを使用して画面遷移タスク開始 - {task_id}"
                )
        except Exception as e:
            error_msg = (
                f"HomeContent: プレビュー画面への遷移でエラー発生 - {task_id}: {str(e)}"
            )
            self.logger.error(error_msg)
            self._show_navigation_error_dialog()

    def _show_navigation_error_dialog(self):
        """画面遷移エラーダイアログを表示"""
        if hasattr(self, "page") and self.page:
            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("エラー"),
                content=ft.Text("プレビュー画面への遷移中にエラーが発生しました。"),
                actions=[
                    ft.TextButton("OK", on_click=self._close_dialog),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
                shape=ft.RoundedRectangleBorder(
                    radius=AppTheme.CONTAINER_BORDER_RADIUS
                ),
            )
            self._show_dialog(dialog)

    def _on_task_selected(self, task_id):
        """タスク選択時の処理"""
        self.logger.info(f"HomeContent: タスク選択 - {task_id}")

        # 非同期処理を実行するために、page.run_taskを使用
        if hasattr(self, "page") and self.page:

            async def run_task():
                # ViewModelがハンドラーメソッドを持っているか確認
                if hasattr(self.contents_viewmodel, "handle_task_selection"):
                    # ViewModelに処理を委譲
                    result = await self.contents_viewmodel.handle_task_selection(
                        task_id
                    )

                    # 結果に応じて画面遷移
                    if result.get("should_navigate", False):
                        self._navigate_to_preview(task_id)
                    elif result.get("show_progress", False):
                        # 進捗ダイアログはViewModelが表示済みなので何もしない
                        pass
                    elif result.get("error"):
                        # エラーダイアログを表示
                        error_dialog = ft.AlertDialog(
                            modal=True,
                            title=ft.Text("エラー"),
                            content=ft.Text(
                                result.get(
                                    "error_message",
                                    "タスク処理中にエラーが発生しました。",
                                )
                            ),
                            actions=[
                                ft.TextButton("OK", on_click=self._close_dialog),
                            ],
                            actions_alignment=ft.MainAxisAlignment.END,
                            shape=ft.RoundedRectangleBorder(
                                radius=AppTheme.CONTAINER_BORDER_RADIUS
                            ),
                        )
                        self._show_dialog(error_dialog)
                else:
                    # ViewModelが必要なメソッドを持っていない場合は直接ホームビューモデルを使用
                    await self._handle_home_viewmodel_select_task(task_id)

            self.page.run_task(run_task)
            self.logger.info(f"HomeContent: 非同期タスク実行開始 - {task_id}")

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
            # エラーログの書き方を修正：task_idとerrorを一つのメッセージにまとめる
            error_message = f"HomeContent: HomeViewModelのselect_task呼び出しでエラー発生 - TaskID: {task_id}, Error: {str(e)}"
            self.logger.error(error_message)

            # エラーが発生した場合はダイアログを表示
            if hasattr(self, "page") and self.page:
                error_dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("エラー"),
                    content=ft.Text(f"タスク選択中にエラーが発生しました: {str(e)}"),
                    actions=[
                        ft.TextButton("OK", on_click=self._close_dialog),
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                    shape=ft.RoundedRectangleBorder(
                        radius=AppTheme.CONTAINER_BORDER_RADIUS
                    ),
                )
                self._show_dialog(error_dialog)
            return False

    def _on_task_delete(self, task_id, e):
        """タスク削除時の処理"""
        self.logger.info("HomeContent: タスク削除処理開始", task_id=task_id)

        # 削除確認ダイアログを表示
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("タスク削除の確認"),
            content=ft.Text(f"タスクID: {task_id} を削除してもよろしいですか？"),
            actions=[
                ft.TextButton("いいえ", on_click=self._close_dialog),
                ft.TextButton(
                    "はい",
                    on_click=lambda e: self._confirm_delete_task(task_id),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=AppTheme.CONTAINER_BORDER_RADIUS),
        )

        # ダイアログを表示
        self._show_dialog(dialog)
        self.logger.debug("HomeContent: 削除確認ダイアログ表示", task_id=task_id)

    def _confirm_delete_task(self, task_id):
        """タスク削除確認時の処理"""
        # ダイアログを閉じる
        self._close_current_dialog()

        # 削除準備ダイアログを表示
        delete_prep_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("削除準備"),
            content=ft.Column(
                [
                    ft.Text("タスクの削除準備を行います。"),
                    ft.Text("削除を実行する前に以下を確認してください:"),
                    ft.Text("• このタスクに関連する全てのファイルが閉じられていること"),
                    ft.Text("• タスクの添付ファイルを開いていないこと"),
                    ft.Text(
                        "• 他のアプリケーションがタスクのデータにアクセスしていないこと"
                    ),
                    ft.Text(""),
                    ft.Text("続行しますか？", weight="bold"),
                ],
                spacing=5,
                tight=True,
            ),
            actions=[
                ft.TextButton("キャンセル", on_click=self._close_dialog),
                ft.TextButton(
                    "続行",
                    on_click=lambda e: self._execute_task_deletion(task_id),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=AppTheme.CONTAINER_BORDER_RADIUS),
        )

        self._show_dialog(delete_prep_dialog)

    def _execute_task_deletion(self, task_id):
        """タスク削除の実行"""
        self.logger.info("HomeContent: タスク削除実行", task_id=task_id)

        # 現在のダイアログを閉じる
        self._close_current_dialog()

        if hasattr(self, "page") and self.page:

            async def run_delete_task():
                # ViewModelがハンドラーメソッドを持っているか確認
                if hasattr(self.contents_viewmodel, "delete_task_with_preparations"):
                    # ViewModelに削除処理を委譲
                    result = (
                        await self.contents_viewmodel.delete_task_with_preparations(
                            task_id, self.main_viewmodel
                        )
                    )

                    if result.get("success", False):
                        # 成功したら、タスクリストを更新
                        tasks = self.home_viewmodel.load_tasks()
                        self.update_task_list(tasks)

                        # 成功メッセージを表示
                        success_dialog = ft.AlertDialog(
                            modal=True,
                            title=ft.Text("削除成功"),
                            content=ft.Text(f"タスクID: {task_id} が削除されました"),
                            actions=[
                                ft.TextButton("OK", on_click=self._close_dialog),
                            ],
                            actions_alignment=ft.MainAxisAlignment.END,
                            shape=ft.RoundedRectangleBorder(
                                radius=AppTheme.CONTAINER_BORDER_RADIUS
                            ),
                        )
                        self._show_dialog(success_dialog)
                    else:
                        # エラーメッセージを表示
                        error_dialog = ft.AlertDialog(
                            modal=True,
                            title=ft.Text("削除エラー"),
                            content=ft.Column(
                                [
                                    ft.Text(
                                        f"タスクID: {task_id} の削除に失敗しました。"
                                    ),
                                    ft.Text(
                                        result.get(
                                            "error_message", "以下の原因が考えられます:"
                                        )
                                    ),
                                    ft.Text(
                                        "• タスクのファイルが他のアプリケーションで使用中"
                                    ),
                                    ft.Text("• 添付ファイルが開かれている"),
                                    ft.Text("• 権限が不足している"),
                                    ft.Text(""),
                                    ft.Text(
                                        "全てのアプリケーションを閉じてから再試行してください。"
                                    ),
                                ],
                                spacing=5,
                                tight=True,
                            ),
                            actions=[
                                ft.TextButton("OK", on_click=self._close_dialog),
                            ],
                            actions_alignment=ft.MainAxisAlignment.END,
                            shape=ft.RoundedRectangleBorder(
                                radius=AppTheme.CONTAINER_BORDER_RADIUS
                            ),
                        )
                        self._show_dialog(error_dialog)
                else:
                    # 旧実装のままのメソッドを直接使用
                    success = self.home_viewmodel.delete_task(task_id)
                    if success:
                        # 成功したら、タスクリストを更新
                        tasks = self.home_viewmodel.load_tasks()
                        self.update_task_list(tasks)
                        # 成功メッセージを表示
                        success_dialog = ft.AlertDialog(
                            modal=True,
                            title=ft.Text("削除成功"),
                            content=ft.Text(f"タスクID: {task_id} が削除されました"),
                            actions=[
                                ft.TextButton("OK", on_click=self._close_dialog),
                            ],
                            actions_alignment=ft.MainAxisAlignment.END,
                            shape=ft.RoundedRectangleBorder(
                                radius=AppTheme.CONTAINER_BORDER_RADIUS
                            ),
                        )
                        self._show_dialog(success_dialog)
                    else:
                        # エラーメッセージを表示
                        error_dialog = ft.AlertDialog(
                            modal=True,
                            title=ft.Text("削除エラー"),
                            content=ft.Column(
                                [
                                    ft.Text(
                                        f"タスクID: {task_id} の削除に失敗しました。"
                                    ),
                                    ft.Text("以下の原因が考えられます:"),
                                    ft.Text(
                                        "• タスクのファイルが他のアプリケーションで使用中"
                                    ),
                                    ft.Text("• 添付ファイルが開かれている"),
                                    ft.Text("• 権限が不足している"),
                                    ft.Text(""),
                                    ft.Text(
                                        "全てのアプリケーションを閉じてから再試行してください。"
                                    ),
                                ],
                                spacing=5,
                                tight=True,
                            ),
                            actions=[
                                ft.TextButton("OK", on_click=self._close_dialog),
                            ],
                            actions_alignment=ft.MainAxisAlignment.END,
                            shape=ft.RoundedRectangleBorder(
                                radius=AppTheme.CONTAINER_BORDER_RADIUS
                            ),
                        )
                        self._show_dialog(error_dialog)

            self.page.run_task(run_delete_task)

    def _on_add_task_click(self, e):
        """新規タスク追加ボタンクリック時の処理"""
        self.logger.info("HomeContent: 新規タスク追加ボタンクリック")
        # タスク設定画面に遷移（シンプルな画面遷移処理）
        if self.main_viewmodel:
            self.main_viewmodel.set_destination("task")
        else:
            self.home_viewmodel.set_destination("task")
