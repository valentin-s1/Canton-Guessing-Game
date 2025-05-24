##### test
# streamlit_canton_game.py
import streamlit as st
import random
import pandas as pd

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
if "rounds" not in st.session_state:
    st.session_state.rounds = 0
    st.session_state.score = 0
    st.session_state.current_round = 0
    st.session_state.round_cantons = []
    st.session_state.current_difficulty = 10
    st.session_state.pending_score = 10
    st.session_state.current_question = None
    st.session_state.correct = False

# ----- Spielstart: Auswahl der Rundenzahl -----
if st.session_state.rounds == 0:
    st.title("🇨🇭 Canton Guessing Game")
    st.write("Choose number of rounds:")
    rounds = st.radio("Rounds", [4, 8, 12])
    if st.button("Start Game"):
        st.session_state.rounds = rounds
        st.session_state.round_cantons = random.sample(cantons, rounds)
        st.rerun()

# ----- Aktuelle Spielrunde anzeigen -----
elif st.session_state.current_round < st.session_state.rounds:
    st.title(f"Round {st.session_state.current_round + 1} of {st.session_state.rounds}")
    st.write(f"Current Score: {st.session_state.score}")
    
    current_canton = st.session_state.round_cantons[st.session_state.current_round]

    if st.session_state.current_question is None:
        question_row = df[(df["canton"] == current_canton) & (df["difficulty"] == st.session_state.current_difficulty)].iloc[0]
        st.session_state.current_question = question_row

    st.subheader(f"Question (Difficulty {st.session_state.current_difficulty})")
    st.write(st.session_state.current_question["question"])

    col1, col2 = st.columns(2)
    with col1:
        guess = st.text_input("Your Guess:")
        if guess:
            if guess.strip().lower() == current_canton.lower():
                st.success(f"Correct! You earned {st.session_state.pending_score} points.")
                st.session_state.score += st.session_state.pending_score
                st.session_state.correct = True
    
    with col2:
        if st.button("Don't know / Next Hint"):
            if st.session_state.current_difficulty > 1:
                st.session_state.current_difficulty -= 1
                st.session_state.pending_score -= 1
                st.session_state.current_question = None
            else:
                st.warning(f"No more hints. The correct answer was: {current_canton}.")
                st.session_state.correct = True

    if st.session_state.correct:
        if st.button("Next Round"):
            st.session_state.current_round += 1
            st.session_state.current_difficulty = 10
            st.session_state.pending_score = 10
            st.session_state.current_question = None
            st.session_state.correct = False
            st.rerun()

# ----- GAME END -----
else:
    st.title("Game Over")
    st.write(f"Total Score: {st.session_state.score} / {st.session_state.rounds * 10}")
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
# 2. type: streamlit run Code/main.py 

# new idea
