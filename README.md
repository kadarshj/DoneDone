# DoneDone 🧠✅

**DoneDone** is a multi-agent personal assistant system that helps you get things *actually* done — not just planned.  
It listens to your day, understands your intent, and turns your notes and voice logs into meaningful actions.

Built by engineers, for anyone who wants their life and work handled without friction.

---

## 🧩 Inspiration

I always wrote in journals and made to-do lists, but rarely tracked what got done. I wanted a personal assistant that didn't just help plan, but helped finish. As engineers, we love building systems — so we made one for our own messy lives.

---

## 🚀 What It Does

DoneDone uses smart agents to process your daily inputs (voice or text) and take real actions:
- Tracks health, mood, tasks, shopping, and social connections  
- Works in both personal and work modes  
- Sends a daily email that wraps up your day, automatically  

---

## 🔧 How We Built It

- **LLM**: Gemini Flash 2.5 for core agent reasoning  
- **Voice-to-Text**: Whisper for transcribing spoken inputs  
- **Agent Orchestration**: Google Agent SDK running on cloud servers  
- **Prompt Engineering**: Custom-designed prompts for each agent  
- **Integrations**: Google Calendar, Sheets, Drive, and Gmail APIs  
- **UI**: Simple frontend to upload logs and receive DoneDone Reports  
- **CoordinatorAgent**: Reads shared memory and compiles final summary email  

---

## ⚠️ Challenges

- Designing agents that are flexible yet personalized  
- Managing scoped personal data across agents  
- Handling multi-modal input efficiently  
- Mapping intents to the right agents in real time  
- Keeping all agent outputs context-aware for a unified report  
- Avoiding hallucinations from LLMs  
- Building clean data flow and inter-agent coordination  

---

## ✅ What We're Proud Of

- End-to-end working multi-agent system  
- Seamless switch between personal and work life  
- Mood-based suggestions and social nudges  
- Email report that genuinely wraps up your day  

---

## 📚 What We Learned

- Prompt quality and memory management are critical  
- Users want outcomes, not options  
- Simplicity in UX wins over feature overload  
- You can automate a lot with structured thinking and tight flow  

---

## 🔮 What’s Next

- Real-time socket-based voice journaling  
- Feedback loop from users to improve agents  
- More work-focused agents (email replies, meeting scheduler)  
- Integrations: Notion, WhatsApp, Slack  
- Voice-first UI for that human assistant feel  
- Observability with Traceloop and Grafana  
- Agent governance to track token usage, memory, latency  
- Open-source Agent Starter Kit for devs  

---

## 🛠 Setup Instructions (Coming Soon)

We're currently packaging the architecture and flow into an open-source release.  
Stay tuned — or star the repo to follow along.

---

## 👥 Team

Built with love and frustration by engineers who wanted to feel that satisfaction of saying:  
> “It’s DoneDone.”

<img width="472" alt="image" src="https://github.com/user-attachments/assets/694bf0e3-b98c-4431-b52b-e7d6267b59dd" />


---

## 📬 Contact

Open an issue, fork the repo, or reach out if you’d like to build on top of DoneDone.

