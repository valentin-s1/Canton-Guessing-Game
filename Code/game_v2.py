# ======================
# CH Canton Guessing Game - Optimized Version
# ======================

import streamlit as st
from streamlit_autorefresh import st_autorefresh
import random
import time
import pandas as pd
from rapidfuzz import fuzz

# ----- Constants -----
ROUND_TIME = 45
MAX_HINTS = 10
MAX_ATTEMPTS = 2
DEFAULT_DIFFICULTY = 10

# ----- Load game data -----
@st.cache_data
def load_hint_data(path="Data/data_new_long_format.xlsx"):
    return pd.read_excel(path)

df = load_hint_data()
cantons = df["canton"].unique().tolist()

# ----- Initialize session state -----
def init_game_state():
    st.session_state.update({
        "rounds": 0,
        "score": 0,
        "current_round": 0,
        "round_cantons": [],
        "current_difficulty": DEFAULT_DIFFICULTY,
        "pending_score": DEFAULT_DIFFICULTY,
        "current_question": None,
        "correct": False,
        "hints": [],
        "attempts_left": MAX_ATTEMPTS,
        "round_start_time": None,
        "round_finished": False,
        "reveal_message": "",
        "feedback_message": "",
        "username": "",
        "game_started": False,
        "clear_guess": False,
    })

if "rounds" not in st.session_state:
    init_game_state()

if "leaderboard" not in st.session_state:
    st.session_state.leaderboard = {}

# ----- Stage 1: Start Screen -----
if st.session_state.rounds == 0 and not st.session_state.game_started:
    st.title("CH Canton Guessing Game")

    with st.expander("ℹ️ Game Rules & How to Play"):
        st.markdown("""
        **Objective:** Guess the correct Swiss canton based on up to 10 hints.

        - Start by choosing how many rounds you want to play.
        - Enter your name to begin.
        - Each round starts with a difficult hint (10 points).
        - Ask for easier hints if needed (each hint costs 1 point).
        - You have **2 guesses per round**.
        - Rounds are timed — you have 45 seconds!
        """)

    if st.session_state.leaderboard:
        st.subheader("🏆 Leaderboard (Top 5)")
        top_scores = sorted(st.session_state.leaderboard.items(), key=lambda x: -x[1])[:5]
        for name, score in top_scores:
            st.write(f"{name}: {score} points")

    rounds = st.radio("Choose number of rounds:", [4, 8, 12])
    if st.button("Continue"):
        st.session_state.rounds = rounds
        st.session_state.round_cantons = random.sample(cantons, rounds)
        st.rerun()

# ----- Stage 2: Enter Name -----
elif not st.session_state.game_started:
    st.title("Enter your name")
    name = st.text_input("Username:")
    if name and st.button("Start Game"):
        st.session_state.username = name
        st.session_state.game_started = True
        st.session_state.round_start_time = time.time()
        st.rerun()

# ----- Stage 3: Gameplay -----
elif st.session_state.current_round < st.session_state.rounds:
    if not st.session_state.round_finished:
        st_autorefresh(interval=1000, limit=ROUND_TIME, key="auto_refresh")

    round_idx = st.session_state.current_round
    input_key = f"guess_input_{round_idx}"
    if st.session_state.get("clear_guess"):
        st.session_state[input_key] = ""
        st.session_state.clear_guess = False

    st.title(f"Round {round_idx + 1} of {st.session_state.rounds}")
    st.write(f"Player: {st.session_state.username}")
    st.write(f"Score: {st.session_state.score}")
    st.write(f"Attempts left: {st.session_state.attempts_left}")

    remaining_time = max(0, int(ROUND_TIME - (time.time() - st.session_state.round_start_time)))
    st.write(f"⏳ Time remaining: {remaining_time} seconds")

    current_canton = st.session_state.round_cantons[round_idx]

    if not st.session_state.round_finished and remaining_time == 0:
        st.session_state.feedback_message = "⏱️ Time's up!"
        st.session_state.round_finished = True
        st.session_state.reveal_message = f"The correct answer was: {current_canton}"

    if not st.session_state.hints and not st.session_state.round_finished:
        row = df[(df["canton"] == current_canton) & (df["difficulty"] == DEFAULT_DIFFICULTY)].sample(1).iloc[0]
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
                normalized_guess = guess.strip().lower()
                normalized_answer = current_canton.lower()
                correct = normalized_guess == normalized_answer or fuzz.token_set_ratio(normalized_guess, normalized_answer) >= 85

                if correct:
                    st.session_state.feedback_message = f"✅ Correct! You earned {st.session_state.pending_score} points."
                    st.session_state.score += st.session_state.pending_score
                    st.session_state.round_finished = True
                else:
                    st.session_state.attempts_left -= 1
                    if st.session_state.attempts_left == 0:
                        st.session_state.feedback_message = "❌ No attempts left."
                        st.session_state.round_finished = True
                        st.session_state.reveal_message = f"The correct answer was: {current_canton}"
                    else:
                        st.session_state.feedback_message = f"❌ Wrong guess. {st.session_state.attempts_left} attempt(s) left."

                st.session_state.clear_guess = True
                st.rerun()

        with col2:
            if st.button("Next Hint"):
                hint_found = False
                st.session_state.current_difficulty -= 1
                used_hints = set(st.session_state.hints)

                while st.session_state.current_difficulty >= 1:
                    available_hints = df[(df["canton"] == current_canton) & (df["difficulty"] == st.session_state.current_difficulty)]
                    unused_hints = available_hints[~available_hints.apply(lambda r: f"{r['type']}: {r['hint']}" in used_hints, axis=1)]

                    if not unused_hints.empty:
                        selected = unused_hints.sample(1).iloc[0]
                        st.session_state.hints.append(f"{selected['type']}: {selected['hint']}")
                        st.session_state.current_question = selected
                        st.session_state.pending_score = max(1, st.session_state.current_difficulty)
                        hint_found = True
                        st.rerun()

                    st.session_state.current_difficulty -= 1

                if not hint_found:
                    st.warning("No more hints available.")

    if st.session_state.round_finished:
        st.info(st.session_state.reveal_message)
        time.sleep(2)
        init_game_state()
        st.session_state.rounds = st.session_state.rounds
        st.session_state.round_cantons = st.session_state.round_cantons
        st.session_state.current_round = round_idx + 1
        st.session_state.username = st.session_state.username
        st.session_state.leaderboard = st.session_state.leaderboard
        st.session_state.score = st.session_state.score
        st.session_state.game_started = True
        st.session_state.round_start_time = time.time()
        st.rerun()

# ----- Stage 4: Game Over -----
else:
    st.title("Game Over")
    final_score = st.session_state.score
    st.write(f"🎉 Final Score: {final_score} / {st.session_state.rounds * 10}")

    name = st.session_state.username
    st.session_state.leaderboard[name] = max(final_score, st.session_state.leaderboard.get(name, 0))

    if st.button("Play Again"):
        leaderboard = st.session_state.leaderboard.copy()
        st.session_state.clear()
        st.session_state.leaderboard = leaderboard
        st.rerun()
