from abc import ABC, abstractmethod


class PresenterInterface(ABC):
    @abstractmethod
    def initialize(self) -> None:
        pass

    @abstractmethod
    def handle_user_input(self, data: any) -> None:
        pass
