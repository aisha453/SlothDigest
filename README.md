# 🦥 SlothDigest

> **"Channel your inner sloth and let AI do the work so you don't have to."**  
> *Built for the DEV.to **"Slow and Steady" (International Sloth Day)** Community Challenge.*

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Powered by Groq](https://img.shields.io/badge/Powered%20by-Groq%20LPU-f55036.svg)](https://groq.com)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit%20Cloud-FF4B4B.svg)](https://slothdigest.streamlit.app)
[![Ollama Ready](https://img.shields.io/badge/Local%20Inference-Ollama%20Compatible-black.svg)](https://ollama.ai)

---

## 🌟 What is SlothDigest?

Sloths move at their own pace, sleep 15 to 20 hours a day, and fiercely conserve their calories. Humans, on the other hand, spend hours sifting through 200-message WhatsApp group chats, rambling Slack threads, and petty email chains just to see if they actually need to do anything.

**SlothDigest** fixes that. Powered by open-weight AI models hosted on Groq (or run locally on Ollama), it transforms raw message chaos into:

1. **🟢 Urgency Traffic Light**: 
   - `GREEN`: Safe to hibernate. Nobody asked you anything.
   - `YELLOW`: Skim when bored or stretching.
   - `RED`: Real action required. Wake up!
2. **📋 The 2-Line Sleepy Summary**: 
   - Line 1: What actually happened (facts only, drama stripped away).
   - Line 2: The bottom line / current consensus.
3. **💤 1-Click Zero-Brain Replies**: 
   - Three ready-to-send replies (*The Minimalist*, *The Graceful Delayer*, *The Diplomatic Delegator*) with native 1-click clipboard copy buttons.
4. **⚡ Energy Saved Meter**: Calculates how much human time and mental stamina was spared.

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10 or higher.
- A free Groq API key from [console.groq.com](https://console.groq.com) (or a local [Ollama](https://ollama.ai) instance).

### 2. Installation
Clone or navigate to the project directory and install the lightweight dependencies:
```bash
cd sloth-digest
pip install -r requirements.txt
```

### 3. Configure API Key
Create a `.env` file or export your key:
```bash
cp .env.example .env
# Edit .env and paste your Groq API key:
# GROQ_API_KEY=gsk_...
```
*(You can also paste the API key directly into the application sidebar at runtime).*

### 4. Run the App
Launch the Streamlit web application:
```bash
streamlit run app.py
```
Open your browser to `http://localhost:8501`.

---

## 🧪 Testing with Built-In Presets
SlothDigest includes 3 built-in presets so you can evaluate the experience without copying real private messages:
- **🍕 47-Msg Dinner Debate**: 5 friends arguing about where to eat for 45 minutes until deciding on tacos.
- **🚨 Friday Slack False Alarm**: Engineering panic over an automated memory alert that resolved on its own.
- **🏡 Neighborhood HOA Drama**: Petty neighborhood dispute over an illuminated garden gnome named Barnaby.

---

## 🦥 Dual-Engine Architecture: Cloud Speed & Local Privacy

SlothDigest is architected to switch seamlessly between cloud and local open-weight inference:

```
                      ┌────────────────────────────────┐
                      │    Sloth UI (Streamlit Web)    │
                      └───────────────┬────────────────┘
                                      │ 
                                      ▼
               ┌──────────────────────────────────────────────┐
               │              LLM Provider Switch             │
               │   (Groq API for speed / Ollama for offline)  │
               └──────────────┬───────────────────────────────┘
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
       [ Groq Cloud LPU ]           [ Local Ollama ]
       • Llama 3.3 70B (Versatile)  • Llama 3.1 8B / Qwen 2.5
       • Llama 3.1 8B (Instant)     • 100% Offline & Private
       • Free API tier              • Air-gapped on laptop
```

---

<details>
<summary>📝 <strong>Click here to view the pre-written DEV.to Submission Post Draft</strong></summary>

### DEV.to Submission Post (Ready to Copy & Publish!)

**Title:** SlothDigest 🦥: Rewarding Laziness with Open-Weight AI  
**Tags:** `#openweightai`, `#devchallenge`, `#groq`, `#ai`, `#opensource`

---

#### The Inspiration
Tomorrow is **International Sloth Day**, and our favorite DEV moderator [Sloan the Sloth](https://dev.to/sloan) understands something fundamental: **energy conservation is an art form**.

Yet everyday, developers and humans burn mental stamina reading 50-message Slack threads, chaotic family group chats, or petty email chains, asking the same exhausting question: *"Do I actually need to care about this?"*

For the **Slow and Steady** challenge, I built something that honors Sloan by doing the work so you don't have to: **SlothDigest**.

---

#### Live Demo & Repository
- 🌐 **Live Web App**: [https://slothdigest.streamlit.app](https://slothdigest.streamlit.app)
- 💻 **GitHub Repository**: [https://github.com/aisha453/SlothDigest](https://github.com/aisha453/SlothDigest)

---

#### What I Built
**SlothDigest** takes any messy dump of unread messages and gives you:
1. **🟢 The Urgency Traffic Light**: Tells you in plain English if you can safely go back to sleep (🟢 Green), skim it later (🟡 Yellow), or if you actually need to wake up and act (🔴 Red).
2. **📋 The 2-Line Sleepy Summary**: Strips away every bit of drama, emotional venting, and fluff to give you:
   - Line 1: What happened (pure facts).
   - Line 2: The bottom line / consensus.
3. **💤 1-Click Zero-Brain Canned Replies**: Three pre-written responses you can copy with one click:
   - *The Minimalist* ("Sounds good! 👍")
   - *The Graceful Delayer* ("Reviewing this later this afternoon, thanks!")
   - *The Diplomatic Delegator* ("Thanks for handling this, happy to follow your lead!")
4. **⚡ Energy Saved Meter**: Calculates how much human time and mental stamina was spared.
5. **☀️/🌙 Day & Night Themes**: Toggle between high-contrast Day Mode and deep slate Night Mode with a single click.

---

#### Why Open Innovation Matters
The challenge asks: *Tell us where your open-based approach worked better than a closed one.* Here is why open-weight models are the beating heart of SlothDigest:

1. **Absolute Privacy for Personal Messages**:
   Group chats and internal work threads contain private jokes, confidential roadmap discussions, or family gossip. Sending this raw text into proprietary closed-API black boxes means risking your data being used to train future corporate models. With open-weight models, you retain full sovereignty.
2. **True Local Portability with Ollama**:
   Because SlothDigest is built on open standards, you can switch from Groq's cloud to a 100% offline, air-gapped **Ollama** model running locally on your laptop with zero code changes. It works on an airplane or cabin in the woods with zero internet connection.
3. **Zero Cost Forever**:
   By taking advantage of Groq's ultra-fast inference on open weights, anyone can clone this project, run it for $0, and never worry about unexpected credit card bills or API subscription paywalls.

---

#### Tech Stack
- **AI Engine**: Open-weight intelligence on Groq LPU cloud; fully compatible with local `llama3.1` via Ollama.
- **Backend / Schema**: Python 3.11 + Pydantic v2 for structured JSON enforcement.
- **Frontend**: Streamlit with custom Day/Night styling and clipboard integration.

---

#### Conclusion
You don't need a 200-page agentic orchestration framework to solve everyday burnout. Sometimes, all you need is a sleepy open-weight model that reads the drama and tells you: *"Nothing needs your attention. Go back to sleep."*

Happy International Sloth Day! 🦥

</details>

---

## 📄 License
MIT License. Built with ❤️ for the open-source community.
