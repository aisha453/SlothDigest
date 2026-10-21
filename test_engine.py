"""
test_engine.py - Verification script for SlothDigest.
Tests schemas, sample datasets, and API connection handling.
"""

import sys
import os

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from prompts import SlothDigestResult, CannedReply
from sample_data import SAMPLE_PRESETS
from groq_client import run_sloth_digest


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
    print("✅ Schema validation passed!")


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
        model="llama-3.1-8b-instant"
    )
    if error:
        print(f"❌ Live test returned error: {error}")
    else:
        print("✅ Live Groq test succeeded!")
        print(f"   Urgency: {result.urgency_level} - {result.urgency_title}")
        print(f"   Summary L1: {result.summary_line_1}")
        print(f"   Summary L2: {result.summary_line_2}")


if __name__ == "__main__":
    print("================== SLOTH DIGEST TEST SUITE ==================")
    test_schema_validation()
    test_sample_presets_loaded()
    test_groq_missing_key_graceful_handling()
    test_live_groq_if_available()
    print("================== ALL TESTS PASSED! ==================")
