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
    model: str = "llama-3.1-8b-instant",
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
        return None, f"Inference error: {str(e)}"


def get_groq_models(api_key=None):
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
        active = [
            m.id
            for m in response.data
            if not any(x in m.id.lower() for x in ["whisper", "tts", "guard", "orpheus"])
        ]
        if "llama-3.1-8b-instant" in active:
            active.remove("llama-3.1-8b-instant")
            active.insert(0, "llama-3.1-8b-instant")
        return active if active else fallback_models
    except Exception:
        return fallback_models


# Page configuration
st.set_page_config(
    page_title="SlothDigest 🦥 - Conserve Your Energy",
    page_icon="🦥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize Session State
if "chat_input" not in st.session_state:
    st.session_state.chat_input = ""
if "digest_result" not in st.session_state:
    st.session_state.digest_result = None
if "is_night_mode" not in st.session_state:
    st.session_state.is_night_mode = True

# Top Navigation Bar with Day / Night Theme Switch
col_header_left, col_header_right = st.columns([3.8, 1.2])

with col_header_right:
    theme_selection = st.radio(
        "Theme Mode",
        ["🌙 Night Canopy", "☀️ Day Hammock"],
        index=0 if st.session_state.is_night_mode else 1,
        horizontal=True,
        label_visibility="collapsed",
    )
    st.session_state.is_night_mode = "Night" in theme_selection

is_night = st.session_state.is_night_mode

# Dynamic Theme Colors
if is_night:
    bg_gradient = "linear-gradient(180deg, #0b1120 0%, #0f172a 100%)"
    app_bg = "#0b1120"
    text_color = "#f8fafc"
    subtext_color = "#94a3b8"
    card_bg = "rgba(30, 41, 59, 0.75)"
    card_border = "rgba(148, 163, 184, 0.18)"
    quote_bg = "rgba(217, 119, 6, 0.12)"
    quote_border = "#f59e0b"
    metric_bg = "rgba(51, 65, 85, 0.8)"
    metric_text = "#e2e8f0"
    sidebar_bg = "#0f172a"
    hero_title_color = "#38bdf8"
else:
    bg_gradient = "linear-gradient(180deg, #fbf8f3 0%, #f4ede2 100%)"
    app_bg = "#fbf8f3"
    text_color = "#1e293b"
    subtext_color = "#64748b"
    card_bg = "#ffffff"
    card_border = "#e2d9cd"
    quote_bg = "rgba(245, 158, 11, 0.12)"
    quote_border = "#d97706"
    metric_bg = "#ece5da"
    metric_text = "#334155"
    sidebar_bg = "#f5eee4"
    hero_title_color = "#2d5a43"

# Inject Dynamic CSS Styling
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    .stApp {{
        background: {bg_gradient} !important;
        color: {text_color} !important;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }}
    
    [data-testid="stSidebar"] {{
        background-color: {sidebar_bg} !important;
    }}
    
    .sloth-header {{
        font-family: 'Fredoka', cursive;
        font-size: 2.7rem;
        color: {hero_title_color};
        margin-bottom: 2px;
        display: flex;
        align-items: center;
        gap: 12px;
    }}
    
    .sloth-subtitle {{
        font-size: 1.1rem;
        color: {subtext_color};
        margin-bottom: 24px;
        line-height: 1.5;
    }}
    
    .traffic-card {{
        padding: 22px 26px;
        border-radius: 16px;
        margin-bottom: 24px;
        backdrop-filter: blur(8px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
        transition: transform 0.2s ease;
    }}
    
    .traffic-card:hover {{
        transform: translateY(-2px);
    }}
    
    .card-green {{
        background: rgba(16, 185, 129, 0.16);
        border: 1px solid rgba(16, 185, 129, 0.35);
        border-left: 8px solid #10b981;
    }}
    
    .card-yellow {{
        background: rgba(245, 158, 11, 0.16);
        border: 1px solid rgba(245, 158, 11, 0.35);
        border-left: 8px solid #f59e0b;
    }}
    
    .card-red {{
        background: rgba(239, 68, 68, 0.16);
        border: 1px solid rgba(239, 68, 68, 0.35);
        border-left: 8px solid #ef4444;
    }}
    
    .summary-card {{
        background: {card_bg};
        border: 1px solid {card_border};
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 24px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
    }}
    
    .fact-tag {{
        background: #2563eb;
        color: #ffffff !important;
        padding: 4px 11px;
        border-radius: 8px;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        margin-right: 10px;
        display: inline-block;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
    }}
    
    .outcome-tag {{
        background: #059669;
        color: #ffffff !important;
        padding: 4px 11px;
        border-radius: 8px;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        margin-right: 10px;
        display: inline-block;
        box-shadow: 0 2px 8px rgba(5, 150, 105, 0.3);
    }}
    
    .sloth-quote {{
        background: {quote_bg};
        border-left: 5px solid {quote_border};
        padding: 16px 20px;
        border-radius: 0 14px 14px 0;
        font-style: italic;
        margin-bottom: 24px;
        color: {text_color};
        line-height: 1.6;
    }}
    
    .reply-card {{
        background: {card_bg};
        border: 1px solid {card_border};
        border-radius: 14px;
        padding: 18px;
        height: 100%;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }}
    
    .reply-card:hover {{
        border-color: #3b82f6;
        transform: translateY(-2px);
    }}
    
    .energy-metric {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: {metric_bg};
        color: {metric_text};
        padding: 7px 16px;
        border-radius: 30px;
        font-weight: 700;
        font-size: 0.92rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
    }}
    
    .mascot-box {{
        background: {card_bg};
        border: 1px solid {card_border};
        padding: 20px;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 18px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    }}
    
    .status-dot {{
        height: 10px;
        width: 10px;
        background-color: #10b981;
        border-radius: 50%;
        display: inline-block;
        margin-right: 6px;
        animation: pulse 2s infinite;
    }}
    
    @keyframes pulse {{
        0% {{ transform: scale(0.95); opacity: 0.8; }}
        50% {{ transform: scale(1.15); opacity: 1; }}
        100% {{ transform: scale(0.95); opacity: 0.8; }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar - Settings & Model Control
with st.sidebar:
    st.markdown(
        f"""
        <div class="mascot-box">
            <span style="font-size: 3.6rem;">🦥</span>
            <h3 style="margin: 8px 0 2px 0; font-family: 'Fredoka', cursive; font-size: 1.3rem;">Sloan the Sloth</h3>
            <p style="margin: 0; color: {subtext_color}; font-size: 0.85rem;"><span class="status-dot"></span>Conserving Energy</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("### ⚙️ Sloth Settings")
    st.caption("Open-weight intelligence on demand.")

    provider = st.selectbox(
        "AI Provider",
        ["Groq (Free Cloud LPU - Blazing Fast)", "Ollama (Local - 100% Offline)"],
        index=0,
        help="Groq serves open-weight models for free at lightspeed. Ollama runs them directly on your machine with zero internet.",
    )

    is_groq = "Groq" in provider

    if is_groq:
        api_key = st.text_input(
            "Groq API Key",
            type="password",
            value=os.getenv("GROQ_API_KEY", ""),
            help="Get your free API key at https://console.groq.com",
            placeholder="gsk_...",
        )
        groq_models = get_groq_models(api_key)
        model = st.selectbox(
            "Open-Weight Model",
            groq_models,
            index=0,
            help="Select an active open-weight model hosted on Groq.",
        )
        ollama_url = ""
    else:
        api_key = None
        ollama_url = st.text_input("Ollama Host URL", value="http://localhost:11434")
        model = st.text_input("Local Model Name", value="llama3.1:latest")

    st.divider()

    with st.expander("🌱 Why Open Weights Matter"):
        st.markdown(
            """
            - **Privacy First**: Group chats and work messages contain sensitive private chats. Open-weight models guarantee your data isn't harvested for proprietary AI training.
            - **Zero Cost Forever**: Runs entirely on Groq's generous free tier or free local hardware.
            - **Portability**: Switching from cloud to 100% offline air-gapped local inference requires 0 code changes.
            """
        )

# Main Application Area Header
with col_header_left:
    st.markdown('<div class="sloth-header">🦥 SlothDigest</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="sloth-subtitle">Channel your inner sloth. Let open-weight AI digest noisy group chats into a 2-line summary and 1-click canned replies.</div>',
        unsafe_allow_html=True,
    )

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
                    <h3 style="margin: 0; font-size: 1.45rem; font-family: 'Fredoka', cursive;">{badge_icon} {res.urgency_title}</h3>
                    <p style="margin: 8px 0 0 0; font-size: 1.08rem; line-height: 1.4;">{res.urgency_verdict}</p>
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
            <p style="margin: 0 0 16px 0; font-size: 1.12rem; line-height: 1.6;">
                <span class="fact-tag">THE FACTS</span> {res.summary_line_1}
            </p>
            <p style="margin: 0; font-size: 1.12rem; line-height: 1.6;">
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
                    <h4 style="margin: 0 0 4px 0; font-size: 1.05rem;">{reply.title}</h4>
                    <p style="font-size: 0.85rem; color: {subtext_color}; margin-bottom: 12px;">{reply.vibe}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.code(reply.response, language=None)
