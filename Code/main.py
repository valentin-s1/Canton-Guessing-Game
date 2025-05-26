##### test
# streamlit_canton_game.py
import streamlit as st
import random
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh

# ----- Simulierter Datensatz: Jeder Kanton hat 10 Fragen (Schwierigkeit 10 bis 1) -----
cantons = [
    "Zürich", "Bern", "Luzern", "Uri", "Schwyz", "Obwalden", "Nidwalden",
    "Glarus", "Zug", "Fribourg", "Solothurn", "Basel-Stadt", "Basel-Landschaft",
    "Schaffhausen", "Appenzell Ausserrhoden", "Appenzell Innerrhoden", "St. Gallen",
    "Graubünden", "Aargau", "Thurgau", "Ticino", "Vaud", "Valais", "Neuchâtel", "Genève", "Jura"
]

data = []
for canton in cantons:
    for diff in range(10, 0, -1):  # 10 = schwerste Frage, 1 = einfachste
        data.append({
            "canton": canton,
            "difficulty": diff,
            "question": f"Frage {diff} zu {canton} (Platzhalter)",
            "answer": canton  # Richtige Antwort ist immer der Kantonname
        })

df = pd.DataFrame(data)

# ----- Session-Setup -----
# ----- Session state init -----
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
    st.session_state.round_start_time = time.time()
    st.session_state.round_finished = False
    st.session_state.reveal_message = ""
    st.session_state.feedback_message = "" 

# ----- Start screen -----
if st.session_state.rounds == 0:
    st.title("🇨🇭 Canton Guessing Game")
    st.write("Choose number of rounds:")
    rounds = st.radio("Rounds", [4, 8, 12])
    if st.button("Start Game"):
        st.session_state.rounds = rounds
        st.session_state.round_cantons = random.sample(cantons, rounds)
        st.session_state.round_start_time = time.time() # start timer for the first round
        st.rerun()

# ----- Game round -----
elif st.session_state.current_round < st.session_state.rounds:
    
    # NEU: Automatisches Refresh-Intervall (1 Sekunde) für max. 45 Sekunden
    if not st.session_state.round_finished:
        st_autorefresh(interval=1000, limit=45, key="auto_refresh")

    # Reset guess input before rendering it again
    input_key = f"guess_input_{st.session_state.current_round}"
    if st.session_state.get("clear_guess", False):
        st.session_state[input_key] = ""
        st.session_state.clear_guess = False

    st.title(f"Round {st.session_state.current_round + 1} of {st.session_state.rounds}")
    st.write(f"Score: {st.session_state.score}")
    st.write(f"Remaining attempts: {st.session_state.attempts_left}")
    remaining_time = max(0, int(45 - (time.time() - st.session_state.round_start_time)))
    st.write(f"⏳ Time remaining: {remaining_time} seconds")

    current_canton = st.session_state.round_cantons[st.session_state.current_round]

    # Timeout check
    if not st.session_state.round_finished and remaining_time == 0:
        st.session_state.feedback_message = "⏱️ Time's up!"
        st.session_state.round_finished = True
        st.session_state.reveal_message = f"The correct answer was: {current_canton}"

    # Load first hint if none yet
    if not st.session_state.hints and not st.session_state.round_finished:
        first_hint = df[
            (df["canton"] == current_canton) &
            (df["difficulty"] == st.session_state.current_difficulty)
        ].iloc[0]
        st.session_state.current_question = first_hint
        st.session_state.hints.append(first_hint["question"])

    # Show all hints so far
    st.subheader("Hints so far:")
    for hint in st.session_state.hints:
        st.write(f"- {hint}")

    # Show feedback message (e.g., wrong guess, correct, time's up)
    if "feedback_message" in st.session_state and st.session_state.feedback_message:
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

                    next_hint = df[
                        (df["canton"] == current_canton) &
                        (df["difficulty"] == st.session_state.current_difficulty)
                    ].iloc[0]

                    st.session_state.current_question = next_hint
                    st.session_state.hints.append(next_hint["question"])
                    st.rerun()
                else:
                    st.warning("No more hints available.")

    # If round is over
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
    st.write(f"🎉 Final Score: {st.session_state.score} / {st.session_state.rounds * 10}")
    if st.button("Play Again"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()



# ----- Instructions -----
# So far, the game consists of 10 difficulty levels, but each of the 10 question
# refers to the same canton as the correct answer. The game is played in rounds, and the player
# has to guess the canton based on the question. The player can ask for hints, which reduce the score.

# To-do: 
# - Add a real question and answer dataset
# - Add what happens if the player doesn't know the answer / wrong answer
#--> i.e. maybe two tries or whatever then skip to next difficulty level 

# - Add a feature to show the correct answer after the game
# - Add a scoring system based on the number of hints used
# - Add a timer for each question
# - Add a leaderboard to track high scores
# - Add a feature to allow players to submit their own questions and answers
# - Add a feature to allow players to challenge their friends
# - Add a feature to allow players to play against each other in real-time
### or whatever (and adjust the code as now mainly chagpt)


# ------ To run the code -----
# 1. Install streamlit: pip install streamlit
# pip install streamlit-autorefresh
# 2. type: streamlit run Code/main.py 

# new idea
