import streamlit as st
import pandas as pd
import uuid
import datetime
import requests
import random

# === CONFIG ===
SUPABASE_URL = "https://njljwzowdrtyflyzkotr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5qbGp3em93ZHJ0eWZseXprb3RyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQzOTEyMDEsImV4cCI6MjA1OTk2NzIwMX0.hcudB9gVIWFGqD3OUL1HGlRec2-Q1LxKrbAuxm-lhBs"
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}
ADMIN_PASSWORD = "jogabotnito"

# === Supabase Helpers ===
def sb_select(table, filters=None):
    url = f"{SUPABASE_URL}/rest/v1/{table}?select=*"
    if filters:
        url += "&" + "&".join(filters)
    return requests.get(url, headers=HEADERS).json()

def sb_insert(table, payload):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    return requests.post(url, headers={**HEADERS, "Content-Type": "application/json"}, json=payload)

def sb_delete(table, filters):
    url = f"{SUPABASE_URL}/rest/v1/{table}?{'&'.join(filters)}"
    return requests.delete(url, headers=HEADERS)

# === App Start ===
st.set_page_config(page_title="Futsal Session", layout="centered")
st.title("Futsal Session Manager")

# === Admin Panel ===
with st.expander("Start New Session (Admin Only)"):
    admin_pw = st.text_input("Enter Admin Password", type="password")
    if admin_pw == ADMIN_PASSWORD:
        st.success("Admin Access Granted")
        with st.form("start_session_form"):
            location = st.text_input("Location")
            sub_location = st.text_input("Sub-Location")
            date = st.date_input("Date", value=datetime.date.today())
            time = st.time_input("Time", value=datetime.datetime.now().time())
            submitted = st.form_submit_button("Start Session")
            if submitted:
                payload = {
                    "id": str(uuid.uuid4()),
                    "location": location,
                    "sub_location": sub_location,
                    "session_date": str(date),
                    "session_time": str(time)
                }
                response = sb_insert("sessions", payload)
                st.success("Session submitted. Please refresh manually to see it.")
                st.write("DEBUG - Insert status", response.status_code)
                try:
                    st.json(response.json())
                except Exception:
                    st.write("DEBUG - Raw response:", response.text)

# === Fetch current session ===
sessions = sb_select("sessions", filters=["order=created_at.desc", "limit=1"])
if isinstance(sessions, list) and len(sessions) > 0:
    current_session = sessions[0]
else:
    st.warning("No active session found. Please start one from the admin panel above.")
    st.stop()

session_id = current_session["id"]
st.subheader("Active Session")
st.markdown(f"**Location**: {current_session['location']} - {current_session['sub_location']}  \n"
            f"**Date**: {current_session['session_date']} at {current_session['session_time']}")

# === Join/Leave ===
name = st.text_input("Your Name")
participants = sb_select("session_participants", [f"session_id=eq.{session_id}"])
joined_names = [p.get('player_name', '') for p in participants]
already_joined = name in joined_names if name else False

if name:
    if already_joined:
        st.success("You are in the session.")
        if st.button("Leave Session"):
            sb_delete("session_participants", [f"session_id=eq.{session_id}", f"player_name=eq.{name}"])
            st.success("You left the session! Please refresh the page to update.")
    else:
        if st.button("Join Session"):
            sb_insert("session_participants", [{
                "session_id": session_id,
                "player_name": name,
                "joined_by": name
            }])
            st.success("You joined the session! Please refresh the page to update.")

# === Show Players ===
st.markdown("### Joined Players")
if participants:
    df_players = pd.DataFrame(participants)
    if "player_name" in df_players.columns:
        st.write(df_players[["player_name"]])
else:
    st.info("No participants yet.")

# === Sort Teams if 15 Players ===
if len(participants) == 15:
    st.divider()
    st.subheader("Generate Balanced Teams")
    if st.button("Sort Teams"):
        ratings_raw = sb_select("player_ratings")
        rating_df = pd.DataFrame(ratings_raw)
        rating_avg = rating_df.groupby("ratee")["rating"].mean().to_dict() if not rating_df.empty else {}

        players = []
        for p in participants:
            player_name = p.get("player_name")
            rating = round(rating_avg.get(player_name, 5.0), 2)
            players.append((player_name, rating))

        players.sort(key=lambda x: -x[1])
        teams = {1: [], 2: [], 3: []}
        totals = {1: 0.0, 2: 0.0, 3: 0.0}

        for name, rating in players:
            team_id = min(totals, key=totals.get)
            teams[team_id].append((name, rating))
            totals[team_id] += rating

        for i in range(1, 4):
            st.markdown(f"**Team {i}** (Avg Rating: {round(totals[i]/5, 2)})")
            st.write(", ".join([n for n, _ in teams[i]]))

        diff = round(max(totals.values()) - min(totals.values()), 2)
        st.success(f"Rating difference between strongest and weakest team: {diff}")
elif len(participants) > 0:
    st.info("Waiting for 15 players to join...")