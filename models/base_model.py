from enum import Enum
from typing import Optional, TypeVar, Union, List
from mongoengine import (
    Document,
    DateTimeField,
    DoesNotExist,
    MultipleObjectsReturned,
    EmbeddedDocument,
    DynamicDocument,
)
from datetime import datetime
from bson.objectid import ObjectId


T = TypeVar("T", bound=Union[Document, DynamicDocument])


class BaseModel(Document):
    """
    Base class for MongoEngine Documents with built-in utility methods
    for common database operations.
    """

    meta = {"abstract": True}

    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    def save(self, *args, **kwargs) -> "BaseModel":
        """Override save to update the updated_at timestamp"""
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)

    def to_dict(self):
        """Convert the document to a dictionary with proper handling of MongoDB types"""

        def _handle_value(val):
            if isinstance(val, ObjectId):
                return str(val)
            elif isinstance(val, (dict, Document, EmbeddedDocument)):
                return _dictify(val)
            elif isinstance(val, list):
                return [_handle_value(v) for v in val]
            elif isinstance(val, Enum):
                return val.value
            else:
                return val

        def _dictify(d):
            return {k: _handle_value(v) for k, v in d.items()}

        return _dictify(self.to_mongo().to_dict())

    @classmethod
    def _execute_query(cls, operation, *args, **kwargs) -> Optional[T]:
        """Execute a database query safely, returning None on common exceptions"""
        try:
            return operation(*args, **kwargs)
        except (DoesNotExist, MultipleObjectsReturned):
            return None

    @classmethod
    def _check_objects_attribute(cls):
        """Ensure the class has the required 'objects' attribute"""
        if not hasattr(cls, "objects"):
            raise AttributeError(f"{cls.__name__} must have an 'objects' attribute.")

    @classmethod
    def find_by_id(cls, id: str | ObjectId) -> Optional[T]:
        """Find a document by its ID"""
        cls._check_objects_attribute()
        if isinstance(id, ObjectId) or ObjectId.is_valid(id):
            return cls._execute_query(cls.objects(id=id).first)
        return None

    @classmethod
    def find_one(cls, **kwargs) -> Optional[T]:
        """Find a single document matching the given criteria"""
        cls._check_objects_attribute()
        return cls._execute_query(cls.objects(**kwargs).first)

    @classmethod
    def find(cls, page: int = None, per_page: int = None, **kwargs) -> List[T]:
        """
        Find documents matching the given criteria with optional pagination
        """
        cls._check_objects_attribute()
        if page is not None and per_page is not None:
            start = (page - 1) * per_page
            return cls._execute_query(cls.objects(**kwargs).skip(start).limit(per_page))
        return cls._execute_query(cls.objects(**kwargs))

    @classmethod
    def find_by_id_and_update(cls, id: str, **kwargs) -> Optional[T]:
        """Find a document by ID and update it with the given values"""
        cls._check_objects_attribute()
        if isinstance(id, ObjectId) or ObjectId.is_valid(id):
            cls._execute_query(cls.objects(id=id).update, **kwargs)
            return cls.find_by_id(str(id))
        return None

    @classmethod
    def find_by_id_and_delete(cls, id: str) -> Optional[T]:
        """Find a document by ID and delete it"""
        cls._check_objects_attribute()
        if isinstance(id, ObjectId) or ObjectId.is_valid(id):
            doc = cls._execute_query(cls.objects(id=id).first)
            if doc:
                doc.delete()
            return doc
        return None

    @classmethod
    def count(cls, **kwargs) -> int:
        """Count documents matching the given criteria"""
        cls._check_objects_attribute()
        return cls.objects(**kwargs).count()
