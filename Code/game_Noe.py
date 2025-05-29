import streamlit as st
from streamlit_autorefresh import st_autorefresh
import random
import time
import pandas as pd


# ----- Load game data from Excel file -----
@st.cache_data
def load_hint_data(path="Code/data_new_long_format.xlsx"):
    df = pd.read_excel(path)
    return df

st.cache_data.clear()

# TEMPORARY: Clear cache to force reload
load_hint_data.clear()

# Load data from Excel
df = load_hint_data("Code/data_new_long_format.xlsx")
cantons = df["canton"].unique().tolist()

# ----- Leaderboard in session memory -----
if "leaderboard" not in st.session_state:
    st.session_state.leaderboard = {}

# ----- Initial state -----
if "rounds" not in st.session_state:
    st.session_state.rounds = 0
    st.session_state.score = 0
    st.session_state.current_round = 0
    st.session_state.round_cantons = []
    st.session_state.current_difficulty = 10
    st.session_state.pending_score = 10
    st.session_state.current_question = None
    st.session_state.correct = False
    st.session_state.hints = []
    st.session_state.attempts_left = 2
    st.session_state.round_start_time = None
    st.session_state.round_finished = False
    st.session_state.reveal_message = ""
    st.session_state.feedback_message = ""
    st.session_state.username = ""
    st.session_state.game_started = False

# ----- Startscreen -----
if st.session_state.rounds == 0 and not st.session_state.game_started:
    st.title("🇨🇭 Canton Guessing Game")

    with st.expander("ℹ️ Game Rules & How to Play"):
        st.markdown("""
        **Objective:** Guess the correct canton based on up to 10 hints.

        - Select the number of rounds first.
        - Then enter your player name.
        - Each round starts with the hardest hint (worth 10 points).
        - Click "Next Hint" to reveal easier clues (each costs 1 point).
        - You have **2 guess attempts** per round.
        - A round ends automatically after 45 seconds or 2 wrong guesses.

        **Leaderboard:**
        - Scores are tracked during this session.
        - If you enter an existing name, your previous score will be overwritten.
        - The leaderboard always shows the Top 5 scores.
        """)

    if st.session_state.leaderboard:
        st.subheader("🏆 Leaderboard (Top 5)")
        for name, score in sorted(st.session_state.leaderboard.items(), key=lambda x: -x[1])[:5]:
            st.write(f"{name}: {score} points")

    rounds = st.radio("Choose number of rounds:", [4, 8, 12])
    if st.button("Continue"):
        st.session_state.rounds = rounds
        st.session_state.round_cantons = random.sample(cantons, rounds)
        st.rerun()

# ----- Name input -----
elif not st.session_state.game_started:
    st.title("Enter your name")
    name = st.text_input("Username:")
    if name and st.button("Start Game"):
        st.session_state.username = name
        st.session_state.game_started = True
        st.session_state.round_start_time = time.time()
        st.rerun()

# ----- Game logic -----
elif st.session_state.current_round < st.session_state.rounds:

    if not st.session_state.round_finished:
        st_autorefresh(interval=1000, limit=45, key="auto_refresh")

    input_key = f"guess_input_{st.session_state.current_round}"
    if st.session_state.get("clear_guess", False):
        st.session_state[input_key] = ""
        st.session_state.clear_guess = False

    st.title(f"Round {st.session_state.current_round + 1} of {st.session_state.rounds}")
    st.write(f"Player: {st.session_state.username}")
    st.write(f"Score: {st.session_state.score}")
    st.write(f"Attempts left: {st.session_state.attempts_left}")

    start_time = st.session_state.round_start_time or time.time()
    remaining_time = max(0, int(45 - (time.time() - start_time)))
    st.write(f"⏳ Time remaining: {remaining_time} seconds")

    current_canton = st.session_state.round_cantons[st.session_state.current_round]

    if not st.session_state.round_finished and remaining_time == 0:
        st.session_state.feedback_message = "⏱️ Time's up!"
        st.session_state.round_finished = True
        st.session_state.reveal_message = f"The correct answer was: {current_canton}"

    if not st.session_state.hints and not st.session_state.round_finished:
        hint_rows = df[(df["canton"] == current_canton) & (df["difficulty"] == st.session_state.current_difficulty)]
        if not hint_rows.empty:
            row = hint_rows.sample(1).iloc[0]  # randomly choose one if multiple at same difficulty
            st.session_state.current_question = row
            st.session_state.hints.append(f"{row['type']}: {row['hint']}")

    st.subheader("Hints so far:")
    for hint in st.session_state.hints:
        st.write(f"- {hint}")

    if st.session_state.feedback_message:
        st.info(st.session_state.feedback_message)

    if not st.session_state.round_finished:
        col1, col2 = st.columns(2)

        with col1:
            guess = st.text_input("Your Guess:", key=input_key)
            if guess:
                if guess.strip().lower() == current_canton.lower():
                    st.session_state.feedback_message = f"✅ Correct! You earned {st.session_state.pending_score} points."
                    st.session_state.score += st.session_state.pending_score
                    st.session_state.round_finished = True
                    st.session_state.clear_guess = True
                    st.rerun()
                else:
                    st.session_state.attempts_left -= 1
                    st.session_state.clear_guess = True
                    if st.session_state.attempts_left == 0:
                        st.session_state.feedback_message = "❌ No attempts left."
                        st.session_state.round_finished = True
                        st.session_state.reveal_message = f"The correct answer was: {current_canton}"
                    else:
                        st.session_state.feedback_message = f"❌ Wrong guess. {st.session_state.attempts_left} attempt(s) left."
                    st.rerun()

        with col2:
            if st.button("Next Hint"):
                if st.session_state.current_difficulty > 1:
                    st.session_state.current_difficulty -= 1
                    st.session_state.pending_score -= 1
                    next_hint = df[(df["canton"] == current_canton) & (df["difficulty"] == st.session_state.current_difficulty)].iloc[0]
                    st.session_state.current_question = next_hint
                    st.session_state.hints.append(next_hint["question"])
                    st.rerun()
                else:
                    st.warning("No more hints available.")

    if st.session_state.round_finished:
        st.info(st.session_state.reveal_message)
        time.sleep(2)
        st.session_state.current_round += 1
        st.session_state.current_difficulty = 10
        st.session_state.pending_score = 10
        st.session_state.current_question = None
        st.session_state.correct = False
        st.session_state.hints = []
        st.session_state.attempts_left = 2
        st.session_state.round_start_time = time.time()
        st.session_state.round_finished = False
        st.session_state.reveal_message = ""
        st.session_state.clear_guess = True
        st.session_state.feedback_message = ""
        st.rerun()

# ----- Game end -----
else:
    st.title("Game Over")
    final_score = st.session_state.score
    st.write(f"🎉 Final Score: {final_score} / {st.session_state.rounds * 10}")

    name = st.session_state.username
    st.session_state.leaderboard[name] = max(final_score, st.session_state.leaderboard.get(name, 0))

    if st.button("Play Again"):
        keys = list(st.session_state.keys())
        leaderboard = st.session_state.leaderboard
        st.session_state.clear()
        st.session_state.leaderboard = leaderboard
        st.rerun()
