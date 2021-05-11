from abc import abstractmethod
from typing import TypeVar, Generic


T = TypeVar('T')

class AbstractResource(Generic[T]):
    @abstractmethod
    def resource_type(self) -> dict:
        pass

    @abstractmethod
    def concourse(self, name: str) -> dict:
        pass

    @abstractmethod
    def get(self, name: str) -> T:
        pass
