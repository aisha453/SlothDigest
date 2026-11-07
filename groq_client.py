"""
groq_client.py - Dual-backend engine for Groq (Cloud Open Weights) and Ollama (Local Air-Gapped).
"""

import json
import os
import re
from typing import Optional, Tuple
from prompts import SLOTH_SYSTEM_PROMPT, SlothDigestResult, CannedReply


def clean_lead(s: str) -> str:
    """Strips leading numbers, bullets, 'Line 1:', 'The Facts:', etc."""
    if not s:
        return ""
    patterns = [
        r"^[0-9]+[\.\)]\s*",
        r"^(line\s*[0-9]+:?)\s*",
        r"^(the\s*facts?:?|facts?:?)\s*",
        r"^(the\s*consensus:?|consensus:?|the\s*outcome:?|outcome:?)\s*",
    ]
    cleaned = str(s).strip()
    for p in patterns:
        cleaned = re.sub(p, "", cleaned, flags=re.IGNORECASE).strip()
    return cleaned


def extract_summary(clean: dict, raw_json: dict) -> Tuple[str, str]:
    """Extracts summary line 1 and line 2 from any possible LLM output structure."""
    s1, s2 = None, None

    for k in ["summaryline1", "summary1", "line1", "facts", "thefacts", "whathappened"]:
        if clean.get(k) and isinstance(clean[k], str):
            s1 = clean[k]
            break
    for k in ["summaryline2", "summary2", "line2", "consensus", "theconsensus", "outcome"]:
        if clean.get(k) and isinstance(clean[k], str):
            s2 = clean[k]
            break

    val = clean.get("twolinesummary") or clean.get("summary") or clean.get("tldr")
    if val is None:
        for rk, rv in raw_json.items():
            if re.sub(r"[^a-zA-Z0-9]", "", str(rk)).lower() in ["twolinesummary", "summary", "tldr"]:
                val = rv
                break

    if val is not None:
        if isinstance(val, list) and len(val) >= 1:
            s1 = s1 or str(val[0])
            if len(val) >= 2:
                s2 = s2 or str(val[1])
        elif isinstance(val, dict):
            in_c = {re.sub(r"[^a-zA-Z0-9]", "", str(ik)).lower(): iv for ik, iv in val.items()}
            s1 = s1 or in_c.get("line1") or in_c.get("facts") or in_c.get("summaryline1") or in_c.get("summary1")
            s2 = s2 or in_c.get("line2") or in_c.get("consensus") or in_c.get("outcome") or in_c.get("summaryline2") or in_c.get("summary2")
        elif isinstance(val, str) and not (s1 and s2):
            parts = [p.strip() for p in val.split("\n") if p.strip()]
            if len(parts) >= 2:
                s1 = s1 or parts[0]
                s2 = s2 or parts[1]
            elif len(parts) == 1:
                sens = [sent.strip() for sent in parts[0].split(". ") if sent.strip()]
                if len(sens) >= 2:
                    s1 = s1 or (sens[0] + ".")
                    s2 = s2 or (sens[1] if sens[1].endswith(".") else sens[1] + ".")
                else:
                    s1 = s1 or parts[0]

    return clean_lead(s1 or "Discussion occurred in the thread."), clean_lead(s2 or "Consensus reached without requiring your intervention.")


def parse_sloth_result(raw_json: dict) -> SlothDigestResult:
    """Bulletproof parser that maps any casing, handles schema variations, and guarantees valid SlothDigestResult."""
    if not isinstance(raw_json, dict):
        raw_json = {}

    clean = {}
    for k, v in raw_json.items():
        norm_k = re.sub(r"[^a-zA-Z0-9]", "", str(k)).lower()
        clean[norm_k] = v

    urg = str(clean.get("urgencylevel") or clean.get("urgency") or "GREEN").upper()
    if "RED" in urg:
        urgency_level = "RED"
    elif "YELLOW" in urg:
        urgency_level = "YELLOW"
    else:
        urgency_level = "GREEN"

    default_titles = {
        "GREEN": "Safe to Hibernate 🦥",
        "YELLOW": "Skim When Bored 🥱",
        "RED": "Action Required 🚨",
    }
    urgency_title = clean.get("urgencytitle") or clean.get("title") or default_titles[urgency_level]

    urgency_verdict = (
        clean.get("urgencyverdict")
        or clean.get("verdict")
        or clean.get("reason")
        or "No immediate action required. You can safely conserve your energy."
    )

    energy_saved = (
        clean.get("energysaved")
        or clean.get("timesaved")
        or "Saved: ~18 mins & 52 calories"
    )

    s1, s2 = extract_summary(clean, raw_json)

    sloth_take = (
        clean.get("slothtake")
        or clean.get("take")
        or clean.get("wisdom")
        or clean.get("quote")
        or "Humans spend remarkable energy debating things that resolve on their own."
    )

    raw_replies = (
        clean.get("cannedreplies")
        or clean.get("replies")
        or clean.get("cannedreply")
        or []
    )
    parsed_replies = []
    if isinstance(raw_replies, list):
        for r in raw_replies:
            if isinstance(r, dict):
                r_clean = {re.sub(r"[^a-zA-Z0-9]", "", str(rk)).lower(): rv for rk, rv in r.items()}
                rtitle = r_clean.get("title") or "Quick Reply"
                rresp = (
                    r_clean.get("response")
                    or r_clean.get("reply")
                    or r_clean.get("text")
                    or r_clean.get("message")
                    or "Sounds good! 👍"
                )
                rvibe = r_clean.get("vibe") or r_clean.get("reason") or "Zero effort"
                parsed_replies.append(
                    CannedReply(title=str(rtitle), response=str(rresp), vibe=str(rvibe))
                )

    default_canned = [
        CannedReply(
            title="The Minimalist",
            response="Sounds good! 👍",
            vibe="Zero-effort acknowledgment",
        ),
        CannedReply(
            title="The Graceful Delayer",
            response="Reviewing later this afternoon, thanks!",
            vibe="Polite delay",
        ),
        CannedReply(
            title="The Diplomatic Delegator",
            response="Thanks for handling this, happy to follow your lead!",
            vibe="Strategic delegation",
        ),
    ]
    while len(parsed_replies) < 3:
        parsed_replies.append(default_canned[len(parsed_replies)])

    return SlothDigestResult(
        urgency_level=urgency_level,
        urgency_title=str(urgency_title),
        urgency_verdict=str(urgency_verdict),
        energy_saved=str(energy_saved),
        summary_line_1=str(s1),
        summary_line_2=str(s2),
        sloth_take=str(sloth_take),
        canned_replies=parsed_replies[:3],
    )


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
    """Backwards-compatible normalizer for raw dicts."""
    if not isinstance(d, dict):
        return d
    result = parse_sloth_result(d)
    return result.model_dump()


def get_groq_models(api_key: Optional[str] = None) -> list:
    """Fetches currently active models from Groq for the given API key."""
    fallback_models = [
        "openai/gpt-oss-20b",
        "openai/gpt-oss-120b",
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
        priority = [
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b",
            "qwen/qwen3.8-27b",
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
        ]
        ordered = [p for p in priority if p in active]
        for m in active:
            if m not in ordered:
                ordered.append(m)
        return ordered if ordered else fallback_models
    except Exception:
        return fallback_models


def run_sloth_digest(
    messages_text: str,
    api_key: Optional[str] = None,
    provider: str = "Groq",
    model: str = "openai/gpt-oss-20b",
    ollama_url: str = "http://localhost:11434/v1",
) -> Tuple[Optional[SlothDigestResult], Optional[str]]:
    """
    Executes Sloth analysis over the provided messages.
    Returns (result, error_message).
    """
    if not messages_text or not messages_text.strip():
        return None, "Please provide some chat messages or select a sample preset."

    try:
        user_prompt = f"Analyze the following unread message thread and output the SlothDigestResult JSON:\n\n{messages_text}"

        if "Groq" in provider:
            from groq import Groq

            key = api_key or os.getenv("GROQ_API_KEY")
            if not key or not key.strip():
                return None, "Groq API Key is missing. Set GROQ_API_KEY in your environment, Streamlit Secrets, or .env file."

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

        elif "Ollama" in provider:
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
            target_url = (ollama_url.strip() if ollama_url and ollama_url.strip() else "http://localhost:11434").rstrip("/")
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

        cleaned = _clean_json_str(raw_content)
        data = json.loads(cleaned)
        result = parse_sloth_result(data)
        return result, None

    except json.JSONDecodeError as jde:
        return None, f"Model generated non-JSON output: {str(jde)}\nRaw response: {raw_content}"
    except Exception as e:
        err_msg = str(e)
        if "401" in err_msg or "invalid_api_key" in err_msg.lower():
            return None, (
                "🚨 Invalid Groq API Key (Error 401)\n\n"
                "The Groq API key is invalid or has expired. "
                "Please generate a free key at https://console.groq.com/keys and configure GROQ_API_KEY in your environment, Streamlit Secrets, or .env file."
            )
        return None, f"Inference error: {err_msg}"
