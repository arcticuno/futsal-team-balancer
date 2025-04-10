import streamlit as st
import pandas as pd
import sqlite3

# Constants
DB_FILE = 'players.db'
PASSWORD = 'jogabotnito'

# Initialize connection
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

# Create table if not exists
cursor.execute('''
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    rating REAL NOT NULL
)
''')
conn.commit()

# Password protection
def check_password():
    """Returns `True` if the user enters the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == PASSWORD:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password
    st.text_input("Enter Password:", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state:
        st.error("Password incorrect")
    st.stop()

# Check the password before proceeding
if not check_password():
    st.stop()

# Page configuration
st.set_page_config(page_title="Futsal Team Balancer", layout="centered")
st.title("Futsal Team Balancer")

# Section: Add New Player
st.header("Add New Player")
with st.form("add_player_form"):
    new_name = st.text_input("Player Name")
    new_rating = st.number_input("Rating (1.0 - 10.0)", min_value=1.0, max_value=10.0, step=0.1)
    submitted = st.form_submit_button("Add Player")
    if submitted:
        if new_name.strip():
            try:
                cursor.execute("INSERT INTO players (name, rating) VALUES (?, ?)", (new_name.strip(), new_rating))
                conn.commit()
                st.success(f"Player {new_name} added.")
            except sqlite3.IntegrityError:
                st.error(f"Player {new_name} already exists.")

# Section: Manage Player List
st.header("Player List")
df = pd.read_sql_query("SELECT id, name, rating FROM players", conn)
if df.empty:
    st.info("No players added yet.")
else:
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="data_editor")
    if edited_df is not None:
        # Process deletions
        deleted_rows = df[~df['id'].isin(edited_df['id'])]
        for _, row in deleted_rows.iterrows():
            cursor.execute("DELETE FROM players WHERE id = ?", (row['id'],))
        conn.commit()
        # Process edits
        for _, row in edited_df.iterrows():
            cursor.execute("UPDATE players SET name = ?, rating = ? WHERE id = ?", (row['name'], row['rating'], row['id']))
        conn.commit()

    # Export player list
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Player List as CSV", csv, "player_list.csv", "text/csv", key='download-players-csv')

# Section: Select 15 Players for This Week
st.header("Select 15 Players for This Week")
selected_players = st.multiselect("Pick 15 players", df['name'].tolist())

if len(selected_players) == 15:
    players = df[df['name'].isin(selected_players)].sort_values(by='rating', ascending=False)
    player_data = list(zip(players['name'], players['rating']))

    # Team allocation logic
    teams = {1: [], 2: [], 3: []}
    totals = {1: 0.0, 2: 0.0, 3: 0.0}

    for name, rating in player_data:
        min_team = min(totals, key=totals.get)
        teams[min_team].append((name, rating))
        totals[min_team] += rating

    # Display teams
    for i in range(1, 4):
        avg = round(totals[i] / len(teams[i]), 2)
        st.subheader(f"Team {i} (Average Rating: {avg})")
        team_names = [name for name, _ in teams[i]]
        st.write(", ".join(team_names))

    diff = round(max(totals.values()) - min(totals.values()), 2)
    st.success(f"Rating difference between strongest and weakest team: {diff}")

    # Export teams
    teams_df = pd.DataFrame([(team, name) for team, members in teams.items() for name, _ in members], columns=["Team", "Player"])
    teams_csv = teams_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Teams as CSV", teams_csv, "teams.csv", "text/csv", key='download-teams-csv')

elif len(selected_players) > 0:
    st.warning("Please select exactly 15 players.")
