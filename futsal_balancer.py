import streamlit as st
import pandas as pd

st.set_page_config(page_title="Futsal Team Balancer", layout="centered")
st.title("Futsal Team Balancer")
st.markdown("Enter 15 player names and ratings below to generate 3 balanced teams.")

with st.form("team_form"):
    names = []
    ratings = []
    for i in range(15):
        cols = st.columns([2, 1])
        name = cols[0].text_input(f"Player {i+1} Name", key=f"name_{i}")
        rating = cols[1].number_input("Rating (1-10)", 1, 10, key=f"rating_{i}")
        names.append(name)
        ratings.append(rating)
    
    submitted = st.form_submit_button("Generate Teams")

if submitted:
    players = [(n, r) for n, r in zip(names, ratings) if n.strip()]
    
    if len(players) != 15:
        st.error("Please enter exactly 15 players.")
    else:
        players.sort(key=lambda x: -x[1])
        teams = {1: [], 2: [], 3: []}
        totals = {1: 0, 2: 0, 3: 0}

        for name, rating in players:
            min_team = min(totals, key=totals.get)
            teams[min_team].append((name, rating))
            totals[min_team] += rating

        for i in range(1, 4):
            st.subheader(f"Team {i} (Total Rating: {totals[i]})")
            team_df = pd.DataFrame(teams[i], columns=["Name", "Rating"])
            st.table(team_df)

        max_diff = max(totals.values()) - min(totals.values())
        st.success(f"Max rating difference between teams: {max_diff}")
