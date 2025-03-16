"""
タスク設定コンテンツ
タスクの設定と作成を行うUIを提供するクラス
"""

from datetime import datetime, timedelta

import flet as ft

from src.views.components.add_button import AddButton
from src.views.components.icon_dropdown import IconDropdown
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

        # 現在の日時を取得
        now = datetime.now()
        self.start_date = now
        self.end_date = now + timedelta(minutes=30)

        # フォームの初期化
        self._init_form()

        # コンテンツの初期化
        self._init_content()

    def _init_form(self):
        """フォーム要素の初期化"""
        # アカウント選択ドロップダウン
        self.account_dropdown = IconDropdown(
            icon=ft.icons.ACCOUNT_CIRCLE,
            options=self._get_account_options(),
            on_change=self._on_account_change,
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
            on_change=None,
        )

        # 日時選択（開始）
        self.start_date_picker = ft.TextField(
            label="開始日時",
            value=self.start_date.strftime("%Y-%m-%d %H:%M"),
            icon=ft.icons.CALENDAR_TODAY,
            on_change=self._on_date_change,
        )

        # 日時選択（終了）
        self.end_date_picker = ft.TextField(
            label="終了日時",
            value=self.end_date.strftime("%Y-%m-%d %H:%M"),
            icon=ft.icons.CALENDAR_TODAY,
            on_change=self._on_date_change,
        )

        # AIレビューのチェックボックス
        self.ai_review_checkbox = ft.Checkbox(
            label="AIレビューを実行", value=True, on_change=None
        )

        # 添付ファイルダウンロードのチェックボックス
        self.file_download_checkbox = ft.Checkbox(
            label="添付ファイルをダウンロード", value=True, on_change=None
        )

        # 作成ボタン
        self.create_button = ft.ElevatedButton(
            text="タスクを作成",
            icon=ft.icons.ADD_TASK,
            on_click=None,
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
                ft.Text("アカウント選択", size=16, weight="bold"),
                self.account_dropdown,
                ft.Divider(),
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
                ft.Text("新しいタスクの設定", size=18, weight="bold"),
                form_column,
            ],
            spacing=AppTheme.SPACING_MD,
            scroll=ft.ScrollMode.AUTO,
        )

        # 親クラスの初期化
        self.content = content
        self.padding = AppTheme.PAGE_PADDING
        self.bgcolor = AppTheme.PAGE_BGCOLOR
        self.border_radius = AppTheme.CONTAINER_BORDER_RADIUS
        self.expand = True

    def _get_account_options(self):
        """アカウントの選択肢を取得"""
        # 実際にはViewModelからデータを取得する
        # ダミーデータを返す
        return [
            ("", "アカウントを選択"),
            ("acc_001", "山田 太郎 (yamada.taro@example.com)"),
            ("acc_002", "佐藤 花子 (sato.hanako@example.com)"),
            ("acc_003", "鈴木 一郎 (suzuki.ichiro@example.com)"),
        ]

    def _get_folder_options(self, account_id):
        """フォルダの選択肢を取得"""
        # 実際にはViewModelからデータを取得する
        # ダミーデータを返す
        if account_id == "acc_001":
            return [
                ("", "フォルダを選択"),
                ("fold_002", "受信トレイ"),
                ("fold_003", "アーカイブ"),
                ("fold_004", "過去メール"),
            ]
        elif account_id == "acc_002":
            return [
                ("", "フォルダを選択"),
                ("fold_005", "仕事"),
                ("fold_006", "重要"),
                ("fold_007", "保管"),
                ("fold_008", "個人"),
                ("fold_009", "バックアップ"),
            ]
        elif account_id == "acc_003":
            return [
                ("", "フォルダを選択"),
                ("fold_010", "重要"),
                ("fold_011", "会議"),
                ("fold_012", "保存"),
            ]
        else:
            return [("", "フォルダを選択")]

    def _on_account_change(self, e):
        """アカウント選択時の処理"""
        account_id = e.control.value
        if account_id:
            # フォルダ選択肢を更新
            folder_options = self._get_folder_options(account_id)
            self.from_folder_dropdown.update_options(folder_options)
            self.to_folder_dropdown.update_options(folder_options)

            # 値をリセット
            self.from_folder_dropdown.set_value("")
            self.to_folder_dropdown.set_value("")
        else:
            # アカウントが選択されていない場合、フォルダ選択肢をリセット
            self.from_folder_dropdown.update_options([("", "フォルダを選択")])
            self.to_folder_dropdown.update_options([("", "フォルダを選択")])

    def _on_from_folder_change(self, e):
        """送信元フォルダ選択時の処理"""
        # 必要に応じて送信先フォルダの選択肢を調整
        pass

    def _on_date_change(self, e):
        """日時変更時の処理"""
        try:
            if e.control == self.start_date_picker:
                self.start_date = datetime.strptime(e.control.value, "%Y-%m-%d %H:%M")
                # 終了日時が開始日時より前の場合、終了日時を調整
                if self.end_date < self.start_date:
                    self.end_date = self.start_date + timedelta(minutes=30)
                    self.end_date_picker.value = self.end_date.strftime(
                        "%Y-%m-%d %H:%M"
                    )
                    self.end_date_picker.update()
            elif e.control == self.end_date_picker:
                self.end_date = datetime.strptime(e.control.value, "%Y-%m-%d %H:%M")
                # 終了日時が開始日時より前の場合、エラーメッセージを表示
                if self.end_date < self.start_date:
                    # エラー表示
                    self.show_error("終了日時は開始日時より後に設定してください")
                    # 値を元に戻す
                    self.end_date = self.start_date + timedelta(minutes=30)
                    self.end_date_picker.value = self.end_date.strftime(
                        "%Y-%m-%d %H:%M"
                    )
                    self.end_date_picker.update()
        except ValueError:
            # 日付形式が不正な場合
            self.show_error(
                "日付形式が正しくありません。YYYY-MM-DD HH:MM形式で入力してください"
            )

    def show_error(self, message):
        """エラーメッセージを表示"""
        # 実際の実装ではダイアログやスナックバーでエラーを表示
        print(f"エラー: {message}")

    def _on_create_task(self, e):
        """タスク作成ボタンクリック時の処理"""
        # 入力値の検証
        if not self._validate_form():
            return

        # タスク情報の収集
        task_info = {
            "account_id": self.account_dropdown.value,
            "folder_id": self.from_folder_dropdown.value,  # 実際には親フォルダIDを設定
            "from_folder_id": self.from_folder_dropdown.value,
            "from_folder_name": self._get_folder_name(self.from_folder_dropdown.value),
            "from_folder_path": self._get_folder_path(self.from_folder_dropdown.value),
            "to_folder_id": self.to_folder_dropdown.value,
            "to_folder_name": self._get_folder_name(self.to_folder_dropdown.value),
            "to_folder_path": self._get_folder_path(self.to_folder_dropdown.value),
            "start_date": self.start_date.strftime("%Y-%m-%d %H:%M:%S"),
            "end_date": self.end_date.strftime("%Y-%m-%d %H:%M:%S"),
            "ai_review": 1 if self.ai_review_checkbox.value else 0,
            "file_download": 1 if self.file_download_checkbox.value else 0,
            "status": "created",
        }

        # タスクIDの生成（現在時刻をYYYYMMDDHHMMSS形式で）
        task_id = datetime.now().strftime("%Y%m%d%H%M%S")
        task_info["id"] = task_id

        # ViewModelを通じてタスクを作成
        success = self._create_task(task_info)

        if success:
            # 成功メッセージを表示
            self._show_success_message()
            # フォームをリセット
            self._reset_form()
        else:
            # エラーメッセージを表示
            self.show_error("タスクの作成に失敗しました")

    def _validate_form(self):
        """フォームの入力値を検証"""
        # アカウントが選択されているか
        if not self.account_dropdown.value:
            self.show_error("アカウントを選択してください")
            return False

        # 送信元フォルダが選択されているか
        if not self.from_folder_dropdown.value:
            self.show_error("移動元フォルダを選択してください")
            return False

        # 送信先フォルダが選択されているか
        if not self.to_folder_dropdown.value:
            self.show_error("移動先フォルダを選択してください")
            return False

        # 送信元と送信先が同じでないか
        if self.from_folder_dropdown.value == self.to_folder_dropdown.value:
            self.show_error("移動元と移動先のフォルダが同じです")
            return False

        # 日時が正しく設定されているか
        if self.end_date <= self.start_date:
            self.show_error("終了日時は開始日時より後に設定してください")
            return False

        return True

    def _get_folder_name(self, folder_id):
        """フォルダIDからフォルダ名を取得"""
        # 実際にはViewModelからデータを取得する
        # ダミーデータを返す
        folder_map = {
            "fold_002": "受信トレイ",
            "fold_003": "アーカイブ",
            "fold_004": "過去メール",
            "fold_005": "仕事",
            "fold_006": "重要",
            "fold_007": "保管",
            "fold_008": "個人",
            "fold_009": "バックアップ",
            "fold_010": "重要",
            "fold_011": "会議",
            "fold_012": "保存",
        }
        return folder_map.get(folder_id, "不明なフォルダ")

    def _get_folder_path(self, folder_id):
        """フォルダIDからフォルダパスを取得"""
        # 実際にはViewModelからデータを取得する
        # ダミーデータを返す
        folder_path_map = {
            "fold_002": "/メールボックス/受信トレイ",
            "fold_003": "/メールボックス/アーカイブ",
            "fold_004": "/メールボックス/過去メール",
            "fold_005": "/メールボックス/仕事",
            "fold_006": "/メールボックス/仕事/重要",
            "fold_007": "/メールボックス/保管",
            "fold_008": "/メールボックス/個人",
            "fold_009": "/メールボックス/バックアップ",
            "fold_010": "/メールボックス/重要",
            "fold_011": "/メールボックス/会議",
            "fold_012": "/メールボックス/保存",
        }
        return folder_path_map.get(folder_id, "/不明なパス")

    def _create_task(self, task_info):
        """タスクを作成"""
        # 実際にはViewModelを通じてデータベースに保存する
        # ダミー実装
        print(f"タスクを作成: {task_info}")
        return True

    def _show_success_message(self):
        """成功メッセージを表示"""
        # 実際の実装ではダイアログやスナックバーで成功メッセージを表示
        print("タスクが正常に作成されました")

    def _reset_form(self):
        """フォームをリセット"""
        # アカウント選択をリセット
        self.account_dropdown.set_value("")

        # フォルダ選択をリセット
        self.from_folder_dropdown.update_options([("", "フォルダを選択")])
        self.to_folder_dropdown.update_options([("", "フォルダを選択")])

        # 日時を現在時刻にリセット
        now = datetime.now()
        self.start_date = now
        self.end_date = now + timedelta(minutes=30)

        self.start_date_picker.value = self.start_date.strftime("%Y-%m-%d %H:%M")
        self.end_date_picker.value = self.end_date.strftime("%Y-%m-%d %H:%M")

        # チェックボックスをリセット
        self.ai_review_checkbox.value = True
        self.file_download_checkbox.value = True

        # 更新
        self.update()

    def _on_cancel(self, e):
        """キャンセルボタンクリック時の処理"""
        # ホーム画面に戻る
        if self.contents_viewmodel and hasattr(
            self.contents_viewmodel, "main_viewmodel"
        ):
            self.contents_viewmodel.main_viewmodel.set_destination("home")
