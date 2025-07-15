import time

import openai
from openai import OpenAI

from backend.configs import API_KEY
from backend.utils import get_logger

logger = get_logger(__name__)
client = OpenAI(
    api_key=API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)


def chat(
        system_prompt: str,
        user_prompt: str,
        model_name: str = "qwen-turbo",
        temperature: float = 0.5,
        max_tokens: int = 512,
        max_retries: int = 3,
        retry_delay: float = 1.0
) -> str:
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                extra_body={"enable_thinking": False},
                temperature=temperature,
                max_tokens=max_tokens
            )
            return completion.choices[0].message.content
            
        except openai.BadRequestError as e:
            error_code = getattr(e, 'code', 'unknown')
            error_message = str(e)
            
            if 'data_inspection_failed' in error_message:
                logger.warning(f"Content inspection failed on attempt {attempt + 1}: {error_message}")
            elif 'invalid_request_error' in error_message:
                logger.warning(f"Invalid request on attempt {attempt + 1}: {error_message}")
            else:
                logger.warning(f"Bad request error on attempt {attempt + 1}: {error_message}")
            
            last_error = e
            if 'data_inspection_failed' in error_message:
                logger.error(f"Content inspection failed, returning empty response: {error_message}")
                return ""
                
        except openai.RateLimitError as e:
            logger.warning(f"Rate limit exceeded on attempt {attempt + 1}: {str(e)}")
            last_error = e
            if attempt < max_retries:
                sleep_time = retry_delay * (2 ** attempt)
                logger.info(f"Waiting {sleep_time} seconds before retry...")
                time.sleep(sleep_time)
                
        except openai.APIConnectionError as e:
            logger.warning(f"API connection error on attempt {attempt + 1}: {str(e)}")
            last_error = e
            if attempt < max_retries:
                time.sleep(retry_delay)
                
        except openai.InternalServerError as e:
            logger.warning(f"Internal server error on attempt {attempt + 1}: {str(e)}")
            last_error = e
            if attempt < max_retries:
                time.sleep(retry_delay)
                
        except openai.AuthenticationError as e:
            logger.error(f"Authentication error: {str(e)}")
            return ""
            
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
            last_error = e
            if attempt < max_retries:
                time.sleep(retry_delay)
    
    logger.error(f"All attempts failed. Last error: {str(last_error)}")
    return ""


if __name__ == "__main__":
    print(chat("你是一个助手", "你好"))
