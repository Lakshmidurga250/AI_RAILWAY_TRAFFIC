"""Base Generic Repository providing standard CRUD and querying capabilities."""
from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from backend.app.database import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """Generic repository providing decoupled database operations."""

    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get(self, id_val: Any) -> Optional[ModelType]:
        """Fetch entity by primary key."""
        return self.db.query(self.model).filter(self.model.id == id_val).first()

    def get_by(self, **kwargs) -> Optional[ModelType]:
        """Fetch first entity matching attribute kwargs."""
        query = self.db.query(self.model)
        for key, val in kwargs.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == val)
        return query.first()

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        descending: bool = False
    ) -> List[ModelType]:
        """Retrieve a paginated and filtered list of entities."""
        query = self.db.query(self.model)
        
        if filters:
            for key, val in filters.items():
                if hasattr(self.model, key) and val is not None:
                    query = query.filter(getattr(self.model, key) == val)

        if sort_by and hasattr(self.model, sort_by):
            col = getattr(self.model, sort_by)
            query = query.order_by(desc(col) if descending else asc(col))
        elif hasattr(self.model, "id"):
            query = query.order_by(self.model.id.asc())

        return query.offset(skip).limit(limit).all()

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities matching optional filters."""
        query = self.db.query(self.model)
        if filters:
            for key, val in filters.items():
                if hasattr(self.model, key) and val is not None:
                    query = query.filter(getattr(self.model, key) == val)
        return query.count()

    def create(self, entity: ModelType) -> ModelType:
        """Persist a new entity instance."""
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, db_obj: ModelType, updates: Dict[str, Any]) -> ModelType:
        """Update existing entity attributes."""
        for key, value in updates.items():
            if hasattr(db_obj, key):
                setattr(db_obj, key, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id_val: Any) -> bool:
        """Delete entity by ID."""
        obj = self.get(id_val)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False
