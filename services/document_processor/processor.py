import asyncio
from pydantic import BaseModel
from typing import Union

from services.document_processor.document_classification import (
    DocumentClassificationResponse,
    identify_document,
    DocumentType,
)
from services.document_processor.passport_extraction import (
    PassportDataResponse,
    extract_passport_data,
    PassportData,
)
from services.document_processor.license_extraction import (
    LicenseDataResponse,
    extract_license_data,
    LicenseData,
)


class Metadata(BaseModel):
    classification: DocumentClassificationResponse
    extracted_data: Union[PassportDataResponse, LicenseDataResponse, None] = None


class DocumentProcessingResponse(BaseModel):
    document_type: DocumentType
    extracted_data: Union[PassportData, LicenseData, None] = None
    metadata: Metadata = None


class UnsupportedDocumentTypeError(Exception):
    pass


class DocumentNotRecognizedError(Exception):
    pass


async def process_document(image_path: str) -> DocumentProcessingResponse:
    """
    Process an ID document image by first identifying the document type and then extracting
    relevant information based on the document type.

    Args:
        image_path (str): Path to the image file

    Returns:
        DocumentProcessingResponse: Contains both the classification and extracted data
    """
    try:
        classification = await identify_document(image_path)
        response = DocumentProcessingResponse(
            document_type=classification.document_type
        )

        if classification.document_type not in [
            DocumentType.INDECIPHERABLE_DOCUMENT,
            DocumentType.NOT_A_DOCUMENT,
        ]:
            if classification.document_type == DocumentType.AMERICAN_PASSPORT:
                extracted_data_response = await extract_passport_data(image_path)
                response.extracted_data = extracted_data_response.passport_data
            elif classification.document_type == DocumentType.AMERICAN_DRIVERS_LICENSE:
                extracted_data_response = await extract_license_data(image_path)
                response.extracted_data = extracted_data_response.license_data
            else:
                print(classification.document_type)
                print(classification.image_analysis)
                raise UnsupportedDocumentTypeError("Document type not supported")
        else:
            print(classification.image_analysis)
            raise DocumentNotRecognizedError("Document not recognized")

        response.metadata = Metadata(
            classification=classification, extracted_data=extracted_data_response
        )

        return response

    except Exception as e:
        raise ValueError(f"Failed to process document: {str(e)}")


async def main():
    image_path = "../../test_images/cat-test.png"
    result = await process_document(image_path)
    print(f"Document Type: {result.document_type}")
    if result.extracted_data:
        print(f"Extracted Data: {result.extracted_data}")
    if result.metadata:
        print(f"Classification: {result.metadata.classification}")


if __name__ == "__main__":
    asyncio.run(main())
