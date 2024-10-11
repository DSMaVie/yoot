from typing import Protocol


class Tracker(Protocol):
    def log(self, message: str): ...
