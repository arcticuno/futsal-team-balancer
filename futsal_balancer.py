import streamlit as st
import pandas as pd
import sqlite3
import random

# Constants
DB_FILE = 'players.db'
PASSWORD = 'jogabotnito'

# DB setup
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    rating REAL NOT NULL
)
''')
conn.commit()

# Page config
st.set_page_config(page_title="Futsal Team Balancer", layout="centered")
st.title("Futsal Team Balancer")

# --- Admin Panel ---
with st.expander("Admin Panel"):
    pw_input = st.text_input("Enter admin password", type="password")
    is_admin = pw_input == PASSWORD
    if is_admin:
        st.success("Admin access granted.")

        # Add Player
        st.subheader("Add New Player")
        with st.form("add_player_form"):
            new_name = st.text_input("Player Name")
            new_rating = st.number_input("Rating (1.0 - 10.0)", min_value=1.0, max_value=10.0, step=0.1)
            submitted = st.form_submit_button("Add Player")
            if submitted and new_name.strip():
                try:
                    cursor.execute("INSERT INTO players (name, rating) VALUES (?, ?)", (new_name.strip(), new_rating))
                    conn.commit()
                    st.success(f"Player {new_name} added.")
                except sqlite3.IntegrityError:
                    st.error(f"Player {new_name} already exists.")

        # Edit Player List
        st.subheader("Player List")
        df_admin = pd.read_sql_query("SELECT id, name, rating FROM players", conn)
        edited_df = st.data_editor(df_admin, num_rows="dynamic", use_container_width=True)
        if edited_df is not None:
            deleted = df_admin[~df_admin['id'].isin(edited_df['id'])]
            for _, row in deleted.iterrows():
                cursor.execute("DELETE FROM players WHERE id = ?", (row['id'],))
            for _, row in edited_df.iterrows():
                cursor.execute("UPDATE players SET name = ?, rating = ? WHERE id = ?", (row['name'], row['rating'], row['id']))
            conn.commit()

        # Export Player List
        csv_players = df_admin.to_csv(index=False).encode('utf-8')
        st.download_button("Download Player List as CSV", csv_players, "player_list.csv", "text/csv")

# --- Public Section: Team Selection & Shuffle ---
st.header("Generate Balanced Teams")

df = pd.read_sql_query("SELECT name, rating FROM players", conn)
if df.empty:
    st.info("No players in the database. Admins can add players above.")
else:
    selected_players = st.multiselect("Pick 15 players", df['name'].tolist())
    session_key = "team_shuffle"

    if len(selected_players) == 15:
        players_df = df[df['name'].isin(selected_players)]

        if st.button("Generate Teams"):
            st.session_state[session_key] = random.sample(list(zip(players_df['name'], players_df['rating'])), 15)

        if session_key in st.session_state:
            if st.button("Reshuffle Teams"):
                st.session_state[session_key] = random.sample(list(zip(players_df['name'], players_df['rating'])), 15)

            # Get current selection from session
            player_data = st.session_state[session_key]

            # Sort for semi-balanced team distribution
            player_data.sort(key=lambda x: -x[1])  # sort by rating descending
            teams = {1: [], 2: [], 3: []}
            totals = {1: 0.0, 2: 0.0, 3: 0.0}

            for name, rating in player_data:
                min_team = min(totals, key=totals.get)
                teams[min_team].append((name, rating))
                totals[min_team] += rating

            team_export_rows = []

            for i in range(1, 4):
                avg = round(totals[i] / len(teams[i]), 2)
                st.subheader(f"Team {i} (Average Rating: {avg})")
                names_only = [name for name, _ in teams[i]]
                st.write(", ".join(names_only))
                for name in names_only:
                    team_export_rows.append((f"Team {i}", name))

            diff = round(max(totals.values()) - min(totals.values()), 2)
            st.success(f"Rating difference between strongest and weakest team: {diff}")

            teams_df = pd.DataFrame(team_export_rows, columns=["Team", "Player"])
            teams_csv = teams_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Teams as CSV", teams_csv, "teams.csv", "text/csv")
    elif len(selected_players) > 0:
        st.warning("Please select exactly 15 players.")