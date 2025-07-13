"""
Flask service for OpenAI API integration.
"""
import os
from openai import OpenAI
from typing import List, Dict, Tuple
from decimal import Decimal
import tiktoken


# Model pricing per 1K tokens (USD) - Updated rates
MODEL_PRICING = {
    "gpt-4o": 0.01,
    "gpt-4o-mini": 0.005,
    "gpt-4-turbo": 0.01,
    "gpt-4": 0.03,
    "gpt-3.5-turbo": 0.0015,
}

# Model maximum tokens
MODEL_MAX_TOKENS = {
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4-turbo": 128000,
    "gpt-4": 8192,
    "gpt-3.5-turbo": 4096,
}


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """Count tokens in text using tiktoken."""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception:
        # Fallback to character-based estimation
        return len(text) // 4


def get_client():
    """Get OpenAI API client."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OpenAI API key is not configured.")
    return OpenAI(api_key=api_key)


def correct_text(
    processing_mode: str,
    user_custom_prompt: str,
    input_text: str,
    correction_words: List[Dict[str, str]],
    model: str = "gpt-4o",
) -> Tuple[str, Decimal, int, int]:
    """
    Correct text using OpenAI API.

    Args:
        processing_mode: Processing mode ("proofreading", "grammar", "summary", "custom")
        user_custom_prompt: User's custom instructions
        input_text: Text to be corrected
        correction_words: List of word corrections [{"incorrect": "word", "correct": "word"}, ...]
        model: Model name to use

    Returns:
        (corrected_text, cost, input_tokens, output_tokens)
    """
    client = get_client()
    messages = []
    system_content = ""

    if processing_mode == "proofreading":
        strict_system_prompt = (
            "You are an AI specialized in typo and spelling correction. "
            "Do NOT summarize, add, delete, rephrase, reformat, change tone, modify content, "
            "merge/split paragraphs, change word order, or perform any other edits. "
            "Only correct typos and spelling mistakes based on the provided correction list. "
            "Do not modify any parts not listed in the correction list. "
            "Human final review and correction is mandatory."
        )
        correction_instruction = ""
        if correction_words:
            correction_instruction = (
                "Apply the following typo corrections with priority:\n"
            )
            for word in correction_words:
                correction_instruction += f"'{word['incorrect']}' → '{word['correct']}'\n"

        system_content = f"{strict_system_prompt}\n\n{correction_instruction}".strip()
        if user_custom_prompt:
            system_content += f"\n\nUser note: {user_custom_prompt}"

    elif processing_mode == "grammar":
        grammar_system_prompt = (
            "You are an AI that corrects Japanese text to be natural and grammatically correct.\n"
            "Follow these instructions to modify the provided text:\n"
            "1. Fix grammatical errors.\n"
            "2. Correct unnatural expressions to more natural Japanese.\n"
            "3. Fix typos and spelling mistakes."
        )
        if correction_words:
            grammar_system_prompt += (
                "\nEspecially, prioritize correcting words from this list:\n"
            )
            for word in correction_words:
                grammar_system_prompt += f"'{word['incorrect']}' → '{word['correct']}'\n"

        grammar_system_prompt += (
            "\n4. Preserve the original meaning and main information, "
            "do not add or delete content arbitrarily.\n"
            "5. Match the writing style of the original text."
        )
        system_content = grammar_system_prompt.strip()
        if user_custom_prompt:
            system_content += f"\n\nUser note: {user_custom_prompt}"

    elif processing_mode == "summary":
        summarize_system_prompt = (
            "You are an AI that summarizes provided Japanese text.\n"
            "Follow these instructions to summarize the text:\n"
            "1. Understand the main topics and conclusions of the entire text.\n"
            "2. Extract important information and omit redundant parts and details.\n"
            "3. Create a summary that accurately reflects the intent of the original text."
        )
        system_content = summarize_system_prompt.strip()
        if user_custom_prompt:
            system_content += f"\n\nSpecific user instructions: {user_custom_prompt}"

    else:  # custom mode
        system_content = "You are a text processing AI. Follow the user's instructions."
        if user_custom_prompt:
            system_content += f"\n\nUser instructions: {user_custom_prompt}"

    messages.append({"role": "system", "content": system_content})
    messages.append({"role": "user", "content": input_text})

    # Validate model name
    if model not in MODEL_PRICING:
        model = "gpt-4o"  # Default model

    # API request
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
        top_p=1,
        presence_penalty=0,
        frequency_penalty=0,
    )

    corrected_text = response.choices[0].message.content

    # Get actual token usage
    prompt_tokens = response.usage.prompt_tokens
    completion_tokens = response.usage.completion_tokens
    total_tokens = response.usage.total_tokens

    # Calculate cost
    price_per_1k = MODEL_PRICING.get(model, 0.01)
    cost = Decimal(str((total_tokens / 1000) * price_per_1k))

    return corrected_text, cost, prompt_tokens, completion_tokens


def estimate_cost(text: str, model: str = "gpt-4o") -> Decimal:
    """Estimate the cost for processing text."""
    tokens = count_tokens(text, model)
    price_per_1k = MODEL_PRICING.get(model, 0.01)
    # Add some buffer for system prompt and output
    estimated_total_tokens = tokens * 1.5  # 50% buffer
    return Decimal(str((estimated_total_tokens / 1000) * price_per_1k))


def get_max_tokens_for_model(model: str) -> int:
    """Get maximum tokens for a model."""
    return MODEL_MAX_TOKENS.get(model, 4000)


def split_text(text: str, max_tokens: int = 4000) -> List[str]:
    """Split text based on token limits."""
    # Simple implementation - can be enhanced
    chunks = []
    paragraphs = text.split("\n\n")
    current_chunk = []
    current_tokens = 0
    
    for paragraph in paragraphs:
        paragraph_tokens = count_tokens(paragraph)
        
        if current_tokens + paragraph_tokens > max_tokens:
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_tokens = 0
        
        current_chunk.append(paragraph)
        current_tokens += paragraph_tokens
    
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
    
    return chunks