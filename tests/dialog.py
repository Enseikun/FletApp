import asyncio

import flet as ft

from datastore import DataStore


async def show_progress(page: ft.Page):
    progress_bar = ft.ProgressBar(color="blue", bgcolor="grey")

    dialog = ft.AlertDialog(
        title=ft.Text("進捗状況"),
        content=ft.Column([ft.Text("", size=16), progress_bar]),  # ラベル表示用
        content_padding=20,
    )

    page.overlay.append(dialog)
    dialog.open = True
    page.update()

    while True:
        store = DataStore()
        value = store.get_value()
        progress_bar.value = value[0] / value[1]
        # Textコンポーネントを使用してラベルを表示
        dialog.content.controls[0].value = f"進捗: {value[0]}/{value[1]}"
        page.update()
        await asyncio.sleep(1)
