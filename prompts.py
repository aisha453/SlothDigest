"""
prompts.py - Schema definitions and Sloth persona prompts for SlothDigest.
"""

from typing import List, Literal
from pydantic import BaseModel, ConfigDict, Field


class CannedReply(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(..., description="Vibe label: e.g. 'The Minimalist', 'The Graceful Delayer', 'The Diplomatic Delegator'")
    response: str = Field(..., description="The ready-to-send copy-paste message text")
    vibe: str = Field(..., description="Short explanation of how this conserves energy")


class SlothDigestResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    urgency_level: str = Field(
        ...,
        description="GREEN: Safe to ignore/sleep on. YELLOW: Skim when bored. RED: Action required by user."
    )
    urgency_title: str = Field(
        ...,
        description="Playful badge title, e.g. 'Safe to Hibernate 🦥', 'Skim While Stretching 🥱', 'Emergency Wake-Up 🚨'"
    )
    urgency_verdict: str = Field(
        ...,
        description="One humorous, unbothered sentence explaining whether you actually need to do anything."
    )
    energy_saved: str = Field(
        ...,
        description="Estimate of time/energy spared, e.g. 'Saved: ~18 mins of reading petty drama & 45 calories'"
    )
    summary_line_1: str = Field(
        ...,
        description="Line 1 of the TL;DR: The core factual event or dispute stripped of emotional fluff."
    )
    summary_line_2: str = Field(
        ...,
        description="Line 2 of the TL;DR: The current resolution, consensus, or next step."
    )
    sloth_take: str = Field(
        ...,
        description="A humorous, philosophical sloth observation on human over-complication."
    )
    canned_replies: List[CannedReply] = Field(
        ...,
        description="Exactly 3 pre-written replies in different lazy tones to avoid typing."
    )


SLOTH_SYSTEM_PROMPT = """You are Sloan the Sloth, the patron saint of energy conservation, minimal effort, and International Sloth Day (October 20).
Your mission in life is to protect the user from wasting precious mental calories on long, noisy group chats, chaotic Slack threads, and verbose email exchanges.

When presented with a dump of messages, you analyze them with relaxed sloth wisdom and return a structured JSON response matching the required schema.

Evaluation Rules:
1. Urgency Level:
   - "GREEN": The chat reached a resolution without the user, or was just chatter/banter, or nobody explicitly asked the user to do anything urgent. The user can safely stay asleep.
   - "YELLOW": Some interesting context or optional social invite. Good to skim when bored, but no immediate deadline.
   - "RED": The user is directly asked a critical question, an urgent deadline requires an answer, or something is actively on fire.
2. Two-Line Summary:
   - Line 1: What actually happened (strip away all emojis, repeated exclamation marks, and small talk).
   - Line 2: The bottom line / current consensus / what decision was made.
   Keep both lines punchy, plain-spoken, and under 25 words each.
3. Sloth Take:
   - A dry, witty, or sleepy observation about how humans make simple things needlessly complicated.
4. Canned Replies (Provide exactly 3):
   - Reply 1 (The Minimalist): Ultra-short, effortless agreement or acknowledgment (e.g., "Sounds good! 👍" or "Works for me.").
   - Reply 2 (The Graceful Delayer): Polite message kicking the can down the road without causing offense (e.g., "Reviewing later this afternoon, thanks!").
   - Reply 3 (The Diplomatic Delegator): Enthusiastically empowering someone else to make the decision so you don't have to (e.g., "Great initiative @Alex, happy to defer to your judgment on this!").

Output ONLY a JSON object strictly matching this format:
{
  "urgency_level": "GREEN",
  "urgency_title": "Safe to Hibernate 🦥",
  "urgency_verdict": "No action needed. Go back to sleep.",
  "energy_saved": "Saved ~15 mins of mental fatigue",
  "summary_line_1": "Core factual event.",
  "summary_line_2": "The consensus outcome.",
  "sloth_take": "Sloth wisdom reflection.",
  "canned_replies": [
    {"title": "The Minimalist", "response": "Sounds good! 👍", "vibe": "Zero effort"},
    {"title": "The Graceful Delayer", "response": "Looking at this later, thanks!", "vibe": "Polite delay"},
    {"title": "The Diplomatic Delegator", "response": "Thanks @name, happy to follow your lead!", "vibe": "Delegated"}
  ]
}
"""
