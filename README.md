# 🇨🇭 Guess the Canton – A Swiss Canton Guessing Game

## Project Overview
A Python-based quiz game to guess Swiss cantons based on various hints such as population size, capital city, language, or geographic region. 
The game is text-based, interactive, and designed for casual learning and entertainment.
This repository serves as the **submission of the mandatory group project for course "8,789,1 | Skills: Programming with Advanced Computer Languages" taught by Dr. Mario Silic at the University of St.Gallen in the fall semester of 2024.**


## How It Works
- Players can choose the number of rounds (4,8,or 12) and enter the name (for Leaderboard)
- Each round, a hidden canton is randomly selected.
- It starts with one hard hint (worth 10 points) when clicking "Next hint" the user gets an easier clue (each costs 1 point)
- The player has 2 attempts and 45 seconds to guess
- Input is checked ussing fuzzy matching (>85% similarity is correct)
- Correct guesses earn the remaining points.
- Wrong guesses reduce attempts or end the round.
- Your score accumulates across rounds and at the end, your final score is shown.
- The leaderboard is updated with your best score (by name).
- Once all rounds are played, the leaderboard is displayed, and the game can be played again.


## Code Description
- Programming Language: Python
- Main Packages: streamlit, streamlit_autorefresh, random, time, pandas and rapidfuzz
  - Streamlit is used to build the interactive web interface of the app, allowing users to interact with the game directly in their browser.
  - streamlit_autorefresh enables automatic refreshing of the page, which is useful for updating elements like the countdown timer in real time.
  - random is a built-in Python module used to randomly select cantons and hints, making each game session unique.
  - time helps track the duration of each round, ensuring the game enforces a time limit.
  - pandas is used to load and manipulate the hint data from an Excel file, making it easy to filter and access relevant clues.
  - rapidfuzz allows for fuzzy string matching, so user guesses with minor typos or close matches can still be considered correct.
- Data: The file "data_new_long_format.xlsx" contains data about the cantons, including a column for the correct canton, the difficulty level of the hints, the hint category, and the hint itself.
- Structure
  1. Set-up
     - Load Streamlit, pandas, rapidfuzz, and other utilities for UI, data handling, fuzzy matching, timing, and randomness.
     - Load Game Data: Cached function to read canton hints from Excel into a DataFrame.
     - Extract unique cantons list for the game.
     - Initialize Leaderboard and Game State:
     - Create session variables to track scores, rounds, current hints, guesses left, timing, and player info.
  2. Start Screen:
     - Display game title, instructions, leaderboard, and round number selection.
  3. Name Input:
     - Prompt user to enter their name before starting the game.
  4. Gameplay:
     - Show hints with adjustable difficulty.
     - Accept guesses with fuzzy matching to handle typos.
     - Manage attempts, scoring, countdown timer (45 seconds per round), and feedback.
     - Transition rounds automatically when done.
  5. Game Over:
     - Show final score, update leaderboard with best score, and allow replay while preserving leaderboard.

## Work procedure
- We used iterative testing to identify and fix issues throughout development.
- For example we noticed that minor typos in canton names caused correct answers to be marked wrong. We then integrated the rapidfuzz package for fuzzy matching to allow close-but-not-exact guesses (≥70% similarity).
- Or we also adjusted the scoring system to fairly reflect hint difficulty and attempts used.
- Repeated testing helped us balance gameplay and improve user experience.


## Prerequisites

```bash
pip install streamlit streamlit-autorefresh rapidfuzz
```

Clone this repository onto your local drive with [git](https://git-scm.com/).

```bash
git clone https://github.com/valentin-s1/Canton-Guessing-Game
```

## Usage

To run the game, simply navigate to the folder containing the source code and execute [runner.py](https://github.com/valentin-s1/Canton-Guessing-Game/Code/game_Noe_v3.py).

``` bash
cd .../tictactoe 
streamlit run Code/game_Noe_v3.py
```

Consequently, a game window opens where the user can click the corresponding buttons and tiles to play the game. 

## Authors

- Valentin Schnellmann  21-610-084
- Noé Peterhans ....
- Claudia Oberhänsli 20-722-468
- Flamur Miskiqi 17-602-269


