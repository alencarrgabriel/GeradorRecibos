from abc import ABC, abstractmethod
from typing import List, Optional


class GavetaRepository(ABC):
    @abstractmethod
    def get_all(self) -> List[dict]:
        ...

    @abstractmethod
    def get_by_id(self, gaveta_id: int) -> Optional[dict]:
        ...
