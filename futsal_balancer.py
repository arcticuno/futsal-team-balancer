import streamlit as st
import pandas as pd
import uuid
import datetime
import requests

# === CONFIG ===
SUPABASE_URL = "https://njljwzowdrtyflyzkotr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5qbGp3em93ZHJ0eWZseXprb3RyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQzOTEyMDEsImV4cCI6MjA1OTk2NzIwMX0.hcudB9gVIWFGqD3OUL1HGlRec2-Q1LxKrbAuxm-lhBs"
HEADERS = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
ADMIN_PASSWORD = "jogabotnito"

# === HELPER: Supabase ===
def sb_select(table, filters=None):
    url = f"{SUPABASE_URL}/rest/v1/{table}?select=*"
    if filters:
        url += "&" + "&".join(filters)
    res = requests.get(url, headers=HEADERS)
    return res.json()

def sb_insert(table, payload):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    return requests.post(url, headers={**HEADERS, "Content-Type": "application/json"}, json=payload)

def sb_delete(table, filters):
    url = f"{SUPABASE_URL}/rest/v1/{table}?{'&'.join(filters)}"
    return requests.delete(url, headers=HEADERS)

# === PAGE START ===
st.set_page_config(page_title="Futsal Manager", layout="centered")
st.title("Futsal Session Manager")

# === SESSION MANAGEMENT ===
with st.expander("Start New Session (Admin Only)"):
    admin_pw = st.text_input("Enter Admin Password", type="password")
    if admin_pw == ADMIN_PASSWORD:
        st.success("Admin Access Granted")
        with st.form("start_session_form"):
            location = st.text_input("Location")
            sub_location = st.text_input("Sub-Location")
            date = st.date_input("Date", value=datetime.date.today())
            time = st.time_input("Time", value=datetime.datetime.now().time())
            submit_session = st.form_submit_button("Start Session")

            if submit_session:
                payload = {
                    "id": str(uuid.uuid4()),
                    "location": location,
                    "sub_location": sub_location,
                    "session_date": str(date),
                    "session_time": str(time)
                }
                sb_insert("sessions", payload)
                st.success("New session started!")
                st.experimental_rerun()

# === GET CURRENT SESSION ===
sessions = sb_select("sessions", filters=["order=created_at.desc", "limit=1"])
if sessions:
    current_session = sessions[0]
    session_id = current_session["id"]
    st.subheader("Active Session")
    st.markdown(f"**Location**: {current_session['location']} - {current_session['sub_location']}  \n"
                f"**Date**: {current_session['session_date']} at {current_session['session_time']}")

    st.divider()

    # === JOIN / LEAVE ===
    name = st.text_input("Your Name")
    if name:
        participants = sb_select("session_participants", [f"session_id=eq.{session_id}"])
        joined_names = [p['player_name'] for p in participants]
        already_joined = name in joined_names

        if already_joined:
            st.success("You are already in the session.")
            if st.button("Leave Session"):
                response = sb_delete("session_participants", [f"session_id=eq.{session_id}", f"player_name=eq.{name}"])
                if response.status_code == 204:
                    st.success("You have left the session.")
                    st.experimental_rerun()
                else:
                    st.error("Failed to leave session.")
        else:
            if st.button("Join Session"):
                sb_insert("session_participants", [{
                    "session_id": session_id,
                    "player_name": name,
                    "joined_by": name
                }])
                st.success("You have joined the session!")
                st.experimental_rerun()

        # === SESSION PARTICIPANTS VIEW ===
        updated = sb_select("session_participants", [f"session_id=eq.{session_id}"])
        st.markdown("### Players in Session")
        st.write(pd.DataFrame(updated)[["player_name", "joined_by", "joined_at"]])
    else:
        st.info("Enter your name to join or view the session.")
else:
    st.warning("No active session. Admin must start one.")

# === PLAYER RATING ===
st.divider()
st.header("Rate a Player")

rating_rater = st.text_input("Your Name (Rater)", key="rater")
rating_ratee = st.text_input("Who are you rating? (Ratee)", key="ratee")

rating_value = st.slider("Rating (1.0 - 10.0)", 1.0, 10.0, step=0.1)

if st.button("Submit Rating"):
    if rating_rater.strip() and rating_ratee.strip():
        sb_insert("player_ratings", {
            "rater": rating_rater.strip(),
            "ratee": rating_ratee.strip(),
            "rating": float(rating_value)
        })
        st.success(f"{rating_rater} rated {rating_ratee} a {rating_value}")
    else:
        st.warning("Please fill in both names.")

# === LEADERBOARD ===
st.divider()
st.header("Player Rating Leaderboard")

ratings = sb_select("player_ratings")
if ratings:
    df = pd.DataFrame(ratings)
    summary = df.groupby("ratee").agg(
        avg_rating=("rating", "mean"),
        num_ratings=("rating", "count")
    ).reset_index().sort_values("avg_rating", ascending=False)

    summary["avg_rating"] = summary["avg_rating"].round(2)
    st.dataframe(summary, use_container_width=True)
else:
    st.info("No ratings yet.")