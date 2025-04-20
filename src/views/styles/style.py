"""
アプリケーション全体のスタイル定義
コンポーネントのスタイルを集約して一貫性を保つ
"""

from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import flet as ft

from src.views.styles.color import Colors


class ComponentState(str, Enum):
    """コンポーネントの状態を表す列挙型"""

    NORMAL = "normal"
    DISABLED = "disabled"
    HOVERED = "hovered"
    FOCUSED = "focused"
    PRESSED = "pressed"
    ERROR = "error"
    ACTIVE = "active"


# アプリケーション全体のテーマ設定
class AppTheme:
    """アプリケーション全体のテーマ設定"""

    # ページの基本設定
    PAGE_PADDING = 20
    PAGE_BGCOLOR = Colors.BACKGROUND

    # コンテナの基本設定
    CONTAINER_PADDING = 16
    CONTAINER_BORDER_RADIUS = 8

    # テキストの基本設定
    TITLE_SIZE = 24
    SUBTITLE_SIZE = 18
    BODY_SIZE = 14
    CAPTION_SIZE = 12

    # スペーシングの基本設定
    SPACING_XS = 4
    SPACING_SM = 8
    SPACING_MD = 16
    SPACING_LG = 24
    SPACING_XL = 32

    # アイコンの基本設定
    ICON_SIZE_SM = 16
    ICON_SIZE_MD = 24
    ICON_SIZE_LG = 32

    # 共通ボーダー設定
    BORDER_RADIUS = 4
    BORDER_WIDTH = 1
    FOCUSED_BORDER_WIDTH = 2

    # 共通パディング設定
    DEFAULT_PADDING = 8
    CARD_PADDING = 16
    CONTENT_PADDING = 20


class StyleConstants:
    """スタイル定数"""

    # 共通のシャドウ設定
    SHADOW_SM = ft.BoxShadow(
        spread_radius=1,
        blur_radius=2,
        color=ft.colors.with_opacity(0.3, ft.colors.BLACK),
    )
    SHADOW_MD = ft.BoxShadow(
        spread_radius=1,
        blur_radius=4,
        color=ft.colors.with_opacity(0.3, ft.colors.BLACK),
    )
    SHADOW_LG = ft.BoxShadow(
        spread_radius=1,
        blur_radius=8,
        color=ft.colors.with_opacity(0.3, ft.colors.BLACK),
    )


class Styles:
    """スタイル定義とヘルパーメソッドを提供するクラス"""

    # 基本的な共通スタイル
    _COMMON_STYLE = {
        "border_radius": AppTheme.BORDER_RADIUS,
        "padding": AppTheme.DEFAULT_PADDING,
    }

    # ボタン共通スタイル
    _BUTTON_COMMON = {
        "border_radius": AppTheme.BORDER_RADIUS,
        "padding": AppTheme.DEFAULT_PADDING,
    }

    # カード共通スタイル
    _CARD_COMMON = {
        "bgcolor": Colors.BACKGROUND,
        "border_radius": AppTheme.CONTAINER_BORDER_RADIUS,
        "padding": AppTheme.CARD_PADDING,
    }

    # 基本スタイル定義
    BASE_STYLES = {
        ComponentState.NORMAL: {
            **_COMMON_STYLE,
            "bgcolor": Colors.BACKGROUND,
            "border": ft.border.all(AppTheme.BORDER_WIDTH, Colors.BORDER),
        },
        ComponentState.HOVERED: {
            **_COMMON_STYLE,
            "bgcolor": Colors.BACKGROUND_LIGHT,
            "border": ft.border.all(AppTheme.BORDER_WIDTH, Colors.PRIMARY_LIGHT),
            "shadow": StyleConstants.SHADOW_SM,
        },
        ComponentState.FOCUSED: {
            **_COMMON_STYLE,
            "bgcolor": Colors.BACKGROUND,
            "border": ft.border.all(AppTheme.FOCUSED_BORDER_WIDTH, Colors.PRIMARY),
        },
        ComponentState.PRESSED: {
            **_COMMON_STYLE,
            "bgcolor": Colors.PRIMARY_LIGHT,
            "border": ft.border.all(AppTheme.BORDER_WIDTH, Colors.PRIMARY_DARK),
        },
        ComponentState.DISABLED: {
            **_COMMON_STYLE,
            "bgcolor": Colors.BACKGROUND_DARK,
            "border": ft.border.all(AppTheme.BORDER_WIDTH, Colors.BORDER),
            "opacity": 0.5,
        },
        ComponentState.ERROR: {
            **_COMMON_STYLE,
            "bgcolor": Colors.BACKGROUND,
            "border": ft.border.all(AppTheme.BORDER_WIDTH, Colors.ERROR),
        },
        ComponentState.ACTIVE: {
            **_COMMON_STYLE,
            "bgcolor": Colors.SELECTED,
            "border": ft.border.all(AppTheme.FOCUSED_BORDER_WIDTH, Colors.PRIMARY),
            "shadow": StyleConstants.SHADOW_SM,
        },
    }

    # ボタンスタイル
    BUTTON_STYLES = {
        ComponentState.NORMAL: {
            **_BUTTON_COMMON,
            "bgcolor": Colors.PRIMARY,
            "color": Colors.TEXT_ON_PRIMARY,
            "shadow": StyleConstants.SHADOW_SM,
        },
        ComponentState.HOVERED: {
            **_BUTTON_COMMON,
            "bgcolor": Colors.PRIMARY_LIGHT,
            "color": Colors.TEXT_ON_PRIMARY,
            "shadow": StyleConstants.SHADOW_MD,
        },
        ComponentState.PRESSED: {
            **_BUTTON_COMMON,
            "bgcolor": Colors.PRIMARY_DARK,
            "color": Colors.TEXT_ON_PRIMARY,
        },
        ComponentState.DISABLED: {
            **_BUTTON_COMMON,
            "bgcolor": Colors.BACKGROUND_DARK,
            "color": Colors.TEXT_DISABLED,
            "opacity": 0.5,
        },
    }

    # アクションボタンスタイル（トグル、追加などの操作ボタン）
    ACTION_BUTTON_STYLES = {
        ComponentState.NORMAL: {
            **_BUTTON_COMMON,
            "bgcolor": Colors.ACTION,
            "color": Colors.TEXT_ON_ACTION,
            "shadow": StyleConstants.SHADOW_SM,
        },
        ComponentState.HOVERED: {
            **_BUTTON_COMMON,
            "bgcolor": Colors.ACTION_LIGHT,
            "color": Colors.TEXT_ON_ACTION,
            "shadow": StyleConstants.SHADOW_MD,
        },
        ComponentState.PRESSED: {
            **_BUTTON_COMMON,
            "bgcolor": Colors.ACTION_DARK,
            "color": Colors.TEXT_ON_ACTION,
        },
        ComponentState.DISABLED: {
            **_BUTTON_COMMON,
            "bgcolor": Colors.BACKGROUND_DARK,
            "color": Colors.TEXT_DISABLED,
            "opacity": 0.5,
        },
    }

    # テキストボタンスタイル
    TEXT_BUTTON_STYLES = {
        ComponentState.NORMAL: {
            "color": Colors.PRIMARY,
            "padding": AppTheme.DEFAULT_PADDING,
        },
        ComponentState.HOVERED: {
            "color": Colors.PRIMARY_LIGHT,
            "bgcolor": ft.colors.with_opacity(0.1, Colors.PRIMARY),
            "padding": AppTheme.DEFAULT_PADDING,
        },
        ComponentState.PRESSED: {
            "color": Colors.PRIMARY_DARK,
            "bgcolor": ft.colors.with_opacity(0.2, Colors.PRIMARY),
            "padding": AppTheme.DEFAULT_PADDING,
        },
        ComponentState.DISABLED: {
            "color": Colors.TEXT_DISABLED,
            "padding": AppTheme.DEFAULT_PADDING,
            "opacity": 0.6,
        },
    }

    # カードスタイル
    CARD_STYLES = {
        ComponentState.NORMAL: {
            **_CARD_COMMON,
            "shadow": StyleConstants.SHADOW_MD,
        },
        ComponentState.HOVERED: {
            **_CARD_COMMON,
            "shadow": StyleConstants.SHADOW_LG,
        },
    }

    # テキストスタイル
    TEXT_STYLES = {
        "title": {
            "size": AppTheme.TITLE_SIZE,
            "color": Colors.TEXT_PRIMARY,
            "weight": ft.FontWeight.BOLD,
            "overflow": ft.TextOverflow.ELLIPSIS,
        },
        "subtitle": {
            "size": AppTheme.SUBTITLE_SIZE,
            "color": Colors.TEXT_PRIMARY,
            "weight": ft.FontWeight.W_500,
            "overflow": ft.TextOverflow.ELLIPSIS,
        },
        "body": {
            "size": AppTheme.BODY_SIZE,
            "color": Colors.TEXT_PRIMARY,
        },
        "caption": {
            "size": AppTheme.CAPTION_SIZE,
            "color": Colors.TEXT_SECONDARY,
        },
    }

    @staticmethod
    def apply_to(control: ft.Control, style_dict: Dict[str, Any]) -> None:
        """スタイル辞書を指定のコントロールに適用する"""
        for key, value in style_dict.items():
            setattr(control, key, value)

    @staticmethod
    def apply_state(
        control: ft.Control,
        style_map: Dict[ComponentState, Dict[str, Any]],
        state: ComponentState = ComponentState.NORMAL,
    ) -> None:
        """状態に応じたスタイルをコントロールに適用する"""
        if state in style_map:
            Styles.apply_to(control, style_map[state])

    @staticmethod
    def _filter_style(
        style_dict: Dict[str, Any], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """明示的に指定されたプロパティを除外したスタイル辞書を返す"""
        return {k: v for k, v in style_dict.items() if k not in kwargs}

    @staticmethod
    def _setup_hover_handler(
        container: ft.Container,
        style_map: Dict[ComponentState, Dict[str, Any]],
        excluded_keys: List[str] = None,
    ) -> None:
        """ホバーハンドラを設定する"""
        if excluded_keys is None:
            excluded_keys = ["ink", "on_click"]

        def on_hover(e):
            is_hovering = e.data == "true"
            state = ComponentState.HOVERED if is_hovering else ComponentState.NORMAL

            if state in style_map:
                for key, value in style_map[state].items():
                    if key not in excluded_keys:
                        setattr(container, key, value)

                # ホバーが終了した時に、明示的にshadowをNoneに設定
                if (
                    not is_hovering
                    and "shadow" in style_map[ComponentState.HOVERED]
                    and "shadow" not in style_map[ComponentState.NORMAL]
                ):
                    container.shadow = None

                container.update()

        container.on_hover = on_hover

    # コンテナ作成系メソッド
    @staticmethod
    def container(
        content: ft.Control, state: ComponentState = ComponentState.NORMAL, **kwargs
    ) -> ft.Container:
        """基本的なコンテナを作成する"""
        container = ft.Container(content=content, **kwargs)

        # 明示的に指定されたプロパティは上書きしない
        style_dict = Styles._filter_style(Styles.BASE_STYLES[state], kwargs)
        Styles.apply_to(container, style_dict)

        return container

    @staticmethod
    def clickable_container(
        content: ft.Control, on_click=None, **kwargs
    ) -> ft.Container:
        """クリック可能なコンテナを作成する"""
        container = ft.Container(content=content, on_click=on_click, **kwargs)

        # 基本スタイルを適用（明示的に指定されていない場合のみ）
        style_dict = Styles._filter_style(
            Styles.BASE_STYLES[ComponentState.NORMAL], kwargs
        )
        Styles.apply_to(container, style_dict)

        # ホバー効果
        Styles._setup_hover_handler(container, Styles.BASE_STYLES)

        # プレス効果
        def on_tap_down(e):
            for key, value in Styles.BASE_STYLES[ComponentState.PRESSED].items():
                if key not in ["ink", "on_click"]:
                    setattr(container, key, value)

            container.update()

        container.on_tap_down = on_tap_down

        return container

    @staticmethod
    def styled_container(content: ft.Control, **kwargs) -> ft.Container:
        """カードスタイルのコンテナを作成する

        シャドウ付きで角丸の背景を持つコンテナを作成します。
        """
        container = ft.Container(content=content, **kwargs)

        # カードスタイルを適用（明示的に指定されていない場合のみ）
        style_dict = Styles._filter_style(
            Styles.CARD_STYLES[ComponentState.NORMAL], kwargs
        )
        Styles.apply_to(container, style_dict)

        return container

    @staticmethod
    def interactive_styled_container(
        content: ft.Control, on_click=None, **kwargs
    ) -> ft.Container:
        """インタラクティブなカードスタイルのコンテナを作成する

        ホバー効果を持つカードスタイルのコンテナを作成します。
        """
        container = ft.Container(content=content, on_click=on_click, **kwargs)

        # カードスタイルを適用（明示的に指定されていない場合のみ）
        style_dict = Styles._filter_style(
            Styles.CARD_STYLES[ComponentState.NORMAL], kwargs
        )
        Styles.apply_to(container, style_dict)

        # ホバー効果
        Styles._setup_hover_handler(container, Styles.CARD_STYLES)

        # プレス効果（最小限の実装）
        container.on_tap_down = lambda _: container.update()

        return container

    @staticmethod
    def interactive_card(content: ft.Control, on_click=None, **kwargs) -> ft.Container:
        """インタラクティブなカードを作成する（互換性のため）

        interactive_styled_containerの別名です。
        """
        return Styles.interactive_styled_container(content, on_click, **kwargs)

    @staticmethod
    def card(content: ft.Control, **kwargs) -> ft.Container:
        """カードスタイルのコンテナを作成する（互換性のため）

        styled_containerの別名です。
        """
        return Styles.styled_container(content, **kwargs)

    # テキスト作成系メソッド
    @staticmethod
    def text(value: str, style: str = "body", **kwargs) -> ft.Text:
        """スタイル指定付きのテキストを作成する"""
        style_dict = Styles.TEXT_STYLES.get(style, Styles.TEXT_STYLES["body"])

        # スタイル辞書をコピーしてから更新
        text_props = {**style_dict}

        # 明示的に指定されたプロパティで上書き
        text_props.update(kwargs)

        return ft.Text(value=value, **text_props)

    @staticmethod
    def title(value: str, **kwargs) -> ft.Text:
        """タイトルスタイルのテキストを作成する"""
        return Styles.text(value, style="title", **kwargs)

    @staticmethod
    def subtitle(value: str, **kwargs) -> ft.Text:
        """サブタイトルスタイルのテキストを作成する"""
        return Styles.text(value, style="subtitle", **kwargs)

    @staticmethod
    def caption(value: str, **kwargs) -> ft.Text:
        """キャプションスタイルのテキストを作成する"""
        return Styles.text(value, style="caption", **kwargs)

    @staticmethod
    def action_button(
        text: str, icon=None, on_click=None, **kwargs
    ) -> ft.ElevatedButton:
        """操作を促すアクションボタンを作成する"""
        button = ft.ElevatedButton(
            text=text,
            icon=icon,
            on_click=on_click,
            bgcolor=Colors.ACTION,
            color=Colors.TEXT_ON_ACTION,
            **kwargs,
        )
        return button

    @staticmethod
    def selected_container(content: ft.Control, **kwargs) -> ft.Container:
        """選択状態のコンテナを作成する"""
        container = ft.Container(
            content=content,
            bgcolor=Colors.SELECTED,
            **kwargs,
        )
        return container

    @staticmethod
    def action_icon_button(
        icon: str, tooltip: str = None, on_click=None, **kwargs
    ) -> ft.IconButton:
        """操作を促すアイコンボタンを作成する"""
        button = ft.IconButton(
            icon=icon,
            tooltip=tooltip,
            on_click=on_click,
            icon_color=Colors.ACTION,
            **kwargs,
        )
        return button

    # グリッド作成系メソッド
    @staticmethod
    def grid(
        controls: List[ft.Control],
        columns: int = 2,
        spacing: int = 10,
        run_spacing: int = 10,
        padding: int = 10,
        **kwargs,
    ) -> ft.GridView:
        """グリッドビューを作成する"""
        grid = ft.GridView(
            runs_count=columns,
            max_extent=200,
            spacing=spacing,
            run_spacing=run_spacing,
            padding=padding,
            **kwargs,
        )

        grid.controls.extend(controls)

        return grid

    @staticmethod
    def card_grid(
        items: List[Dict[str, Any]],
        title_field: str = "title",
        subtitle_field: Optional[str] = "subtitle",
        image_field: Optional[str] = "image",
        on_item_click: Optional[Callable] = None,
        **kwargs,
    ) -> ft.GridView:
        """カードのグリッドを作成する"""
        controls = []

        for item in items:
            # カードコンテンツの作成
            content_controls = []

            # 画像があれば追加
            if image_field and image_field in item and item[image_field]:
                content_controls.append(
                    ft.Image(
                        src=item[image_field],
                        width=float("inf"),
                        height=120,
                        fit=ft.ImageFit.COVER,
                    )
                )

            # タイトルとサブタイトルの追加
            card_content = []
            if title_field in item:
                card_content.append(Styles.title(item[title_field], size=16))

            if subtitle_field and subtitle_field in item:
                card_content.append(Styles.caption(item[subtitle_field], size=14))

            content_controls.append(
                ft.Container(
                    content=ft.Column(controls=card_content),
                    padding=10,
                )
            )

            # カードの作成
            card = Styles.interactive_styled_container(
                content=ft.Column(controls=content_controls),
                on_click=lambda e, item=item: (
                    on_item_click(e, item) if on_item_click else None
                ),
            )

            controls.append(card)

        # グリッドの作成
        return Styles.grid(controls=controls, **kwargs)
