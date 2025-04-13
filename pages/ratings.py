import streamlit as st
import pandas as pd
import requests

# === CONFIG ===
SUPABASE_URL = "https://njljwzowdrtyflyzkotr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5qbGp3em93ZHJ0eWZseXprb3RyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQzOTEyMDEsImV4cCI6MjA1OTk2NzIwMX0.hcudB9gVIWFGqD3OUL1HGlRec2-Q1LxKrbAuxm-lhBs"
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

# === Supabase Helpers ===
def sb_select(table, filters=None):
    url = f"{SUPABASE_URL}/rest/v1/{table}?select=*"
    if filters:
        url += "&" + "&".join(filters)
    return requests.get(url, headers=HEADERS).json()

def sb_insert(table, payload):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    return requests.post(
        url,
        headers={**HEADERS, "Content-Type": "application/json"},
        json=payload
    )

# === Streamlit UI ===
st.set_page_config(page_title="Rate Players", layout="centered")
st.title("Rate a Player")

rater = st.text_input("Your Name")
ratee = st.text_input("Player You Are Rating")
score = st.slider("Rating (1.0 - 10.0)", 1.0, 10.0, step=0.1)

if st.button("Submit Rating"):
    if rater.strip() and ratee.strip():
        response = sb_insert("player_ratings", {
            "rater": rater.strip(),
            "ratee": ratee.strip(),
            "rating": float(score)
        })
        if response.status_code in [200, 201]:
            st.success(f"You rated {ratee} a {score}")
        else:
            st.error(f"Rating failed: {response.status_code}")
            st.write("DEBUG:", response.text)
    else:
        st.warning("Enter both names before submitting.")

# === Leaderboard ===
st.divider()
st.header("Leaderboard")

ratings = sb_select("player_ratings")
if isinstance(ratings, list) and len(ratings) > 0 and isinstance(ratings[0], dict) and ratings[0]:
    df = pd.DataFrame(ratings)
else:
    df = pd.DataFrame(columns=["rater", "ratee", "rating", "timestamp"])

if not df.empty and "ratee" in df.columns:
    leaderboard = df.groupby("ratee").agg(
        avg_rating=("rating", "mean"),
        num_ratings=("rating", "count")
    ).reset_index().sort_values("avg_rating", ascending=False)
    leaderboard["avg_rating"] = leaderboard["avg_rating"].round(2)
    st.dataframe(leaderboard, use_container_width=True)
else:
    st.info("No ratings yet.")