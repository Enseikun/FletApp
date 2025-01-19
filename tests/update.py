import asyncio

import flet as ft

from datastore import DataStore


async def update_value(page: ft.Page):
    store = DataStore()
    cnt = 0
    max_value = 100

    while cnt <= max_value:
        store.set_value([cnt, max_value])
        cnt += 1
        await asyncio.sleep(1)
