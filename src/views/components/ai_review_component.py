"""
AIレビューコンポーネント
メールや会話のAI評価結果を表示するコンポーネント
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional

import flet as ft

from src.core.logger import get_logger
from src.util.object_util import get_safe


class AIReviewComponent(ft.Container):
    """
    AIレビュー情報を表示するコンポーネント
    メール単体のAI評価と会話グループのAI評価の両方に対応
    """

    def __init__(
        self,
        on_refresh: Optional[Callable] = None,
        viewmodel=None,
        **kwargs,
    ):
        """初期化"""
        super().__init__(**kwargs)
        self.logger = get_logger()
        self.logger.info("AIReviewComponent: 初期化開始")

        # コールバックとViewModel
        self.on_refresh = on_refresh
        self.viewmodel = viewmodel

        # 現在のメールID/スレッドID
        self.current_id = None
        self.is_thread = False  # スレッド(True)かメール単体(False)か

        # コンポーネント初期化
        self._init_components()

        # UIを構築
        self._build()

        self.logger.info("AIReviewComponent: 初期化完了")

    def _init_components(self):
        """コンポーネントの初期化"""
        # メインのコンテンツコンテナ
        self.content_column = ft.Column(
            [],
            spacing=5,
        )

    def _build(self):
        """UIを構築"""
        # コンテナの設定
        self.padding = 0
        self.expand = False
        self.content = self.content_column
        self.bgcolor = ft.colors.WHITE
        self.border_radius = 5
        self.border = ft.border.all(1, ft.colors.BLACK12)

    def _safe_update(self):
        """安全なUI更新"""
        try:
            if hasattr(self, "page") and self.page:
                self.update()
        except Exception as e:
            self.logger.error(f"AIReviewComponent: UI更新エラー - {str(e)}")

    def show_review_for_mail(
        self,
        mail_id: str,
        ai_review: Optional[Dict] = None,
        risk_score: Optional[Dict] = None,
    ):
        """
        メール単体のAIレビュー情報を表示

        Args:
            mail_id: メールID
            ai_review: AIレビュー情報（Noneの場合はViewModelから取得）
            risk_score: リスクスコア情報（Noneの場合はViewModelから取得）
        """
        self.logger.info(
            f"AIReviewComponent: メール単体のレビュー表示 mail_id={mail_id}"
        )
        self.current_id = mail_id
        self.is_thread = False

        # ViewModelからAIレビュー情報を取得（必要な場合）
        if not ai_review and self.viewmodel and mail_id:
            mail = self.viewmodel.get_mail_content(mail_id)
            if mail and mail.get("ai_review"):
                ai_review = mail["ai_review"]
                self.logger.debug(
                    "AIReviewComponent: メールからAIレビュー情報を取得",
                    ai_review=ai_review,
                )

        # ViewModelからリスクスコア情報を取得（必要な場合）
        if not risk_score and self.viewmodel and mail_id:
            mail = self.viewmodel.get_mail_content(mail_id)
            if mail:
                # メール単体のリスクスコア（将来的な拡張性のため）
                if hasattr(self.viewmodel, "get_mail_risk_score"):
                    risk_score = self.viewmodel.get_mail_risk_score(mail)
                # 会話のリスクスコアで代用
                elif mail.get("thread_id") and hasattr(
                    self.viewmodel, "get_thread_risk_score"
                ):
                    risk_score = self.viewmodel.get_thread_risk_score([mail])

        # AIレビュー情報を表示
        self._display_ai_review(ai_review, risk_score)

    def show_review_for_thread(
        self,
        thread_id: str,
        mails: List[Dict] = None,
        ai_review: Optional[Dict] = None,
        risk_score: Optional[Dict] = None,
    ):
        """
        会話グループのAIレビュー情報を表示

        Args:
            thread_id: 会話ID
            mails: 会話に含まれるメールのリスト（ViewModelからAIレビュー情報を取得する際に使用）
            ai_review: AIレビュー情報（Noneの場合はViewModelから取得）
            risk_score: リスクスコア情報（Noneの場合はViewModelから取得）
        """
        self.logger.info(
            f"AIReviewComponent: 会話グループのレビュー表示 thread_id={thread_id}"
        )
        self.current_id = thread_id
        self.is_thread = True

        # ViewModelからAIレビュー情報を取得（必要な場合）
        if not ai_review and self.viewmodel and thread_id:
            # ViewModelのメソッドを確認
            if hasattr(self.viewmodel.model, "get_ai_review_for_thread"):
                ai_review = self.viewmodel.model.get_ai_review_for_thread(thread_id)

            # メールリストからAIレビュー情報を取得（バックアップ）
            if not ai_review and mails:
                for mail in mails:
                    if mail.get("ai_review"):
                        ai_review = mail["ai_review"]
                        self.logger.debug(
                            "AIReviewComponent: メールからAIレビュー情報を取得",
                            ai_review=ai_review,
                        )
                        break

        # ViewModelからリスクスコア情報を取得（必要な場合）
        if not risk_score and self.viewmodel and thread_id:
            if hasattr(self.viewmodel, "get_thread_risk_score") and mails:
                risk_score = self.viewmodel.get_thread_risk_score(mails)

        # AIレビュー情報を表示
        self._display_ai_review(ai_review, risk_score)

    def _display_ai_review(
        self, ai_review: Optional[Dict] = None, risk_score: Optional[Dict] = None
    ):
        """AIレビュー情報を表示"""
        # コンテンツをクリア
        self.content_column.controls.clear()

        # AIレビューセクションを作成
        ai_review_section = self._create_ai_review_section(ai_review, risk_score)

        # コンテンツに追加
        self.content_column.controls.append(ai_review_section)

        # 表示を更新
        self._safe_update()

    def _create_ai_review_section(self, ai_review_info=None, risk_score=None):
        """AIレビュー情報セクションを作成"""
        # デフォルトのリスクスコア
        if not risk_score:
            risk_score = {
                "label": "不明",
                "color": ft.colors.GREY,
                "score": 0,
                "tooltip": "リスク評価が利用できません",
            }

        # AI情報の安全な取得
        summary = get_safe(
            ai_review_info, "summary", "AIによる会話の要約情報はありません。"
        )
        attention_points = get_safe(ai_review_info, "attention_points", [])
        organizations = get_safe(ai_review_info, "organizations", [])
        review = get_safe(ai_review_info, "review", "詳細な評価情報はありません。")
        score = get_safe(ai_review_info, "score", 0)

        # リスクスコアの表示
        risk_label = risk_score.get("label", "不明")
        risk_color = risk_score.get("color", ft.colors.GREY)
        risk_tooltip = risk_score.get("tooltip", "リスク評価情報")

        # 注目ポイントのコントロールを作成
        attention_controls = []
        for i, point in enumerate(attention_points):
            is_important = i < 2  # 最初の2つは重要なポイントとして扱う
            attention_controls.append(
                self._create_animated_point(point, i * 200, is_important)
            )

        # 組織情報が存在する場合は表示用のコンポーネントを作成
        organizations_ui = None
        if organizations:
            org_chips = []
            for org in organizations:
                org_chips.append(
                    ft.Chip(
                        label=ft.Text(org),
                        bgcolor=ft.colors.BLUE_50,
                        label_style=ft.TextStyle(size=12),
                    )
                )

            organizations_ui = ft.Column(
                [
                    ft.Text("関連組織:", weight="bold"),
                    ft.Wrap(
                        spacing=5,
                        run_spacing=5,
                        children=org_chips,
                    ),
                ]
            )

        # AI評価セクションを作成して返す
        return ft.Container(
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
                            ft.Container(
                                content=ft.Icon(
                                    name=ft.icons.REFRESH,
                                    size=16,
                                    color=ft.colors.BLUE,
                                ),
                                tooltip="AIに再評価させる",
                                width=32,
                                height=32,
                                border_radius=16,
                                on_hover=self._on_hover_effect,
                                on_click=self._on_ai_review_refresh,
                                alignment=ft.alignment.center,
                            ),
                        ],
                        spacing=5,
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(
                        content=ft.Column(
                            [
                                # リスクスコア表示
                                ft.Row(
                                    [
                                        ft.Text("リスクスコア:", weight="bold"),
                                        ft.Container(
                                            content=ft.Text(
                                                risk_label,
                                                color=ft.colors.WHITE,
                                                text_align=ft.TextAlign.CENTER,
                                            ),
                                            bgcolor=risk_color,
                                            border_radius=5,
                                            padding=5,
                                            width=50,
                                            alignment=ft.alignment.center,
                                            tooltip=risk_tooltip,
                                        ),
                                    ],
                                    spacing=10,
                                ),
                                # 会話要約セクション
                                ft.Column(
                                    [
                                        ft.Text("要約:", weight="bold"),
                                        ft.Container(
                                            content=ft.Text(summary, size=12),
                                            bgcolor=ft.colors.GREY_50,
                                            border_radius=5,
                                            padding=10,
                                            width=float("inf"),
                                        ),
                                    ],
                                    spacing=5,
                                ),
                                # 注目ポイントセクション
                                ft.Column(
                                    [
                                        ft.Text("注目ポイント:", weight="bold"),
                                        (
                                            ft.Column(
                                                attention_controls,
                                                spacing=2,
                                            )
                                            if attention_controls
                                            else ft.Text(
                                                "特に注目すべきポイントはありません",
                                                size=12,
                                                italic=True,
                                            )
                                        ),
                                    ],
                                    spacing=5,
                                ),
                                # 組織情報セクション（存在する場合のみ）
                                (
                                    organizations_ui
                                    if organizations_ui
                                    else ft.Container()
                                ),
                                # レビュー詳細セクション
                                ft.Container(
                                    content=ft.Column(
                                        [
                                            ft.Text("詳細評価:", weight="bold"),
                                            ft.Container(
                                                content=ft.Text(review, size=12),
                                                bgcolor=ft.colors.GREY_50,
                                                border_radius=5,
                                                padding=10,
                                                width=float("inf"),
                                            ),
                                        ]
                                    ),
                                    margin=ft.margin.only(top=10),
                                ),
                            ],
                            spacing=10,
                        ),
                        padding=10,
                    ),
                ],
                spacing=5,
            ),
            padding=0,
            border=ft.border.all(1, ft.colors.BLACK12),
            border_radius=5,
            margin=ft.margin.only(top=10),
            bgcolor=ft.colors.WHITE,
        )

    def _create_animated_point(self, text, delay_ms, is_important=False):
        """アニメーション付きのポイントを作成"""
        return ft.Container(
            content=ft.Text(
                f"• {text}",
                size=12,
                color=ft.colors.RED if is_important else None,
                weight="bold" if is_important else None,
            ),
            opacity=1.0,
            data={"delay": delay_ms, "text": text},
        )

    def _on_hover_effect(self, e):
        """ホバー効果"""
        # マウスが入ったとき
        if e.data == "true":
            e.control.bgcolor = ft.colors.with_opacity(0.1, ft.colors.BLUE)
        # マウスが出たとき
        else:
            e.control.bgcolor = None
        e.control.update()

    def _on_ai_review_refresh(self, e):
        """AIレビューの再評価ボタンがクリックされたときの処理"""
        self.logger.info("AIReviewComponent: AIレビュー再評価リクエスト")

        # 再評価中の表示
        ai_review_section = e.control.parent.parent.parent

        # 読み込み中表示に切り替え
        ai_review_section.content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(
                            name=ft.icons.PSYCHOLOGY_ALT,
                            size=16,
                            color=ft.colors.BLUE,
                        ),
                        ft.Text("AIレビュー", weight="bold"),
                        ft.ProgressRing(width=16, height=16),
                    ],
                    spacing=5,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("AIによる再評価中...", italic=True),
                            ft.ProgressBar(width=300),
                        ],
                        spacing=10,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    padding=20,
                    alignment=ft.alignment.center,
                ),
            ],
            spacing=5,
        )
        self._safe_update()

        # 外部で定義されたリフレッシュハンドラがあれば使用
        if self.on_refresh:
            self.on_refresh(self.current_id, self.is_thread)
            return

        # ViewModelが設定されていない場合はモック処理を行う
        if not self.viewmodel:
            self._run_mock_refresh(ai_review_section)
            return

        # IDがない場合はモック処理
        if not self.current_id:
            self._run_mock_refresh(ai_review_section)
            return

        # スレッドかメール単体かに応じて処理を分岐
        if self.is_thread:
            self._refresh_thread_review(ai_review_section)
        else:
            self._refresh_mail_review(ai_review_section)

    def _run_mock_refresh(self, ai_review_section):
        """モックのリフレッシュ処理を実行"""

        async def simulate_ai_review():
            # 処理時間をシミュレート
            await asyncio.sleep(2)
            # モックのAIレビュー結果
            mock_review = {
                "summary": "この会話はプロジェクトの納期に関する相談と予算の確認について述べています。",
                "attention_points": [
                    "来週金曜日までに納品が必要です",
                    "予算超過の可能性があります",
                    "関係者全員への確認が必要です",
                ],
                "organizations": ["株式会社テクノ", "ABCコンサルティング"],
                "review": "この会話は納期と予算に関する重要な情報を含んでいます。特に期限が迫っているため早急な対応が必要です。",
                "score": 2,
            }

            # レビュー結果表示を更新
            self._update_ai_review_section(ai_review_section, mock_review, None)

        # 非同期処理を開始
        asyncio.create_task(simulate_ai_review())

    def _refresh_thread_review(self, ai_review_section):
        """会話グループのAIレビューを更新"""

        # AIレビューを実行する非同期処理
        async def run_ai_review():
            try:
                # 実際のAIレビュー結果を取得（本来はAPI呼び出しなど）
                await asyncio.sleep(2)  # APIレスポンスを待つ時間を模倣

                # ViewModelからAIレビュー結果を再取得
                thread_id = self.current_id
                ai_review = None

                if hasattr(self.viewmodel.model, "get_ai_review_for_thread"):
                    ai_review = self.viewmodel.model.get_ai_review_for_thread(thread_id)

                # AIレビュー結果がない場合はモックデータを使用
                if not ai_review:
                    self.logger.warning(
                        "AIReviewComponent: AIレビュー結果がないためモックデータを使用",
                        thread_id=thread_id,
                    )
                    # モックデータ
                    ai_review = {
                        "summary": "この会話はプロジェクトの納期に関する相談と予算の確認について述べています。",
                        "attention_points": [
                            "来週金曜日までに納品が必要です",
                            "予算超過の可能性があります",
                            "関係者全員への確認が必要です",
                        ],
                        "organizations": ["株式会社テクノ", "ABCコンサルティング"],
                        "review": "この会話は納期と予算に関する重要な情報を含んでいます。特に期限が迫っているため早急な対応が必要です。",
                        "score": 2,
                    }

                # リスクスコア情報を取得
                risk_score = self._get_risk_score_from_ai_review(ai_review)

                # レビュー結果表示を更新
                self._update_ai_review_section(ai_review_section, ai_review, risk_score)
            except Exception as e:
                self.logger.error(f"AIレビュー更新中にエラー: {str(e)}")
                # エラー表示
                self._show_ai_review_error(ai_review_section, str(e))

        # 非同期処理を開始
        asyncio.create_task(run_ai_review())

    def _refresh_mail_review(self, ai_review_section):
        """メール単体のAIレビューを更新"""

        # AIレビューを実行する非同期処理
        async def run_ai_review():
            try:
                # 実際のAIレビュー結果を取得（本来はAPI呼び出しなど）
                await asyncio.sleep(2)  # APIレスポンスを待つ時間を模倣

                # ViewModelからメール情報を再取得
                mail_id = self.current_id
                mail = None
                ai_review = None

                if hasattr(self.viewmodel, "get_mail_content"):
                    mail = self.viewmodel.get_mail_content(mail_id)
                    if mail and mail.get("ai_review"):
                        ai_review = mail["ai_review"]

                # AIレビュー結果がない場合はモックデータを使用
                if not ai_review:
                    self.logger.warning(
                        "AIReviewComponent: AIレビュー結果がないためモックデータを使用",
                        mail_id=mail_id,
                    )
                    # モックデータ
                    ai_review = {
                        "summary": "このメールはプロジェクトの納期に関する重要な通知です。",
                        "attention_points": [
                            "納期が1週間延長されました",
                            "追加予算の承認が必要です",
                        ],
                        "organizations": ["株式会社テクノ"],
                        "review": "このメールには納期と予算に関する重要な変更が含まれています。関係者への周知が必要です。",
                        "score": 2,
                    }

                # リスクスコア情報を取得
                risk_score = self._get_risk_score_from_ai_review(ai_review)

                # レビュー結果表示を更新
                self._update_ai_review_section(ai_review_section, ai_review, risk_score)
            except Exception as e:
                self.logger.error(f"AIレビュー更新中にエラー: {str(e)}")
                # エラー表示
                self._show_ai_review_error(ai_review_section, str(e))

        # 非同期処理を開始
        asyncio.create_task(run_ai_review())

    def _show_ai_review_error(self, section, error_message):
        """AIレビューエラー表示"""
        section.content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(
                            name=ft.icons.ERROR_OUTLINE,
                            size=16,
                            color=ft.colors.RED,
                        ),
                        ft.Text("AIレビューエラー", weight="bold"),
                        ft.Container(
                            content=ft.Icon(
                                name=ft.icons.REFRESH,
                                size=16,
                                color=ft.colors.BLUE,
                            ),
                            tooltip="再試行",
                            width=32,
                            height=32,
                            border_radius=16,
                            on_hover=self._on_hover_effect,
                            on_click=self._on_ai_review_refresh,
                            alignment=ft.alignment.center,
                        ),
                    ],
                    spacing=5,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "AIレビューの取得中にエラーが発生しました：",
                                color=ft.colors.RED,
                            ),
                            ft.Text(error_message, size=12, italic=True),
                        ],
                        spacing=5,
                    ),
                    padding=10,
                ),
            ],
            spacing=5,
        )
        self._safe_update()

    def _get_risk_score_from_ai_review(self, ai_review):
        """AIレビュー結果からリスクスコア情報を取得"""
        # AIレビュー結果がない場合はデフォルト値を返す
        if not ai_review:
            return {
                "label": "不明",
                "color": ft.colors.GREY,
                "score": 0,
                "tooltip": "リスク評価が利用できません",
            }

        # 新しいAIレビュー形式からスコアを取得
        score = get_safe(ai_review, "score", 0)

        # スコアに応じてリスクレベルを設定
        if score > 3:
            return {
                "label": "高",
                "color": ft.colors.RED,
                "score": 3,
                "tooltip": "複数の注意点があります。内容を慎重に確認してください。",
            }
        elif score > 1:
            return {
                "label": "中",
                "color": ft.colors.ORANGE,
                "score": 2,
                "tooltip": "いくつかの注意点があります。確認を推奨します。",
            }
        elif score > 0:
            return {
                "label": "低",
                "color": ft.colors.YELLOW,
                "score": 1,
                "tooltip": "軽微な注意点があります。",
            }
        else:
            return {
                "label": "なし",
                "color": ft.colors.GREEN,
                "score": 0,
                "tooltip": "特に問題は見つかりませんでした。",
            }

    def _update_ai_review_section(self, section, ai_review, risk_score):
        """AIレビューセクションの表示を更新"""
        # 新しいAIレビューセクションを作成
        new_section = self._create_ai_review_section(ai_review, risk_score)

        # セクションの内容を更新
        section.content = new_section.content

        # 表示を更新
        self._safe_update()

    def reset(self):
        """コンポーネントのリセット"""
        self.content_column.controls.clear()
        self.current_id = None
        self.is_thread = False
        self._safe_update()
