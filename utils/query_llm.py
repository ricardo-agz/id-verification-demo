from typing import TypeVar, List, Any, Optional, Type, Dict
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel

from utils.image_utils import encode_image

load_dotenv()


client = AsyncOpenAI(
    base_url="https://api.fireworks.ai/inference/v1",
    api_key=os.getenv("FIREWORKS_API_KEY"),
)


T = TypeVar("T", bound=BaseModel)


class ModelFallbackError(Exception):
    """Custom exception for when all models fail"""

    def __init__(self, last_error: Optional[Exception] = None):
        self.last_error = last_error
        super().__init__(f"All models failed. Last error: {str(last_error)}")


async def query_llm_with_fallbacks(
    models: List[str],
    response_schema: Type[T],
    messages: List[Dict[str, Any]],
    **kwargs,
) -> T:
    last_exception = None

    for model in models:
        try:
            completion = await client.beta.chat.completions.parse(
                model=model,
                response_format={
                    "type": "json_object",
                    "schema": response_schema.model_json_schema(),
                },
                messages=messages,
                **kwargs,
            )

            json_content = completion.choices[0].message.content
            return response_schema.model_validate_json(json_content)

        except Exception as e:
            last_exception = e
            print(
                f"Model {model} failed with error: {str(e)}. Attempting next model..."
            )
            continue

    raise ModelFallbackError(last_exception)


async def main():
    image = "../test_images/cat-test.png"
    base64_image = encode_image(image)
    models = [
        "accounts/fireworks/models/llama-v3p1-8b-instruct",
        "accounts/fireworks/models/llama-v3p2-11b-vision-instruct",
    ]
    message = [
        {
            "role": "system",
            "content": "You are a helpful assistant",
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Classify the following image of a document.",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                },
            ],
        },
    ]

    class TestResponse(BaseModel):
        response: str

    response = await query_llm_with_fallbacks(
        models=models,
        response_schema=TestResponse,
        messages=message,
        temperature=0.0,
        max_tokens=1000,
    )

    print(response.response)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
