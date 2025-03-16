import flet as ft

from src.viewmodels.home_content_viewmodel import HomeContentViewModel
from src.viewmodels.home_viewmodel import HomeViewModel
from src.views.components.add_button import AddButton
from src.views.components.text_with_subtitle import TextWithSubtitle
from src.views.styles.style import AppTheme


class HomeContent(ft.Container):
    """
    ホーム画面のコンテンツ
    TextWithSubtitleコンポーネントを使用したリストを表示
    """

    def __init__(self, contents_viewmodel):
        """初期化"""

        super().__init__()
        self.contents_viewmodel = contents_viewmodel

        # HomeViewModelのインスタンスを作成
        self.home_viewmodel = HomeViewModel(contents_viewmodel)

        # タスクリストを取得
        tasks = self.home_viewmodel.load_tasks()

        # タスクリストを表示するコントロールを作成
        task_items = []
        for task in tasks:
            task_item = TextWithSubtitle(
                text=f"タスクID: {task['id']}",
                subtitle=f"フォルダ: {task.get('from_folder_name', '未設定')}",
                on_click=lambda e, task_id=task["id"]: self.on_task_selected(task_id),
                enable_hover=True,
                enable_press=True,
            )
            task_items.append(task_item)

        # 新規タスク追加ボタン
        add_button = AddButton(
            on_click=self.on_add_task_click,
            tooltip="新しいタスクを追加",
            size=50,
        )

        # メインコンテンツ
        self.content = ft.Column(
            controls=[
                ft.Row(
                    [
                        ft.Text("利用可能なアーカイブ", size=24, weight="bold"),
                        add_button,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Divider(),
                ft.Column(
                    task_items, scroll=ft.ScrollMode.AUTO, spacing=10, expand=True
                ),
            ],
            spacing=10,
            expand=True,
        )
        self.padding = 20
        self.expand = True

    def on_task_selected(self, task_id):
        """タスク選択時の処理"""
        print(f"HomeContent: タスク選択 - {task_id}")
        # タスクIDをViewModelに設定
        self.contents_viewmodel.set_current_task_id(task_id)
        # プレビュー画面に遷移
        self.contents_viewmodel.main_viewmodel.set_destination("preview")

    def on_add_task_click(self, e):
        """新規タスク追加ボタンクリック時の処理"""
        # タスク設定画面に遷移
        self.contents_viewmodel.main_viewmodel.set_destination("task")
