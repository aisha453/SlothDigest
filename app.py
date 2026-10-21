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

    # 1. Check direct keys in normalized dict
    for k in ["summaryline1", "summary1", "line1", "facts", "thefacts", "whathappened"]:
        if clean.get(k) and isinstance(clean[k], str):
            s1 = clean[k]
            break
    for k in ["summaryline2", "summary2", "line2", "consensus", "theconsensus", "outcome"]:
        if clean.get(k) and isinstance(clean[k], str):
            s2 = clean[k]
            break

    # 2. Check for two_line_summary / summary / tldr container
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
    """Bulletproof parser that maps any casing and guarantees valid, clean SlothDigestResult."""
    clean = {}
    for k, v in raw_json.items():
        norm_k = re.sub(r"[^a-zA-Z0-9]", "", str(k)).lower()
        clean[norm_k] = v

    # 1. Urgency Level
    urg = str(clean.get("urgencylevel") or clean.get("urgency") or "GREEN").upper()
    if "RED" in urg:
        urgency_level = "RED"
    elif "YELLOW" in urg:
        urgency_level = "YELLOW"
    else:
        urgency_level = "GREEN"

    # 2. Urgency Title
    default_titles = {
        "GREEN": "Safe to Hibernate 🦥",
        "YELLOW": "Skim When Bored 🥱",
        "RED": "Action Required 🚨",
    }
    urgency_title = clean.get("urgencytitle") or clean.get("title") or default_titles[urgency_level]

    # 3. Urgency Verdict
    urgency_verdict = (
        clean.get("urgencyverdict")
        or clean.get("verdict")
        or clean.get("reason")
        or "No immediate action required. You can safely conserve your energy."
    )

    # 4. Energy Saved
    energy_saved = (
        clean.get("energysaved")
        or clean.get("timesaved")
        or "Saved: ~15 mins of reading & mental fatigue"
    )

    # 5. Extract Summary Lines
    s1, s2 = extract_summary(clean, raw_json)

    # 6. Sloth Take
    sloth_take = (
        clean.get("slothtake")
        or clean.get("take")
        or clean.get("wisdom")
        or clean.get("quote")
        or "Humans spend remarkable energy debating things that resolve on their own."
    )

    # 7. Canned Replies
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

# Custom Styling for Sloth Vibe (Works seamlessly in Dark and Light mode)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@400;600&family=Nunito:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Nunito', sans-serif;
    }
    
    .sloth-header {
        font-family: 'Fredoka', cursive;
        font-size: 2.4rem;
        margin-bottom: 0px;
    }
    
    .sloth-subtitle {
        font-size: 1.05rem;
        opacity: 0.85;
        margin-bottom: 20px;
    }
    
    .traffic-card {
        padding: 18px 24px;
        border-radius: 14px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }
    
    .card-green {
        background-color: rgba(16, 185, 129, 0.15);
        border-left: 6px solid #10b981;
    }
    
    .card-yellow {
        background-color: rgba(245, 158, 11, 0.15);
        border-left: 6px solid #f59e0b;
    }
    
    .card-red {
        background-color: rgba(239, 68, 68, 0.15);
        border-left: 6px solid #ef4444;
    }
    
    .summary-card {
        background: rgba(148, 163, 184, 0.08);
        border: 1px solid rgba(148, 163, 184, 0.25);
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 20px;
    }
    
    .fact-tag {
        background: #2563eb;
        color: white !important;
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 700;
        margin-right: 8px;
        display: inline-block;
    }
    
    .outcome-tag {
        background: #059669;
        color: white !important;
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 700;
        margin-right: 8px;
        display: inline-block;
    }
    
    .sloth-quote {
        background: rgba(217, 119, 6, 0.1);
        border-left: 4px solid #d97706;
        padding: 14px 18px;
        border-radius: 0 10px 10px 0;
        font-style: italic;
        margin-bottom: 20px;
    }
    
    .reply-card {
        background: rgba(148, 163, 184, 0.08);
        border: 1px solid rgba(148, 163, 184, 0.25);
        border-radius: 12px;
        padding: 16px;
        height: 100%;
    }
    
    .energy-metric {
        display: inline-block;
        background: rgba(148, 163, 184, 0.15);
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize Session State
if "chat_input" not in st.session_state:
    st.session_state.chat_input = ""
if "digest_result" not in st.session_state:
    st.session_state.digest_result = None

# Sidebar - Settings & Model Control
with st.sidebar:
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%); padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 15px;">
            <span style="font-size: 3.5rem;">🦥</span>
            <p style="margin: 8px 0 0 0; font-weight: 700; color: #1e293b; font-size: 1rem;">Sloan the Sloth</p>
            <p style="margin: 0; color: #64748b; font-size: 0.8rem;">Chief Energy Conservation Officer</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("### 🦥 Sloth Settings")
    st.caption("Powered by Open-Source AI. Conserve human energy.")

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
            - **Privacy First**: Group chats and work messages contain sensitive private chats. Open-weight models (via Groq or local Ollama) guarantee your data isn't harvested for proprietary AI training.
            - **Zero Cost Forever**: Runs entirely on Groq's generous free tier or free local hardware.
            - **Portability**: Switching from cloud to 100% offline air-gapped local inference requires 0 code changes.
            """
        )

# Main Application Area
st.markdown('<h1 class="sloth-header">🦥 SlothDigest</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="sloth-subtitle">For International Sloth Day: Conserve your energy. Turn noisy group chats into a 2-line summary and copy-paste ready replies.</p>',
    unsafe_allow_html=True,
)

# Preset Quick-Load Buttons
st.markdown("**Too lazy to type? Test with one-click presets:**")
col_p1, col_p2, col_p3, col_clear = st.columns([1.2, 1.3, 1.3, 0.8])

with col_p1:
    if st.button("🍕 47-Msg Dinner Debate", use_container_width=True):
        st.session_state.chat_input = SAMPLE_PRESETS["🍕 Dinner Debate (Green - 47 Messages)"]["text"]
        st.session_state.digest_result = None

with col_p2:
    if st.button("🚨 Friday Slack False Alarm", use_container_width=True):
        st.session_state.chat_input = SAMPLE_PRESETS["🚨 Friday 4:45 PM Slack Emergency (Yellow/Green)"]["text"]
        st.session_state.digest_result = None

with col_p3:
    if st.button("🏡 Neighborhood HOA Drama", use_container_width=True):
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
    height=200,
    placeholder="e.g. [5:30 PM] Bob: Hey team, did anyone see the ticket? [5:32 PM] Alice: Looking into it...",
)

# Action Button
col_btn, col_info = st.columns([1, 2])
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
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <div>
                    <h3 style="margin: 0; font-size: 1.4rem;">{badge_icon} {res.urgency_title}</h3>
                    <p style="margin: 8px 0 0 0; font-size: 1.05rem;">{res.urgency_verdict}</p>
                </div>
                <div style="margin-top: 8px;">
                    <span class="energy-metric">⚡ {res.energy_saved}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. The 2-Line Sleepy Summary (Clean, dark-mode & light-mode responsive)
    st.markdown("### 📋 The 2-Line Sleepy Summary")
    st.markdown(
        f"""
        <div class="summary-card">
            <p style="margin: 0 0 12px 0; font-size: 1.1rem; line-height: 1.5;">
                <span class="fact-tag">THE FACTS</span> {res.summary_line_1}
            </p>
            <p style="margin: 0; font-size: 1.1rem; line-height: 1.5;">
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
            <strong>🦥 Sloan's Reflection:</strong> "{res.sloth_take}"
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 4. 1-Click Lazy Canned Replies
    st.markdown("### 💤 1-Click Zero-Effort Replies")
    st.caption("Click the copy button on the top right of any code card to send without typing a word:")

    cols = st.columns(len(res.canned_replies))
    for idx, (col, reply) in enumerate(zip(cols, res.canned_replies)):
        with col:
            st.markdown(
                f"""
                <div class="reply-card">
                    <h4 style="margin: 0 0 4px 0;">{reply.title}</h4>
                    <p style="font-size: 0.85rem; opacity: 0.75; margin-bottom: 12px;">{reply.vibe}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.code(reply.response, language=None)
