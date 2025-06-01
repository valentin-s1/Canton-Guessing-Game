# ----- Import necessary libraries -----
import streamlit as st  # Streamlit is used for creating the web app interface
from streamlit_autorefresh import st_autorefresh  # Allows page to refresh automatically (for countdown timer)
import random
import time 
import pandas as pd 
from rapidfuzz import fuzz  # for fuzzy string matching (to check guesses against canton names)

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
    st.title("CH Canton Guessing Game")

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
    # This block handles user input during a quiz round — specifically, the user's guess and the response logic
    if not st.session_state.round_finished:
        # Divide the UI into two columns for layout purposes
        col1, col2 = st.columns(2)

        # ----- Column 1: Guess input -----
        with col1:
            # Display a text input box for the user to enter their guess
            # The input is stored with a key to allow clearing/resetting later
            guess = st.text_input("Your Guess:", key=input_key)

            # Proceed only if the user has entered something
            if guess:
                # Normalize both guess and correct answer to lowercase and strip whitespace for robust comparison
                normalized_guess = guess.strip().lower()
                normalized_answer = current_canton.lower()

                # Determine whether the guess is correct
                # First, check for an exact match
                if normalized_guess == normalized_answer:
                    correct = True
                else:
                    # If not exact, compute fuzzy match score (token set ratio)
                    # A score ≥ 85 is considered a correct match
                    similarity = fuzz.token_set_ratio(normalized_guess, normalized_answer)
                    correct = similarity >= 85

                # ======= CORRECT GUESS =======
                if correct:
                    # Show positive feedback to the user with points earned
                    st.session_state.feedback_message = f"✅ Correct! You earned {st.session_state.pending_score} points."
                    # Add the score for this round to the total score
                    st.session_state.score += st.session_state.pending_score
                    # Mark the round as finished so the app doesn’t allow more guesses for this round
                    st.session_state.round_finished = True
                    # Clear the text input on rerun
                    st.session_state.clear_guess = True
                    # Rerun the app so that changes are reflected immediately (feedback shown, inputs locked, etc.)
                    st.rerun()

                # ======= INCORRECT GUESS =======
                else:
                    # Deduct one attempt
                    st.session_state.attempts_left -= 1
                    # Clear the text input box on rerun
                    st.session_state.clear_guess = True

                    # If no attempts remain, end the round and show the correct answer
                    if st.session_state.attempts_left == 0:
                        st.session_state.feedback_message = "❌ No attempts left."
                        st.session_state.round_finished = True
                        st.session_state.reveal_message = f"The correct answer was: {current_canton}"
                    else:
                        # Otherwise, inform the player of the incorrect guess and how many tries are left
                        st.session_state.feedback_message = f"❌ Wrong guess. {st.session_state.attempts_left} attempt(s) left."
                    # Rerun the app to immediately update the interface and feedback message
                    st.rerun()

                # ----- Column 2: Ask for next hint -----
        with col2:
            # Button to request the next hint
            if st.button("Next Hint", key="next_hint_button"):
                hint_found = False # Flag to track whether a new hint was successfully added
                
                # Reduce the difficulty level by 1 to ensure next hint is *easier* than the last
                st.session_state.current_difficulty -= 1

                # Loop to continue searching for a hint at lower difficulties if none are available at current level
                while st.session_state.current_difficulty >= 1:
                    # Keep track of hints that have already been shown, so we don’t repeat them
                    used_hints = set(st.session_state.hints)

                    # Filter the full dataset to get hints:
                        # - for the current canton in this round
                        # - at the current (decreased) difficulty level
                    available_hints = df[
                        (df["canton"] == current_canton) &
                        (df["difficulty"] == st.session_state.current_difficulty)
                    ]

                    # Of these available hints, exclude the ones that have already been shown
                    unused_hints = available_hints[
                        ~available_hints.apply(lambda r: f"{r['type']}: {r['hint']}" in used_hints, axis=1)
                    ]

                    # If we find any unused hints at this difficulty level:
                    if not unused_hints.empty:
                        # Randomly select one unused hint
                        selected = unused_hints.sample(1).iloc[0]
                        # Store the selected hint as the current question
                        st.session_state.current_question = selected
                        # Append the formatted hint to the list shown to the user
                        st.session_state.hints.append(f"{selected['type']}: {selected['hint']}")
                        # Update the score the user will receive if they guess correctly now.
                        # Score is equal to the current difficulty, but can't go below 1
                        st.session_state.pending_score = max(1, st.session_state.current_difficulty)
                        # Mark that a hint was successfully found so we don’t show a warning
                        hint_found = True
                        # Rerun the Streamlit app so the new hint is displayed immediately
                        st.rerun()
                        # Exit the loop after we found a suitable hint
                        break

                    # If no unused hint was found at this level, go one level easier and try again
                    st.session_state.current_difficulty -= 1

                # If no hints were found at any easier difficulty levels, show a warning to the player
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


