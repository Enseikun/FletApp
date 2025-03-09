"""
アプリケーションの配色を規定するモジュール
MaterialUIのDarkBlue600をプライマリカラーとして使用
"""


class Colors:
    # プライマリカラー (MaterialUI DarkBlue600)
    PRIMARY = "#1E88E5"
    PRIMARY_LIGHT = "#6AB7FF"
    PRIMARY_DARK = "#005CB2"

    # テキストカラー
    TEXT_ON_PRIMARY = "#FFFFFF"
    TEXT_PRIMARY = "#212121"
    TEXT_SECONDARY = "#757575"
    TEXT_DISABLED = "#9E9E9E"

    # 背景色
    BACKGROUND = "#FFFFFF"
    BACKGROUND_LIGHT = "#F5F5F5"
    BACKGROUND_DARK = "#E0E0E0"

    # アクセントカラー
    ACCENT = "#FF4081"
    ACCENT_LIGHT = "#FF79B0"
    ACCENT_DARK = "#C60055"

    # 状態カラー
    SUCCESS = "#4CAF50"
    WARNING = "#FFC107"
    ERROR = "#F44336"
    INFO = "#2196F3"

    # ボーダーカラー
    BORDER = "#BDBDBD"
    DIVIDER = "#EEEEEE"


class ComponentColors:
    """コンポーネント状態に応じた色の設定"""

    # 通常状態
    NORMAL_BG = Colors.BACKGROUND
    NORMAL_TEXT = Colors.TEXT_PRIMARY
    NORMAL_BORDER = Colors.BORDER

    # ホバー状態
    HOVER_BG = Colors.BACKGROUND_LIGHT
    HOVER_TEXT = Colors.TEXT_PRIMARY
    HOVER_BORDER = Colors.PRIMARY_LIGHT

    # アクティブ状態
    ACTIVE_BG = Colors.PRIMARY_LIGHT
    ACTIVE_TEXT = Colors.TEXT_ON_PRIMARY
    ACTIVE_BORDER = Colors.PRIMARY

    # 無効状態
    DISABLED_BG = Colors.BACKGROUND_DARK
    DISABLED_TEXT = Colors.TEXT_DISABLED
    DISABLED_BORDER = Colors.BORDER

    # プライマリボタン
    PRIMARY_BUTTON_BG = Colors.PRIMARY
    PRIMARY_BUTTON_TEXT = Colors.TEXT_ON_PRIMARY
    PRIMARY_BUTTON_BORDER = Colors.PRIMARY_DARK

    # セカンダリボタン
    SECONDARY_BUTTON_BG = Colors.BACKGROUND
    SECONDARY_BUTTON_TEXT = Colors.PRIMARY
    SECONDARY_BUTTON_BORDER = Colors.PRIMARY
