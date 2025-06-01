# ----- Import necessary libraries -----
import streamlit as st  # Streamlit is used for creating the web app interface
from streamlit_autorefresh import st_autorefresh  # Allows page to refresh automatically (for countdown timer)
import random  # To randomly select cantons and hints
import time  # To track how much time has passed in a round
import pandas as pd  # To load and manipulate the hint data from Excel
from rapidfuzz import fuzz  # Used for fuzzy matching to allow minor typos in user guesses

# ----- Load game data from Excel file -----
@st.cache_data  # Caches the data so it's not reloaded on every interaction
def load_hint_data(path="Data/data_new_long_format.xlsx"):
    """Reads the Excel file containing canton hints and returns it as a DataFrame."""
    df = pd.read_excel(path)
    return df

# Load the data and extract a unique list of cantons
df = load_hint_data("Data/data_new_long_format.xlsx")
cantons = df["canton"].unique().tolist()

# ----- Initialize leaderboard -----
if "leaderboard" not in st.session_state:
    st.session_state.leaderboard = {}  # Keeps track of each user's highest score

# ----- Initialize game state -----
# Set default values for all session variables at the start of the game
if "rounds" not in st.session_state:
    # Game progress tracking (number, score, current round, etc.)
    st.session_state.rounds = 0 
    st.session_state.score = 0 
    st.session_state.current_round = 0 
    st.session_state.round_cantons = []  # List of cantons for current round (randomly selected, see below)

    # Round level variables (difficulty, score, current hint, etc.)
    st.session_state.current_difficulty = 10  
    st.session_state.pending_score = 10 
    st.session_state.current_question = None
    st.session_state.correct = False
    st.session_state.hints = [] 
    st.session_state.attempts_left = 2 
    st.session_state.round_start_time = None 
    st.session_state.round_finished = False 

    # Feedback initialization
    st.session_state.reveal_message = "" 
    st.session_state.feedback_message = ""  

    # User session variables
    st.session_state.username = "" 
    st.session_state.game_started = False  

# =======================
# STAGE 1: START SCREEN
# =======================
if st.session_state.rounds == 0 and not st.session_state.game_started:
    st.title("🇨🇭 Canton Guessing Game")

    # Expandable section with game instructions
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

    # Show leaderboard (top 5 scores)
    if st.session_state.leaderboard:
        st.subheader("🏆 Leaderboard (Top 5)")
        top_scores = sorted(st.session_state.leaderboard.items(), key=lambda x: -x[1])[:5]
        for name, score in top_scores:
            st.write(f"{name}: {score} points")

    # Let the player choose the number of rounds and continue
    rounds = st.radio("Choose number of rounds:", [4, 8, 12])
    if st.button("Continue"):
        st.session_state.rounds = rounds
        # Randomly choose the cantons to guess in this session
        st.session_state.round_cantons = random.sample(cantons, rounds)
        st.rerun()

# =======================
# STAGE 2: NAME INPUT
# =======================
elif not st.session_state.game_started:
    st.title("Enter your name")
    name = st.text_input("Username:")
    if name and st.button("Start Game"):
        # Store name, mark game as started, and note start time
        st.session_state.username = name
        st.session_state.game_started = True
        st.session_state.round_start_time = time.time()
        st.rerun()

# =======================
# STAGE 3: GAMEPLAY
# =======================
elif st.session_state.current_round < st.session_state.rounds:
    # Use autorefresh to make timer work
    if not st.session_state.round_finished:
        st_autorefresh(interval=1000, limit=45, key="auto_refresh")

    # Reset guess input box if necessary
    input_key = f"guess_input_{st.session_state.current_round}"
    if st.session_state.get("clear_guess", False):
        st.session_state[input_key] = ""
        st.session_state.clear_guess = False

    # Show header and current status
    st.title(f"Round {st.session_state.current_round + 1} of {st.session_state.rounds}")
    st.write(f"Player: {st.session_state.username}")
    st.write(f"Score: {st.session_state.score}")
    st.write(f"Attempts left: {st.session_state.attempts_left}")

    # Timer logic: show countdown from 45 seconds
    start_time = st.session_state.round_start_time or time.time()
    remaining_time = max(0, int(45 - (time.time() - start_time)))
    st.write(f"⏳ Time remaining: {remaining_time} seconds")

    current_canton = st.session_state.round_cantons[st.session_state.current_round]

    # If time runs out, end the round and reveal the answer
    if not st.session_state.round_finished and remaining_time == 0:
        st.session_state.feedback_message = "⏱️ Time's up!"
        st.session_state.round_finished = True
        st.session_state.reveal_message = f"The correct answer was: {current_canton}"

    # Load the first (hardest) hint if none shown yet
    if not st.session_state.hints and not st.session_state.round_finished:
        hint_rows = df[(df["canton"] == current_canton) & (df["difficulty"] == st.session_state.current_difficulty)]
        if not hint_rows.empty:
            row = hint_rows.sample(1).iloc[0]
            st.session_state.current_question = row
            st.session_state.hints.append(f"{row['type']}: {row['hint']}")

    # Display all hints shown so far
    st.subheader("Hints so far:")
    for hint in st.session_state.hints:
        st.write(f"- {hint}")

    # Show feedback (e.g., "Wrong guess" or "Correct!")
    if st.session_state.feedback_message:
        st.info(st.session_state.feedback_message)

    # ======= PLAYER INPUT + ACTIONS =======
    if not st.session_state.round_finished:
        col1, col2 = st.columns(2)

        # ----- Column 1: Guess input -----
        with col1:
            guess = st.text_input("Your Guess:", key=input_key)

            if guess:
                # Normalize both guess and target to lowercase
                normalized_guess = guess.strip().lower()
                normalized_answer = current_canton.lower()

                # Check exact match or fuzzy match ≥ 85%
                if normalized_guess == normalized_answer:
                    correct = True
                else:
                    similarity = fuzz.token_set_ratio(normalized_guess, normalized_answer)
                    correct = similarity >= 85

                if correct:
                    st.session_state.feedback_message = f"✅ Correct! You earned {st.session_state.pending_score} points."
                    st.session_state.score += st.session_state.pending_score
                    st.session_state.round_finished = True
                    st.session_state.clear_guess = True
                    st.rerun()
                else:
                    # Handle incorrect guess
                    st.session_state.attempts_left -= 1
                    st.session_state.clear_guess = True
                    if st.session_state.attempts_left == 0:
                        st.session_state.feedback_message = "❌ No attempts left."
                        st.session_state.round_finished = True
                        st.session_state.reveal_message = f"The correct answer was: {current_canton}"
                    else:
                        st.session_state.feedback_message = f"❌ Wrong guess. {st.session_state.attempts_left} attempt(s) left."
                    st.rerun()

        # ----- Column 2: Ask for next hint -----
        with col2:
            if st.button("Next Hint", key="next_hint_button"):
                hint_found = False
                while st.session_state.current_difficulty > 1:
                    used_hints = set(st.session_state.hints)

                    # Get all hints of current difficulty not yet used
                    available_hints = df[
                        (df["canton"] == current_canton) &
                        (df["difficulty"] == st.session_state.current_difficulty)
                    ]
                    unused_hints = available_hints[
                        ~available_hints.apply(lambda r: f"{r['type']}: {r['hint']}" in used_hints, axis=1)
                    ]

                    # If hint found, use it
                    if not unused_hints.empty:
                        selected = unused_hints.sample(1).iloc[0]
                        st.session_state.current_question = selected
                        st.session_state.hints.append(f"{selected['type']}: {selected['hint']}")
                        st.session_state.pending_score = max(1, st.session_state.current_difficulty)
                        hint_found = True
                        st.rerun()
                        break
                    # No hints found for current difficulty, try easier level
                    st.session_state.current_difficulty -= 1

                if not hint_found:
                    st.warning("No more hints available.")

    # ======= END OF ROUND: show answer and transition =======
    if st.session_state.round_finished:
        st.info(st.session_state.reveal_message)
        time.sleep(2)  # Wait 2 seconds before moving to next round
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

# =======================
# STAGE 4: GAME OVER
# =======================
else:
    st.title("Game Over")

    # Show total score
    final_score = st.session_state.score
    st.write(f"🎉 Final Score: {final_score} / {st.session_state.rounds * 10}")

    # Update leaderboard (keep highest score per user)
    name = st.session_state.username
    st.session_state.leaderboard[name] = max(final_score, st.session_state.leaderboard.get(name, 0))

    # Option to replay the game
    if st.button("Play Again"):
        leaderboard = st.session_state.leaderboard  # Save current leaderboard
        st.session_state.clear()  # Reset game
        st.session_state.leaderboard = leaderboard  # Restore leaderboard
        st.rerun()


