import logging
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

class DeepSeekService:

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            timeout=30.0,  # fail fast instead of hanging if DeepSeek is unreachable
            max_retries=1,
        )

    def generate_answer(self, system_prompt: str, user_prompt: str):
        logger.info("Sending request to DeepSeek.")

        response = self.client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # Lower for more factual answers
            max_tokens=1000,
            stream=False
        )

        logger.info("DeepSeek responded successfully.")
        return response.choices[0].message.content