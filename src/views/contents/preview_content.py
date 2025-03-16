"""
プレビューコンテンツ
メールプレビュー画面のコンテンツを提供するクラス
"""

import flet as ft

from src.viewmodels.preview_content_viewmodel import PreviewContentViewModel
from src.views.components.text_with_subtitle import TextWithSubtitle
from src.views.styles.style import AppTheme


class PreviewContent(ft.Container):
    """
    メールプレビュー画面のコンテンツ
    左側にメールリスト、右側に選択したメールのプレビューを表示
    """

    def __init__(self, contents_viewmodel):
        """初期化"""
        # 親クラスを先に初期化
        super().__init__()
        self.contents_viewmodel = contents_viewmodel

        # ViewModelのインスタンスを作成
        # contents_viewmodelから現在のタスクIDを取得
        task_id = contents_viewmodel.get_current_task_id()
        self.preview_viewmodel = PreviewContentViewModel(task_id)

        # 選択中のメールID
        self.selected_mail_id = None

        # タスク情報の表示
        task_info = self.preview_viewmodel.get_task_info()
        task_title = f"タスク: {task_info['name'] if task_info else '不明なタスク'}"
        task_id_text = f"ID: {task_id if task_id else '不明'}"

        # 戻るボタン
        back_button = ft.IconButton(
            icon=ft.icons.ARROW_BACK,
            tooltip="ホームに戻る",
            on_click=self.on_back_click,
        )

        # フォルダ選択用ドロップダウン
        self.folders = self.preview_viewmodel.get_folders()
        folder_options = [
            ft.dropdown.Option(key=folder["entry_id"], text=folder["name"])
            for folder in self.folders
        ]

        # メールリストカラム（初期状態は空）
        mail_list_message = (
            "フォルダを選択するとメールが表示されます"
            if folder_options
            else "タスクデータが見つかりません"
        )
        self.mail_list_column = ft.Column(
            spacing=AppTheme.SPACING_SM,
            controls=[
                ft.Text(
                    mail_list_message,
                    italic=True,
                    color=ft.colors.GREY,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
        )

        # フォルダドロップダウン
        self.folder_dropdown = ft.Dropdown(
            options=folder_options,
            width=250,
            label="フォルダを選択",
            hint_text="表示するフォルダを選択してください",
            on_change=self.on_folder_change,
            disabled=not folder_options,  # フォルダがない場合は無効化
        )

        # 検索ボックス
        self.search_box = ft.TextField(
            label="メールを検索",
            hint_text="キーワードを入力",
            width=250,
            suffix=ft.IconButton(
                icon=ft.icons.SEARCH,
                on_click=self.on_search_click,
            ),
            on_submit=self.on_search_click,
            disabled=not folder_options,  # フォルダがない場合は無効化
        )

        # メールリスト部分（左側）
        self.mail_list_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        [self.folder_dropdown, self.search_box],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(),
                    self.mail_list_column,
                ],
                spacing=AppTheme.SPACING_SM,
            ),
            width=300,  # 左側の幅を固定
            padding=AppTheme.SPACING_MD,
            bgcolor=ft.colors.WHITE,
            border_radius=AppTheme.CONTAINER_BORDER_RADIUS,
            border=ft.border.all(1, ft.colors.BLACK12),
        )

        # メールプレビュー部分（右側）
        self.mail_preview_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("メールプレビュー", size=18, weight="bold"),
                    ft.Divider(),
                    ft.Text(
                        "左側のメールを選択してください",
                        italic=True,
                        color=ft.colors.GREY,
                    ),
                ],
                spacing=AppTheme.SPACING_MD,
            ),
            expand=True,  # 右側は残りのスペースを埋める
            padding=AppTheme.SPACING_MD,
            bgcolor=ft.colors.WHITE,
            border_radius=AppTheme.CONTAINER_BORDER_RADIUS,
            border=ft.border.all(1, ft.colors.BLACK12),
        )

        # メインコンテンツ（左右のコンテナを横に並べる）
        self.main_row = ft.Row(
            controls=[
                self.mail_list_container,
                self.mail_preview_container,
            ],
            spacing=AppTheme.SPACING_MD,
            expand=True,
        )

        # プロパティを設定
        self.content = ft.Column(
            controls=[
                ft.Row(
                    [
                        back_button,
                        ft.Column(
                            [
                                ft.Text(
                                    task_title, size=AppTheme.TITLE_SIZE, weight="bold"
                                ),
                                ft.Text(task_id_text, size=14, color=ft.colors.GREY),
                            ],
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                ft.Divider(),
                self.main_row,
            ],
            spacing=AppTheme.SPACING_MD,
            expand=True,
        )
        self.padding = AppTheme.PAGE_PADDING
        self.bgcolor = AppTheme.PAGE_BGCOLOR
        self.border_radius = AppTheme.CONTAINER_BORDER_RADIUS
        self.expand = True

        # 初期フォルダがあれば読み込む
        if folder_options:
            self.folder_dropdown.value = folder_options[0].key
            self.load_mails_for_folder(folder_options[0].key)

    def on_back_click(self, e):
        """戻るボタンクリック時の処理"""
        # ホーム画面に戻る
        self.contents_viewmodel.main_viewmodel.set_destination("home")

    def on_folder_change(self, e):
        """フォルダ選択時の処理"""
        if self.folder_dropdown.value:
            self.load_mails_for_folder(self.folder_dropdown.value)
            self.update()

    def on_search_click(self, e):
        """検索ボタンクリック時の処理"""
        search_term = self.search_box.value
        if search_term and len(search_term) >= 2:
            self.load_search_results(search_term)
            self.update()

    def load_mails_for_folder(self, folder_id):
        """指定フォルダのメールを読み込む"""
        mails = self.preview_viewmodel.load_folder_mails(folder_id)
        self.update_mail_list(mails)

    def load_search_results(self, search_term):
        """検索結果を読み込む"""
        mails = self.preview_viewmodel.search_mails(search_term)
        self.update_mail_list(mails)

    def update_mail_list(self, mails):
        """メールリストを更新する"""

        # メールリストアイテムのクリックハンドラ
        def on_mail_item_click(e, entry_id):
            self.selected_mail_id = entry_id
            self.update_mail_preview(entry_id)
            self.preview_viewmodel.mark_as_read(entry_id)
            self.update()

        # メールリストの作成
        mail_list_items = []
        for mail in mails:
            # 未読メールは太字で表示
            text_weight = "bold" if mail["unread"] == 1 else "normal"

            item = TextWithSubtitle(
                text=f"{mail['sender']} - {mail['subject']}",
                subtitle=f"{mail['preview']}... ({mail['date']})",
                on_click_callback=lambda e, id=mail["entry_id"]: on_mail_item_click(
                    e, id
                ),
                text_weight=text_weight,
            )
            mail_list_items.append(item)

        # リストが空の場合のメッセージ
        if not mail_list_items:
            mail_list_items = [
                ft.Text(
                    "このフォルダにメールはありません",
                    italic=True,
                    color=ft.colors.GREY,
                )
            ]

        # メールリストカラムを更新
        self.mail_list_column.controls = mail_list_items

    def update_mail_preview(self, entry_id):
        """選択されたメールのプレビューを更新する"""
        mail = self.preview_viewmodel.get_mail_content(entry_id)

        if mail:
            # プレビュー部分を更新
            self.mail_preview_container.content = ft.Column(
                controls=[
                    ft.Text(f"件名: {mail['subject']}", size=20, weight="bold"),
                    ft.Text(f"差出人: {mail['sender']}", size=16),
                    ft.Text(f"日付: {mail['date']}", size=14, color=ft.colors.GREY),
                    ft.Divider(),
                    ft.Container(
                        content=ft.Text(mail["content"], size=16),
                        padding=10,
                        expand=True,
                    ),
                ],
                spacing=AppTheme.SPACING_SM,
                scroll=ft.ScrollMode.AUTO,
            )

    def did_mount(self):
        """コンポーネントがマウントされた時の処理"""
        # 初期データの読み込みなど
        pass

    def will_unmount(self):
        """コンポーネントがアンマウントされる時の処理"""
        # ViewModelのクリーンアップ
        self.preview_viewmodel.close()
