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

# ----- Game state initialization -----
def initialize_game_state():
    """Initialize or reset all game state variables"""
    # Game progress tracking
    st.session_state.rounds = 0 
    st.session_state.score = 0 
    st.session_state.current_round = 0 
    st.session_state.round_cantons = []
    st.session_state.all_hints = {}  # New: Stores all hints for current game
    
    # Round level variables
    st.session_state.current_difficulty = 10  
    st.session_state.pending_score = 10 
    st.session_state.hints = [] 
    st.session_state.attempts_left = 2  # Players get 2 attempts per round
    st.session_state.round_start_time = None 
    st.session_state.round_finished = False 
    
    # Feedback messages
    st.session_state.reveal_message = "" 
    st.session_state.feedback_message = ""  
    
    # User session
    st.session_state.username = "" 
    st.session_state.game_started = False  

# Initialize if not already set
if "rounds" not in st.session_state:
    initialize_game_state()

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
        # Pre-load all hints for these cantons for faster access during game
        st.session_state.all_hints = {
            canton: df[df["canton"] == canton].sort_values('difficulty', ascending=False)
            .to_dict('records')
            for canton in st.session_state.round_cantons
        }
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
    # Use autorefresh to make timer work (limited to 45 refreshes max)
    if not st.session_state.round_finished:
        st_autorefresh(interval=1000, limit=45, key="auto_refresh")

    current_canton = st.session_state.round_cantons[st.session_state.current_round]
    
    # Show header and current status
    st.title(f"Round {st.session_state.current_round + 1} of {st.session_state.rounds}")
    st.write(f"Player: {st.session_state.username}")
    st.write(f"Score: {st.session_state.score}")
    st.write(f"Attempts left: {st.session_state.attempts_left}")

    # Timer logic - more efficient calculation using saved start time
    start_time = st.session_state.round_start_time or time.time()
    remaining_time = max(0, int(45 - (time.time() - start_time)))
    st.write(f"⏳ Time remaining: {remaining_time} seconds")

    # Handle timeout
    if not st.session_state.round_finished and remaining_time == 0:
        st.session_state.feedback_message = "⏱️ Time's up!"
        st.session_state.round_finished = True
        st.session_state.reveal_message = f"The correct answer was: {current_canton}"
        st.rerun()

    # Load first hint if none shown yet (using pre-loaded hints)
    if not st.session_state.hints and not st.session_state.round_finished:
        # Get the hardest hint (difficulty 10) for current canton
        available_hints = [h for h in st.session_state.all_hints[current_canton] 
                          if h['difficulty'] == 10]
        if available_hints:
            hint = random.choice(available_hints)
            st.session_state.hints.append(f"{hint['type']}: {hint['hint']}")

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
            # Using round number in key ensures fresh input each round
            guess = st.text_input("Your Guess:", 
                                key=f"guess_{st.session_state.current_round}")

            if guess:
                # Normalized comparison with fuzzy matching
                normalized_guess = guess.strip().lower()
                normalized_answer = current_canton.lower()
                similarity = fuzz.token_set_ratio(normalized_guess, normalized_answer)
                correct = (normalized_guess == normalized_answer) or (similarity >= 85)

                if correct:
                    st.session_state.feedback_message = f"✅ Correct! You earned {st.session_state.pending_score} points."
                    st.session_state.score += st.session_state.pending_score
                    st.session_state.round_finished = True
                    st.rerun()
                else:
                    # Handle incorrect guess
                    st.session_state.attempts_left -= 1
                    if st.session_state.attempts_left <= 0:  # Changed to <= 0 for safety
                        st.session_state.feedback_message = "❌ No attempts left."
                        st.session_state.round_finished = True
                        st.session_state.reveal_message = f"The correct answer was: {current_canton}"
                    else:
                        st.session_state.feedback_message = f"❌ Wrong guess. {st.session_state.attempts_left} attempt(s) left."
                    st.rerun()

        # ----- Column 2: Ask for next hint -----
        with col2:
            if st.button("Next Hint", key="next_hint_button"):
                # Get all unused hints that are easier than current difficulty
                used_hint_texts = set(st.session_state.hints)
                available_hints = [
                    h for h in st.session_state.all_hints[current_canton]
                    if h['difficulty'] < st.session_state.current_difficulty
                    and f"{h['type']}: {h['hint']}" not in used_hint_texts
                ]
                
                if available_hints:
                    # Select the most difficult remaining hint
                    selected = max(available_hints, key=lambda x: x['difficulty'])
                    st.session_state.hints.append(f"{selected['type']}: {selected['hint']}")
                    st.session_state.current_difficulty = selected['difficulty']
                    st.session_state.pending_score = max(1, selected['difficulty'])
                    st.rerun()
                else:
                    st.warning("No more hints available.")

    # ======= END OF ROUND: transition to next round =======
    if st.session_state.round_finished:
        st.info(st.session_state.reveal_message)
        time.sleep(2)  # Brief pause before next round
        
        # Reset round-specific variables
        st.session_state.current_round += 1
        st.session_state.current_difficulty = 10
        st.session_state.pending_score = 10
        st.session_state.hints = []
        st.session_state.attempts_left = 2  # Reset attempts for new round
        st.session_state.round_start_time = time.time()
        st.session_state.round_finished = False
        st.session_state.reveal_message = ""
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
        initialize_game_state()  # Reset game using our function
        st.session_state.leaderboard = leaderboard  # Restore leaderboard
        st.rerun()
