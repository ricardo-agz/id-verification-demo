from pydantic import BaseModel
from enum import Enum
from utils.image_utils import encode_image
from utils.query_llm import query_llm_with_fallbacks


class DocumentType(Enum):
    AMERICAN_PASSPORT = "american_passport"
    FOREIGN_PASSPORT = "foreign_passport"
    AMERICAN_DRIVERS_LICENSE = "american_drivers_license"
    FOREIGN_DRIVERS_LICENSE = "foreign_drivers_license"
    OTHER_VALID_DOCUMENT = "other_valid_document"
    INDECIPHERABLE_DOCUMENT = "indecipherable"
    NOT_A_DOCUMENT = "not_a_document"


class DocumentClassificationResponse(BaseModel):
    image_analysis: str
    document_type: DocumentType


async def identify_document(image_path: str) -> DocumentClassificationResponse:
    base64_image = encode_image(image_path)

    response = await query_llm_with_fallbacks(
        models=[
            "accounts/fireworks/models/llama-v3p2-11b-vision-instruct",
            "accounts/fireworks/models/llama-v3p2-90b-vision-instruct",
        ],
        response_schema=DocumentClassificationResponse,
        temperature=0.0,
        max_tokens=1000,
        messages=[
            {
                "role": "system",
                "content": """You are a precise document scanner specialized in extracting information from a 
                valid identification document for . You must determine if the provided image depicts a valid 
                identification document and classify it accordingly.
                """,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                    {
                        "type": "text",
                        "text": "Classify the following image of a document.",
                    },
                ],
            },
        ],
    )

    return response


async def main():
    res = await identify_document("../../test_images/cat-test.png")
    print(res.document_type)
    print(res.image_analysis)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
