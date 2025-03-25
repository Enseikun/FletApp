"""
タスク設定コンテンツ
タスクの設定と作成を行うUIを提供するクラス
"""

from datetime import datetime

import flet as ft

from src.viewmodels.task_content_viewmodel import TaskContentViewModel
from src.views.components.icon_dropdown import IconDropdown
from src.views.components.progress_dialog import ProgressDialog
from src.views.styles.style import AppTheme, Colors


class TaskContent(ft.Container):
    """
    タスク設定画面のコンテンツ
    タスクの設定と作成を行うUIを提供
    """

    def __init__(self, contents_viewmodel):
        """初期化"""
        super().__init__()
        self.contents_viewmodel = contents_viewmodel
        self.viewmodel = TaskContentViewModel()
        self.progress_dialog = ProgressDialog()

        # フォームの初期化
        self._init_form()

        # コンテンツの初期化
        self._init_content()

        # コンテナの設定
        self.padding = AppTheme.PAGE_PADDING
        self.bgcolor = AppTheme.PAGE_BGCOLOR
        self.border_radius = AppTheme.CONTAINER_BORDER_RADIUS
        self.expand = True

    def _init_form(self):
        """フォーム要素の初期化"""
        # Outlook接続ボタン
        self.outlook_connect_button = ft.ElevatedButton(
            text="Outlook接続",
            icon=ft.icons.SYNC,
            on_click=lambda e: self.page.run_async(self._on_outlook_connect(e)),
        )

        # フォルダ選択ドロップダウン（送信元）
        self.from_folder_dropdown = IconDropdown(
            icon=ft.icons.FOLDER_OPEN,
            options=[("", "フォルダを選択")],
            on_change=self._on_from_folder_change,
        )

        # フォルダ選択ドロップダウン（送信先）
        self.to_folder_dropdown = IconDropdown(
            icon=ft.icons.FOLDER_SPECIAL,
            options=[("", "フォルダを選択")],
            on_change=self._on_to_folder_change,
        )

        # 日時選択（開始）
        self.start_date_picker = ft.TextField(
            label="開始日時",
            value=self.viewmodel.start_date.strftime("%Y-%m-%d %H:%M"),
            icon=ft.icons.CALENDAR_TODAY,
            on_change=self._on_date_change,
        )

        # 日時選択（終了）
        self.end_date_picker = ft.TextField(
            label="終了日時",
            value=self.viewmodel.end_date.strftime("%Y-%m-%d %H:%M"),
            icon=ft.icons.CALENDAR_TODAY,
            on_change=self._on_date_change,
        )

        # AIレビューのチェックボックス
        self.ai_review_checkbox = ft.Checkbox(
            label="AIレビューを実行",
            value=self.viewmodel.ai_review,
            on_change=self._on_ai_review_change,
        )

        # 添付ファイルダウンロードのチェックボックス
        self.file_download_checkbox = ft.Checkbox(
            label="添付ファイルをダウンロード",
            value=self.viewmodel.file_download,
            on_change=self._on_file_download_change,
        )

        # ダウンロード除外拡張子のテキストエリア
        self.exclude_extensions_textarea = ft.TextField(
            label="ダウンロードを除外する拡張子",
            hint_text="例: exe, dll, bat (カンマ区切りで入力)",
            multiline=False,
            height=100,
            value=self.viewmodel.exclude_extensions,
            disabled=not self.viewmodel.file_download,
            on_change=self._on_exclude_extensions_change,
        )

        # 作成ボタン
        self.create_button = ft.ElevatedButton(
            text="タスクを作成",
            icon=ft.icons.ADD_TASK,
            on_click=self._on_create_task,
            bgcolor=Colors.PRIMARY,
            color=Colors.TEXT_ON_PRIMARY,
        )

        # キャンセルボタン
        self.cancel_button = ft.OutlinedButton(
            text="キャンセル",
            icon=ft.icons.CANCEL,
            on_click=self._on_cancel,
        )

    def _init_content(self):
        """コンテンツの初期化"""
        # フォーム要素をレイアウト
        form_column = ft.Column(
            controls=[
                self.outlook_connect_button,
                ft.Text("フォルダ設定", size=16, weight="bold"),
                ft.Text("移動元フォルダ", size=14),
                self.from_folder_dropdown,
                ft.Text("移動先フォルダ", size=14),
                self.to_folder_dropdown,
                ft.Divider(),
                ft.Text("期間設定", size=16, weight="bold"),
                ft.Row(
                    [
                        ft.Column(
                            [ft.Text("開始日時", size=14), self.start_date_picker],
                            expand=1,
                        ),
                        ft.Column(
                            [ft.Text("終了日時", size=14), self.end_date_picker],
                            expand=1,
                        ),
                    ]
                ),
                ft.Divider(),
                ft.Text("オプション", size=16, weight="bold"),
                self.ai_review_checkbox,
                self.file_download_checkbox,
                ft.Container(
                    content=self.exclude_extensions_textarea,
                    visible=self.viewmodel.file_download,
                ),
                ft.Divider(),
                ft.Container(
                    content=ft.Row(
                        [
                            self.cancel_button,
                            ft.Container(width=10),  # スペーサー
                            self.create_button,
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(top=20),
                ),
            ],
            spacing=AppTheme.SPACING_MD,
            scroll=ft.ScrollMode.AUTO,
        )

        # メインコンテンツ
        content = ft.Column(
            controls=[
                ft.Text("タスク設定", size=AppTheme.TITLE_SIZE, weight="bold"),
                ft.Divider(),
                form_column,
            ],
            spacing=AppTheme.SPACING_MD,
            scroll=ft.ScrollMode.AUTO,
        )

        # コンテナのコンテンツを設定
        self.content = content

    async def _on_outlook_connect(self, e):
        """Outlook接続ボタンクリック時の処理"""
        await self.progress_dialog.show_async(
            "接続中", "Outlookに接続しています...", max_value=0
        )  # Indeterminate mode
        self.viewmodel.connect_outlook()
        self._update_folders()
        await self.progress_dialog.close_async()  # 接続完了後にダイアログを閉じる

    def _update_folders(self):
        """フォルダ選択肢を更新"""
        folders = self.viewmodel.get_folders()
        folder_options = [("", "フォルダを選択")]
        folder_options.extend([(folder["id"], folder["name"]) for folder in folders])

        self.from_folder_dropdown.update_options(folder_options)
        self.to_folder_dropdown.update_options(folder_options)

        # 値をリセット
        self.from_folder_dropdown.set_value("")
        self.to_folder_dropdown.set_value("")

    def _on_from_folder_change(self, e):
        """送信元フォルダ選択時の処理"""
        self.viewmodel.from_folder_id = e.control.value

    def _on_to_folder_change(self, e):
        """送信先フォルダ選択時の処理"""
        try:
            self.viewmodel.to_folder_id = e.control.value
        except ValueError as ex:
            self.show_error(str(ex))
            # 値を元に戻す
            self.to_folder_dropdown.set_value("")

    def _on_date_change(self, e):
        """日時変更時の処理"""
        try:
            if e.control == self.start_date_picker:
                self.viewmodel.start_date = datetime.strptime(
                    e.control.value, "%Y-%m-%d %H:%M"
                )
                # 終了日時が開始日時より前の場合、終了日時を調整
                if self.viewmodel.end_date < self.viewmodel.start_date:
                    self.end_date_picker.value = self.viewmodel.end_date.strftime(
                        "%Y-%m-%d %H:%M"
                    )
                    self.end_date_picker.update()
            elif e.control == self.end_date_picker:
                self.viewmodel.end_date = datetime.strptime(
                    e.control.value, "%Y-%m-%d %H:%M"
                )
        except ValueError as ex:
            self.show_error(str(ex))
            # 値を元に戻す
            if e.control == self.start_date_picker:
                e.control.value = self.viewmodel.start_date.strftime("%Y-%m-%d %H:%M")
            else:
                e.control.value = self.viewmodel.end_date.strftime("%Y-%m-%d %H:%M")
            e.control.update()

    def _on_ai_review_change(self, e):
        """AIレビュー設定変更時の処理"""
        self.viewmodel.ai_review = e.control.value

    def _on_file_download_change(self, e):
        """添付ファイルダウンロードオプション変更時の処理"""
        self.viewmodel.file_download = e.control.value
        # テキストエリアの表示/非表示を切り替え
        self.exclude_extensions_textarea.disabled = not e.control.value
        self.exclude_extensions_textarea.parent.visible = e.control.value
        self.update()

    def _on_exclude_extensions_change(self, e):
        """除外拡張子変更時の処理"""
        self.viewmodel.exclude_extensions = e.control.value

    def _on_create_task(self, e):
        """タスク作成ボタンクリック時の処理"""
        try:
            success = self.viewmodel.create_task()
            if success:
                self._show_success_message("タスクが正常に作成されました")
                self._reset_form()
            else:
                self.show_error("タスクの作成に失敗しました")
        except ValueError as ex:
            self.show_error(str(ex))

    def show_error(self, message):
        """エラーメッセージを表示"""
        # 実際の実装ではダイアログやスナックバーでエラーを表示
        print(f"エラー: {message}")

    def _show_success_message(self, message):
        """成功メッセージを表示"""
        # 実際の実装ではダイアログやスナックバーで成功メッセージを表示
        print(f"成功: {message}")

    def _reset_form(self):
        """フォームをリセット"""
        self.viewmodel.reset_form()

        # UIの更新
        self.from_folder_dropdown.update_options([("", "フォルダを選択")])
        self.to_folder_dropdown.update_options([("", "フォルダを選択")])
        self.start_date_picker.value = self.viewmodel.start_date.strftime(
            "%Y-%m-%d %H:%M"
        )
        self.end_date_picker.value = self.viewmodel.end_date.strftime("%Y-%m-%d %H:%M")
        self.ai_review_checkbox.value = self.viewmodel.ai_review
        self.file_download_checkbox.value = self.viewmodel.file_download
        self.exclude_extensions_textarea.value = self.viewmodel.exclude_extensions
        self.exclude_extensions_textarea.disabled = not self.viewmodel.file_download
        self.exclude_extensions_textarea.parent.visible = self.viewmodel.file_download

        self.update()

    def _on_cancel(self, e):
        """キャンセルボタンクリック時の処理"""
        # ホーム画面に戻る
        if self.contents_viewmodel and hasattr(
            self.contents_viewmodel, "main_viewmodel"
        ):
            self.contents_viewmodel.main_viewmodel.set_destination("home")
