"""
app.py - SlothDigest: The Lazy Message Catch-up & Reply Generator.
DEV.to "Slow and Steady" (International Sloth Day) Hackathon Project.
"""

import json
import os
import re
from typing import Optional, Tuple
import streamlit as st
from dotenv import load_dotenv

# Load local .env if present
load_dotenv()

# Bridge Streamlit Cloud Secrets into environment if present
try:
    if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
        if not os.getenv("GROQ_API_KEY"):
            os.environ["GROQ_API_KEY"] = str(st.secrets["GROQ_API_KEY"]).strip()
except Exception:
    pass

from prompts import SLOTH_SYSTEM_PROMPT, SlothDigestResult, CannedReply
from sample_data import SAMPLE_PRESETS


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
                sens = [st.strip() for st in parts[0].split(". ") if st.strip()]
                if len(sens) >= 2:
                    s1 = s1 or (sens[0] + ".")
                    s2 = s2 or (sens[1] if sens[1].endswith(".") else sens[1] + ".")
                else:
                    s1 = s1 or parts[0]

    return clean_lead(s1 or "Discussion occurred in the thread."), clean_lead(s2 or "Consensus reached without requiring your intervention.")


def parse_sloth_result(raw_json: dict) -> SlothDigestResult:
    """Bulletproof parser that maps any casing and guarantees valid SlothDigestResult."""
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


def execute_sloth_digest(
    messages_text: str,
    api_key: Optional[str] = None,
    provider: str = "Groq",
    model: str = "openai/gpt-oss-20b",
    ollama_url: str = "http://localhost:11434/v1",
) -> Tuple[Optional[SlothDigestResult], Optional[str]]:
    """Analyzes message dump and returns bulletproof SlothDigestResult."""
    if not messages_text.strip():
        return None, "Please provide some chat messages or select a sample preset."

    try:
        user_prompt = f"Analyze the following unread message thread and output the SlothDigestResult JSON:\n\n{messages_text}"

        if "Groq" in provider:
            from groq import Groq

            key = api_key or os.getenv("GROQ_API_KEY")
            if not key or not key.strip():
                return None, "Groq API Key is missing. Enter your key in the sidebar."

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

        else:
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

        cleaned = raw_content.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        data = json.loads(cleaned.strip())
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
                "Please generate a free key at https://console.groq.com/keys and enter it in the sidebar or update your Secrets."
            )
        return None, f"Inference error: {err_msg}"


@st.cache_data(ttl=300)
def check_groq_key_status(key: str) -> Tuple[bool, str]:
    """Checks if a Groq API key is valid by testing against Groq API."""
    if not key or not key.strip():
        return False, "No key provided"
    try:
        from groq import Groq

        client = Groq(api_key=key.strip())
        client.models.list()
        return True, "Valid"
    except Exception as e:
        err = str(e)
        if "401" in err or "invalid_api_key" in err.lower():
            return False, "Invalid API key"
        return False, err


def get_groq_models(api_key=None):
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
        active = [
            m.id
            for m in response.data
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


# Page configuration
st.set_page_config(
    page_title="SlothDigest 🦥 - Conserve Your Energy",
    page_icon="🦥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Initialize Session State
if "chat_input" not in st.session_state:
    st.session_state.chat_input = ""
if "digest_result" not in st.session_state:
    st.session_state.digest_result = None
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "☀️"

is_night = (st.session_state.theme_mode == "🌙")

# Inject Powerful, Comprehensive CSS Overrides for 100% Crisp Visibility
if not is_night:
    # ------------------ DAY MODE (Clean, Crisp, High-Contrast) ------------------
    theme_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    /* Global App Background & Base Font */
    html, body, .stApp {
        background-color: #f8fafc !important;
        color: #0f172a !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    
    /* Remove Black Top Header */
    header[data-testid="stHeader"] {
        background: #ffffff !important;
        border-bottom: 1px solid #e2e8f0 !important;
        z-index: 9999 !important;
    }
    
    /* Hide Deploy Button & Streamlit Footer */
    .stDeployButton, [data-testid="stDeployButton"], div[class*="stDeployButton"], div[data-testid="stDecoration"] {
        display: none !important;
        visibility: hidden !important;
    }
    footer {
        visibility: hidden !important;
        display: none !important;
    }
    
    /* Ensure ALL text elements in main page are crisp and dark */
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
        color: #0f172a !important;
        font-family: 'Fredoka', cursive !important;
    }
    
    .stApp p, .stApp span, .stApp div, .stApp label, [data-testid="stMarkdownContainer"] p {
        color: #1e293b !important;
    }
    
    /* Completely Remove Left Menu / Sidebar in Day Mode */
    [data-testid="stSidebar"],
    [data-testid="collapsedControl"],
    section[data-testid="stSidebar"],
    div[data-testid="stSidebarCollapsedControl"],
    button[kind="header"] {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
    }
    
    /* Header & Subtitle */
    .sloth-header {
        font-family: 'Fredoka', cursive !important;
        font-size: 2.8rem !important;
        color: #047857 !important;
        margin-bottom: 4px !important;
    }
    
    .sloth-subtitle {
        font-size: 1.15rem !important;
        color: #334155 !important;
        margin-bottom: 12px !important;
        font-weight: 500 !important;
        line-height: 1.5 !important;
    }

    /* ---------------- Animated Sloth Hero (Day Mode) ---------------- */
    @keyframes slothSwing {
        0% { transform: rotate(-5deg); }
        50% { transform: rotate(4deg); }
        100% { transform: rotate(-5deg); }
    }
    
    @keyframes slothCrawl {
        0% { transform: translateX(0px); }
        50% { transform: translateX(28px); }
        100% { transform: translateX(0px); }
    }
    
    @keyframes slothBreathe {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.025, 0.985); }
    }
    
    @keyframes slothBlink {
        0%, 92%, 100% { transform: scaleY(1); }
        96% { transform: scaleY(0.08); }
    }
    
    @keyframes leafFlutter {
        0%, 100% { transform: rotate(0deg); }
        50% { transform: rotate(6deg); }
    }
    
    @keyframes zzzFloat1 {
        0% { opacity: 0; transform: translate(0, 0) scale(0.6); }
        30% { opacity: 0.9; }
        80% { opacity: 0.8; }
        100% { opacity: 0; transform: translate(22px, -34px) scale(1.2); }
    }
    
    @keyframes zzzFloat2 {
        0% { opacity: 0; transform: translate(0, 0) scale(0.5); }
        30% { opacity: 0.9; }
        80% { opacity: 0.8; }
        100% { opacity: 0; transform: translate(28px, -46px) scale(1.3); }
    }
    
    @keyframes zzzFloat3 {
        0% { opacity: 0; transform: translate(0, 0) scale(0.5); }
        30% { opacity: 0.9; }
        80% { opacity: 0.8; }
        100% { opacity: 0; transform: translate(34px, -56px) scale(1.4); }
    }
    
    @keyframes pulseGlow {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.45; transform: scale(0.85); }
    }

    .anim-branch-mover {
        animation: slothCrawl 13s ease-in-out infinite;
        transform-origin: 120px 20px;
    }
    .anim-sloth-swinger {
        animation: slothSwing 4.5s ease-in-out infinite;
        transform-origin: 120px 30px;
    }
    .anim-sloth-body {
        animation: slothBreathe 3s ease-in-out infinite;
        transform-origin: 120px 90px;
    }
    .anim-sloth-eyes {
        animation: slothBlink 5.5s infinite;
        transform-origin: 120px 88px;
    }
    .anim-leaf-1 {
        animation: leafFlutter 3.2s ease-in-out infinite alternate;
        transform-origin: 22px 30px;
    }
    .anim-leaf-2 {
        animation: leafFlutter 4s ease-in-out infinite alternate 0.8s;
        transform-origin: 215px 26px;
    }
    .zzz-1 {
        animation: zzzFloat1 3.4s ease-out infinite 0s;
        font-family: 'Fredoka', cursive, sans-serif;
        font-weight: 700;
    }
    .zzz-2 {
        animation: zzzFloat2 3.4s ease-out infinite 1.1s;
        font-family: 'Fredoka', cursive, sans-serif;
        font-weight: 700;
    }
    .zzz-3 {
        animation: zzzFloat3 3.4s ease-out infinite 2.2s;
        font-family: 'Fredoka', cursive, sans-serif;
        font-weight: 700;
    }

    .sloth-hero-card {
        background: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 20px !important;
        padding: 24px 30px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05) !important;
        display: flex !important;
        align-items: center !important;
        gap: 32px !important;
        margin-bottom: 24px !important;
        position: relative !important;
        overflow: visible !important;
    }
    
    .sloth-anim-container {
        flex-shrink: 0 !important;
        width: 230px !important;
        height: 165px !important;
        position: relative !important;
        cursor: pointer !important;
    }
    
    .sloth-speech-bubble {
        position: absolute !important;
        top: -12px !important;
        left: 20px !important;
        background: #ffffff !important;
        border: 1.5px solid #059669 !important;
        color: #064e3b !important;
        font-size: 0.82rem !important;
        font-weight: 700 !important;
        padding: 5px 12px !important;
        border-radius: 12px !important;
        white-space: nowrap !important;
        opacity: 0 !important;
        transform: translateY(6px) !important;
        transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
        pointer-events: none !important;
        z-index: 10 !important;
        box-shadow: 0 4px 14px rgba(5, 150, 105, 0.2) !important;
    }
    .sloth-anim-container:hover .sloth-speech-bubble {
        opacity: 1 !important;
        transform: translateY(0) !important;
    }

    .sloth-hero-content {
        flex-grow: 1 !important;
    }

    .sloth-badges {
        display: flex !important;
        gap: 10px !important;
        align-items: center !important;
        flex-wrap: wrap !important;
        margin-top: 10px !important;
    }

    .sloth-badge {
        font-size: 0.82rem !important;
        font-weight: 700 !important;
        padding: 5px 12px !important;
        border-radius: 9999px !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        line-height: 1.2 !important;
    }

    .mascot-badge {
        background: #ecfdf5 !important;
        border: 1px solid #a7f3d0 !important;
        color: #065f46 !important;
    }
    .mascot-badge .status-dot-pulse {
        background: #10b981 !important;
        box-shadow: 0 0 8px #10b981 !important;
    }
    .speed-badge {
        background: #f0fdf4 !important;
        border: 1px solid #bbf7d0 !important;
        color: #15803d !important;
    }
    .privacy-badge {
        background: #f8fafc !important;
        border: 1px solid #cbd5e1 !important;
        color: #334155 !important;
    }

    .status-dot-pulse {
        width: 8px !important;
        height: 8px !important;
        border-radius: 50% !important;
        animation: pulseGlow 2s infinite ease-in-out !important;
        display: inline-block !important;
    }

    @media (max-width: 768px) {
        .sloth-hero-card {
            flex-direction: column !important;
            text-align: center !important;
            padding: 18px 14px !important;
            gap: 16px !important;
        }
        .sloth-anim-container {
            margin: 0 auto !important;
        }
        .sloth-badges {
            justify-content: center !important;
        }
        .sloth-header {
            font-size: 2.2rem !important;
        }
    }
    
    /* Day Mode Theme Toggle Switcher Pinned to Absolute Top Right Corner */
    [data-testid="stElementContainer"]:has([data-testid="stButtonGroup"]),
    [data-testid="stElementContainer"]:has([data-testid="stSegmentedControl"]),
    [data-testid="stElementContainer"]:has(.stButtonGroup),
    div[data-testid="stButtonGroup"],
    .stButtonGroup,
    div[data-testid="stSegmentedControl"] {
        position: fixed !important;
        top: 10px !important;
        right: 18px !important;
        z-index: 9999999 !important;
        width: fit-content !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    div[data-testid="stButtonGroup"],
    .stButtonGroup,
    div[data-testid="stSegmentedControl"] {
        display: inline-flex !important;
        flex-direction: row !important;
        align-items: center !important;
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 9999px !important;
        padding: 2px !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08) !important;
        gap: 2px !important;
    }
    
    div[data-testid="stButtonGroup"] button,
    .stButtonGroup button,
    div[data-testid="stSegmentedControl"] button {
        font-size: 1.2rem !important;
        border-radius: 9999px !important;
        border: none !important;
        padding: 4px 14px !important;
        background: transparent !important;
        cursor: pointer !important;
        line-height: 1 !important;
        min-height: 32px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.15s ease !important;
    }
    
    div[data-testid="stButtonGroup"] button[aria-selected="true"],
    div[data-testid="stButtonGroup"] button[data-selected="true"],
    div[data-testid="stButtonGroup"] button[aria-checked="true"],
    .stButtonGroup button[aria-selected="true"],
    .stButtonGroup button[data-selected="true"],
    .stButtonGroup button[aria-checked="true"],
    div[data-testid="stSegmentedControl"] button[aria-selected="true"],
    div[data-testid="stSegmentedControl"] button[data-selected="true"] {
        background-color: #059669 !important;
        color: #ffffff !important;
        box-shadow: 0 2px 6px rgba(5, 150, 105, 0.35) !important;
    }

    div[data-testid="stButtonGroup"] button:not([aria-selected="true"]):not([data-selected="true"]):hover,
    .stButtonGroup button:not([aria-selected="true"]):not([data-selected="true"]):hover {
        background-color: #f1f5f9 !important;
    }
    
    /* Preset Buttons in Day Mode (Clean White Cards, NOT Black!) */
    [data-testid="stHorizontalBlock"] button {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05) !important;
        transition: all 0.2s ease !important;
        padding: 10px 14px !important;
    }
    
    [data-testid="stHorizontalBlock"] button:hover {
        background-color: #f0fdf4 !important;
        border-color: #10b981 !important;
        color: #047857 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15) !important;
    }
    
    /* Chat Text Area in Day Mode */
    [data-testid="stTextArea"] label p {
        color: #0f172a !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        margin-bottom: 8px !important;
    }
    
    [data-testid="stTextArea"] textarea {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 2px solid #cbd5e1 !important;
        border-radius: 14px !important;
        font-size: 1rem !important;
        padding: 16px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
    }
    
    [data-testid="stTextArea"] textarea:focus {
        border-color: #059669 !important;
        box-shadow: 0 0 0 4px rgba(5, 150, 105, 0.12) !important;
    }
    
    /* Primary Action Button */
    button[kind="primary"] {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 1.15rem !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 14px 28px !important;
        box-shadow: 0 4px 14px rgba(4, 120, 87, 0.35) !important;
        transition: all 0.2s ease !important;
    }
    
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #047857 0%, #065f46 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(4, 120, 87, 0.45) !important;
    }
    
    /* Traffic Alert Cards */
    .traffic-card {
        padding: 22px 26px !important;
        border-radius: 16px !important;
        margin-bottom: 24px !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.06) !important;
    }
    
    .card-green {
        background-color: #ecfdf5 !important;
        border: 1.5px solid #a7f3d0 !important;
        border-left: 8px solid #059669 !important;
    }
    .card-green h3, .card-green p { color: #064e3b !important; }
    
    .card-yellow {
        background-color: #fffbeb !important;
        border: 1.5px solid #fde68a !important;
        border-left: 8px solid #d97706 !important;
    }
    .card-yellow h3, .card-yellow p { color: #78350f !important; }
    
    .card-red {
        background-color: #fef2f2 !important;
        border: 1.5px solid #fecaca !important;
        border-left: 8px solid #dc2626 !important;
    }
    .card-red h3, .card-red p { color: #7f1d1d !important; }
    
    /* Summary Card in Day Mode */
    .summary-card {
        background: #ffffff !important;
        border: 1.5px solid #e2e8f0 !important;
        border-radius: 16px !important;
        padding: 26px 30px !important;
        margin-bottom: 24px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05) !important;
    }
    
    .summary-card p {
        color: #0f172a !important;
        font-size: 1.15rem !important;
        line-height: 1.6 !important;
        font-weight: 500 !important;
    }
    
    .fact-tag {
        background: #2563eb !important;
        color: #ffffff !important;
        padding: 4px 12px !important;
        border-radius: 8px !important;
        font-size: 0.85rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.5px !important;
        margin-right: 12px !important;
        display: inline-block !important;
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.25) !important;
    }
    
    .outcome-tag {
        background: #059669 !important;
        color: #ffffff !important;
        padding: 4px 12px !important;
        border-radius: 8px !important;
        font-size: 0.85rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.5px !important;
        margin-right: 12px !important;
        display: inline-block !important;
        box-shadow: 0 2px 6px rgba(5, 150, 105, 0.25) !important;
    }
    
    /* Quote & Replies */
    .sloth-quote {
        background: #fef9c3 !important;
        border-left: 6px solid #eab308 !important;
        padding: 18px 24px !important;
        border-radius: 0 16px 16px 0 !important;
        color: #713f12 !important;
        font-size: 1.05rem !important;
        font-style: italic !important;
        margin-bottom: 24px !important;
    }
    
    .reply-card {
        background: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 16px !important;
        padding: 20px !important;
        min-height: 105px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-start !important;
        box-shadow: 0 3px 10px rgba(0,0,0,0.04) !important;
    }
    
    .reply-card h4 {
        color: #0f172a !important;
        font-size: 1.15rem !important;
        font-weight: 800 !important;
        margin-bottom: 4px !important;
    }
    
    .reply-card p {
        color: #64748b !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        margin-bottom: 0px !important;
    }
    
    /* Canned Reply Code Blocks in Day Mode (Clean White/Soft-Slate with Crisp Dark Text) */
    [data-testid="stCode"], 
    .stCode,
    [data-testid="stCode"] > div,
    [data-testid="stCodeUnhighlighted"],
    [data-testid="stCode"] pre,
    [data-testid="stCode"] code {
        background-color: #f1f5f9 !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 12px !important;
    }
    
    [data-testid="stCode"] *,
    .stCode *,
    [data-testid="stCodeUnhighlighted"] *,
    [data-testid="stCode"] pre *,
    [data-testid="stCode"] code * {
        color: #0f172a !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        background: transparent !important;
    }
    
    [data-testid="stCode"] button {
        background-color: #e2e8f0 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        color: #334155 !important;
    }
    [data-testid="stCode"] button:hover {
        background-color: #cbd5e1 !important;
        color: #0f172a !important;
    }
    [data-testid="stCode"] button svg {
        fill: #334155 !important;
    }
    
    .energy-metric {
        background: #e2e8f0 !important;
        color: #0f172a !important;
        padding: 8px 18px !important;
        border-radius: 30px !important;
        font-weight: 800 !important;
        font-size: 0.95rem !important;
    }
    
    .status-dot {
        height: 10px;
        width: 10px;
        background-color: #10b981;
        border-radius: 50%;
        display: inline-block;
        margin-right: 6px;
    }
    </style>
    """
else:
    # ------------------ NIGHT MODE (Deep Slate Canopy, Sleek & Glowing) ------------------
    theme_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, .stApp {
        background-color: #0b1120 !important;
        color: #f8fafc !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    
    header[data-testid="stHeader"] {
        background: #0b1120 !important;
        border-bottom: 1px solid #1e293b !important;
        z-index: 9999 !important;
    }
    
    /* Hide Deploy Button & Streamlit Footer */
    .stDeployButton, [data-testid="stDeployButton"], div[class*="stDeployButton"], div[data-testid="stDecoration"] {
        display: none !important;
        visibility: hidden !important;
    }
    footer {
        visibility: hidden !important;
        display: none !important;
    }
    
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
        color: #f8fafc !important;
        font-family: 'Fredoka', cursive !important;
    }
    
    .stApp p, .stApp span, .stApp div, .stApp label, [data-testid="stMarkdownContainer"] p {
        color: #cbd5e1 !important;
    }
    
    /* Completely Remove Left Menu / Sidebar in Night Mode */
    [data-testid="stSidebar"],
    [data-testid="collapsedControl"],
    section[data-testid="stSidebar"],
    div[data-testid="stSidebarCollapsedControl"],
    button[kind="header"] {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
    }
    
    .sloth-header {
        font-family: 'Fredoka', cursive !important;
        font-size: 2.8rem !important;
        color: #38bdf8 !important;
        margin-bottom: 4px !important;
    }
    
    .sloth-subtitle {
        font-size: 1.15rem !important;
        color: #94a3b8 !important;
        margin-bottom: 12px !important;
        font-weight: 500 !important;
        line-height: 1.5 !important;
    }

    /* ---------------- Animated Sloth Hero (Night Mode) ---------------- */
    @keyframes slothSwing {
        0% { transform: rotate(-5deg); }
        50% { transform: rotate(4deg); }
        100% { transform: rotate(-5deg); }
    }
    
    @keyframes slothCrawl {
        0% { transform: translateX(0px); }
        50% { transform: translateX(28px); }
        100% { transform: translateX(0px); }
    }
    
    @keyframes slothBreathe {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.025, 0.985); }
    }
    
    @keyframes slothBlink {
        0%, 92%, 100% { transform: scaleY(1); }
        96% { transform: scaleY(0.08); }
    }
    
    @keyframes leafFlutter {
        0%, 100% { transform: rotate(0deg); }
        50% { transform: rotate(6deg); }
    }
    
    @keyframes zzzFloat1 {
        0% { opacity: 0; transform: translate(0, 0) scale(0.6); }
        30% { opacity: 0.9; }
        80% { opacity: 0.8; }
        100% { opacity: 0; transform: translate(22px, -34px) scale(1.2); }
    }
    
    @keyframes zzzFloat2 {
        0% { opacity: 0; transform: translate(0, 0) scale(0.5); }
        30% { opacity: 0.9; }
        80% { opacity: 0.8; }
        100% { opacity: 0; transform: translate(28px, -46px) scale(1.3); }
    }
    
    @keyframes zzzFloat3 {
        0% { opacity: 0; transform: translate(0, 0) scale(0.5); }
        30% { opacity: 0.9; }
        80% { opacity: 0.8; }
        100% { opacity: 0; transform: translate(34px, -56px) scale(1.4); }
    }
    
    @keyframes pulseGlow {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.45; transform: scale(0.85); }
    }

    .anim-branch-mover {
        animation: slothCrawl 13s ease-in-out infinite;
        transform-origin: 120px 20px;
    }
    .anim-sloth-swinger {
        animation: slothSwing 4.5s ease-in-out infinite;
        transform-origin: 120px 30px;
    }
    .anim-sloth-body {
        animation: slothBreathe 3s ease-in-out infinite;
        transform-origin: 120px 90px;
    }
    .anim-sloth-eyes {
        animation: slothBlink 5.5s infinite;
        transform-origin: 120px 88px;
    }
    .anim-leaf-1 {
        animation: leafFlutter 3.2s ease-in-out infinite alternate;
        transform-origin: 22px 30px;
    }
    .anim-leaf-2 {
        animation: leafFlutter 4s ease-in-out infinite alternate 0.8s;
        transform-origin: 215px 26px;
    }
    .zzz-1 {
        animation: zzzFloat1 3.4s ease-out infinite 0s;
        font-family: 'Fredoka', cursive, sans-serif;
        font-weight: 700;
    }
    .zzz-2 {
        animation: zzzFloat2 3.4s ease-out infinite 1.1s;
        font-family: 'Fredoka', cursive, sans-serif;
        font-weight: 700;
    }
    .zzz-3 {
        animation: zzzFloat3 3.4s ease-out infinite 2.2s;
        font-family: 'Fredoka', cursive, sans-serif;
        font-weight: 700;
    }

    .sloth-hero-card {
        background: rgba(30, 41, 59, 0.75) !important;
        border: 1px solid rgba(148, 163, 184, 0.2) !important;
        border-radius: 20px !important;
        padding: 24px 30px !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35) !important;
        display: flex !important;
        align-items: center !important;
        gap: 32px !important;
        margin-bottom: 24px !important;
        position: relative !important;
        overflow: visible !important;
    }
    
    .sloth-anim-container {
        flex-shrink: 0 !important;
        width: 230px !important;
        height: 165px !important;
        position: relative !important;
        cursor: pointer !important;
    }
    
    .sloth-speech-bubble {
        position: absolute !important;
        top: -12px !important;
        left: 20px !important;
        background: #1e293b !important;
        border: 1.5px solid #38bdf8 !important;
        color: #f8fafc !important;
        font-size: 0.82rem !important;
        font-weight: 700 !important;
        padding: 5px 12px !important;
        border-radius: 12px !important;
        white-space: nowrap !important;
        opacity: 0 !important;
        transform: translateY(6px) !important;
        transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
        pointer-events: none !important;
        z-index: 10 !important;
        box-shadow: 0 4px 14px rgba(56, 189, 248, 0.3) !important;
    }
    .sloth-anim-container:hover .sloth-speech-bubble {
        opacity: 1 !important;
        transform: translateY(0) !important;
    }

    .sloth-hero-content {
        flex-grow: 1 !important;
    }

    .sloth-badges {
        display: flex !important;
        gap: 10px !important;
        align-items: center !important;
        flex-wrap: wrap !important;
        margin-top: 10px !important;
    }

    .sloth-badge {
        font-size: 0.82rem !important;
        font-weight: 700 !important;
        padding: 5px 12px !important;
        border-radius: 9999px !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        line-height: 1.2 !important;
    }

    .mascot-badge {
        background: rgba(16, 185, 129, 0.15) !important;
        border: 1px solid rgba(16, 185, 129, 0.35) !important;
        color: #6ee7b7 !important;
    }
    .mascot-badge .status-dot-pulse {
        background: #10b981 !important;
        box-shadow: 0 0 8px #10b981 !important;
    }
    .speed-badge {
        background: rgba(56, 189, 248, 0.15) !important;
        border: 1px solid rgba(56, 189, 248, 0.35) !important;
        color: #7dd3fc !important;
    }
    .privacy-badge {
        background: rgba(148, 163, 184, 0.12) !important;
        border: 1px solid rgba(148, 163, 184, 0.25) !important;
        color: #cbd5e1 !important;
    }

    .status-dot-pulse {
        width: 8px !important;
        height: 8px !important;
        border-radius: 50% !important;
        animation: pulseGlow 2s infinite ease-in-out !important;
        display: inline-block !important;
    }

    @media (max-width: 768px) {
        .sloth-hero-card {
            flex-direction: column !important;
            text-align: center !important;
            padding: 18px 14px !important;
            gap: 16px !important;
        }
        .sloth-anim-container {
            margin: 0 auto !important;
        }
        .sloth-badges {
            justify-content: center !important;
        }
        .sloth-header {
            font-size: 2.2rem !important;
        }
    }
    
    /* Night Mode Theme Toggle Switcher Pinned to Absolute Top Right Corner */
    [data-testid="stElementContainer"]:has([data-testid="stButtonGroup"]),
    [data-testid="stElementContainer"]:has([data-testid="stSegmentedControl"]),
    [data-testid="stElementContainer"]:has(.stButtonGroup),
    div[data-testid="stButtonGroup"],
    .stButtonGroup,
    div[data-testid="stSegmentedControl"] {
        position: fixed !important;
        top: 10px !important;
        right: 18px !important;
        z-index: 9999999 !important;
        width: fit-content !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    div[data-testid="stButtonGroup"],
    .stButtonGroup,
    div[data-testid="stSegmentedControl"] {
        display: inline-flex !important;
        flex-direction: row !important;
        align-items: center !important;
        background-color: #1e293b !important;
        border: 1.5px solid #334155 !important;
        border-radius: 9999px !important;
        padding: 2px !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.4) !important;
        gap: 2px !important;
    }
    
    div[data-testid="stButtonGroup"] button,
    .stButtonGroup button,
    div[data-testid="stSegmentedControl"] button {
        font-size: 1.2rem !important;
        border-radius: 9999px !important;
        border: none !important;
        padding: 4px 14px !important;
        background: transparent !important;
        cursor: pointer !important;
        line-height: 1 !important;
        min-height: 32px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.15s ease !important;
    }
    
    div[data-testid="stButtonGroup"] button[aria-selected="true"],
    div[data-testid="stButtonGroup"] button[data-selected="true"],
    div[data-testid="stButtonGroup"] button[aria-checked="true"],
    .stButtonGroup button[aria-selected="true"],
    .stButtonGroup button[data-selected="true"],
    .stButtonGroup button[aria-checked="true"],
    div[data-testid="stSegmentedControl"] button[aria-selected="true"],
    div[data-testid="stSegmentedControl"] button[data-selected="true"] {
        background-color: #38bdf8 !important;
        color: #ffffff !important;
        box-shadow: 0 2px 8px rgba(56, 189, 248, 0.4) !important;
    }

    div[data-testid="stButtonGroup"] button:not([aria-selected="true"]):not([data-selected="true"]):hover,
    .stButtonGroup button:not([aria-selected="true"]):not([data-selected="true"]):hover {
        background-color: #334155 !important;
    }
    
    [data-testid="stHorizontalBlock"] button {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 1.5px solid #334155 !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2) !important;
        transition: all 0.2s ease !important;
        padding: 10px 14px !important;
    }
    
    [data-testid="stHorizontalBlock"] button:hover {
        background-color: #334155 !important;
        border-color: #38bdf8 !important;
        color: #38bdf8 !important;
        transform: translateY(-2px) !important;
    }
    
    [data-testid="stTextArea"] label p {
        color: #f8fafc !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        margin-bottom: 8px !important;
    }
    
    [data-testid="stTextArea"] textarea {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 2px solid #334155 !important;
        border-radius: 14px !important;
        font-size: 1rem !important;
        padding: 16px !important;
    }
    
    [data-testid="stTextArea"] textarea:focus {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 0 4px rgba(56, 189, 248, 0.2) !important;
    }
    
    button[kind="primary"] {
        background: linear-gradient(135deg, #f43f5e 0%, #e11d48 100%) !important;
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 1.15rem !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 14px 28px !important;
        box-shadow: 0 4px 16px rgba(225, 29, 72, 0.4) !important;
        transition: all 0.2s ease !important;
    }
    
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #e11d48 0%, #be123c 100%) !important;
        transform: translateY(-2px) !important;
    }
    
    .traffic-card {
        padding: 22px 26px !important;
        border-radius: 16px !important;
        margin-bottom: 24px !important;
        box-shadow: 0 6px 20px rgba(0,0,0,0.2) !important;
    }
    
    .card-green {
        background: rgba(16, 185, 129, 0.16) !important;
        border: 1px solid rgba(16, 185, 129, 0.35) !important;
        border-left: 8px solid #10b981 !important;
    }
    .card-green h3, .card-green p { color: #6ee7b7 !important; }
    
    .card-yellow {
        background: rgba(245, 158, 11, 0.16) !important;
        border: 1px solid rgba(245, 158, 11, 0.35) !important;
        border-left: 8px solid #f59e0b !important;
    }
    .card-yellow h3, .card-yellow p { color: #fcd34d !important; }
    
    .card-red {
        background: rgba(239, 68, 68, 0.16) !important;
        border: 1px solid rgba(239, 68, 68, 0.35) !important;
        border-left: 8px solid #ef4444 !important;
    }
    .card-red h3, .card-red p { color: #fca5a5 !important; }
    
    .summary-card {
        background: rgba(30, 41, 59, 0.75) !important;
        border: 1px solid rgba(148, 163, 184, 0.2) !important;
        border-radius: 16px !important;
        padding: 26px 30px !important;
        margin-bottom: 24px !important;
    }
    
    .summary-card p {
        color: #f8fafc !important;
        font-size: 1.15rem !important;
        line-height: 1.6 !important;
        font-weight: 500 !important;
    }
    
    .fact-tag {
        background: #3b82f6 !important;
        color: #ffffff !important;
        padding: 4px 12px !important;
        border-radius: 8px !important;
        font-size: 0.85rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.5px !important;
        margin-right: 12px !important;
        display: inline-block !important;
    }
    
    .outcome-tag {
        background: #10b981 !important;
        color: #ffffff !important;
        padding: 4px 12px !important;
        border-radius: 8px !important;
        font-size: 0.85rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.5px !important;
        margin-right: 12px !important;
        display: inline-block !important;
    }
    
    .sloth-quote {
        background: rgba(217, 119, 6, 0.15) !important;
        border-left: 6px solid #f59e0b !important;
        padding: 18px 24px !important;
        border-radius: 0 16px 16px 0 !important;
        color: #fef3c7 !important;
        font-size: 1.05rem !important;
        font-style: italic !important;
        margin-bottom: 24px !important;
    }
    
    .reply-card {
        background: rgba(30, 41, 59, 0.75) !important;
        border: 1px solid rgba(148, 163, 184, 0.2) !important;
        border-radius: 16px !important;
        padding: 20px !important;
        min-height: 105px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-start !important;
    }
    
    .reply-card h4 {
        color: #f8fafc !important;
        font-size: 1.15rem !important;
        font-weight: 800 !important;
        margin-bottom: 4px !important;
    }
    
    .reply-card p {
        color: #94a3b8 !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        margin-bottom: 0px !important;
    }
    
    /* Canned Reply Code Blocks in Night Mode (Deep Slate with Crisp Glowing White Text) */
    [data-testid="stCode"], 
    .stCode,
    [data-testid="stCode"] > div,
    [data-testid="stCodeUnhighlighted"],
    [data-testid="stCode"] pre,
    [data-testid="stCode"] code {
        background-color: #1e293b !important;
        border: 1.5px solid #334155 !important;
        border-radius: 12px !important;
    }
    
    [data-testid="stCode"] *,
    .stCode *,
    [data-testid="stCodeUnhighlighted"] *,
    [data-testid="stCode"] pre *,
    [data-testid="stCode"] code * {
        color: #f8fafc !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        background: transparent !important;
    }
    
    [data-testid="stCode"] button {
        background-color: #334155 !important;
        border: 1px solid #475569 !important;
        border-radius: 8px !important;
        color: #f8fafc !important;
    }
    [data-testid="stCode"] button:hover {
        background-color: #475569 !important;
        color: #ffffff !important;
    }
    [data-testid="stCode"] button svg {
        fill: #f8fafc !important;
    }
    
    .energy-metric {
        background: #334155 !important;
        color: #e2e8f0 !important;
        padding: 8px 18px !important;
        border-radius: 30px !important;
        font-weight: 800 !important;
        font-size: 0.95rem !important;
    }
    
    .status-dot {
        height: 10px;
        width: 10px;
        background-color: #10b981;
        border-radius: 50%;
        display: inline-block;
        margin-right: 6px;
    }
    </style>
    """

st.markdown(theme_css, unsafe_allow_html=True)

# Theme Toggle Switcher (Pinned to top-right corner via CSS)
theme_selection = st.segmented_control(
    "Theme",
    options=["☀️", "🌙"],
    default=st.session_state.theme_mode,
    key="theme_mode_control",
    label_visibility="collapsed",
    help="Switch between Day ☀️ and Night 🌙 mode",
)
if theme_selection and theme_selection != st.session_state.theme_mode:
    st.session_state.theme_mode = theme_selection
    st.rerun()

# Backend AI Engine Configuration (Operates securely in background, 0 frontend display)
is_groq = True
provider = "Groq"
api_key = os.getenv("GROQ_API_KEY", "").strip()
model = "openai/gpt-oss-20b"
ollama_url = ""

# Main Application Area Header with Animated Moving Sloth
SLOTH_HERO_HTML = """
<div class="sloth-hero-card">
    <div class="sloth-anim-container" title="Shhh... Sloan is conserving energy! 🦥 (Hover to say hi)">
        <div class="sloth-speech-bubble">Zzz... why rush? Let AI digest it 🍃</div>
        <svg viewBox="0 0 250 170" width="100%" height="100%" style="overflow: visible;">
            <!-- Tree Branch (Static across top) -->
            <path d="M 0,32 Q 60,38 125,32 Q 190,26 250,30" stroke="#784c28" stroke-width="13" stroke-linecap="round" fill="none"/>
            <path d="M 3,30 Q 60,35 125,29 Q 190,24 247,28" stroke="#925e34" stroke-width="4" stroke-linecap="round" fill="none"/>
            
            <!-- Lush Jungle Leaves -->
            <g class="anim-leaf-1">
                <path d="M 22,30 C 5,15 10,-5 32,8 C 30,20 26,27 22,30 Z" fill="#10b981"/>
                <path d="M 25,26 Q 20,10 20,-2" stroke="#047857" stroke-width="1.5" fill="none"/>
                <path d="M 35,32 C 45,15 65,12 55,30 Z" fill="#059669"/>
            </g>
            <g class="anim-leaf-2">
                <path d="M 215,26 C 235,10 250,18 240,36 C 228,34 220,30 215,26 Z" fill="#10b981"/>
                <path d="M 220,28 Q 235,20 246,18" stroke="#047857" stroke-width="1.5" fill="none"/>
            </g>

            <!-- Crawling & Swinging Sloth Assembly -->
            <g class="anim-branch-mover">
                <g class="anim-sloth-swinger">
                    
                    <!-- Back Claws gripping the branch -->
                    <g fill="#e2e8f0" stroke="#94a3b8" stroke-width="1">
                        <!-- Front Paw Claws (Right side as hanging) -->
                        <path d="M 148,22 C 148,16 153,16 153,23 L 153,30 C 153,30 148,30 148,22 Z" />
                        <path d="M 154,20 C 154,14 159,14 159,22 L 159,30 C 159,30 154,30 154,20 Z" />
                        <path d="M 160,22 C 160,16 165,16 165,24 L 165,30 C 165,30 160,30 160,22 Z" />

                        <!-- Back Paw Claws (Left side as hanging) -->
                        <path d="M 85,22 C 85,16 90,16 90,23 L 90,30 C 90,30 85,30 85,22 Z" />
                        <path d="M 91,20 C 91,14 96,14 96,22 L 96,30 C 96,30 91,30 91,20 Z" />
                        <path d="M 97,22 C 97,16 102,16 102,24 L 102,30 C 102,30 97,30 97,22 Z" />
                    </g>

                    <!-- Front Arm & Back Leg (Reaching up to branch) -->
                    <path d="M 125,70 Q 155,60 155,27" stroke="#8c6a51" stroke-width="18" stroke-linecap="round" fill="none"/>
                    <path d="M 100,72 Q 88,58 92,27" stroke="#8c6a51" stroke-width="18" stroke-linecap="round" fill="none"/>

                    <!-- Sloth Body (Plump & Cozy) -->
                    <g class="anim-sloth-body">
                        <!-- Main Torso -->
                        <ellipse cx="120" cy="85" rx="38" ry="32" fill="#8c6a51"/>
                        <!-- Fluffy Light Belly -->
                        <ellipse cx="122" cy="86" rx="26" ry="22" fill="#d8bc9d"/>

                        <!-- Sloth Head (Tucked affectionately forward) -->
                        <g transform="translate(142, 85)">
                            <!-- Head Base -->
                            <circle cx="0" cy="0" r="23" fill="#8c6a51"/>
                            <!-- Light Face Mask -->
                            <ellipse cx="2" cy="1" rx="18" ry="16" fill="#f5ede0"/>

                            <!-- Eye Stripes (Classic Sloth Signature Mask) -->
                            <path d="M -8,-6 Q 0,-2 7,-8 Q 11,-4 8,0 Q -1,5 -9,0 Z" fill="#543622" opacity="0.9"/>
                            <path d="M 5,-7 Q 13,-2 20,-6 Q 22,-2 19,2 Q 12,6 4,1 Z" fill="#543622" opacity="0.9"/>

                            <!-- Sweet Sleeping / Blinking Eyes -->
                            <g class="anim-sloth-eyes">
                                <path d="M -3,-1 Q 0,3 4,-1" stroke="#231409" stroke-width="2.2" stroke-linecap="round" fill="none"/>
                                <path d="M 10,-1 Q 13,3 17,-1" stroke="#231409" stroke-width="2.2" stroke-linecap="round" fill="none"/>
                            </g>

                            <!-- Cute Button Nose -->
                            <ellipse cx="7" cy="5" rx="3.5" ry="2.5" fill="#231409"/>
                            <circle cx="6" cy="4.2" r="0.8" fill="#ffffff" opacity="0.7"/>

                            <!-- Gentle Smile -->
                            <path d="M 4,9 Q 7,13 11,9" stroke="#231409" stroke-width="1.8" stroke-linecap="round" fill="none"/>

                            <!-- Rosy Cheeks -->
                            <circle cx="-2" cy="5" r="3.2" fill="#f43f5e" opacity="0.3"/>
                            <circle cx="16" cy="5" r="3.2" fill="#f43f5e" opacity="0.3"/>

                            <!-- Tiny Round Ears -->
                            <circle cx="-18" cy="-5" r="4.5" fill="#71523c"/>
                            <circle cx="-18" cy="-5" r="2.5" fill="#d8bc9d"/>
                        </g>

                        <!-- Little Fluffy Tail -->
                        <ellipse cx="80" cy="88" rx="6" ry="5" fill="#71523c"/>
                    </g>

                    <!-- Sleeping ZZZ Bubbles -->
                    <text x="170" y="70" class="zzz-1" fill="#10b981" font-size="14">z</text>
                    <text x="175" y="65" class="zzz-2" fill="#38bdf8" font-size="18">Z</text>
                    <text x="182" y="60" class="zzz-3" fill="#f59e0b" font-size="22">Z</text>

                </g>
            </g>
        </svg>
    </div>

    <div class="sloth-hero-content">
        <div class="sloth-header">🦥 SlothDigest</div>
        <div class="sloth-subtitle">Channel your inner sloth. Let open-weight AI digest noisy group chats into a 2-line summary and 1-click canned replies.</div>
        <div class="sloth-badges">
            <span class="sloth-badge mascot-badge"><span class="status-dot-pulse"></span> Sloan the Sloth • Conserving Energy</span>
            <span class="sloth-badge speed-badge">⚡ Instant Groq LPU</span>
            <span class="sloth-badge privacy-badge">🔒 100% Private</span>
        </div>
    </div>
</div>
"""
st.markdown(SLOTH_HERO_HTML, unsafe_allow_html=True)

# Preset Quick-Load Buttons with polished styling
st.markdown("**⚡ Too lazy to type? Test with 1-click scenario presets:**")
col_p1, col_p2, col_p3, col_clear = st.columns([1.3, 1.4, 1.4, 0.7])

with col_p1:
    if st.button("🍕 47-Msg Dinner Debate", use_container_width=True):
        st.session_state.chat_input = SAMPLE_PRESETS["🍕 Dinner Debate (Green - 47 Messages)"]["text"]
        st.session_state.digest_result = None

with col_p2:
    if st.button("🚨 Friday Slack False Alarm", use_container_width=True):
        st.session_state.chat_input = SAMPLE_PRESETS["🚨 Friday 4:45 PM Slack Emergency (Yellow/Green)"]["text"]
        st.session_state.digest_result = None

with col_p3:
    if st.button("🏡 Lawn Gnome HOA War", use_container_width=True):
        st.session_state.chat_input = SAMPLE_PRESETS["🏡 Neighborhood HOA Lawn Gnome War (Yellow - Petty Drama)"]["text"]
        st.session_state.digest_result = None

with col_clear:
    if st.button("🧹 Clear", use_container_width=True):
        st.session_state.chat_input = ""
        st.session_state.digest_result = None

# Chat Input Area
chat_text = st.text_area(
    "Paste your group chat, email thread, or Slack channel dump here:",
    value=st.session_state.chat_input,
    height=210,
    placeholder="e.g. [5:30 PM] Bob: Hey team, did anyone see the ticket? [5:32 PM] Alice: Looking into it...",
)

# Action Button
col_btn, col_info = st.columns([1.2, 2])
with col_btn:
    analyze_clicked = st.button("🦥 Hibernate & Digest Messages", type="primary", use_container_width=True)

# Trigger Analysis
if analyze_clicked:
    if not chat_text.strip():
        st.warning("⚠️ Please paste some messages or click one of the quick presets above!")
    else:
        with st.spinner("Sloan the Sloth is slowly digesting the drama..."):
            provider_type = "Groq" if is_groq else "Ollama (Local)"
            result, error = execute_sloth_digest(
                messages_text=chat_text,
                api_key=api_key,
                provider=provider_type,
                model=model,
                ollama_url=ollama_url,
            )
            if error:
                st.error(f"❌ {error}")
            else:
                st.session_state.digest_result = result

# Display Results
res = st.session_state.digest_result
if res:
    st.divider()

    # Determine Traffic Light Color Class & Emoji
    card_class = "card-green"
    badge_icon = "🟢"
    if res.urgency_level == "YELLOW":
        card_class = "card-yellow"
        badge_icon = "🟡"
    elif res.urgency_level == "RED":
        card_class = "card-red"
        badge_icon = "🔴"

    # 1. Urgency Banner
    st.markdown(
        f"""
        <div class="traffic-card {card_class}">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                <div>
                    <h3 style="margin: 0; font-size: 1.5rem; font-family: 'Fredoka', cursive;">{badge_icon} {res.urgency_title}</h3>
                    <p style="margin: 8px 0 0 0; font-size: 1.1rem; line-height: 1.4;">{res.urgency_verdict}</p>
                </div>
                <div>
                    <span class="energy-metric">⚡ {res.energy_saved}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. The 2-Line Sleepy Summary
    st.markdown("### 📋 The 2-Line Sleepy Summary")
    st.markdown(
        f"""
        <div class="summary-card">
            <p style="margin: 0 0 16px 0; font-size: 1.15rem; line-height: 1.6;">
                <span class="fact-tag">THE FACTS</span> {res.summary_line_1}
            </p>
            <p style="margin: 0; font-size: 1.15rem; line-height: 1.6;">
                <span class="outcome-tag">THE CONSENSUS</span> {res.summary_line_2}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 3. Sloth Quote / Wisdom
    st.markdown(
        f"""
        <div class="sloth-quote">
            <strong>🍃 Sloan's Reflection:</strong> "{res.sloth_take}"
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 4. 1-Click Lazy Canned Replies
    st.markdown("### 💤 1-Click Zero-Effort Replies")
    st.caption("Click the copy button on the top right of any card to send without typing a word:")

    cols = st.columns(len(res.canned_replies))
    for idx, (col, reply) in enumerate(zip(cols, res.canned_replies)):
        with col:
            st.markdown(
                f"""
                <div class="reply-card">
                    <h4>{reply.title}</h4>
                    <p>{reply.vibe}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.code(reply.response, language=None)

st.divider()
with st.expander("🌱 Why Open Weights Matter"):
    st.markdown(
        """
        - **Privacy First**: Group chats and work messages contain sensitive private chats. Open-weight models guarantee your data isn't harvested for proprietary AI training.
        - **Zero Cost Forever**: Runs entirely on Groq's generous free tier or free local hardware.
        - **Portability**: Switching from cloud to 100% offline air-gapped local inference requires 0 code changes.
        """
    )
