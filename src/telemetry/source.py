from abc import ABC, abstractmethod
from typing import AsyncIterator

from src.telemetry.fix import Fix


class LocationSource(ABC):
    @abstractmethod
    def __aiter__(self) -> AsyncIterator[Fix]:
        raise NotImplementedError
