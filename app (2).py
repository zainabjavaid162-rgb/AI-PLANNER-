"""
🌸 Bloom Planner — a girly, editable, AI-powered weekly study calendar
Built with Streamlit + Groq.

Run it with:
    streamlit run app.py
"""

import base64
import json
import os
from datetime import datetime

import pandas as pd
import streamlit as st

try:
    from groq import Groq
except ImportError:
    Groq = None


# ----------------------------------------------------------------------------
# Config & constants
# ----------------------------------------------------------------------------

st.set_page_config(page_title="Bloom Planner", page_icon="🌸", layout="wide")

DATA_FILE = "bloom_calendar_data.json"
SETTINGS_FILE = "bloom_calendar_settings.json"

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

DEFAULT_SLOTS = [
    "9:00 – 10:30 AM",
    "10:45 – 11:45 AM",
    "6:00 – 9:00 PM",
    "9:30 – 10:00 PM",
]

THEMES = {
    "Cherry Blossom": {
        "primary": "#e8779f",
        "text": "#7a2947",
        "panel": "#fffaf9",
        "bg_from": "#fdf1f5",
        "bg_to": "#fbe4ec",
    },
    "Lavender Dream": {
        "primary": "#a685e2",
        "text": "#4b2e6f",
        "panel": "#fbf9ff",
        "bg_from": "#f4eeff",
        "bg_to": "#e9defc",
    },
    "Peach Fizz": {
        "primary": "#f2a26b",
        "text": "#7a3f1d",
        "panel": "#fffaf6",
        "bg_from": "#fff2e6",
        "bg_to": "#ffe3cf",
    },
    "Rose Gold": {
        "primary": "#d98a9d",
        "text": "#6d2f3e",
        "panel": "#fff8f7",
        "bg_from": "#fbeae7",
        "bg_to": "#f4d9d9",
    },
    "Mint Sugar": {
        "primary": "#79c2a2",
        "text": "#1f5c46",
        "panel": "#f7fffb",
        "bg_from": "#e9fbf3",
        "bg_to": "#d3f3e4",
    },
}

FONT_STACKS = {
    "Poppins": "'Poppins', sans-serif",
    "Quicksand": "'Quicksand', sans-serif",
    "Comfortaa": "'Comfortaa', sans-serif",
    "Playfair Display": "'Playfair Display', serif",
    "Dancing Script": "'Dancing Script', cursive",
    "Pacifico": "'Pacifico', cursive",
}

WALLPAPER_PATTERNS = {
    "Soft Petals": "radial-gradient(circle at 10% 15%, {bg_to} 0%, transparent 45%), "
                   "radial-gradient(circle at 90% 10%, {bg_to} 0%, transparent 40%), "
                   "radial-gradient(circle at 50% 100%, {bg_to} 0%, transparent 50%)",
    "Diagonal Bloom": "repeating-linear-gradient(135deg, {bg_from} 0px, {bg_from} 40px, "
                       "{bg_to} 40px, {bg_to} 80px)",
    "Dotted Garden": "radial-gradient({bg_to} 2px, transparent 2px)",
    "Plain": "none",
}

GROQ_MODEL_FALLBACKS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
]


# ----------------------------------------------------------------------------
# Persistence helpers
# ----------------------------------------------------------------------------

def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def default_calendar():
    return {
        day: {slot: "" for slot in DEFAULT_SLOTS} for day in DAYS
    }


def calendar_to_df(cal, slots):
    rows = []
    for slot in slots:
        row = {"Time": slot}
        for day in DAYS:
            row[day] = cal.get(day, {}).get(slot, "")
        rows.append(row)
    return pd.DataFrame(rows)


def df_to_calendar(df):
    cal = {day: {} for day in DAYS}
    for _, row in df.iterrows():
        slot = row["Time"]
        for day in DAYS:
            cal[day][slot] = row.get(day, "")
    return cal


# ----------------------------------------------------------------------------
# Session state init
# ----------------------------------------------------------------------------

if "calendar" not in st.session_state:
    st.session_state.calendar = load_json(DATA_FILE, default_calendar())

if "slots" not in st.session_state:
    saved = load_json(DATA_FILE, None)
    if saved:
        # recover slot order from whichever day has the most entries
        any_day = next(iter(saved.values()))
        st.session_state.slots = list(any_day.keys())
    else:
        st.session_state.slots = list(DEFAULT_SLOTS)

if "notes" not in st.session_state:
    st.session_state.notes = load_json(DATA_FILE + ".notes", {day: "" for day in DAYS})

settings = load_json(SETTINGS_FILE, {
    "theme": "Cherry Blossom",
    "font": "Quicksand",
    "wallpaper": "Soft Petals",
    "custom_bg_image": None,
})
for key, val in settings.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ----------------------------------------------------------------------------
# Styling
# ----------------------------------------------------------------------------

def inject_css():
    theme = THEMES[st.session_state.theme]
    font_stack = FONT_STACKS[st.session_state.font]
    pattern_template = WALLPAPER_PATTERNS[st.session_state.wallpaper]
    pattern = pattern_template.format(bg_from=theme["bg_from"], bg_to=theme["bg_to"])

    if st.session_state.get("custom_bg_image"):
        bg_layer = f"url('data:image/png;base64,{st.session_state.custom_bg_image}')"
        bg_size = "background-size: cover; background-position: center;"
    else:
        bg_layer = pattern if pattern != "none" else "none"
        bg_size = "background-size: 26px 26px;" if st.session_state.wallpaper == "Dotted Garden" else ""

    google_fonts = "&family=".join(
        f.replace(" ", "+") for f in FONT_STACKS.keys()
    )

    st.markdown(
        f"""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family={google_fonts}&display=swap" rel="stylesheet">
        <style>
            html, body, [class*="css"] {{
                font-family: {font_stack} !important;
            }}
            .stApp {{
                background-color: {theme['bg_from']};
                background-image: {bg_layer};
                {bg_size}
            }}
            h1, h2, h3 {{
                color: {theme['primary']} !important;
                font-family: {font_stack} !important;
            }}
            p, span, label, .stMarkdown {{
                color: {theme['text']};
            }}
            section[data-testid="stSidebar"] {{
                background-color: {theme['panel']};
                border-right: 2px solid {theme['bg_to']};
            }}
            div[data-testid="stDataEditor"] {{
                border-radius: 16px;
                overflow: hidden;
                border: 1px solid {theme['bg_to']};
            }}
            .bloom-title {{
                font-size: 46px;
                text-align: center;
                color: {theme['primary']};
                margin-bottom: 0px;
            }}
            .bloom-sub {{
                text-align: center;
                color: {theme['text']};
                opacity: 0.8;
                margin-top: 0px;
                margin-bottom: 24px;
                font-style: italic;
            }}
            .stButton>button {{
                background-color: {theme['primary']};
                color: white;
                border-radius: 20px;
                border: none;
                padding: 8px 20px;
                font-family: {font_stack};
            }}
            .stButton>button:hover {{
                filter: brightness(1.08);
            }}
            .stTextArea textarea {{
                border-radius: 12px !important;
                border: 1px solid {theme['bg_to']} !important;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_css()


# ----------------------------------------------------------------------------
# Sidebar — customization
# ----------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## 🌷 Customize your planner")

    tab_theme, tab_ai, tab_data = st.tabs(["🎨 Look", "🤖 AI", "💾 Data"])

    with tab_theme:
        st.selectbox(
            "Color theme",
            list(THEMES.keys()),
            key="theme",
        )
        st.selectbox(
            "Font",
            list(FONT_STACKS.keys()),
            key="font",
        )
        st.selectbox(
            "Wallpaper pattern",
            list(WALLPAPER_PATTERNS.keys()),
            key="wallpaper",
        )
        uploaded_bg = st.file_uploader(
            "Or upload your own wallpaper image", type=["png", "jpg", "jpeg"]
        )
        if uploaded_bg is not None:
            st.session_state.custom_bg_image = base64.b64encode(
                uploaded_bg.read()
            ).decode("utf-8")
        if st.session_state.get("custom_bg_image") and st.button("Remove custom wallpaper"):
            st.session_state.custom_bg_image = None
            st.rerun()

        if st.button("💾 Save look as default"):
            save_json(SETTINGS_FILE, {
                "theme": st.session_state.theme,
                "font": st.session_state.font,
                "wallpaper": st.session_state.wallpaper,
                "custom_bg_image": st.session_state.get("custom_bg_image"),
            })
            st.success("Saved! This look will load next time. 🌸")

    with tab_ai:
        st.markdown("Let AI build your whole week for you.")
        api_key = st.text_input(
            "Groq API key",
            value=os.environ.get("GROQ_API_KEY", ""),
            type="password",
            help="Get a free key at console.groq.com. It's only used locally, never stored.",
        )

        model_options = GROQ_MODEL_FALLBACKS.copy()
        if st.button("🔄 Refresh available models") and api_key and Groq:
            try:
                client = Groq(api_key=api_key)
                live_models = [m.id for m in client.models.list().data]
                if live_models:
                    model_options = live_models
                    st.session_state["_live_models"] = live_models
            except Exception as e:
                st.warning(f"Couldn't fetch live model list: {e}")

        model_options = st.session_state.get("_live_models", model_options)
        model_name = st.selectbox("Model", model_options)

        goal_text = st.text_area(
            "Describe your courses, goals, fixed commitments, and how many hours/day you can study",
            placeholder="e.g. MS AI semester 1: ML, AI, and Math courses at NUST 6-9pm daily. "
                        "I want deep study mornings, coding practice, and light review at night. "
                        "Keep Sunday lighter for research.",
            height=140,
        )

        if st.button("✨ Generate my calendar with AI"):
            if not api_key:
                st.error("Please add your Groq API key first.")
            elif Groq is None:
                st.error("The groq package isn't installed. Run: pip install groq")
            elif not goal_text.strip():
                st.error("Tell the AI a bit about your week first.")
            else:
                with st.spinner("Blooming your schedule... 🌸"):
                    try:
                        client = Groq(api_key=api_key)
                        slot_list = st.session_state.slots
                        system_prompt = (
                            "You are a scheduling assistant. Produce ONLY a JSON object, no prose, "
                            "with this exact shape: {\"Monday\": {\"<time slot>\": \"<activity text>\", ...}, "
                            "\"Tuesday\": {...}, ... for all 7 days: "
                            + ", ".join(DAYS)
                            + ". Use exactly these time slots for every day as keys: "
                            + ", ".join(slot_list)
                            + ". Each activity value should be a short, specific plan (under 20 words)."
                        )
                        response = client.chat.completions.create(
                            model=model_name,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": goal_text},
                            ],
                            response_format={"type": "json_object"},
                            temperature=0.6,
                        )
                        content = response.choices[0].message.content
                        new_cal = json.loads(content)

                        # normalize: ensure all days/slots exist even if model omits some
                        for day in DAYS:
                            if day not in new_cal:
                                new_cal[day] = {}
                            for slot in slot_list:
                                new_cal[day].setdefault(slot, "")

                        st.session_state.calendar = new_cal
                        save_json(DATA_FILE, new_cal)
                        st.success("Your new calendar is ready below! 🌼")
                        st.rerun()
                    except json.JSONDecodeError:
                        st.error("The AI response wasn't valid JSON — try again, or try a different model.")
                    except Exception as e:
                        st.error(f"Something went wrong: {e}")

    with tab_data:
        st.markdown("**Time slots**")
        new_slot = st.text_input("Add a new time slot", placeholder="e.g. 7:00 – 8:00 AM")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("➕ Add slot") and new_slot.strip():
                if new_slot not in st.session_state.slots:
                    st.session_state.slots.append(new_slot)
                    for day in DAYS:
                        st.session_state.calendar.setdefault(day, {})[new_slot] = ""
                    st.rerun()
        with col_b:
            removable = st.selectbox("Remove a slot", ["—"] + st.session_state.slots)
            if st.button("🗑️ Remove") and removable != "—":
                st.session_state.slots.remove(removable)
                for day in DAYS:
                    st.session_state.calendar.get(day, {}).pop(removable, None)
                st.rerun()

        st.markdown("---")
        st.markdown("**Save / Load / Export**")
        if st.button("💾 Save calendar"):
            save_json(DATA_FILE, st.session_state.calendar)
            save_json(DATA_FILE + ".notes", st.session_state.notes)
            st.success("Calendar saved to disk.")

        if st.button("↩️ Reset to blank week"):
            st.session_state.calendar = default_calendar()
            st.session_state.slots = list(DEFAULT_SLOTS)
            st.rerun()

        df_export = calendar_to_df(st.session_state.calendar, st.session_state.slots)
        st.download_button(
            "⬇️ Download as CSV",
            df_export.to_csv(index=False).encode("utf-8"),
            file_name="bloom_calendar.csv",
            mime="text/csv",
        )
        st.download_button(
            "⬇️ Download as JSON",
            json.dumps(st.session_state.calendar, indent=2).encode("utf-8"),
            file_name="bloom_calendar.json",
            mime="application/json",
        )


# ----------------------------------------------------------------------------
# Main area — the calendar itself
# ----------------------------------------------------------------------------

st.markdown('<div class="bloom-title">🌸 Bloom Planner 🌸</div>', unsafe_allow_html=True)
st.markdown(
    f'<p class="bloom-sub">{datetime.now().strftime("%A, %d %B %Y")} — your week, your way</p>',
    unsafe_allow_html=True,
)

df = calendar_to_df(st.session_state.calendar, st.session_state.slots)

edited_df = st.data_editor(
    df,
    use_container_width=True,
    num_rows="fixed",
    hide_index=True,
    height=(len(st.session_state.slots) + 1) * 38 + 20,
    key="editor",
)

# persist any manual edits back into session state
st.session_state.calendar = df_to_calendar(edited_df)

st.markdown("### 🌷 Weekly notes")
note_cols = st.columns(7)
for i, day in enumerate(DAYS):
    with note_cols[i]:
        st.session_state.notes[day] = st.text_area(
            day,
            value=st.session_state.notes.get(day, ""),
            height=100,
            key=f"note_{day}",
            placeholder="add a note...",
        )

auto_col1, auto_col2 = st.columns([1, 5])
with auto_col1:
    if st.button("💾 Save everything"):
        save_json(DATA_FILE, st.session_state.calendar)
        save_json(DATA_FILE + ".notes", st.session_state.notes)
        st.toast("Saved! 🌸")

st.markdown(
    "<p style='text-align:center; opacity:0.6; margin-top:30px; font-style:italic;'>"
    "made with 🌷 — edit any cell, change your theme anytime, or let AI redo your week"
    "</p>",
    unsafe_allow_html=True,
)
