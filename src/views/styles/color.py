"""
アプリケーションの配色を規定するモジュール
プライマリカラーにBLUEGRAY、セカンダリカラーにDEEPORANGEを使用
"""


class Colors:
    # プライマリカラー (BLUEGRAY)
    PRIMARY = "#607D8B"  # BlueGray 500
    PRIMARY_LIGHT = "#90A4AE"  # BlueGray 300
    PRIMARY_DARK = "#455A64"  # BlueGray 700

    # セカンダリカラー (DEEPORANGE)
    SECONDARY = "#FF5722"  # DeepOrange 500
    SECONDARY_LIGHT = "#FF8A65"  # DeepOrange 300
    SECONDARY_DARK = "#E64A19"  # DeepOrange 700

    # アクションカラー (明るいブルー)
    ACTION = "#2196F3"  # Blue 500
    ACTION_LIGHT = "#64B5F6"  # Blue 300
    ACTION_DARK = "#1976D2"  # Blue 700

    # テキストカラー
    TEXT_ON_PRIMARY = "#FFFFFF"
    TEXT_ON_SECONDARY = "#FFFFFF"
    TEXT_ON_ACTION = "#FFFFFF"
    TEXT_PRIMARY = "#263238"  # BlueGray 900
    TEXT_SECONDARY = "#546E7A"  # BlueGray 600
    TEXT_DISABLED = "#B0BEC5"  # BlueGray 200

    # 背景色
    BACKGROUND = "#FFFFFF"
    BACKGROUND_LIGHT = "#ECEFF1"  # BlueGray 50
    BACKGROUND_DARK = "#CFD8DC"  # BlueGray 100

    # セレクト背景色
    SELECTED = "#CFD8DC"  # BlueGray 100
    SELECTED_LIGHT = "#ECEFF1"  # BlueGray 50
    SELECTED_DARK = "#CFD8DC"  # BlueGray 200

    # アクセントカラー (DEEPORANGE)
    ACCENT = "#FF5722"  # DeepOrange 500
    ACCENT_LIGHT = "#FF8A65"  # DeepOrange 300
    ACCENT_DARK = "#E64A19"  # DeepOrange 700

    # 状態カラー
    SUCCESS = "#4CAF50"  # Green 500
    WARNING = "#FFC107"  # Amber 500
    ERROR = "#F44336"  # Red 500
    INFO = "#2196F3"  # Blue 500

    # ボーダーカラー
    BORDER = "#B0BEC5"  # BlueGray 200
    DIVIDER = "#ECEFF1"  # BlueGray 50

    # 強調色
    HIGHLIGHT = "#FFD180"  # Orange A100


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

    # セレクト状態
    SELECTED_BG = Colors.SELECTED
    SELECTED_TEXT = Colors.TEXT_PRIMARY
    SELECTED_BORDER = Colors.PRIMARY

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
    PRIMARY_BUTTON_BORDER = Colors.PRIMARY_LIGHT

    # セカンダリボタン
    SECONDARY_BUTTON_BG = Colors.SECONDARY
    SECONDARY_BUTTON_TEXT = Colors.TEXT_ON_SECONDARY
    SECONDARY_BUTTON_BORDER = Colors.SECONDARY_DARK

    # アクションボタン（Toggle、Add等の操作ボタン）
    ACTION_BUTTON_BG = Colors.ACTION
    ACTION_BUTTON_TEXT = Colors.TEXT_ON_ACTION
    ACTION_BUTTON_BORDER = Colors.ACTION_DARK

    # アクションアイコン（操作を促すアイコン）
    ACTION_ICON = Colors.ACTION
    ACTION_ICON_HOVER = Colors.ACTION_LIGHT
    ACTION_ICON_PRESSED = Colors.ACTION_DARK

    # アクセントボタン
    ACCENT_BUTTON_BG = Colors.ACCENT
    ACCENT_BUTTON_TEXT = Colors.TEXT_ON_SECONDARY
    ACCENT_BUTTON_BORDER = Colors.ACCENT_DARK
