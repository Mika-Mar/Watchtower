from abc import ABC, abstractmethod

from app.models import Item


class Collector(ABC):

    @abstractmethod
    def fetch(self) -> list[Item]:
        pass