from openai import OpenAI
from app.config.settings import get_settings
from typing import Optional, Dict, Any

settings = get_settings()
client = OpenAI(api_key=settings.openai_api_key)


def call_openai(
    prompt: str,
    system_message: str = "You are a helpful financial research assistant.",
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: int = 2000
) -> str:
    """
    Call OpenAI API with the given prompt
    
    Args:
        prompt: The user prompt
        system_message: System message to set context
        model: OpenAI model to use (default: gpt-4o-mini for cost efficiency)
        temperature: Creativity level (0-1)
        max_tokens: Maximum tokens in response
        
    Returns:
        The generated text response
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise Exception(f"OpenAI API error: {str(e)}")


def call_openai_with_function(
    prompt: str,
    functions: list[Dict[str, Any]],
    system_message: str = "You are a helpful financial research assistant.",
    model: str = "gpt-4o-mini",
    temperature: float = 0.7
) -> Dict[str, Any]:
    """
    Call OpenAI API with function calling
    
    Args:
        prompt: The user prompt
        functions: List of function definitions
        system_message: System message to set context
        model: OpenAI model to use
        temperature: Creativity level (0-1)
        
    Returns:
        Dict containing function call details
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            functions=functions,
            function_call="auto",
            temperature=temperature
        )
        
        message = response.choices[0].message
        
        if message.function_call:
            return {
                "type": "function_call",
                "function_name": message.function_call.name,
                "arguments": message.function_call.arguments
            }
        else:
            return {
                "type": "text",
                "content": message.content
            }
    except Exception as e:
        raise Exception(f"OpenAI API error: {str(e)}")

