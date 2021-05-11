from typing import TypeVar, Generic, Optional, Dict, Collection
from abc import abstractmethod


T = TypeVar('T')


class AbstractResource(Generic[T]):
    @abstractmethod
    def resource_type(self) -> Optional[Dict]:
        pass

    @abstractmethod
    def concourse(self, name: str) -> Dict[str, Collection[str]]:
        pass

    @abstractmethod
    def get(self, name: str) -> T:
        pass
