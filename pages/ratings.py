import streamlit as st
import pandas as pd
import requests

# === CONFIG ===
SUPABASE_URL = "https://njljwzowdrtyflyzkotr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # use your actual full key
HEADERS = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}

def sb_select(table, filters=None):
    url = f"{SUPABASE_URL}/rest/v1/{table}?select=*"
    if filters:
        url += "&" + "&".join(filters)
    return requests.get(url, headers=HEADERS).json()

def sb_insert(table, payload):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    return requests.post(url, headers={**HEADERS, "Content-Type": "application/json"}, json=payload)

st.set_page_config(page_title="Rate Players", layout="centered")
st.title("Rate a Player")

rater = st.text_input("Your Name")
ratee = st.text_input("Player You Are Rating")
score = st.slider("Rating (1.0 - 10.0)", 1.0, 10.0, step=0.1)

if st.button("Submit Rating"):
    if rater.strip() and ratee.strip():
        sb_insert("player_ratings", {
            "rater": rater.strip(),
            "ratee": ratee.strip(),
            "rating": float(score)
        })
        st.success(f"You rated {ratee} a {score}")
    else:
        st.warning("Enter both names.")

st.divider()
st.header("Leaderboard")

ratings = sb_select("player_ratings")
if ratings:
    df = pd.DataFrame(ratings)
    if not df.empty and "ratee" in df.columns:
        leaderboard = df.groupby("ratee").agg(
            avg_rating=("rating", "mean"),
            num_ratings=("rating", "count")
        ).reset_index().sort_values("avg_rating", ascending=False)
        leaderboard["avg_rating"] = leaderboard["avg_rating"].round(2)
        st.dataframe(leaderboard, use_container_width=True)
    else:
        st.info("No ratings data available.")
else:
    st.info("No ratings data available.")