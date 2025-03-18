"""
プレビューコンテンツ
メールプレビュー画面のコンテンツを提供するクラス
"""

import asyncio
import os
from typing import Any, Dict, List, Optional

import flet as ft

from src.core.database import DatabaseManager
from src.core.logger import get_logger
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
        super().__init__()
        self.contents_viewmodel = contents_viewmodel  # ViewModelへの参照を保持
        self.logger = get_logger()
        self.logger.info("PreviewContent: 初期化開始")

        # 初期化時にはタスクIDを取得しない
        # ViewModelの初期化も遅延させる
        self.viewmodel = None
        self.task_id = None

        # 会話ごとに集約するフラグ
        self.group_by_conversation = False

        # 会話グループのコンテナを保存する辞書
        self.conversation_containers = {}

        # 検索フィールド
        self.search_field = ft.TextField(
            hint_text="メールを検索...",
            prefix_icon=ft.icons.SEARCH,
            expand=True,
            on_submit=self.on_search,
            border_radius=20,
            height=40,
        )

        # メールリスト
        self.mail_list = ft.ListView(
            expand=True,
            spacing=2,
            padding=5,
        )

        # メール内容表示
        self.mail_content = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

        # UIを構築
        self._build()
        self.logger.info("PreviewContent: 初期化完了")

        # サンプルデータフラグ
        self.use_sample_data = True

    def _build(self):
        """UIを構築"""
        self.logger.debug("PreviewContent: UI構築開始")

        # 左側のペイン（メールリスト）
        left_pane = ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Text("メール一覧", weight="bold", size=16),
                                ft.IconButton(
                                    icon=ft.icons.REFRESH,
                                    tooltip="更新",
                                    on_click=lambda _: self.load_all_mails(),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        padding=ft.padding.only(left=10, top=10, right=10, bottom=5),
                    ),
                    ft.Container(
                        content=self.search_field,
                        padding=ft.padding.only(left=10, right=10, bottom=5),
                    ),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Text("会話ごとに集約:", size=12),
                                ft.Switch(
                                    value=False,
                                    on_change=self.on_group_by_conversation_changed,
                                    scale=0.8,
                                ),
                                ft.IconButton(
                                    icon=ft.icons.HELP_OUTLINE,
                                    tooltip="同じ件名のメールをまとめて表示します",
                                    icon_size=16,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.END,
                        ),
                        padding=ft.padding.only(left=10, right=10, bottom=5),
                    ),
                    ft.Container(
                        content=self.mail_list,
                        expand=True,
                        border=ft.border.all(1, ft.colors.BLACK12),
                        border_radius=AppTheme.CONTAINER_BORDER_RADIUS,
                        padding=5,
                    ),
                ],
                spacing=0,
                expand=True,
            ),
            expand=1,
        )

        # 右側のペイン（メール内容表示）
        right_pane = ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Text("メールプレビュー", weight="bold", size=16),
                        padding=ft.padding.only(left=10, top=10, right=10, bottom=10),
                    ),
                    ft.Container(
                        content=self.mail_content,
                        expand=True,
                        border=ft.border.all(1, ft.colors.BLACK12),
                        border_radius=AppTheme.CONTAINER_BORDER_RADIUS,
                        padding=10,
                    ),
                ],
                spacing=0,
                expand=True,
            ),
            expand=2,
        )

        # メインコンテンツ
        self.content = ft.Column(
            [
                ft.Row(
                    [left_pane, right_pane],
                    spacing=10,
                    expand=True,
                ),
            ],
            spacing=10,
            expand=True,
        )

        self.padding = 20
        self.expand = True
        self.bgcolor = ft.colors.WHITE
        self.logger.debug("PreviewContent: UI構築完了")

    def did_mount(self):
        """コンポーネントがマウントされた時の処理"""
        self.logger.info("PreviewContent: マウント処理開始")

        # タスクIDを取得
        self.task_id = self._get_task_id()
        self.logger.debug("PreviewContent: タスクID取得", task_id=self.task_id)

        # サンプルデータを使用するフラグを明示的に設定
        self.use_sample_data = True
        self.logger.debug(
            "PreviewContent: サンプルデータ使用フラグ設定",
            use_sample=self.use_sample_data,
        )

        # データを読み込む
        self.load_data()
        self.logger.info("PreviewContent: マウント処理完了")

    def load_data(self):
        """データを読み込む"""
        self.logger.info("PreviewContent: データ読み込み開始")

        # サンプルデータを使用する場合
        if self.use_sample_data:
            self.logger.debug("PreviewContent: サンプルデータを使用")
            self.load_sample_data()
            return

        if self.task_id:
            self.logger.debug("PreviewContent: タスクID有効", task_id=self.task_id)
            # ViewModelを初期化
            self.viewmodel = PreviewContentViewModel(self.task_id)

            try:
                # タスク情報を取得して表示を更新
                task_info = self.viewmodel.get_task_info()
                if task_info:
                    task_name = task_info.get("name", "不明なタスク")
                    self.logger.debug(
                        "PreviewContent: タスク情報取得", task_name=task_name
                    )

                # すべてのメールを読み込む
                self.load_all_mails()
                self.logger.info("PreviewContent: データ読み込み完了")
            except Exception as e:
                self.logger.error("PreviewContent: データ読み込みエラー", error=str(e))
                self.show_error_message(f"データ読み込みエラー: {str(e)}")
        else:
            self.logger.error("PreviewContent: 有効なタスクIDがありません")
            self.show_error_message("有効なタスクIDがありません")

        self.update()
        self.logger.info("PreviewContent: すべてのメール読み込み完了")

    def _get_task_id(self):
        """タスクIDを取得する内部メソッド"""
        task_id = None

        # 直接contents_viewmodelからtask_idを取得
        if hasattr(self.contents_viewmodel, "get_current_task_id"):
            task_id = self.contents_viewmodel.get_current_task_id()
            self.logger.debug(
                "PreviewContent: contents_viewmodelからタスクID取得", task_id=task_id
            )

        # main_viewmodelからも取得を試みる
        if (
            task_id is None
            and hasattr(self.contents_viewmodel, "main_viewmodel")
            and self.contents_viewmodel.main_viewmodel
        ):
            if hasattr(self.contents_viewmodel.main_viewmodel, "get_current_task_id"):
                task_id = self.contents_viewmodel.main_viewmodel.get_current_task_id()
                self.logger.debug(
                    "PreviewContent: main_viewmodelからタスクID取得", task_id=task_id
                )

        # デバッグ用に追加のログを出力
        if task_id is None:
            self.logger.error("PreviewContent: タスクIDの取得に失敗しました")
            # contents_viewmodelの状態を確認
            if hasattr(self.contents_viewmodel, "current_task_id"):
                self.logger.debug(
                    "PreviewContent: contents_viewmodel.current_task_id",
                    value=self.contents_viewmodel.current_task_id,
                )

        return task_id

    def load_all_mails(self):
        """すべてのメールを読み込む"""
        self.logger.info("PreviewContent: すべてのメール読み込み開始")
        if not self.viewmodel and not self.use_sample_data:
            self.logger.error("PreviewContent: ViewModelが初期化されていません")
            return

        # メールリストをクリア
        self.mail_list.controls.clear()

        # サンプルデータを使用する場合
        if self.use_sample_data:
            # サンプルメールデータ
            sample_mails = [
                {
                    "id": 1,
                    "subject": "プロジェクト進捗報告",
                    "sender": "田中太郎 <tanaka@example.com>",
                    "recipient": "山田花子 <yamada@example.com>",
                    "date": "2023-11-15 14:30",
                    "content": "山田さん\n\n先日のミーティングでお話しした件について進捗をご報告します。\n\n現在、システム設計の最終段階に入っており、来週には実装フェーズに移行できる見込みです。\n\n添付資料に詳細な進捗状況をまとめましたので、ご確認ください。\n\n何かご質問があればお知らせください。\n\n田中",
                    "preview": "先日のミーティングでお話しした件について進捗をご報告します。",
                    "unread": 1,
                    "attachments": [
                        {"id": 101, "name": "プロジェクト進捗報告.pdf"},
                        {"id": 102, "name": "スケジュール.xlsx"},
                    ],
                },
                {
                    "id": 2,
                    "subject": "週次会議の議事録",
                    "sender": "佐藤一郎 <sato@example.com>",
                    "recipient": "プロジェクトチーム <project-team@example.com>",
                    "date": "2023-11-14 17:45",
                    "content": "プロジェクトチームの皆様\n\n本日の週次会議の議事録を送付いたします。\n\n【議題】\n1. 前回のタスク進捗確認\n2. 新機能の要件定義\n3. テスト計画の策定\n\n【決定事項】\n・11月末までに要件定義を完了させる\n・12月第1週からテスト計画の策定を開始する\n\n詳細は添付ファイルをご確認ください。\n\n佐藤",
                    "preview": "本日の週次会議の議事録を送付いたします。",
                    "unread": 0,
                    "attachments": [
                        {"id": 103, "name": "週次会議議事録_20231114.docx"}
                    ],
                },
                {
                    "id": 3,
                    "subject": "新機能のフィードバック依頼",
                    "sender": "鈴木健太 <suzuki@example.com>",
                    "recipient": "山田花子 <yamada@example.com>",
                    "date": "2023-11-13 10:15",
                    "content": "山田さん\n\n先日リリースした新機能について、ユーザーからのフィードバックを集めています。\n\n特に以下の点についてご意見をいただけると助かります：\n\n1. UI/UXの使いやすさ\n2. 処理速度\n3. 追加して欲しい機能\n\n来週の金曜日までにご回答いただけますと幸いです。\n\nよろしくお願いいたします。\n\n鈴木",
                    "preview": "先日リリースした新機能について、ユーザーからのフィードバックを集めています。",
                    "unread": 0,
                    "attachments": [],
                },
                {
                    "id": 4,
                    "subject": "セキュリティアップデートのお知らせ",
                    "sender": "システム管理者 <admin@example.com>",
                    "recipient": "全社員 <all-staff@example.com>",
                    "date": "2023-11-12 09:00",
                    "content": "全社員の皆様\n\n重要なセキュリティアップデートのお知らせです。\n\n本日15時より、社内システムのセキュリティアップデートを実施します。\nアップデート中（約30分間）はシステムにアクセスできなくなりますので、ご注意ください。\n\n作業完了後、改めてご連絡いたします。\n\nご不便をおかけしますが、ご協力のほどよろしくお願いいたします。\n\nシステム管理者",
                    "preview": "重要なセキュリティアップデートのお知らせです。",
                    "unread": 1,
                    "attachments": [],
                },
                {
                    "id": 5,
                    "subject": "クライアントミーティングの日程調整",
                    "sender": "高橋美咲 <takahashi@example.com>",
                    "recipient": "山田花子 <yamada@example.com>",
                    "date": "2023-11-10 13:20",
                    "content": "山田さん\n\nABC株式会社との次回ミーティングの日程調整をお願いします。\n\n先方から以下の候補日が挙がっています：\n・11月20日（月）14:00-16:00\n・11月22日（水）10:00-12:00\n・11月24日（金）15:00-17:00\n\nご都合の良い日をお知らせください。\n\n高橋",
                    "preview": "ABC株式会社との次回ミーティングの日程調整をお願いします。",
                    "unread": 0,
                    "attachments": [],
                },
                {
                    "id": 6,
                    "subject": "年末パーティーのお知らせ",
                    "sender": "総務部 <soumu@example.com>",
                    "recipient": "全社員 <all-staff@example.com>",
                    "date": "2023-11-08 11:30",
                    "content": "社員の皆様\n\n恒例の年末パーティーについてお知らせいたします。\n\n【日時】2023年12月22日（金）18:30～21:00\n【場所】ホテルグランドパレス 2階「クリスタルルーム」\n【会費】5,000円（当日受付にてお支払いください）\n\n出欠確認のため、11月30日までに添付のフォームにてご回答ください。\n\n皆様のご参加をお待ちしております。\n\n総務部",
                    "preview": "恒例の年末パーティーについてお知らせいたします。",
                    "unread": 0,
                    "attachments": [
                        {"id": 104, "name": "年末パーティー出欠フォーム.xlsx"}
                    ],
                },
            ]

            # デバッグログを追加
            self.logger.debug(
                "PreviewContent: 会話集約モード",
                group_by_conversation=self.group_by_conversation,
            )

            # 会話ごとに集約する場合
            if self.group_by_conversation:
                self._display_grouped_mails(sample_mails)
            else:
                # 通常表示
                for mail in sample_mails:
                    mail_item = self._create_mail_item(mail)
                    self.mail_list.controls.append(mail_item)
        else:
            # すべてのメールを取得
            mails = self.viewmodel.get_all_mails()
            self.logger.debug("PreviewContent: メール取得完了", mail_count=len(mails))

            # メール一覧を表示
            if mails:
                # 会話ごとに集約する場合
                if self.group_by_conversation:
                    self._display_grouped_mails(mails)
                else:
                    # 通常表示
                    for mail in mails:
                        mail_item = self._create_mail_item(mail)
                        self.mail_list.controls.append(mail_item)
            else:
                # データがない場合の表示を改善
                self.mail_list.controls.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Icon(
                                    name=ft.icons.EMAIL_OUTLINED,
                                    size=40,
                                    color=ft.colors.GREY,
                                ),
                                ft.Text(
                                    "メールはありません",
                                    color=ft.colors.GREY,
                                    text_align=ft.TextAlign.CENTER,
                                    weight="bold",
                                ),
                                ft.Text(
                                    "このタスクにはメールデータが登録されていません",
                                    color=ft.colors.GREY,
                                    size=12,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10,
                        ),
                        alignment=ft.alignment.center,
                        expand=True,
                    )
                )

        # メール内容表示をクリア
        self._show_empty_mail_content()

        # 明示的に更新
        self.update()
        self.logger.info("PreviewContent: すべてのメール読み込み完了")

    def _create_mail_item(self, mail):
        """メールアイテムを作成"""
        is_unread = mail.get("unread", 0)
        has_attachments = bool(mail.get("attachments", []))

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Icon(
                                    name=ft.icons.CIRCLE,
                                    size=8,
                                    color=(
                                        ft.colors.BLUE
                                        if is_unread
                                        else ft.colors.TRANSPARENT
                                    ),
                                ),
                                width=15,
                            ),
                            ft.Text(
                                mail["date"],
                                size=12,
                                color=ft.colors.GREY,
                                width=100,
                            ),
                            ft.Text(
                                mail["sender"]
                                .split("<")[0]
                                .strip(),  # 名前部分のみ表示
                                size=12,
                                color=ft.colors.GREY,
                                expand=True,
                                text_align=ft.TextAlign.RIGHT,
                            ),
                            (
                                ft.Icon(
                                    name=ft.icons.ATTACH_FILE,
                                    size=14,
                                    color=ft.colors.GREY,
                                )
                                if has_attachments
                                else ft.Container(width=0)
                            ),
                        ],
                    ),
                    ft.Text(
                        mail["subject"] or "(件名なし)",
                        weight="bold" if is_unread else "normal",
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Text(
                        mail.get("preview", ""),
                        size=12,
                        color=ft.colors.GREY,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
                spacing=2,
            ),
            padding=ft.padding.all(8),
            border_radius=5,
            on_click=lambda e, mail_id=mail["id"]: self.show_mail_content(mail_id),
            ink=True,
            bgcolor=ft.colors.WHITE,
            border=ft.border.all(1, ft.colors.BLACK12),
            margin=ft.margin.only(bottom=5),
        )

    def _show_empty_mail_content(self):
        """空のメール内容表示"""
        self.mail_content.controls.clear()
        self.mail_content.controls.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(
                            name=ft.icons.EMAIL_OUTLINED,
                            size=40,
                            color=ft.colors.GREY,
                        ),
                        ft.Text(
                            "メールを選択してください",
                            color=ft.colors.GREY,
                            text_align=ft.TextAlign.CENTER,
                            weight="bold",
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                alignment=ft.alignment.center,
                expand=True,
            )
        )

    def on_search(self, e):
        """検索実行時の処理"""
        search_term = self.search_field.value
        self.logger.info("PreviewContent: 検索実行", search_term=search_term)
        if not search_term:
            self.load_all_mails()
            return

        if not self.viewmodel:
            self.logger.error("PreviewContent: ViewModelが初期化されていません")
            return

        # メールリストをクリア
        self.mail_list.controls.clear()

        # 検索を実行
        mails = self.viewmodel.search_mails(search_term)
        self.logger.debug("PreviewContent: 検索結果取得", result_count=len(mails))

        # 検索結果を表示
        if mails:
            for mail in mails:
                mail_item = self._create_mail_item(mail)
                self.mail_list.controls.append(mail_item)
        else:
            self.mail_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(
                                name=ft.icons.SEARCH_OFF,
                                size=40,
                                color=ft.colors.GREY,
                            ),
                            ft.Text(
                                f"「{search_term}」に一致するメールはありません",
                                color=ft.colors.GREY,
                                text_align=ft.TextAlign.CENTER,
                                weight="bold",
                            ),
                            ft.TextButton(
                                text="すべてのメールを表示",
                                on_click=lambda _: self.load_all_mails(),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    alignment=ft.alignment.center,
                    expand=True,
                )
            )

        self.update()
        self.logger.info("PreviewContent: 検索完了", search_term=search_term)

    def show_mail_content(self, mail_id):
        """メール内容を表示"""
        self.logger.info("PreviewContent: メール内容表示", mail_id=mail_id)

        # サンプルデータを使用する場合
        if self.use_sample_data:
            # サンプルメールデータから該当するメールを検索
            sample_mails = [
                {
                    "id": 1,
                    "subject": "プロジェクト進捗報告",
                    "sender": "田中太郎 <tanaka@example.com>",
                    "recipient": "山田花子 <yamada@example.com>",
                    "date": "2023-11-15 14:30",
                    "content": "山田さん\n\n先日のミーティングでお話しした件について進捗をご報告します。\n\n現在、システム設計の最終段階に入っており、来週には実装フェーズに移行できる見込みです。\n\n添付資料に詳細な進捗状況をまとめましたので、ご確認ください。\n\n何かご質問があればお知らせください。\n\n田中",
                    "preview": "先日のミーティングでお話しした件について進捗をご報告します。",
                    "unread": 1,
                    "attachments": [
                        {"id": 101, "name": "プロジェクト進捗報告.pdf"},
                        {"id": 102, "name": "スケジュール.xlsx"},
                    ],
                },
                {
                    "id": 2,
                    "subject": "週次会議の議事録",
                    "sender": "佐藤一郎 <sato@example.com>",
                    "recipient": "プロジェクトチーム <project-team@example.com>",
                    "date": "2023-11-14 17:45",
                    "content": "プロジェクトチームの皆様\n\n本日の週次会議の議事録を送付いたします。\n\n【議題】\n1. 前回のタスク進捗確認\n2. 新機能の要件定義\n3. テスト計画の策定\n\n【決定事項】\n・11月末までに要件定義を完了させる\n・12月第1週からテスト計画の策定を開始する\n\n詳細は添付ファイルをご確認ください。\n\n佐藤",
                    "preview": "本日の週次会議の議事録を送付いたします。",
                    "unread": 0,
                    "attachments": [
                        {"id": 103, "name": "週次会議議事録_20231114.docx"}
                    ],
                },
                {
                    "id": 3,
                    "subject": "新機能のフィードバック依頼",
                    "sender": "鈴木健太 <suzuki@example.com>",
                    "recipient": "山田花子 <yamada@example.com>",
                    "date": "2023-11-13 10:15",
                    "content": "山田さん\n\n先日リリースした新機能について、ユーザーからのフィードバックを集めています。\n\n特に以下の点についてご意見をいただけると助かります：\n\n1. UI/UXの使いやすさ\n2. 処理速度\n3. 追加して欲しい機能\n\n来週の金曜日までにご回答いただけますと幸いです。\n\nよろしくお願いいたします。\n\n鈴木",
                    "preview": "先日リリースした新機能について、ユーザーからのフィードバックを集めています。",
                    "unread": 0,
                    "attachments": [],
                },
                {
                    "id": 4,
                    "subject": "セキュリティアップデートのお知らせ",
                    "sender": "システム管理者 <admin@example.com>",
                    "recipient": "全社員 <all-staff@example.com>",
                    "date": "2023-11-12 09:00",
                    "content": "全社員の皆様\n\n重要なセキュリティアップデートのお知らせです。\n\n本日15時より、社内システムのセキュリティアップデートを実施します。\nアップデート中（約30分間）はシステムにアクセスできなくなりますので、ご注意ください。\n\n作業完了後、改めてご連絡いたします。\n\nご不便をおかけしますが、ご協力のほどよろしくお願いいたします。\n\nシステム管理者",
                    "preview": "重要なセキュリティアップデートのお知らせです。",
                    "unread": 1,
                    "attachments": [],
                },
                {
                    "id": 5,
                    "subject": "クライアントミーティングの日程調整",
                    "sender": "高橋美咲 <takahashi@example.com>",
                    "recipient": "山田花子 <yamada@example.com>",
                    "date": "2023-11-10 13:20",
                    "content": "山田さん\n\nABC株式会社との次回ミーティングの日程調整をお願いします。\n\n先方から以下の候補日が挙がっています：\n・11月20日（月）14:00-16:00\n・11月22日（水）10:00-12:00\n・11月24日（金）15:00-17:00\n\nご都合の良い日をお知らせください。\n\n高橋",
                    "preview": "ABC株式会社との次回ミーティングの日程調整をお願いします。",
                    "unread": 0,
                    "attachments": [],
                },
                {
                    "id": 6,
                    "subject": "年末パーティーのお知らせ",
                    "sender": "総務部 <soumu@example.com>",
                    "recipient": "全社員 <all-staff@example.com>",
                    "date": "2023-11-08 11:30",
                    "content": "社員の皆様\n\n恒例の年末パーティーについてお知らせいたします。\n\n【日時】2023年12月22日（金）18:30～21:00\n【場所】ホテルグランドパレス 2階「クリスタルルーム」\n【会費】5,000円（当日受付にてお支払いください）\n\n出欠確認のため、11月30日までに添付のフォームにてご回答ください。\n\n皆様のご参加をお待ちしております。\n\n総務部",
                    "preview": "恒例の年末パーティーについてお知らせいたします。",
                    "unread": 0,
                    "attachments": [
                        {"id": 104, "name": "年末パーティー出欠フォーム.xlsx"}
                    ],
                },
            ]

            mail = next((m for m in sample_mails if m["id"] == mail_id), None)

            if not mail:
                self.logger.error("PreviewContent: メール内容取得失敗", mail_id=mail_id)
                return

            # メールを既読にする処理（サンプルデータでは実際には更新されない）
            if mail.get("unread", 0):
                mail["unread"] = 0
                self.logger.debug("PreviewContent: メールを既読に設定", mail_id=mail_id)
                # メールリストを更新して既読状態を反映
                self.mail_list.controls.clear()
                for m in sample_mails:
                    mail_item = self._create_mail_item(m)
                    self.mail_list.controls.append(mail_item)

            # メール内容表示をクリア
            self.mail_content.controls.clear()

            # 送信者情報を解析
            sender_name = mail["sender"].split("<")[0].strip()
            sender_email = (
                mail["sender"].split("<")[1].replace(">", "")
                if "<" in mail["sender"]
                else mail["sender"]
            )

            # 受信者情報を解析
            recipient_name = mail.get("recipient", "").split("<")[0].strip()
            recipient_email = (
                mail.get("recipient", "").split("<")[1].replace(">", "")
                if "<" in mail.get("recipient", "")
                else mail.get("recipient", "")
            )

            # 添付ファイルがあれば表示用のリストを作成
            attachments_section = []
            if mail.get("attachments"):
                attachments = mail["attachments"]
                attachments_list = ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(
                                        name=ft.icons.ATTACH_FILE,
                                        size=16,
                                        color=ft.colors.BLUE,
                                    ),
                                    ft.Text("添付ファイル", weight="bold"),
                                ],
                                spacing=5,
                            ),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Row(
                                            [
                                                self._get_file_icon(attachment["name"]),
                                                ft.Text(attachment["name"]),
                                                ft.Text(
                                                    self._get_file_type(
                                                        attachment["name"]
                                                    ),
                                                    size=12,
                                                    color=ft.colors.GREY,
                                                ),
                                            ],
                                            spacing=10,
                                        )
                                        for attachment in attachments
                                    ],
                                    spacing=5,
                                ),
                                padding=10,
                            ),
                        ],
                        spacing=5,
                    ),
                    padding=10,
                    border=ft.border.all(1, ft.colors.BLACK12),
                    border_radius=5,
                    margin=ft.margin.only(top=10),
                )
                attachments_section = [attachments_list]

            # メール内容を表示
            self.mail_content.controls.extend(
                [
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    mail["subject"] or "(件名なし)",
                                    size=18,
                                    weight="bold",
                                ),
                                ft.Divider(height=1, color=ft.colors.BLACK12),
                                ft.Row(
                                    [
                                        ft.Column(
                                            [
                                                ft.Row(
                                                    [
                                                        ft.Text(
                                                            "送信者:",
                                                            weight="bold",
                                                            width=80,
                                                        ),
                                                        ft.Text(
                                                            f"{sender_name} <{sender_email}>"
                                                        ),
                                                    ],
                                                ),
                                                ft.Row(
                                                    [
                                                        ft.Text(
                                                            "宛先:",
                                                            weight="bold",
                                                            width=80,
                                                        ),
                                                        ft.Text(
                                                            f"{recipient_name} <{recipient_email}>"
                                                        ),
                                                    ],
                                                ),
                                                ft.Row(
                                                    [
                                                        ft.Text(
                                                            "日時:",
                                                            weight="bold",
                                                            width=80,
                                                        ),
                                                        ft.Text(mail["date"]),
                                                    ],
                                                ),
                                            ],
                                            spacing=5,
                                        ),
                                    ],
                                ),
                            ],
                            spacing=10,
                        ),
                        padding=10,
                        bgcolor=ft.colors.WHITE,
                        border_radius=5,
                        border=ft.border.all(1, ft.colors.BLACK12),
                    ),
                    *attachments_section,
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    "本文:",
                                    weight="bold",
                                ),
                                ft.Container(
                                    content=ft.Text(mail["content"]),
                                    padding=10,
                                    bgcolor=ft.colors.WHITE,
                                    border_radius=5,
                                    border=ft.border.all(1, ft.colors.BLACK12),
                                ),
                            ],
                            spacing=5,
                        ),
                        padding=10,
                        margin=ft.margin.only(top=10),
                        expand=True,
                    ),
                ]
            )

            # メールリスト内の該当アイテムの背景色を変更して選択状態を示す
            for item in self.mail_list.controls:
                if hasattr(item, "on_click") and item.on_click.__closure__:
                    for cell in item.on_click.__closure__:
                        if (
                            hasattr(cell, "cell_contents")
                            and cell.cell_contents == mail_id
                        ):
                            item.bgcolor = ft.colors.BLUE_50
                        else:
                            item.bgcolor = ft.colors.WHITE

            self.update()
            self.logger.info("PreviewContent: メール内容表示完了", mail_id=mail_id)
            return

        if not self.viewmodel:
            self.logger.error("PreviewContent: ViewModelが初期化されていません")
            return

        # メール内容を取得
        mail = self.viewmodel.get_mail_content(mail_id)
        if not mail:
            self.logger.error("PreviewContent: メール内容取得失敗", mail_id=mail_id)
            return

        # メールを既読にする
        if mail.get("unread", 0):
            self.viewmodel.mark_as_read(mail_id)
            self.logger.debug("PreviewContent: メールを既読に設定", mail_id=mail_id)
            # メールリストを更新して既読状態を反映
            self.load_all_mails()

        # メール内容表示をクリア
        self.mail_content.controls.clear()

        # 送信者情報を解析
        sender_name = mail["sender"].split("<")[0].strip()
        sender_email = (
            mail["sender"].split("<")[1].replace(">", "")
            if "<" in mail["sender"]
            else mail["sender"]
        )

        # 受信者情報を解析
        recipient_name = mail.get("recipient", "").split("<")[0].strip()
        recipient_email = (
            mail.get("recipient", "").split("<")[1].replace(">", "")
            if "<" in mail.get("recipient", "")
            else mail.get("recipient", "")
        )

        # 添付ファイルがあれば表示用のリストを作成
        attachments_section = []
        if mail.get("attachments"):
            attachments = mail["attachments"]
            attachments_list = ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(
                                    name=ft.icons.ATTACH_FILE,
                                    size=16,
                                    color=ft.colors.BLUE,
                                ),
                                ft.Text("添付ファイル", weight="bold"),
                            ],
                            spacing=5,
                        ),
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Row(
                                        [
                                            self._get_file_icon(attachment["name"]),
                                            ft.Text(attachment["name"]),
                                            ft.Text(
                                                self._get_file_type(attachment["name"]),
                                                size=12,
                                                color=ft.colors.GREY,
                                            ),
                                        ],
                                        spacing=10,
                                    )
                                    for attachment in attachments
                                ],
                                spacing=5,
                            ),
                            padding=10,
                        ),
                    ],
                    spacing=5,
                ),
                padding=10,
                border=ft.border.all(1, ft.colors.BLACK12),
                border_radius=5,
                margin=ft.margin.only(top=10),
            )
            attachments_section = [attachments_list]

        # メール内容を表示
        self.mail_content.controls.extend(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                mail["subject"] or "(件名なし)",
                                size=18,
                                weight="bold",
                            ),
                            ft.Divider(height=1, color=ft.colors.BLACK12),
                            ft.Row(
                                [
                                    ft.Column(
                                        [
                                            ft.Row(
                                                [
                                                    ft.Text(
                                                        "送信者:",
                                                        weight="bold",
                                                        width=80,
                                                    ),
                                                    ft.Text(
                                                        f"{sender_name} <{sender_email}>"
                                                    ),
                                                ],
                                            ),
                                            ft.Row(
                                                [
                                                    ft.Text(
                                                        "宛先:", weight="bold", width=80
                                                    ),
                                                    ft.Text(
                                                        f"{recipient_name} <{recipient_email}>"
                                                    ),
                                                ],
                                            ),
                                            ft.Row(
                                                [
                                                    ft.Text(
                                                        "日時:", weight="bold", width=80
                                                    ),
                                                    ft.Text(mail["date"]),
                                                ],
                                            ),
                                        ],
                                        spacing=5,
                                    ),
                                ],
                            ),
                        ],
                        spacing=10,
                    ),
                    padding=10,
                    bgcolor=ft.colors.WHITE,
                    border_radius=5,
                    border=ft.border.all(1, ft.colors.BLACK12),
                ),
                *attachments_section,
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "本文:",
                                weight="bold",
                            ),
                            ft.Container(
                                content=ft.Text(mail["content"]),
                                padding=10,
                                bgcolor=ft.colors.WHITE,
                                border_radius=5,
                                border=ft.border.all(1, ft.colors.BLACK12),
                            ),
                        ],
                        spacing=5,
                    ),
                    padding=10,
                    margin=ft.margin.only(top=10),
                    expand=True,
                ),
            ]
        )

        # メールリスト内の該当アイテムの背景色を変更して選択状態を示す
        for item in self.mail_list.controls:
            if hasattr(item, "on_click") and item.on_click.__closure__:
                for cell in item.on_click.__closure__:
                    if hasattr(cell, "cell_contents") and cell.cell_contents == mail_id:
                        item.bgcolor = ft.colors.BLUE_50
                    else:
                        item.bgcolor = ft.colors.WHITE

        self.update()
        self.logger.info("PreviewContent: メール内容表示完了", mail_id=mail_id)

    def download_attachment(self, file_id):
        """添付ファイルをダウンロード"""
        self.logger.info("PreviewContent: 添付ファイルダウンロード", file_id=file_id)

        # サンプルデータを使用する場合
        if self.use_sample_data:
            # サンプルデータでは常に成功とする
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("ファイルをダウンロードしました"),
                action="閉じる",
            )
            self.page.snack_bar.open = True
            self.page.update()
            return

        if not self.viewmodel:
            return

        # ここで添付ファイルのダウンロード処理を実装
        # 実際の実装はViewModelに委譲する
        success = self.viewmodel.download_attachment(file_id)

        if success:
            # ダウンロード成功時の通知
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("ファイルをダウンロードしました"),
                action="閉じる",
            )
            self.page.snack_bar.open = True
            self.page.update()
        else:
            # ダウンロード失敗時の通知
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("ファイルのダウンロードに失敗しました"),
                action="閉じる",
            )
            self.page.snack_bar.open = True
            self.page.update()

    def show_error_message(self, message):
        """エラーメッセージを表示"""
        self.logger.error("PreviewContent: エラーメッセージ表示", message=message)
        # メール内容表示をクリア
        self.mail_content.controls.clear()
        self.mail_content.controls.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(
                            name=ft.icons.ERROR_OUTLINE,
                            size=40,
                            color=ft.colors.RED,
                        ),
                        ft.Text(
                            "エラーが発生しました",
                            color=ft.colors.RED,
                            text_align=ft.TextAlign.CENTER,
                            weight="bold",
                        ),
                        ft.Text(
                            message,
                            color=ft.colors.RED_700,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                alignment=ft.alignment.center,
                expand=True,
            )
        )
        self.update()

    def show_no_data_message(self, message):
        """データがない場合のメッセージを表示"""
        self.logger.info("PreviewContent: データなしメッセージ表示", message=message)

        # メールリストをクリア
        self.mail_list.controls.clear()
        self.mail_list.controls.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(
                            name=ft.icons.WARNING_AMBER_ROUNDED,
                            size=40,
                            color=ft.colors.AMBER,
                        ),
                        ft.Text(
                            "メールデータがありません",
                            color=ft.colors.GREY,
                            text_align=ft.TextAlign.CENTER,
                            weight="bold",
                        ),
                        ft.Text(
                            message,
                            color=ft.colors.GREY,
                            size=12,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                alignment=ft.alignment.center,
                expand=True,
            )
        )

        # メール内容表示をクリア
        self._show_empty_mail_content()
        self.update()

    def on_dispose(self):
        """リソース解放時の処理"""
        self.logger.info("PreviewContent: リソース解放")
        if self.viewmodel:
            self.viewmodel.close()

    def load_sample_data(self):
        """サンプルデータを読み込む"""
        self.logger.info("PreviewContent: サンプルデータ読み込み開始")

        # サンプルメールデータ
        sample_mails = [
            {
                "id": 1,
                "subject": "プロジェクト進捗報告",
                "sender": "田中太郎 <tanaka@example.com>",
                "recipient": "山田花子 <yamada@example.com>",
                "date": "2023-11-15 14:30",
                "content": "山田さん\n\n先日のミーティングでお話しした件について進捗をご報告します。\n\n現在、システム設計の最終段階に入っており、来週には実装フェーズに移行できる見込みです。\n\n添付資料に詳細な進捗状況をまとめましたので、ご確認ください。\n\n何かご質問があればお知らせください。\n\n田中",
                "preview": "先日のミーティングでお話しした件について進捗をご報告します。",
                "unread": 1,
                "attachments": [
                    {"id": 101, "name": "プロジェクト進捗報告.pdf"},
                    {"id": 102, "name": "スケジュール.xlsx"},
                ],
            },
            {
                "id": 2,
                "subject": "週次会議の議事録",
                "sender": "佐藤一郎 <sato@example.com>",
                "recipient": "プロジェクトチーム <project-team@example.com>",
                "date": "2023-11-14 17:45",
                "content": "プロジェクトチームの皆様\n\n本日の週次会議の議事録を送付いたします。\n\n【議題】\n1. 前回のタスク進捗確認\n2. 新機能の要件定義\n3. テスト計画の策定\n\n【決定事項】\n・11月末までに要件定義を完了させる\n・12月第1週からテスト計画の策定を開始する\n\n詳細は添付ファイルをご確認ください。\n\n佐藤",
                "preview": "本日の週次会議の議事録を送付いたします。",
                "unread": 0,
                "attachments": [{"id": 103, "name": "週次会議議事録_20231114.docx"}],
            },
            {
                "id": 3,
                "subject": "新機能のフィードバック依頼",
                "sender": "鈴木健太 <suzuki@example.com>",
                "recipient": "山田花子 <yamada@example.com>",
                "date": "2023-11-13 10:15",
                "content": "山田さん\n\n先日リリースした新機能について、ユーザーからのフィードバックを集めています。\n\n特に以下の点についてご意見をいただけると助かります：\n\n1. UI/UXの使いやすさ\n2. 処理速度\n3. 追加して欲しい機能\n\n来週の金曜日までにご回答いただけますと幸いです。\n\nよろしくお願いいたします。\n\n鈴木",
                "preview": "先日リリースした新機能について、ユーザーからのフィードバックを集めています。",
                "unread": 0,
                "attachments": [],
            },
            {
                "id": 4,
                "subject": "セキュリティアップデートのお知らせ",
                "sender": "システム管理者 <admin@example.com>",
                "recipient": "全社員 <all-staff@example.com>",
                "date": "2023-11-12 09:00",
                "content": "全社員の皆様\n\n重要なセキュリティアップデートのお知らせです。\n\n本日15時より、社内システムのセキュリティアップデートを実施します。\nアップデート中（約30分間）はシステムにアクセスできなくなりますので、ご注意ください。\n\n作業完了後、改めてご連絡いたします。\n\nご不便をおかけしますが、ご協力のほどよろしくお願いいたします。\n\nシステム管理者",
                "preview": "重要なセキュリティアップデートのお知らせです。",
                "unread": 1,
                "attachments": [],
            },
            {
                "id": 5,
                "subject": "クライアントミーティングの日程調整",
                "sender": "高橋美咲 <takahashi@example.com>",
                "recipient": "山田花子 <yamada@example.com>",
                "date": "2023-11-10 13:20",
                "content": "山田さん\n\nABC株式会社との次回ミーティングの日程調整をお願いします。\n\n先方から以下の候補日が挙がっています：\n・11月20日（月）14:00-16:00\n・11月22日（水）10:00-12:00\n・11月24日（金）15:00-17:00\n\nご都合の良い日をお知らせください。\n\n高橋",
                "preview": "ABC株式会社との次回ミーティングの日程調整をお願いします。",
                "unread": 0,
                "attachments": [],
            },
            {
                "id": 6,
                "subject": "年末パーティーのお知らせ",
                "sender": "総務部 <soumu@example.com>",
                "recipient": "全社員 <all-staff@example.com>",
                "date": "2023-11-08 11:30",
                "content": "社員の皆様\n\n恒例の年末パーティーについてお知らせいたします。\n\n【日時】2023年12月22日（金）18:30～21:00\n【場所】ホテルグランドパレス 2階「クリスタルルーム」\n【会費】5,000円（当日受付にてお支払いください）\n\n出欠確認のため、11月30日までに添付のフォームにてご回答ください。\n\n皆様のご参加をお待ちしております。\n\n総務部",
                "preview": "恒例の年末パーティーについてお知らせいたします。",
                "unread": 0,
                "attachments": [{"id": 104, "name": "年末パーティー出欠フォーム.xlsx"}],
            },
        ]

        # メールリストをクリア
        self.mail_list.controls.clear()

        # サンプルメールを表示
        for mail in sample_mails:
            mail_item = self._create_mail_item(mail)
            self.mail_list.controls.append(mail_item)

        # 初期状態では空のメール内容を表示
        self._show_empty_mail_content()

        self.update()
        self.logger.info("PreviewContent: サンプルデータ読み込み完了")

    def on_group_by_conversation_changed(self, e):
        """会話ごとに集約する設定が変更された時の処理"""
        self.logger.info("PreviewContent: 会話集約設定変更", value=e.control.value)

        # 状態を更新
        self.group_by_conversation = e.control.value

        # 会話コンテナを初期化
        self.conversation_containers = {}
        self.logger.debug("PreviewContent: 会話コンテナ初期化")

        # メール一覧を再読み込み
        self.load_all_mails()

        # 明示的に更新
        self.update()

    def _display_grouped_mails(self, mails):
        """会話ごとにグループ化されたメールを表示（静的な階層表示）"""
        self.logger.debug("PreviewContent: 会話ごとにグループ化して表示")

        # メールリストをクリア
        self.mail_list.controls.clear()

        # 件名でグループ化
        conversation_groups = {}
        for mail in mails:
            # 件名を正規化（Re:や空白を除去）して会話IDとする
            subject = mail["subject"] or "(件名なし)"
            normalized_subject = subject.lower().replace("re:", "").strip()

            if normalized_subject not in conversation_groups:
                conversation_groups[normalized_subject] = []

            conversation_groups[normalized_subject].append(mail)

        # 各グループを日付順にソート
        for subject, group in conversation_groups.items():
            conversation_groups[subject] = sorted(
                group, key=lambda x: x["date"], reverse=True  # 新しい順
            )

        # グループごとに表示
        for subject, group in conversation_groups.items():
            # グループの最新メールを代表として表示
            latest_mail = group[0]
            unread_count = sum(1 for mail in group if mail.get("unread", 0))
            has_attachments = any(mail.get("attachments") for mail in group)

            # 会話グループヘッダーを作成
            # グループのコピーを作成し、グループIDとして保存
            group_id = f"group_{subject}"
            self.conversation_containers[group_id] = group.copy()

            group_header = ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Container(
                                    content=ft.Text(
                                        f"{len(group)}",
                                        color=ft.colors.WHITE,
                                        text_align=ft.TextAlign.CENTER,
                                        size=12,
                                    ),
                                    bgcolor=(
                                        ft.colors.BLUE
                                        if unread_count
                                        else ft.colors.GREY
                                    ),
                                    border_radius=15,
                                    width=25,
                                    height=25,
                                    alignment=ft.alignment.center,
                                ),
                                ft.Text(
                                    latest_mail["subject"] or "(件名なし)",
                                    weight="bold" if unread_count else "normal",
                                    expand=True,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                (
                                    ft.Icon(
                                        name=ft.icons.ATTACH_FILE,
                                        size=14,
                                        color=ft.colors.GREY,
                                    )
                                    if has_attachments
                                    else ft.Container(width=0)
                                ),
                            ],
                            spacing=5,
                        ),
                        ft.Text(
                            f"{group[-1]['date']} - {group[0]['date']}",
                            size=11,
                            color=ft.colors.GREY,
                        ),
                    ],
                    spacing=2,
                ),
                padding=ft.padding.all(10),
                border_radius=5,
                # データをdata属性に保存して、クリックイベントで取得
                data=group_id,
                on_click=self._on_conversation_click,
                ink=True,
                bgcolor=ft.colors.BLUE_50 if unread_count else ft.colors.WHITE,
                border=ft.border.all(1, ft.colors.BLACK12),
                margin=ft.margin.only(bottom=5, top=5),
            )

            # グループヘッダーをリストに追加
            self.mail_list.controls.append(group_header)

    def _on_conversation_click(self, e):
        """会話グループがクリックされたときの処理"""
        self.logger.info(
            "PreviewContent: 会話グループクリック",
            group_id=e.control.data,
            control_type=type(e.control).__name__,
        )

        # コンテナのdata属性からグループIDを取得
        group_id = e.control.data

        # 会話コンテナの状態をログ出力
        self.logger.debug(
            "PreviewContent: 会話コンテナ状態",
            container_keys=list(self.conversation_containers.keys()),
            container_count=len(self.conversation_containers),
        )

        # グループIDに対応するメールリストを取得
        if group_id in self.conversation_containers:
            mails = self.conversation_containers[group_id]
            self.logger.debug(
                "PreviewContent: 会話メール取得成功", mail_count=len(mails)
            )
            self._show_conversation(mails)
        else:
            self.logger.error(
                "PreviewContent: 会話グループが見つかりません", group_id=group_id
            )

    def _get_file_icon(self, filename):
        """ファイル名から適切なアイコンを返す"""
        extension = filename.split(".")[-1].lower() if "." in filename else ""

        if extension in ["pdf"]:
            return ft.Icon(name=ft.icons.PICTURE_AS_PDF, size=24, color=ft.colors.RED)
        elif extension in ["doc", "docx"]:
            return ft.Icon(name=ft.icons.ARTICLE, size=24, color=ft.colors.BLUE)
        elif extension in ["xls", "xlsx"]:
            return ft.Icon(name=ft.icons.TABLE_CHART, size=24, color=ft.colors.GREEN)
        elif extension in ["ppt", "pptx"]:
            return ft.Icon(name=ft.icons.SLIDESHOW, size=24, color=ft.colors.ORANGE)
        elif extension in ["jpg", "jpeg", "png", "gif"]:
            return ft.Icon(name=ft.icons.IMAGE, size=24, color=ft.colors.PURPLE)
        elif extension in ["zip", "rar", "7z"]:
            return ft.Icon(name=ft.icons.FOLDER_ZIP, size=24, color=ft.colors.BROWN)
        else:
            return ft.Icon(
                name=ft.icons.INSERT_DRIVE_FILE, size=24, color=ft.colors.GREY
            )

    def _get_file_type(self, filename):
        """ファイル名から種類の説明を返す"""
        extension = filename.split(".")[-1].lower() if "." in filename else ""

        if extension in ["pdf"]:
            return "PDF文書"
        elif extension in ["doc", "docx"]:
            return "Word文書"
        elif extension in ["xls", "xlsx"]:
            return "Excel表計算"
        elif extension in ["ppt", "pptx"]:
            return "PowerPointプレゼンテーション"
        elif extension in ["jpg", "jpeg", "png", "gif"]:
            return "画像ファイル"
        elif extension in ["zip", "rar", "7z"]:
            return "圧縮ファイル"
        else:
            return f"{extension.upper()}ファイル" if extension else "ファイル"

    def _show_conversation(self, mails):
        """会話グループのメール内容を表示"""
        self.logger.info("PreviewContent: 会話内容表示開始", mail_count=len(mails))

        # メール内容表示をクリア
        self.mail_content.controls.clear()

        if not mails:
            self.logger.error("PreviewContent: 会話内容が空です")
            return

        # 最新のメールを取得
        latest_mail = mails[0]

        # 送信者情報を解析
        sender_name = latest_mail["sender"].split("<")[0].strip()
        sender_email = (
            latest_mail["sender"].split("<")[1].replace(">", "")
            if "<" in latest_mail["sender"]
            else latest_mail["sender"]
        )

        # 受信者情報を解析
        recipient_name = latest_mail.get("recipient", "").split("<")[0].strip()
        recipient_email = (
            latest_mail.get("recipient", "").split("<")[1].replace(">", "")
            if "<" in latest_mail.get("recipient", "")
            else latest_mail.get("recipient", "")
        )

        # 添付ファイルがあれば表示用のリストを作成
        attachments_section = []
        if latest_mail.get("attachments"):
            attachments = latest_mail["attachments"]
            attachments_list = ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(
                                    name=ft.icons.ATTACH_FILE,
                                    size=16,
                                    color=ft.colors.BLUE,
                                ),
                                ft.Text("添付ファイル", weight="bold"),
                            ],
                            spacing=5,
                        ),
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Row(
                                        [
                                            self._get_file_icon(attachment["name"]),
                                            ft.Text(attachment["name"]),
                                            ft.Text(
                                                self._get_file_type(attachment["name"]),
                                                size=12,
                                                color=ft.colors.GREY,
                                            ),
                                        ],
                                        spacing=10,
                                    )
                                    for attachment in attachments
                                ],
                                spacing=5,
                            ),
                            padding=10,
                        ),
                    ],
                    spacing=5,
                ),
                padding=10,
                border=ft.border.all(1, ft.colors.BLACK12),
                border_radius=5,
                margin=ft.margin.only(top=10),
            )
            attachments_section = [attachments_list]

        # AIレビューセクション（会話集約モード専用）
        ai_review_section = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(
                                name=ft.icons.PSYCHOLOGY_ALT,
                                size=16,
                                color=ft.colors.BLUE,
                            ),
                            ft.Text("AIレビュー", weight="bold"),
                        ],
                        spacing=5,
                    ),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Text("リスクスコア:", weight="bold"),
                                        ft.Container(
                                            content=ft.Text(
                                                "低",
                                                color=ft.colors.WHITE,
                                                text_align=ft.TextAlign.CENTER,
                                            ),
                                            bgcolor=ft.colors.GREEN,
                                            border_radius=5,
                                            padding=5,
                                            width=50,
                                            alignment=ft.alignment.center,
                                        ),
                                    ],
                                    spacing=10,
                                ),
                                ft.Text(
                                    "この会話はビジネス関連の通常のやり取りであり、特に注意すべき点は見つかりませんでした。",
                                    size=14,
                                ),
                                ft.Row(
                                    [
                                        ft.Text("キーポイント:", weight="bold"),
                                    ],
                                ),
                                ft.Column(
                                    [
                                        ft.Text(
                                            "• プロジェクトの進捗報告が主な内容です",
                                            size=14,
                                        ),
                                        ft.Text(
                                            "• 期限や重要な決定事項が含まれています",
                                            size=14,
                                        ),
                                        ft.Text(
                                            "• フォローアップが必要な項目があります",
                                            size=14,
                                        ),
                                    ],
                                    spacing=2,
                                ),
                            ],
                            spacing=10,
                        ),
                        padding=10,
                    ),
                ],
                spacing=5,
            ),
            padding=10,
            border=ft.border.all(1, ft.colors.BLACK12),
            border_radius=5,
            margin=ft.margin.only(top=10),
        )

        # 会話の概要セクション
        conversation_summary = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        latest_mail["subject"] or "(件名なし)",
                        size=18,
                        weight="bold",
                    ),
                    ft.Divider(height=1, color=ft.colors.BLACK12),
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Text(
                                                "会話数:",
                                                weight="bold",
                                                width=80,
                                            ),
                                            ft.Text(f"{len(mails)}件のメール"),
                                        ],
                                    ),
                                    ft.Row(
                                        [
                                            ft.Text(
                                                "期間:",
                                                weight="bold",
                                                width=80,
                                            ),
                                            ft.Text(
                                                f"{mails[-1]['date']} - {mails[0]['date']}"
                                            ),
                                        ],
                                    ),
                                    ft.Row(
                                        [
                                            ft.Text(
                                                "参加者:",
                                                weight="bold",
                                                width=80,
                                            ),
                                            ft.Text(f"{sender_name}、{recipient_name}"),
                                        ],
                                    ),
                                ],
                                spacing=5,
                            ),
                        ],
                    ),
                ],
                spacing=10,
            ),
            padding=10,
            bgcolor=ft.colors.WHITE,
            border_radius=5,
            border=ft.border.all(1, ft.colors.BLACK12),
        )

        # 最新のメール内容
        latest_mail_content = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "最新のメール:",
                        weight="bold",
                    ),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Text(
                                            "送信者:",
                                            weight="bold",
                                            width=80,
                                        ),
                                        ft.Text(f"{sender_name} <{sender_email}>"),
                                    ],
                                ),
                                ft.Row(
                                    [
                                        ft.Text(
                                            "日時:",
                                            weight="bold",
                                            width=80,
                                        ),
                                        ft.Text(latest_mail["date"]),
                                    ],
                                ),
                                ft.Divider(height=1, color=ft.colors.BLACK12),
                                ft.Text(latest_mail["content"]),
                            ],
                            spacing=5,
                        ),
                        padding=10,
                        bgcolor=ft.colors.WHITE,
                        border_radius=5,
                        border=ft.border.all(1, ft.colors.BLACK12),
                    ),
                ],
                spacing=5,
            ),
            padding=10,
            margin=ft.margin.only(top=10),
            expand=True,
        )

        # メール内容を表示
        self.mail_content.controls.extend(
            [
                conversation_summary,
                ai_review_section,
                *attachments_section,
                latest_mail_content,
            ]
        )

        self.update()
        self.logger.info("PreviewContent: 会話内容表示完了")
