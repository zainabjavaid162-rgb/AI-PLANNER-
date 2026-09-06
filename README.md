

Readme · MD
🌸 Bloom Planner
A girly, fully editable, AI-powered weekly calendar app — built with Streamlit (the interface) and Groq (the AI that can auto-generate your schedule).

What it does
Editable weekly grid — click any cell in the table and type. Add or remove time slots from the sidebar.
Per-day notes — a little text box under each day for anything extra.
Themes — 5 built-in color palettes (Cherry Blossom, Lavender Dream, Peach Fizz, Rose Gold, Mint Sugar).
Fonts — Poppins, Quicksand, Comfortaa, Playfair Display, Dancing Script, Pacifico.
Wallpapers — built-in soft patterns, or upload your own image as a background.
AI auto-scheduling — describe your courses, goals, and fixed commitments in plain English, and it will generate a full week for you using Groq's LLMs (no manual typing required).
Save/load/export — your calendar and look are saved to local JSON files so they persist between runs, and you can export to CSV or JSON any time.
Setup
Install Python 3.9+ if you don't already have it.
Install dependencies (from this folder):
bash
   pip install -r requirements.txt
Get a free Groq API key (only needed for the AI auto-generate feature):
Go to https://console.groq.com
Sign up, then create an API key.
You'll paste this into the app's sidebar under "🤖 AI" — it's never saved to disk, only used for that session. (You can also set it once as an environment variable GROQ_API_KEY so it's pre-filled.)
Run the app:
bash
   streamlit run app.py
It'll open automatically in your browser at http://localhost:8501.

Using it
Edit manually: click any cell in the weekly table and type. Click "💾 Save everything" to write it to disk.
Change your look: sidebar → "🎨 Look" tab. Pick a theme, font, and wallpaper. Click "Save look as default" to keep it next time you open the app.
Let AI build your week: sidebar → "🤖 AI" tab. Paste your Groq API key, describe your week in the text box, hit "✨ Generate my calendar with AI". It fills in the whole grid for you — you can still edit anything afterward.
Add/remove time slots: sidebar → "💾 Data" tab.
Export: same tab, download as CSV or JSON any time.
Notes
Groq periodically updates which models are available. If a model in the dropdown doesn't work, click "🔄 Refresh available models" to pull the current list from your account.
Everything is stored locally in bloom_calendar_data.json and bloom_calendar_settings.json in this folder — nothing is sent anywhere except your prompt text to Groq when you use the AI feature.

