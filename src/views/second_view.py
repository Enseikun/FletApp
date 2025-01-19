import flet as ft

from views.interfaces.view_interface import ViewInterface


class SecondView(ViewInterface):
    def __init__(self, presenter):
        self.presenter = presenter
        self.input_value = ft.TextField(label="Enter value")

    def build(self) -> ft.Control:
        return ft.Column(
            [
                ft.Text("Second View"),
                self.input_value,
                ft.ElevatedButton(
                    "Back to First View",
                    on_click=self._handle_back_click,
                ),
            ]
        )

    def _handle_back_click(self, _):
        # 入力値を共有データとして渡す
        shared_data = {"message": self.input_value.value}
        self.presenter.show_first_view(shared_data)
