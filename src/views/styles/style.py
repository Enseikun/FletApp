"""
アプリケーション全体のスタイル定義
コンポーネントのスタイルを集約して一貫性を保つ
"""

from enum import Enum
from typing import Dict, Optional

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


class ComponentStyle:
    """コンポーネントのスタイル情報を保持するクラス"""

    def __init__(self):
        # 背景色
        self.bgcolor: Optional[str] = None
        # テキスト色
        self.text_color: Optional[str] = None
        # ボーダー色
        self.border_color: Optional[str] = None
        # ボーダー幅
        self.border_width: Optional[float] = None
        # ボーダー半径
        self.border_radius: Optional[float] = None
        # パディング
        self.padding: Optional[int] = None
        # マージン
        self.margin: Optional[int] = None
        # 透明度
        self.opacity: Optional[float] = 1.0
        # 影の深さ
        self.shadow: Optional[int] = None

    def to_dict(self) -> dict:
        """スタイル情報を辞書形式で返す"""
        result = {}

        if self.bgcolor is not None:
            result["bgcolor"] = self.bgcolor

        if self.border_color is not None and self.border_width is not None:
            result["border"] = ft.border.all(self.border_width, self.border_color)

        if self.border_radius is not None:
            result["border_radius"] = self.border_radius

        if self.padding is not None:
            result["padding"] = self.padding

        if self.margin is not None:
            result["margin"] = self.margin

        if self.opacity is not None:
            result["opacity"] = self.opacity

        if self.shadow is not None:
            result["shadow"] = ft.BoxShadow(
                spread_radius=1,
                blur_radius=self.shadow * 2,
                color=ft.colors.with_opacity(0.3, ft.colors.BLACK),
            )

        return result


class StyleManager:
    """
    コンポーネントのスタイルを管理するクラス
    各コンポーネントタイプに対するデフォルトスタイルを提供
    """

    @staticmethod
    def get_default_styles() -> Dict[ComponentState, ComponentStyle]:
        """基本的なコンポーネントスタイルを取得"""
        styles = {state: ComponentStyle() for state in ComponentState}

        # 通常状態のスタイル
        styles[ComponentState.NORMAL].bgcolor = Colors.BACKGROUND
        styles[ComponentState.NORMAL].text_color = Colors.TEXT_PRIMARY
        styles[ComponentState.NORMAL].border_color = Colors.BORDER
        styles[ComponentState.NORMAL].border_width = 1
        styles[ComponentState.NORMAL].border_radius = 4
        styles[ComponentState.NORMAL].padding = 8

        # ホバー状態のスタイル
        styles[ComponentState.HOVERED].bgcolor = Colors.BACKGROUND_LIGHT
        styles[ComponentState.HOVERED].text_color = Colors.TEXT_PRIMARY
        styles[ComponentState.HOVERED].border_color = Colors.PRIMARY_LIGHT
        styles[ComponentState.HOVERED].border_width = 1
        styles[ComponentState.HOVERED].border_radius = 4
        styles[ComponentState.HOVERED].padding = 8
        styles[ComponentState.HOVERED].shadow = 1

        # フォーカス状態のスタイル
        styles[ComponentState.FOCUSED].bgcolor = Colors.BACKGROUND
        styles[ComponentState.FOCUSED].text_color = Colors.PRIMARY
        styles[ComponentState.FOCUSED].border_color = Colors.PRIMARY
        styles[ComponentState.FOCUSED].border_width = 2
        styles[ComponentState.FOCUSED].border_radius = 4
        styles[ComponentState.FOCUSED].padding = 8

        # プレス状態のスタイル
        styles[ComponentState.PRESSED].bgcolor = Colors.PRIMARY_LIGHT
        styles[ComponentState.PRESSED].text_color = Colors.TEXT_ON_PRIMARY
        styles[ComponentState.PRESSED].border_color = Colors.PRIMARY_DARK
        styles[ComponentState.PRESSED].border_width = 1
        styles[ComponentState.PRESSED].border_radius = 4
        styles[ComponentState.PRESSED].padding = 8

        # 無効状態のスタイル
        styles[ComponentState.DISABLED].bgcolor = Colors.BACKGROUND_DARK
        styles[ComponentState.DISABLED].text_color = Colors.TEXT_DISABLED
        styles[ComponentState.DISABLED].border_color = Colors.BORDER
        styles[ComponentState.DISABLED].border_width = 1
        styles[ComponentState.DISABLED].border_radius = 4
        styles[ComponentState.DISABLED].padding = 8
        styles[ComponentState.DISABLED].opacity = 0.5

        # エラー状態のスタイル
        styles[ComponentState.ERROR].bgcolor = Colors.BACKGROUND
        styles[ComponentState.ERROR].text_color = Colors.ERROR
        styles[ComponentState.ERROR].border_color = Colors.ERROR
        styles[ComponentState.ERROR].border_width = 1
        styles[ComponentState.ERROR].border_radius = 4
        styles[ComponentState.ERROR].padding = 8

        # アクティブ状態のスタイル
        styles[ComponentState.ACTIVE].bgcolor = Colors.PRIMARY_LIGHT
        styles[ComponentState.ACTIVE].text_color = Colors.TEXT_ON_PRIMARY
        styles[ComponentState.ACTIVE].border_color = Colors.PRIMARY
        styles[ComponentState.ACTIVE].border_width = 1
        styles[ComponentState.ACTIVE].border_radius = 4
        styles[ComponentState.ACTIVE].padding = 8

        return styles

    @staticmethod
    def get_button_styles() -> Dict[ComponentState, ComponentStyle]:
        """ボタン用のスタイルを取得"""
        styles = StyleManager.get_default_styles()

        # ボタン特有のスタイル調整
        styles[ComponentState.NORMAL].bgcolor = Colors.PRIMARY
        styles[ComponentState.NORMAL].text_color = Colors.TEXT_ON_PRIMARY
        styles[ComponentState.NORMAL].shadow = 1

        styles[ComponentState.HOVERED].bgcolor = Colors.PRIMARY_LIGHT
        styles[ComponentState.HOVERED].shadow = 2

        styles[ComponentState.PRESSED].bgcolor = Colors.PRIMARY_DARK
        styles[ComponentState.PRESSED].shadow = 0

        return styles

    @staticmethod
    def get_card_styles() -> Dict[ComponentState, ComponentStyle]:
        """カード用のスタイルを取得"""
        styles = StyleManager.get_default_styles()

        # カード特有のスタイル調整
        for state in ComponentState:
            styles[state].padding = 16
            styles[state].border_radius = 8
            styles[state].shadow = 2

        styles[ComponentState.HOVERED].shadow = 4

        return styles

    @staticmethod
    def get_text_field_styles() -> Dict[ComponentState, ComponentStyle]:
        """テキストフィールド用のスタイルを取得"""
        styles = StyleManager.get_default_styles()

        # テキストフィールド特有のスタイル調整
        styles[ComponentState.FOCUSED].border_color = Colors.PRIMARY
        styles[ComponentState.FOCUSED].border_width = 2

        styles[ComponentState.ERROR].border_color = Colors.ERROR
        styles[ComponentState.ERROR].border_width = 2

        return styles

    @staticmethod
    def get_label_styles() -> Dict[ComponentState, ComponentStyle]:
        """ラベル用のスタイルを取得"""
        styles = StyleManager.get_default_styles()

        # ラベル特有のスタイル調整
        for state in ComponentState:
            styles[state].border_width = None
            styles[state].border_color = None
            styles[state].padding = 4
            styles[state].margin = 2

        return styles


# 共通のテーマ設定
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
