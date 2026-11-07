"""
test_engine.py - Verification script for SlothDigest.
Tests schemas, sample datasets, robust JSON parsing, Ollama endpoints, and HTML/SVG markdown rendering cleanliness.
"""

import sys
import os

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from prompts import SlothDigestResult, CannedReply
from sample_data import SAMPLE_PRESETS
from groq_client import run_sloth_digest, parse_sloth_result, _normalize_data


def test_schema_validation():
    print("Testing schema validation...")
    mock_data = {
        "urgency_level": "GREEN",
        "urgency_title": "Safe to Hibernate 🦥",
        "urgency_verdict": "Dinner was decided without you. Keep sleeping.",
        "energy_saved": "Saved: 14 mins & 30 calories",
        "summary_line_1": "The group debated Thai, sushi, and burgers for 25 minutes.",
        "summary_line_2": "Consensus was reached: Tacos at Los Amigos at 8 PM.",
        "sloth_take": "Humans spend 45 minutes picking a restaurant when tacos were the answer all along.",
        "canned_replies": [
            {"title": "The Minimalist", "response": "Sounds great! 👍", "vibe": "Zero effort agreement"},
            {"title": "The Graceful Delayer", "response": "See you at 8!", "vibe": "Short confirmation"},
            {"title": "The Diplomatic Delegator", "response": "Thanks Dave for booking!", "vibe": "Credit to someone else"}
        ]
    }
    result = SlothDigestResult.model_validate(mock_data)
    assert result.urgency_level == "GREEN"
    assert len(result.canned_replies) == 3

    # Test parse_sloth_result with schema variations (two_line_summary list, alternate field names)
    variant_data = {
        "urgency": "yellow",
        "title": "Skim When Bored 🥱",
        "verdict": "Minor thread activity.",
        "timesaved": "Saved 10 mins",
        "two_line_summary": [
            "1. Team discussed server alert.",
            "2. Auto-resolved by cron job."
        ],
        "wisdom": "Never rush to fix what fixes itself.",
        "replies": [
            {"title": "Short", "reply": "Acknowledged.", "reason": "No typing"}
        ]
    }
    parsed = parse_sloth_result(variant_data)
    assert parsed.urgency_level == "YELLOW"
    assert parsed.urgency_title == "Skim When Bored 🥱"
    assert parsed.summary_line_1 == "Team discussed server alert."
    assert parsed.summary_line_2 == "Auto-resolved by cron job."
    assert len(parsed.canned_replies) == 3  # padded with defaults
    assert parsed.canned_replies[0].response == "Acknowledged."

    # Test _normalize_data backwards compatibility
    norm = _normalize_data(variant_data)
    assert norm["urgency_level"] == "YELLOW"
    assert "summary_line_1" in norm

    print("✅ Schema validation and robust parsing passed!")


def test_sample_presets_loaded():
    print("Testing sample presets...")
    assert len(SAMPLE_PRESETS) >= 3
    for name, data in SAMPLE_PRESETS.items():
        assert "text" in data and len(data["text"]) > 50
    print(f"✅ Loaded {len(SAMPLE_PRESETS)} sample presets successfully!")


def test_groq_missing_key_graceful_handling():
    print("Testing graceful error handling without API key...")
    result, error = run_sloth_digest(
        messages_text="Hello world",
        api_key="",
        provider="Groq",
    )
    assert result is None
    assert "Groq API Key is missing" in error
    print("✅ Missing key handled gracefully without crashing!")


def test_ollama_fallback_url_handling():
    print("Testing Ollama fallback endpoint and empty URL handling...")
    # Empty or None ollama_url should default to localhost:11434 without an UnsupportedProtocol crash
    result, error = run_sloth_digest(
        messages_text="Hello local model",
        provider="Ollama (Local)",
        ollama_url="",
    )
    assert result is None
    assert error is not None
    # Must not crash with 'Request URL is missing an http:// or https:// protocol'
    assert "missing an 'http://'" not in error.lower()
    print("✅ Ollama fallback URL resolved safely to local default!")


def test_html_rendering_cleanliness():
    print("Testing HTML/SVG markdown rendering cleanliness across UI states in app.py...")
    from streamlit.testing.v1 import AppTest
    app_path = os.path.join(os.path.dirname(__file__), "app.py")
    at = AppTest.from_file(app_path)
    at.run()

    # 1. Day Mode Initial State
    for i, m in enumerate(at.markdown):
        indented = [l for l in m.value.splitlines() if l.startswith("    ") or l.startswith("\t")]
        assert len(indented) == 0, f"Day mode markdown block {i} contains indented lines: {indented[:2]}"

    # 2. Night Mode
    at.session_state.theme_mode = "🌙"
    at.run()
    for i, m in enumerate(at.markdown):
        indented = [l for l in m.value.splitlines() if l.startswith("    ") or l.startswith("\t")]
        assert len(indented) == 0, f"Night mode markdown block {i} contains indented lines: {indented[:2]}"

    # 3. Dynamic Results Card Rendering with Special Characters
    mock_res = SlothDigestResult(
        urgency_level="GREEN",
        urgency_title="Safe to Hibernate <🦥>",
        urgency_verdict="CPU is < 15% & memory > 80%. No action needed.",
        energy_saved="Saved: <30 mins>",
        summary_line_1="Discussion on <ticket #104> concluded.",
        summary_line_2="Consensus reached without user intervention.",
        sloth_take="Why stress over <drama>?",
        canned_replies=[
            CannedReply(title="<The Minimalist>", response="ok", vibe="<zero effort>"),
            CannedReply(title="The Graceful Delayer", response="later", vibe="polite delay"),
            CannedReply(title="The Diplomatic Delegator", response="you lead", vibe="delegated"),
        ]
    )
    at.session_state.digest_result = mock_res
    at.run()

    all_markdown = "\n".join(m.value for m in at.markdown)
    for i, m in enumerate(at.markdown):
        indented = [l for l in m.value.splitlines() if l.startswith("    ") or l.startswith("\t")]
        assert len(indented) == 0, f"Result card markdown block {i} contains indented lines: {indented[:2]}"

    # Verify that dynamic content with < > was properly escaped to &lt; &gt; and not swallowed as HTML tags
    assert "&lt;ticket #104&gt;" in all_markdown, "Dynamic text with brackets was swallowed instead of escaped!"
    assert "&lt;The Minimalist&gt;" in all_markdown, "Reply title brackets were swallowed instead of escaped!"
    print("✅ All HTML/SVG markdown blocks verified across Day, Night, and Result states with 0 code-block triggers and proper escaping!")


def test_live_groq_if_available():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("ℹ️ GROQ_API_KEY not found in environment. Skipping live API test. (Add key to .env to test live).")
        return

    print("Testing live Groq API with sample preset...")
    sample_text = SAMPLE_PRESETS["🍕 Dinner Debate (Green - 47 Messages)"]["text"]
    result, error = run_sloth_digest(
        messages_text=sample_text,
        api_key=api_key,
        provider="Groq",
        model="openai/gpt-oss-20b"
    )
    assert not error, f"Live Groq test returned error: {error}"
    assert result is not None, "Live Groq test returned None result"
    assert result.urgency_level in ["GREEN", "YELLOW", "RED"]
    print("✅ Live Groq test succeeded!")
    print(f"   Urgency: {result.urgency_level} - {result.urgency_title}")
    print(f"   Summary L1: {result.summary_line_1}")
    print(f"   Summary L2: {result.summary_line_2}")


if __name__ == "__main__":
    print("================== SLOTH DIGEST TEST SUITE ==================")
    test_schema_validation()
    test_sample_presets_loaded()
    test_groq_missing_key_graceful_handling()
    test_ollama_fallback_url_handling()
    test_html_rendering_cleanliness()
    test_live_groq_if_available()
    print("================== ALL TESTS PASSED! ==================")
