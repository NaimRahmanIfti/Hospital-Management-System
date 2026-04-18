from abc import ABC, abstractmethod
from sqlalchemy.orm import Session


class BaseService(ABC):
    """
    Abstract base class for all services.
    Provides common functionality and enforces encapsulation.
    """
    def __init__(self, db: Session):
        self._db = db  # Encapsulated database session

    @abstractmethod
    def get_by_id(self, id: int):
        """Abstract method to get entity by ID."""
        pass

    def commit(self):
        """Common method to commit changes."""
        self._db.commit()

    def refresh(self, obj):
        """Common method to refresh an object."""
        self._db.refresh(obj)