"""
タスク設定コンテンツ
タスクの設定と作成を行うUIを提供するクラス
"""

import os
from datetime import datetime

import flet as ft

from src.core.logger import get_logger
from src.viewmodels.task_content_viewmodel import TaskContentViewModel
from src.views.components.alert_dialog import AlertDialog
from src.views.components.simple_dropdown import SimpleDropdown
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
        self.logger = get_logger()

        # AlertDialogインスタンスを取得
        self.alert_dialog = AlertDialog()

        # フォームの初期化
        self._init_form()

        # コンテンツの初期化
        self._init_content()

        # コンテナの設定
        self.padding = AppTheme.PAGE_PADDING
        self.bgcolor = AppTheme.PAGE_BGCOLOR
        self.border_radius = AppTheme.CONTAINER_BORDER_RADIUS
        self.expand = True

        self.logger.info("TaskContentの初期化が完了しました")

    def _init_form(self):
        """フォーム要素の初期化"""
        # Outlook接続ボタン
        self.outlook_connect_button = ft.ElevatedButton(
            text="Outlook接続",
            icon=ft.icons.SYNC,
            on_click=self._on_outlook_connect,
            bgcolor=Colors.PRIMARY,
            color=Colors.TEXT_ON_PRIMARY,
        )

        # フォルダ選択ドロップダウン（送信元）
        self.from_folder_dropdown = SimpleDropdown(
            icon=ft.icons.FOLDER_OPEN,
            options=[("", "フォルダを選択")],
            on_change=self._on_from_folder_change,
        )

        # フォルダ選択ドロップダウン（送信先）
        self.to_folder_dropdown = SimpleDropdown(
            icon=ft.icons.FOLDER_SPECIAL,
            options=[("", "フォルダを選択")],
            on_change=self._on_to_folder_change,
        )

        # 日時選択（開始）
        self.start_date_picker = ft.TextField(
            label="開始日時",
            value=self.viewmodel.start_date.strftime("%Y-%m-%d %H:%M"),
            icon=ft.icons.CALENDAR_TODAY,
            on_submit=self._on_date_submit,
            on_blur=self._on_date_blur,
        )

        # 日時選択（終了）
        self.end_date_picker = ft.TextField(
            label="終了日時",
            value=self.viewmodel.end_date.strftime("%Y-%m-%d %H:%M"),
            icon=ft.icons.CALENDAR_TODAY,
            on_submit=self._on_date_submit,
            on_blur=self._on_date_blur,
        )

        # AIレビューのチェックボックス（メール単位）
        self.ai_review_mail_unit_checkbox = ft.Checkbox(
            label="AIレビュー（メール単位）を実行",
            value=self.viewmodel.ai_review_mail_unit,
            on_change=self._on_ai_review_mail_unit_change,
        )
        # AIレビューのチェックボックス（会話単位）
        self.ai_review_thread_unit_checkbox = ft.Checkbox(
            label="AIレビュー（会話単位）を実行",
            value=self.viewmodel.ai_review_thread_unit,
            on_change=self._on_ai_review_thread_unit_change,
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

        # フォームコンテナ
        self.form_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("フォルダ設定", size=16, weight="bold"),
                    ft.Text("移動元フォルダ", size=14),
                    self.from_folder_dropdown,
                    ft.Text("移動先フォルダ（任意）", size=14),
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
                    self.ai_review_mail_unit_checkbox,
                    self.ai_review_thread_unit_checkbox,
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
            ),
            visible=False,  # 初期状態では非表示
        )

    def _init_content(self):
        """コンテンツの初期化"""
        # メインコンテンツ
        content = ft.Column(
            controls=[
                ft.Text("タスク設定", size=AppTheme.TITLE_SIZE, weight="bold"),
                ft.Divider(),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Container(
                                content=self.outlook_connect_button,
                                alignment=ft.alignment.center,
                            ),
                            ft.Container(
                                content=ft.Row(
                                    [self.cancel_button],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                                alignment=ft.alignment.center,
                                margin=ft.margin.only(top=20),
                            ),
                        ],
                        spacing=AppTheme.SPACING_MD,
                    ),
                ),
                self.form_container,
            ],
            spacing=AppTheme.SPACING_MD,
            scroll=ft.ScrollMode.AUTO,
        )

        # コンテナのコンテンツを設定
        self.content = content

        # 最初のキャンセルボタンのコンテナを保持
        self.initial_cancel_container = content.controls[2].content.controls[1]
        # Outlook接続ボタンのコンテナを保持
        self.outlook_connect_container = content.controls[2].content.controls[0]

    def _filter_folders_by_root(self, folders, root):
        """指定されたrootフォルダに属するフォルダのみをフィルタリング"""
        return [
            ft.dropdownm2.Option(key=folder["entry_id"], text=folder["path"])
            for folder in folders
            if os.path.normpath(folder["path"]).split(os.sep)[2] == root
        ]

    async def _update_folders(self):
        """フォルダ選択肢を更新"""
        # フォルダ情報を取得
        folders = self.viewmodel.get_folder_info()
        if not folders:
            return

        # フォルダパスをドロップダウン用の形式に変換（タプルリストに変更）
        from_options = [(folder["entry_id"], folder["path"]) for folder in folders]
        to_options = [(folder["entry_id"], folder["path"]) for folder in folders]

        # デフォルトオプションを追加
        from_options.insert(0, ("", "フォルダを選択"))
        to_options.insert(0, ("", "フォルダを選択"))

        # ドロップダウンの選択肢を更新
        self.from_folder_dropdown.update_options(from_options)
        self.to_folder_dropdown.update_options(to_options)

        # 値をリセット
        self.from_folder_dropdown.set_value("")
        self.to_folder_dropdown.set_value("")

    async def _on_outlook_connect(self, e):
        """Outlook接続ボタンクリック時の処理"""
        self.logger.info("Outlook接続を開始します")
        try:
            # ボタンを無効化
            self.outlook_connect_button.disabled = True
            self.outlook_connect_button.update()

            # Outlook接続を実行
            success = await self.viewmodel.connect_outlook()
            if success:
                await self._update_folders()
                # フォームを表示
                self.form_container.visible = True
                self.form_container.update()
                # Outlook接続ボタンを削除
                self.outlook_connect_container.parent.controls.remove(
                    self.outlook_connect_container
                )
                # 最初のキャンセルボタンを削除
                self.initial_cancel_container.parent.controls.remove(
                    self.initial_cancel_container
                )
                self.initial_cancel_container.parent.update()
                self.logger.info("Outlook接続が成功しました")
            else:
                self.logger.error("Outlook接続に失敗しました")
        except Exception as ex:
            self.logger.error(f"Outlook接続中にエラーが発生しました: {str(ex)}")
        finally:
            # ボタンを再有効化（失敗した場合のみ）
            if not self.form_container.visible:
                self.outlook_connect_button.disabled = False
                self.outlook_connect_button.update()

    def _on_from_folder_change(self, e):
        """送信元フォルダ変更時の処理"""
        selected_value = e.control.value
        # 選択されたフォルダの情報を取得
        folder_info = next(
            (
                f
                for f in self.viewmodel.get_folder_info()
                if f["entry_id"] == selected_value
            ),
            None,
        )
        if folder_info:
            self.viewmodel.from_folder_id = folder_info["entry_id"]
            self.viewmodel.from_folder_path = folder_info["path"]
            self.viewmodel.from_folder_name = folder_info["name"]
            self.viewmodel.store_id = folder_info["store_id"]

            # 移動先フォルダの選択肢を更新
            if selected_value:
                root = os.path.normpath(folder_info["path"]).split(os.sep)[2]
                filtered_folders = [
                    (f["entry_id"], f["path"])
                    for f in self.viewmodel.get_folder_info()
                    if os.path.normpath(f["path"]).split(os.sep)[2] == root
                ]
                filtered_folders.insert(0, ("", "フォルダを選択"))
                self.to_folder_dropdown.update_options(filtered_folders)
            else:
                # 移動元フォルダが未選択の場合、すべてのフォルダを表示
                all_folders = [
                    (f["entry_id"], f["path"]) for f in self.viewmodel.get_folder_info()
                ]
                all_folders.insert(0, ("", "フォルダを選択"))
                self.to_folder_dropdown.update_options(all_folders)

    def _on_to_folder_change(self, e):
        """送信先フォルダ変更時の処理"""
        selected_value = e.control.value
        # 選択されたフォルダの情報を取得
        folder_info = next(
            (
                f
                for f in self.viewmodel.get_folder_info()
                if f["entry_id"] == selected_value
            ),
            None,
        )
        if folder_info:
            self.viewmodel.to_folder_id = folder_info["entry_id"]
            self.viewmodel.to_folder_path = folder_info["path"]

            # 移動元フォルダの選択肢を更新
            if selected_value:
                root = os.path.normpath(folder_info["path"]).split(os.sep)[2]
                filtered_folders = [
                    (f["entry_id"], f["path"])
                    for f in self.viewmodel.get_folder_info()
                    if os.path.normpath(f["path"]).split(os.sep)[2] == root
                ]
                filtered_folders.insert(0, ("", "フォルダを選択"))
                self.from_folder_dropdown.update_options(filtered_folders)
            else:
                # 移動先フォルダが未選択の場合、すべてのフォルダを表示
                all_folders = [
                    (f["entry_id"], f["path"]) for f in self.viewmodel.get_folder_info()
                ]
                all_folders.insert(0, ("", "フォルダを選択"))
                self.from_folder_dropdown.update_options(all_folders)

    def _validate_date(self, value):
        """日時のバリデーション"""
        try:
            value = value.strip()
            if not value:  # 空の場合はスキップ
                return None

            # 日付部分と時刻部分を分離
            parts = value.split()
            if len(parts) == 1:  # 日付のみの場合
                date_str = parts[0]
                time_str = "00:00"  # デフォルト時刻
            else:  # 日付と時刻がある場合
                date_str, time_str = parts

            # 日付のバリデーション
            try:
                date_parts = date_str.split("-")
                if len(date_parts) != 3:
                    raise ValueError("日付形式が不正です")
                year = int(date_parts[0])
                month = int(date_parts[1])
                day = int(date_parts[2])
                if not (1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31):
                    raise ValueError("日付が範囲外です")
            except (ValueError, IndexError):
                raise ValueError("日付形式が不正です")

            # 時刻のバリデーション
            try:
                time_parts = time_str.split(":")
                if len(time_parts) != 2:
                    raise ValueError("時刻形式が不正です")
                hour = int(time_parts[0])
                minute = int(time_parts[1])
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError("時刻が範囲外です")
            except (ValueError, IndexError):
                raise ValueError("時刻形式が不正です")

            # 日時オブジェクトの作成
            return datetime(year, month, day, hour, minute)

        except ValueError as ex:
            self.logger.warning(f"日時バリデーションでエラーが発生しました: {str(ex)}")
            self.show_error(str(ex))
            return None

    def _on_date_submit(self, e):
        """日時入力確定時の処理"""
        new_date = self._validate_date(e.control.value)
        if new_date:
            if e.control == self.start_date_picker:
                # 終了日時が開始日時より前の場合、エラーを表示
                if self.viewmodel.end_date < new_date:
                    self.show_error("終了日時は開始日時より前の日時を指定できません")
                    # 値を元に戻す
                    e.control.value = self.viewmodel.start_date.strftime(
                        "%Y-%m-%d %H:%M"
                    )
                    e.control.update()
                    return
                self.viewmodel.start_date = new_date
            elif e.control == self.end_date_picker:
                # 終了日時が開始日時より前の場合、エラーを表示
                if new_date < self.viewmodel.start_date:
                    self.show_error("終了日時は開始日時より前の日時を指定できません")
                    # 値を元に戻す
                    e.control.value = self.viewmodel.end_date.strftime("%Y-%m-%d %H:%M")
                    e.control.update()
                    return
                self.viewmodel.end_date = new_date

    def _on_date_blur(self, e):
        """日時入力フィールドからフォーカスが外れた時の処理"""
        new_date = self._validate_date(e.control.value)
        if new_date:
            if e.control == self.start_date_picker:
                # 終了日時が開始日時より前の場合、エラーを表示
                if self.viewmodel.end_date < new_date:
                    self.show_error("終了日時は開始日時より前の日時を指定できません")
                    # 値を元に戻す
                    e.control.value = self.viewmodel.start_date.strftime(
                        "%Y-%m-%d %H:%M"
                    )
                    e.control.update()
                    return
                self.viewmodel.start_date = new_date
            elif e.control == self.end_date_picker:
                # 終了日時が開始日時より前の場合、エラーを表示
                if new_date < self.viewmodel.start_date:
                    self.show_error("終了日時は開始日時より前の日時を指定できません")
                    # 値を元に戻す
                    e.control.value = self.viewmodel.end_date.strftime("%Y-%m-%d %H:%M")
                    e.control.update()
                    return
                self.viewmodel.end_date = new_date
        else:
            # バリデーションエラーの場合、値を元に戻す
            if e.control == self.start_date_picker:
                e.control.value = self.viewmodel.start_date.strftime("%Y-%m-%d %H:%M")
            else:
                e.control.value = self.viewmodel.end_date.strftime("%Y-%m-%d %H:%M")
            e.control.update()

    def _on_ai_review_mail_unit_change(self, e):
        """AIレビュー（メール単位）設定変更時の処理"""
        self.viewmodel.ai_review_mail_unit = e.control.value

    def _on_ai_review_thread_unit_change(self, e):
        """AIレビュー（会話単位）設定変更時の処理"""
        self.viewmodel.ai_review_thread_unit = e.control.value

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
        self.logger.info("タスク作成を開始します")
        try:
            # ボタンを無効化
            self.create_button.disabled = True
            self.create_button.update()

            # タスクを作成
            success = self.viewmodel.create_task()
            if success:
                self.logger.info("タスクが正常に作成されました")
                self._show_success_message("タスクが正常に作成されました")
                self._reset_form()
            else:
                self.logger.error("タスクの作成に失敗しました")
                self.show_error("タスクの作成に失敗しました")
        except ValueError as ex:
            self.logger.error(f"タスク作成でエラーが発生しました: {str(ex)}")
            self.show_error(str(ex))
        except Exception as ex:
            self.logger.error(f"予期せぬエラーが発生しました: {str(ex)}")
            self.show_error("予期せぬエラーが発生しました")
        finally:
            # ボタンを再有効化
            self.create_button.disabled = False
            self.create_button.update()
            # ホーム画面に戻る
            if self.contents_viewmodel and hasattr(
                self.contents_viewmodel, "main_viewmodel"
            ):
                self.contents_viewmodel.main_viewmodel.set_destination("home")

    def show_error(self, message):
        """エラーメッセージを表示"""
        self.logger.error(f"エラーメッセージを表示: {message}")
        # AlertDialogを使用してエラーを表示
        if hasattr(self, "alert_dialog"):
            self.alert_dialog.show_error_dialog("エラー", message)
        else:
            # フォールバック（初期化前など）
            print(f"エラー: {message}")

    def _show_success_message(self, message):
        """成功メッセージを表示"""
        self.logger.info(f"成功メッセージを表示: {message}")
        # AlertDialogを使用して成功メッセージを表示
        if hasattr(self, "alert_dialog"):
            self.alert_dialog.show_completion_dialog("完了", message)
        else:
            # フォールバック（初期化前など）
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
        self.ai_review_mail_unit_checkbox.value = self.viewmodel.ai_review_mail_unit
        self.ai_review_thread_unit_checkbox.value = self.viewmodel.ai_review_thread_unit
        self.file_download_checkbox.value = self.viewmodel.file_download
        self.exclude_extensions_textarea.value = self.viewmodel.exclude_extensions
        self.exclude_extensions_textarea.disabled = not self.viewmodel.file_download
        self.exclude_extensions_textarea.parent.visible = self.viewmodel.file_download

        self.update()

    def _on_cancel(self, e):
        """キャンセルボタンクリック時の処理"""
        self.logger.info("キャンセルボタンがクリックされました")
        # ホーム画面に戻る
        if self.contents_viewmodel and hasattr(
            self.contents_viewmodel, "main_viewmodel"
        ):
            self.contents_viewmodel.main_viewmodel.set_destination("home")

    def did_mount(self):
        """コンポーネントがマウントされた時の処理"""
        # AlertDialogを初期化
        self.alert_dialog.initialize(self.page)
        self.logger.debug("TaskContent: AlertDialogを初期化しました")
