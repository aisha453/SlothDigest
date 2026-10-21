"""
groq_client.py - Dual-backend engine for Groq (Cloud Open Weights) and Ollama (Local Air-Gapped).
"""

import json
import os
import re
from typing import Optional, Tuple
from prompts import SLOTH_SYSTEM_PROMPT, SlothDigestResult


def _clean_json_str(raw_content: str) -> str:
    """Strips markdown code fences and whitespace from raw JSON response."""
    cleaned = raw_content.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


def _normalize_data(d):
    """Recursively converts camelCase keys to snake_case and standardizes variations."""
    if not isinstance(d, dict):
        return d
    normalized = {}
    for k, v in d.items():
        snake_k = re.sub(r'(?<!^)(?=[A-Z0-9])', '_', k).lower()
        if snake_k in ["summary_line_1", "summary_line1", "line_1", "line1"]:
            snake_k = "summary_line_1"
        elif snake_k in ["summary_line_2", "summary_line2", "line_2", "line2"]:
            snake_k = "summary_line_2"
        elif snake_k in ["canned_replies", "cannedreplies", "replies"]:
            snake_k = "canned_replies"

        if isinstance(v, dict):
            normalized[snake_k] = _normalize_data(v)
        elif isinstance(v, list):
            normalized[snake_k] = [_normalize_data(item) if isinstance(item, dict) else item for item in v]
        else:
            normalized[snake_k] = v

    # Standardize urgency level
    if "urgency_level" not in normalized and "urgency" in normalized:
        normalized["urgency_level"] = normalized["urgency"]
    if "urgency_level" in normalized and normalized["urgency_level"]:
        val = str(normalized["urgency_level"]).upper()
        if "GREEN" in val:
            normalized["urgency_level"] = "GREEN"
        elif "YELLOW" in val:
            normalized["urgency_level"] = "YELLOW"
        elif "RED" in val:
            normalized["urgency_level"] = "RED"
        else:
            normalized["urgency_level"] = "GREEN"

    return normalized


def get_groq_models(api_key: Optional[str] = None) -> list:
    """Fetches currently active models from Groq for the given API key."""
    fallback_models = [
        "llama-3.1-8b-instant",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "qwen/qwen3.8-27b",
    ]
    key = api_key or os.getenv("GROQ_API_KEY")
    if not key or not key.strip():
        return fallback_models
    try:
        from groq import Groq
        client = Groq(api_key=key.strip())
        response = client.models.list()
        # Filter out audio, whisper, tts, and guard models
        active = [
            m.id for m in response.data
            if not any(x in m.id.lower() for x in ["whisper", "tts", "guard", "orpheus"])
        ]
        if "llama-3.1-8b-instant" in active:
            active.remove("llama-3.1-8b-instant")
            active.insert(0, "llama-3.1-8b-instant")
        return active if active else fallback_models
    except Exception:
        return fallback_models


def run_sloth_digest(
    messages_text: str,
    api_key: Optional[str] = None,
    provider: str = "Groq",
    model: str = "llama-3.1-8b-instant",
    ollama_url: str = "http://localhost:11434/v1",
) -> Tuple[Optional[SlothDigestResult], Optional[str]]:
    """
    Executes Sloth analysis over the provided messages.
    Returns (result, error_message).
    """
    if not messages_text.strip():
        return None, "Please provide some chat messages or select a sample preset."

    try:
        user_prompt = f"Analyze the following unread message thread and output the SlothDigestResult JSON:\n\n{messages_text}"

        if provider == "Groq":
            from groq import Groq

            key = api_key or os.getenv("GROQ_API_KEY")
            if not key or not key.strip():
                return None, "Groq API Key is missing. Enter your key in the sidebar or set GROQ_API_KEY in .env."

            client = Groq(api_key=key.strip())
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": SLOTH_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                model=model,
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            raw_content = response.choices[0].message.content

        elif provider == "Ollama (Local)":
            import httpx

            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": SLOTH_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "format": "json",
                "stream": False,
                "options": {"temperature": 0.2},
            }
            target_url = ollama_url.rstrip("/")
            if not target_url.endswith("/v1"):
                base_url = f"{target_url}/api/chat"
                res = httpx.post(base_url, json=payload, timeout=60.0)
                res.raise_for_status()
                raw_content = res.json()["message"]["content"]
            else:
                base_url = f"{target_url}/chat/completions"
                res = httpx.post(
                    base_url,
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": SLOTH_SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                        "response_format": {"type": "json_object"},
                    },
                    timeout=60.0,
                )
                res.raise_for_status()
                raw_content = res.json()["choices"][0]["message"]["content"]
        else:
            return None, f"Unsupported provider: {provider}"

        # Clean, normalize, and parse JSON
        cleaned = _clean_json_str(raw_content)
        data = json.loads(cleaned)
        data = _normalize_data(data)
        result = SlothDigestResult.model_validate(data)
        return result, None

    except json.JSONDecodeError as jde:
        return None, f"Model generated non-JSON output: {str(jde)}\nRaw response: {raw_content}"
    except Exception as e:
        return None, f"Inference error: {str(e)}"
