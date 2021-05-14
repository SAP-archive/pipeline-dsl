from typing import TypeVar, Generic, Optional, Dict, Any
from abc import abstractmethod
from dataclasses import dataclass


T = TypeVar("T")


@dataclass
class ConcourseResource:
    name: str
    type: str
    icon: str
    source: Dict[str, Any]


class AbstractResource(Generic[T]):
    @abstractmethod
    def resource_type(self) -> Optional[Dict]:
        pass

    @abstractmethod
    def concourse(self, name: str) -> ConcourseResource:
        pass

    @abstractmethod
    def get(self, name: str) -> T:
        pass
