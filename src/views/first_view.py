import flet as ft

from views.interfaces.view_interface import ViewInterface


class FirstView(ViewInterface):
    def initialize(self):
        self.route = "/"
        self.message_text = ft.Text("")
        self.controls = [
            ft.Column(
                [
                    ft.Text("First View"),
                    self.message_text,
                    ft.ElevatedButton(
                        "Go to Second View",
                        on_click=lambda _: self.page.go("/second"),
                    ),
                ]
            )
        ]

    def update_with_shared_data(self, data: dict):
        if "message" in data:
            self.message_text.value = f"Received: {data['message']}"
            # 表示されていなくても更新可能
            self.message_text.update()
