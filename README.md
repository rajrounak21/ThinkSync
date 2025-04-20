# 🤖 ThinkSync — AI Chatbot Powered by Gemini & Flask

ThinkSync is a modern, session-based AI chatbot built using **Flask**, **Google Gemini Flash**, and **MySQL**. It supports user authentication, Markdown-rich responses, and a beautiful chat interface designed for real-time conversations and persistent history.

---

## ✨ Features

- 🔐 User authentication (register & login)
- 💬 Conversational chat UI with typing effect
- 🧠 Powered by Google Gemini (Generative AI)
- 📜 Markdown rendering (supports code, lists, tables, etc.)
- 🗂️ Session-based chat history stored in MySQL
- 🎨 Responsive frontend built with minimal JavaScript and clean HTML/CSS
- 🔑 Environment-based secret management via `.env`

---

## 📦 Tech Stack

- **Backend**: Python (Flask), Google Generative AI SDK
- **Frontend**: HTML5, CSS3, Jinja2, Marked.js
- **Database**: MySQL
- **Security**: Hashed passwords, session management

---
🔑 How to Get Your Google Gemini API Key
To use ThinkSync, you need access to the Google Generative AI API (Gemini). Here's how you can get your API key:

🧭 Step-by-Step Guide
Go to Google AI Studio
Visit https://makersuite.google.com/app

Sign In with Your Google Account
Use a Google account to access the platform.

Enable the Gemini API
You’ll be prompted to agree to terms and enable API access for your account.

Generate an API Key

Go to this site : https://makersuite.google.com/app/apikey

Click "Create API key"

Copy the key shown

Paste it in your .env file
GEMINI_API_KEY=your-copied-api-key


⚠️ Important: Do not share this API key publicly. Treat it like a password.


## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ThinkSync.git
cd ThinkSync
