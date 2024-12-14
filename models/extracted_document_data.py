import enum
from datetime import datetime, timedelta
from mongoengine import *

from models.base_model import BaseModel


class ExtractedDocumentData(BaseModel):
    document_type = StringField(required=True)
    extracted_data = DictField(required=True)
    document_image_s3_url = StringField()
    needs_manual_review = BooleanField(default=False)
    manual_review_completed = BooleanField(default=False)
    metadata = DictField()

    def to_dict(self):
        return {
            "id": str(self.id),
            "document_type": self.document_type,
            "extracted_data": self.extracted_data,
            "document_image_s3_url": self.document_image_s3_url,
            "needs_manual_review": self.needs_manual_review,
            "manual_review_completed": self.manual_review_completed,
            "metadata": self.metadata,
        }
