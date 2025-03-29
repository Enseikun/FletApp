import os
from datetime import datetime

import flet as ft

from src.core.logger import get_logger
from src.viewmodels.home_content_viewmodel import HomeContentViewModel
from src.viewmodels.home_viewmodel import HomeViewModel
from src.views.components.add_button import AddButton
from src.views.components.task_list_item import TaskListItem
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

    def on_task_selected(self, task_id):
        """タスク選択時の処理"""
        self.logger.info(f"HomeContent: タスク選択 - {task_id}")
        self.logger.debug(
            "HomeContent: contents_viewmodelの状態確認",
            has_contents_viewmodel=self.contents_viewmodel is not None,
        )

        # タスクIDを設定
        try:
            self.logger.debug(
                "HomeContent: main_viewmodelの状態確認",
                has_main_viewmodel=self.main_viewmodel is not None,
            )

            # Outlookのスナップショットを作成
            if self.contents_viewmodel:
                success = self.contents_viewmodel.create_outlook_snapshot(task_id)
                if success:
                    self.logger.info(
                        f"HomeContent: Outlookスナップショット作成成功 - {task_id}"
                    )
                else:
                    self.logger.error(
                        f"HomeContent: Outlookスナップショット作成失敗 - {task_id}"
                    )

            if self.main_viewmodel:
                self.main_viewmodel.set_current_task_id(task_id)
                self.main_viewmodel.set_destination("preview")
                self.logger.info(
                    f"HomeContent: MainViewModelを使用して画面遷移 - {task_id}"
                )
            else:
                # HomeViewModelのselect_taskメソッドを使用
                self.home_viewmodel.select_task(task_id)
                self.logger.info(
                    f"HomeContent: HomeViewModelを使用して画面遷移 - {task_id}"
                )
        except Exception as e:
            self.logger.error(
                "HomeContent: タスクID設定または画面遷移でエラー発生", error=str(e)
            )

    def on_task_delete(self, task_id, e):
        """タスク削除時の処理"""
        self.logger.info("HomeContent: タスク削除処理開始", task_id=task_id)

        # 削除確認ダイアログを表示
        def confirm_delete(e):
            if e.control.data == "yes":
                self.logger.info("HomeContent: タスク削除確認", task_id=task_id)
                try:
                    # タスクを削除
                    success = self.home_viewmodel.delete_task(task_id)
                    if success:
                        # タスクリストを再取得して更新
                        tasks = self.home_viewmodel.load_tasks()
                        self.update_task_list(tasks)
                        # 成功メッセージを表示
                        self.page.snack_bar = ft.SnackBar(
                            content=ft.Text(f"タスクID: {task_id} が削除されました"),
                            action="閉じる",
                        )
                        self.page.snack_bar.open = True
                        self.logger.info("HomeContent: タスク削除成功", task_id=task_id)
                    else:
                        # エラーメッセージを表示
                        self.page.snack_bar = ft.SnackBar(
                            content=ft.Text(
                                f"タスクID: {task_id} の削除に失敗しました。ファイルが使用中または権限が不足している可能性があります。"
                            ),
                            action="閉じる",
                        )
                        self.page.snack_bar.open = True
                        self.logger.error(
                            "HomeContent: タスク削除失敗", task_id=task_id
                        )
                except Exception as ex:
                    # 予期せぬエラーメッセージを表示
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text(
                            f"タスクID: {task_id} の削除中にエラーが発生しました: {str(ex)}"
                        ),
                        action="閉じる",
                    )
                    self.page.snack_bar.open = True
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
                ft.TextButton(
                    "いいえ", on_click=lambda e: self.page.close(dialog), data="no"
                ),
                ft.TextButton(
                    "はい",
                    on_click=lambda e: (confirm_delete(e), self.page.close(dialog)),
                    data="yes",
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=AppTheme.CONTAINER_BORDER_RADIUS),
        )

        # ダイアログを表示（推奨される方法）
        self.page.open(dialog)
        self.logger.debug("HomeContent: 削除確認ダイアログ表示", task_id=task_id)

    def on_add_task_click(self, e):
        """新規タスク追加ボタンクリック時の処理"""
        self.logger.info("HomeContent: 新規タスク追加ボタンクリック")
        # タスク設定画面に遷移
        if self.main_viewmodel:
            self.main_viewmodel.set_destination("task")
        else:
            self.home_viewmodel.set_destination("task")
