import os
import shutil
import tempfile
from enum import Enum

from fastapi import APIRouter, HTTPException, UploadFile, File

from services.document_processor.document_classification import DocumentType
from services.document_processor.processor import (
    UnsupportedDocumentTypeError,
    DocumentNotRecognizedError,
    process_document,
    DocumentProcessingResponse,
)
from services.s3_service import S3Service
from models.extracted_document_data import ExtractedDocumentData
from config.settings import settings


router = APIRouter()
s3_service = S3Service(
    bucket_name=settings.document_images_s3_bucket_name,
    aws_region=settings.s3_region
)


@router.post("/process")
async def process_document_route(
    file: UploadFile = File(...),
):
    """
    Process the image of an uploaded document and extract relevant data.

    :param file: The image file of the document to process
    :return: Extracted document data
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    file_extension = os.path.splitext(file.filename)[1] if file.filename else '.jpg'
    temp_file_path = None

    try:
        with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
            temp_file_path = temp_file.name
            await file.seek(0)
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()
            os.fsync(temp_file.fileno())

        result = await process_document(temp_file_path)

        if result.document_type not in [
            DocumentType.INDECIPHERABLE_DOCUMENT,
            DocumentType.NOT_A_DOCUMENT,
        ]:
            if not os.path.exists(temp_file_path) or os.path.getsize(temp_file_path) == 0:
                raise HTTPException(
                    status_code=500,
                    detail="Error processing document: Temporary file is missing or empty"
                )

            s3_url = s3_service.upload_document(
                temp_file_path,
                result.document_type.value
            )

            if not s3_url:
                raise HTTPException(
                    status_code=500,
                    detail="Error processing document: Failed to upload to S3"
                )

            extracted_data = result.extracted_data.dict() if result.extracted_data else {}
            metadata = result.metadata.dict() if result.metadata else {}
            serialized_extracted_data = {
                field: {
                    k: v.value if isinstance(v, Enum) else v
                    for k, v in field_data.items()
                }
                for field, field_data in extracted_data.items()
            }
            confidence_values = [
                field.get("confidence")
                for field in serialized_extracted_data.values()
                if isinstance(field, dict) and "confidence" in field
            ]
            needs_manual_review = any(
                confidence == "unsure" for confidence in confidence_values
            )

            document_data = ExtractedDocumentData(
                document_type=result.document_type.value,
                extracted_data=serialized_extracted_data,
                document_image_s3_url=s3_url,
                needs_manual_review=needs_manual_review,
            )
            document_data.save()

            return {
                "document_type": result.document_type.value,
                "extracted_data": serialized_extracted_data,
                "needs_manual_review": needs_manual_review,
                "document_image_s3_url": s3_url,
                "document_id": str(document_data.id),
            }

        return result

    except UnsupportedDocumentTypeError:
        raise HTTPException(status_code=422, detail="Unsupported document type")
    except DocumentNotRecognizedError:
        raise HTTPException(status_code=422, detail="Document not recognized")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                print(f"Error cleaning up temp file: {str(e)}")
                pass  # Ignore cleanup errors


@router.get("/documents")
async def get_documents():
    """
    Get all extracted document data.

    :return: List of extracted document data
    """
    documents = ExtractedDocumentData.find()
    return {
        "data": [doc.to_dict() for doc in documents],
        "message": "Documents retrieved successfully",
    }


@router.get("/documents/{document_id}")
async def get_document(document_id: str):
    """
    Get extracted document data by ID.

    :param document_id: The ID of the document to retrieve
    :return: Extracted document data
    """
    document = ExtractedDocumentData.find_by_id(document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "data": document.to_dict(),
        "message": "Document retrieved successfully",
    }


@router.get("/documents-to-review")
async def get_documents_to_review():
    """
    Get all extracted document data that need manual review.

    :return: List of extracted document data
    """
    documents = ExtractedDocumentData.find(needs_manual_review=True)
    documents_with_urls = []

    for doc in documents:
        doc_dict = doc.to_dict()
        if doc_dict.get('document_image_s3_url'):
            presigned_url = s3_service.generate_presigned_url(doc_dict['document_image_s3_url'])
            doc_dict['viewable_url'] = presigned_url
        documents_with_urls.append(doc_dict)

    return {
        "data": documents_with_urls,
        "message": "Documents retrieved successfully",
    }
