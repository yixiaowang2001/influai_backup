import time
from typing import Optional

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
    """
    与AI模型进行对话
    
    Args:
        system_prompt: 系统提示词
        user_prompt: 用户提示词
        model_name: 模型名称
        temperature: 温度参数
        max_tokens: 最大token数
        max_retries: 最大重试次数
        retry_delay: 重试延迟时间
        
    Returns:
        str: AI回复内容
    """
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
                logger.warning(f"第{attempt + 1}次尝试内容检查失败: {error_message}")
            elif 'invalid_request_error' in error_message:
                logger.warning(f"第{attempt + 1}次尝试请求无效: {error_message}")
            else:
                logger.warning(f"第{attempt + 1}次尝试请求错误: {error_message}")
            
            last_error = e
            if 'data_inspection_failed' in error_message:
                logger.error(f"内容检查失败，返回空响应: {error_message}")
                return ""
                
        except openai.RateLimitError as e:
            logger.warning(f"第{attempt + 1}次尝试超出速率限制: {str(e)}")
            last_error = e
            if attempt < max_retries:
                sleep_time = retry_delay * (2 ** attempt)
                logger.info(f"等待{sleep_time}秒后重试...")
                time.sleep(sleep_time)
                
        except openai.APIConnectionError as e:
            logger.warning(f"第{attempt + 1}次尝试API连接错误: {str(e)}")
            last_error = e
            if attempt < max_retries:
                time.sleep(retry_delay)
                
        except openai.InternalServerError as e:
            logger.warning(f"第{attempt + 1}次尝试服务器内部错误: {str(e)}")
            last_error = e
            if attempt < max_retries:
                time.sleep(retry_delay)
                
        except openai.AuthenticationError as e:
            logger.error(f"认证错误: {str(e)}")
            return ""
            
        except Exception as e:
            logger.error(f"第{attempt + 1}次尝试发生意外错误: {str(e)}")
            last_error = e
            if attempt < max_retries:
                time.sleep(retry_delay)
    
    logger.error(f"所有尝试都失败了。最后错误: {str(last_error)}")
    return ""


if __name__ == "__main__":
    print(chat("你是一个助手", "你好"))
