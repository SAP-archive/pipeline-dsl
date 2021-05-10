from abc import ABC, abstractmethod


class AbstractResource(ABC):
    @abstractmethod
    def resource_type(self) -> dict:
        pass

    @abstractmethod
    def concourse(self, name: str) -> dict:
        pass

    @abstractmethod
    def get(self, name: str):
        pass
