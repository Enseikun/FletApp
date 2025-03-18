# ハイライトされたMail本文の取得

import re
from typing import Any, Dict, List

import flet as ft

from src.views.styles.style import AppTheme


class StyledText:
    def __init__(self):
        self.theme = AppTheme()
        self.default_match_style = ft.TextStyle(
            color=ft.Color.white,
            bgcolor=ft.Colors.DEEP_ORANGE,
            weight=ft.FontWeight.BOLD,
            size=self.theme.BODY_SIZE,
        )

        self.default_no_match_style = ft.TextStyle(
            color=self.theme.TEXT_COLOR,
            bgcolor=self.theme.BACKGROUND,
            weight=ft.FontWeight.NORMAL,
            size=self.theme.BODY_SIZE,
        )

    def _style_specific_words(
        self, text: str, target_words: List, match_style: Dict, non_match_style: Dict
    ) -> List[ft.TextSpan]:
        """
        特定の単語にスタイルを適用する
        """
        spans = []
        pattern = re.compile("|".join(map(re.escape, target_words)), re.IGNORECASE)
        last_end = 0

        for match in pattern.finditer(text):
            # マッチした部分の前のテキストを追加
            if match.start() > last_end:
                spans.append(
                    ft.TextSpan(
                        text=text[last_end : match.start()],
                        style=non_match_style,
                    )
                )

            # マッチした部分を追加
            spans.append(
                ft.TextSpan(
                    text=match.group(),
                    style=match_style,
                )
            )

            last_end = match.end()

        # 残りのテキストを追加
        if last_end < len(text):
            spans.append(
                ft.TextSpan(
                    text=text[last_end:],
                    style=non_match_style,
                )
            )

        return spans

    def generate_styled_text(
        self,
        text: str,
        target_words: list[str],
        match_style: Dict[str, Any],
        non_match_style: Dict[str, Any],
    ) -> ft.Text:
        """
        ハイライトされたテキストを生成する
        """
        if match_style is None:
            match_style = self.default_match_style
        elif isinstance(match_style, dict):
            match_style = ft.TextStyle(**match_style)

        if non_match_style is None:
            non_match_style = self.default_no_match_style
        elif isinstance(non_match_style, dict):
            non_match_style = ft.TextStyle(**non_match_style)

        return ft.Text(
            spans=self._style_specific_words(
                text, target_words, match_style, non_match_style
            ),
            selectable=True,
        )
