from __future__ import annotations

from abc import ABC, abstractmethod


class NotifierClient(ABC):
    @abstractmethod
    def send(self, message: str) -> None:
        raise NotImplementedError
