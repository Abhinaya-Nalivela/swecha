import streamlit as st
import google.generativeai as genai
import re
from datetime import date, timedelta, datetime
import uuid
import os
import glob
def add_gym_ui_theme():
    st.markdown("""
        <style>
        /* Set a background image */
        .stApp {
            background-image: url("https://images.unsplash.com/photo-1583454110558-6cc0dfef29f1?auto=format&fit=crop&w=1600&q=80");
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
            color: white !important;
        }

        /* Dark card styling */
        .st-emotion-cache-1v0mbdj, .st-emotion-cache-1r6slb0 {
            background-color: rgba(0, 0, 0, 0.6) !important;
            border-radius: 12px;
            padding: 16px;
            color: white !important;
        }

        /* Header styling */
        h1, h2, h3, h4, h5 {
            color: #00FFAA !important;
            text-shadow: 1px 1px 2px black;
        }

        /* Button styling */
        button[kind="primary"] {
            background-color: #00FFAA !important;
            color: black !important;
            font-weight: bold;
            border-radius: 8px;
        }

        /* Sidebar styling */
        .st-emotion-cache-6qob1r {
            background-color: rgba(0, 0, 0, 0.8) !important;
        }

        /* Markdown custom headers */
        .markdown-text-container h2 {
            border-bottom: 2px solid #00FFAA;
            padding-bottom: 4px;
        }

        /* Input fields & sliders */
        .st-emotion-cache-1c7y2kd {
            background-color: rgba(255,255,255,0.1) !important;
            border-radius: 8px;
            padding: 6px;
        }
        
        </style>
    """, unsafe_allow_html=True)

add_gym_ui_theme()


# --- Gemini API Configuration (set API key directly for local testing) ---
GEMINI_API_KEY = "AIzaSyAgv6bVBWBccxuosY9DxNqo2eIFfBhfArw"
genai.configure(api_key=GEMINI_API_KEY)

# --- Page Configuration ---
#st.set_page_config(
 #   page_title="Personal AI Workout Coach",
   # page_icon="💪",
  #  layout="wide",
    #initial_sidebar_state="expanded"
#)

# --- Helper Function to Parse AI Output ---
def parse_workout_plan(ai_output, num_days):
    workout_days = {}
    current_day = None
    lines = ai_output.strip().split('\n')
    day_count = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue

        day_match = re.match(r"--- DAY (\d+) ---", line.upper())
        if day_match:
            day_count += 1
            if day_count > num_days:
                break
            current_day = f"Day {day_match.group(1)}"
            workout_days[current_day] = []
        elif current_day:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 3:
                workout_days[current_day].append({
                    "name": parts[0], "sets": parts[1], "reps": parts[2],
                    "note": parts[3] if len(parts) > 3 else ""
                })
            else:
                workout_days[current_day].append({"raw_note": line})
        else:
            if "intro" not in workout_days:
                workout_days["intro"] = []
            workout_days["intro"].append(line)
    return workout_days

# --- Function to Generate Workout with Gemini ---
@st.cache_data(show_spinner=False)
def generate_workout_with_gemini(fitness_goal, gender, available_equipment, workout_duration_minutes, num_days):
    model = genai.GenerativeModel('gemini-1.5-flash')
    equipment_str = f"They have access to: {', '.join(available_equipment)}." if available_equipment else "They only have access to bodyweight exercises."
    prompt = (
        f"Create a detailed {num_days}-day workout plan for a {gender.lower()} whose primary fitness goal is '{fitness_goal}'. "
        f"The total workout duration per session should be around {workout_duration_minutes} minutes. "
        f"{equipment_str} For each of the {num_days} days, list 4-6 exercises. "
        f"Strictly format each day like this:\n"
        f"--- DAY X ---\n"
        f"Exercise Name | Sets | Reps | Optional Notes (e.g., rest time, form tip)\n"
        f"Example: Push-ups | 3 | 10-15 | Keep core tight\n"
        f"Ensure no extra descriptive text before the first '--- DAY 1 ---'. Just the workout plan."
    )
    try:
        response = model.generate_content(prompt)
        return parse_workout_plan(response.text, num_days)
    except Exception as e:
        st.error(f"Failed to generate workout plan: {e}")
        return None

# --- Main App Title and Description ---
st.title("🏋️‍♂️Your AI-Powered Workout Coach🏋️‍♀️")
st.markdown("Craft personalized workout routines tailored to your goals, gender, and available equipment.")

# --- User Inputs in Sidebar ---
with st.sidebar:
    st.header("⚙️ Your Fitness Profile")
    fitness_goal = st.selectbox("What's your primary fitness goal?", ["Muscle Gain", "Weight Loss", "Endurance", "General Fitness", "Strength", "Flexibility"])
    gender = st.selectbox("Are you planning a workout for a man or a woman?", ["Man", "Woman"])
    workout_duration_minutes = st.slider("Approximate workout duration per session (minutes)", 20, 90, 45, 5)
    num_days = st.slider("Number of days for your workout routine", 1, 7, 3, 1)
    equipment_options = ["Bodyweight", "Dumbbells", "Barbell", "Kettlebell", "Pull-up Bar", "Resistance Bands", "Yoga Mat", "Treadmill", "Stationary Bike", "Gym Machines"]
    available_equipment = st.multiselect("What equipment do you have available?", equipment_options, default=["Bodyweight"])
    st.markdown("---")
    if st.button(" Generate Workout Plan", use_container_width=True, type="primary"):
        if not available_equipment:
            st.warning("Please select at least one piece of equipment.")
        else:
            st.session_state.clear()  # Clear old state on new generation
            st.session_state.current_fitness_goal = fitness_goal
            st.session_state.current_gender = gender
            st.session_state.current_equipment = available_equipment
            st.session_state.current_duration = workout_duration_minutes
            st.session_state.current_num_days = num_days

            with st.spinner("🚀 Generating your custom workout plan..."):
                st.session_state.workout_plan = generate_workout_with_gemini(
                    fitness_goal, gender, available_equipment, workout_duration_minutes, num_days
                )

# --- Display Workout Plan ---
if "workout_plan" not in st.session_state or not st.session_state.workout_plan:
    st.info("Select your fitness profile in the sidebar and click 'Generate Workout Plan' to get started!")
else:
    st.header(f"🏋️ Your Custom Workout for {st.session_state.current_gender} - {st.session_state.current_fitness_goal}")
    st.markdown(f"**Duration:** ~{st.session_state.current_duration} mins | **Equipment:** {', '.join(st.session_state.current_equipment)} | **Days:** {st.session_state.current_num_days}")
    st.markdown("---")

    if "intro" in st.session_state.workout_plan:
        st.write(" ".join(st.session_state.workout_plan["intro"]))
        st.markdown("---")

    for day_key, exercises in st.session_state.workout_plan.items():
        if day_key.startswith("Day"):
            with st.expander(f"🗓️ {day_key}", expanded=True):
                if not exercises:
                    st.info(f"No exercises listed for {day_key}.")
                    continue
                for exercise in exercises:
                    if "raw_note" in exercise:
                        st.markdown(f"**Note:** _{exercise['raw_note']}_")
                    else:
                        exercise_text = f"**{exercise['name']}**: {exercise['sets']} sets of {exercise['reps']} reps"
                        if exercise['note']:
                            exercise_text += f" ({exercise['note']})"
                        st.markdown(exercise_text)

from streamlit_calendar import calendar as st_calendar

st.header(" Workout Calendar & Progress Pic Tracker")

# Session state initialization
if "workout_dates" not in st.session_state:
    st.session_state.workout_dates = set()
if "workout_not_done_dates" not in st.session_state:
    st.session_state.workout_not_done_dates = set()
if "progress_pics" not in st.session_state:
    st.session_state.progress_pics = {}
if "calendar_key" not in st.session_state:
    st.session_state["calendar_key"] = str(uuid.uuid4())

# Input for start date of workout journey
start_date = st.date_input("Select the start date of your workout journey", date.today())

today = date.today()
first_day = date(today.year, today.month, 1)
if today.month == 12:
    next_month = date(today.year + 1, 1, 1)
else:
    next_month = date(today.year, today.month + 1, 1)
last_day = next_month - timedelta(days=1)

# --- Build events for calendar: check both sets ---
events = []
d = first_day
while d <= last_day:
    if d < start_date:
        pass
    elif d <= today:
        if d in st.session_state.workout_dates:
            events.append({
                "title": "✅",
                "start": d.isoformat(),
                "end": (d + timedelta(days=1)).isoformat(),
                "color": "green"
            })
        elif d in st.session_state.workout_not_done_dates:
            events.append({
                "title": "❌",
                "start": d.isoformat(),
                "end": (d + timedelta(days=1)).isoformat(),
                "color": "red"
            })
    d += timedelta(days=1)

calendar_options = {
    "initialView": "dayGridMonth",
    "height": 500,
    "selectable": True,
    "headerToolbar": {
        "left": "today prev,next",
        "center": "title",
        "right": "dayGridMonth"
    },
    "validRange": {
        "start": first_day.isoformat(),
    }
}

state = st_calendar(
    events=events,
    options=calendar_options,
    key=st.session_state["calendar_key"]
)

# Folder for persistent image storage
SAVE_DIR = "progress_pics"
os.makedirs(SAVE_DIR, exist_ok=True)

# Use a date picker to select date for actions
selected_date = st.date_input(
    "Pick a date to manage workout and progress pic",
    min_value=first_day,
    max_value=last_day,
    value=today,
    key="calendar_date_picker"
)

if selected_date > today:
    st.warning("You cannot mark a future date as done/not done.")
elif selected_date < start_date:
    st.warning("This date is before your workout journey started.")
else:
    # --- Mark as Done / Not Done buttons ---
    done = selected_date in st.session_state.workout_dates
    not_done = selected_date in st.session_state.workout_not_done_dates

    cols = st.columns(2)
    with cols[0]:
        if not done:
            if st.button(f"✅ Mark {selected_date} as Workout Done"):
                st.session_state.workout_dates.add(selected_date)
                st.session_state.workout_not_done_dates.discard(selected_date)
                st.success(f"Marked {selected_date.strftime('%A, %B %d, %Y')} as workout done!")
                st.session_state["calendar_key"] = str(uuid.uuid4())
                st.rerun()
        else:
            st.success(f"{selected_date.strftime('%A, %B %d, %Y')} is already marked as workout done.")

    with cols[1]:
        if not not_done:
            if st.button(f"❌ Mark {selected_date} as Workout Not Done"):
                st.session_state.workout_not_done_dates.add(selected_date)
                st.session_state.workout_dates.discard(selected_date)
                st.warning(f"Marked {selected_date.strftime('%A, %B %d, %Y')} as workout not done.")
                st.session_state["calendar_key"] = str(uuid.uuid4())
                st.rerun()
        else:
            st.info(f"{selected_date.strftime('%A, %B %d, %Y')} is already marked as workout not done.")

    # Progress pic upload only (no camera)
    st.markdown("####  Progress Pic")
    uploaded_file = st.file_uploader(
        f"Upload your progress pic for {selected_date}",
        type=["jpg", "jpeg", "png"],
        key=f"uploader_{selected_date}"
    )

    file_path = os.path.join(SAVE_DIR, f"{selected_date}.jpg")
    # Save uploaded file in session state and disk immediately if present
    if uploaded_file is not None:
        st.session_state.progress_pics[str(selected_date)] = uploaded_file.getvalue()
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        st.success(f"Progress pic uploaded and saved for {selected_date}!")

    # Display the image from disk if present, else from session state
    pic_exists = os.path.exists(file_path)
    if pic_exists:
        st.image(file_path, caption=f"Progress Pic for {selected_date}")
        # --- Delete button for this date's pic ---
        if st.button(f"🗑️ Delete Progress Pic for {selected_date}"):
            os.remove(file_path)
            st.session_state.progress_pics.pop(str(selected_date), None)
            st.success(f"Deleted progress pic for {selected_date}.")
            st.rerun()
    elif str(selected_date) in st.session_state.progress_pics:
        st.image(st.session_state.progress_pics[str(selected_date)], caption=f"Progress Pic for {selected_date}", use_container_width=True)
        # --- Delete button for session-only image ---
        if st.button(f"🗑️ Delete Progress Pic for {selected_date}"):
            st.session_state.progress_pics.pop(str(selected_date), None)
            st.success(f"Deleted progress pic for {selected_date}.")
            st.rerun()
    else:
        st.info("No progress pic uploaded for this date yet.")

# Show list of workout days
if st.session_state.workout_dates:
    st.markdown("#### Workout Days:")
    for d in sorted(st.session_state.workout_dates):
        st.write(f"- {d.strftime('%A, %B %d, %Y')}")

# --- Progress Pic Gallery Section ---
st.header(" Progress Pic Gallery")

gallery_dir = "progress_pics"
image_files = sorted(glob.glob(os.path.join(gallery_dir, "*.jpg")))  # Add png if needed

if not image_files:
    st.info("No progress pics have been uploaded yet.")
else:
    cols = st.columns(4)  # 4 images per row
    for idx, img_path in enumerate(image_files):
        date_str = os.path.splitext(os.path.basename(img_path))[0]
        with cols[idx % 4]:
            st.image(img_path, caption=f"{date_str}")
            if st.button(f"🗑️ Delete ({date_str})", key=f"delete_{date_str}"):
                os.remove(img_path)
                st.session_state.progress_pics.pop(date_str, None)
                st.success(f"Deleted progress pic for {date_str}.")
                st.rerun()
