import flet as ft

from presenters.main_presenter import MainPresenter


async def main(page: ft.Page):
    page.title = "Test App"
    presenter = MainPresenter(page)
    presenter.initialize()


if __name__ == "__main__":
    ft.app(target=main)
