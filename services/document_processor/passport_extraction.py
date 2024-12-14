from pydantic import BaseModel
from enum import Enum
from utils.image_utils import encode_image
from utils.query_llm import query_llm_with_fallbacks


class Confidence(Enum):
    HIGH = "high"
    UNSURE = "unsure"


class FieldExtraction(BaseModel):
    visible: bool
    value: str
    confidence: Confidence


class PassportData(BaseModel):
    issuing_country: FieldExtraction
    passport_number: FieldExtraction
    surname: FieldExtraction
    given_names: FieldExtraction
    nationality: FieldExtraction
    birth_date: FieldExtraction
    sex: FieldExtraction
    place_of_birth: FieldExtraction
    date_of_issue: FieldExtraction
    date_of_expiry: FieldExtraction
    authority: FieldExtraction


class PassportDataResponse(BaseModel):
    image_analysis: str
    passport_data: PassportData


async def extract_passport_data(image_path: str) -> PassportDataResponse:
    base64_image = encode_image(image_path)

    response = await query_llm_with_fallbacks(
        models=[
            "accounts/fireworks/models/llama-v3p2-90b-vision-instruct",
            "accounts/fireworks/models/llama-v3p2-11b-vision-instruct",
        ],
        response_schema=PassportDataResponse,
        temperature=0.0,
        max_tokens=1000,
        messages=[
            {
                "role": "system",
                "content": """You are a precise document scanner specialized in extracting information from passports. 
                            For each field, you must:
                            1. Determine if the field is visible or not.
                            2. Extract the value of the field.
                            3. Provide a confidence level in the extraction. If a field is not visible, the confidence level
                            should be 'unsure'.

                            Mark a field as 'unsure' if:
                            - Any part of the text is unclear or ambiguous
                            - There are multiple possible interpretations
                            - The field is partially obscured or damaged
                            - The text is too blurry to read with certainty
                            - There is glare or other visual interference that makes the text unclear

                            Special considerations:
                            - All dates should be in DD/MM/YYYY format (international standard for passports)
                            - Passport numbers may contain both letters and numbers
                            - Names should be extracted exactly as shown, including special characters and diacritical marks
                            - For the sex field, use 'M', 'F', or 'X' only
                            
                            Carefully examine the image and analyze all relevant fields and provide a short 1 sentence
                            analysis of the image before extracting the data. 
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
                        "text": "Extract the passport information and mark your confidence for each field.",
                    },
                ],
            },
        ],
    )

    return response


async def main():
    data = await extract_passport_data("../../test_images/test-passport.png")
    print(type(data))
    print(data)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
