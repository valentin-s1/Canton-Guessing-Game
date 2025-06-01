# Guess the Canton – A Swiss Canton Guessing Game

## Project Overview

A Python-based quiz game to guess Swiss cantons based on various hints such as population size, capital city, language, or geographic region. 
The game is text-based, interactive, and designed for casual learning and entertainment.
This repository serves as the **submission of the mandatory group project for course "8,789,1 | Skills: Programming with Advanced Computer Languages" taught by Dr. Mario Silic at the University of St.Gallen in the spring semester of 2025.**


#### How It Works

- Players can choose the number of rounds (4, 8, or 12) and enter their name (for Leaderboard)
- Each round, a hidden canton is randomly selected
- It starts with one hard hint (worth 10 points) when clicking "Next hint" the user gets an easier clue (each new hint deducts 1 point of players score)
- The player has 2 attempts and 45 seconds to guess for each round
- Input is checked using exact and fuzzy matching (>85% similarity is correct)
- Correct guesses earn the remaining points
- Wrong guesses reduce attempts or end the round
- Your score accumulates across rounds and at the end, your final score is shown
- The leaderboard is updated with your best score (by name)
- Once all rounds are played, the leaderboard is displayed, and the game can be played again

---

## Programming Language and Libraries

- **Language**: Python
- **Main Packagees**:
  - `streamlit`: Builds the interactive web app, allowing users to interact witht he game directly in their browser
  - `streamlit_autorefresh`: Enables automatic refreshing the page, which is used for updating the countdown timer in real time
  - `random`: Built-in Python module used to randomly select cantons and hints, making each game session unique
  - `time`: Tracks countdowns and ensuring the game enforces a time limit
  - `pandas`: Used to load and filter the data from Excel
  - `rapidfuzz`: Allows fuzzy mathcing to tolerate small typos in user input

---

## Data Structure

The game uses a custom-built dataset  compiled by the authors and includes hints for all 26 Swiss cantons across multiple difficulty levels and categories.
It is stored in [`data_new_long_format.xlsx`](Data/data_new_long_format.xlsx), containing:
- canton: The correct answer for each hint
- difficulty: Numeric difficulty level (1-10)
- type: Hint category
- hint: the actual clue shown to the user

---

## Code Architecture

The game runs throguh four main stages, with persistent variables managed using 'st.session_state'.

#### 1. Set-up and Initialization
- Imports necessary modules and deines a cached data loader
- Loades the Excel data into a DataFrame and extracts all unique cantons
- Initialize Leaderboard to track top scores
- Initializes session variables:
  - Score and round tracking
  - current difficulty and hints
  - guesses left, timing and player input fields

#### 2. Start Screen
- Displays game instructions and rules using an expandable info box
- Allows players to select the number of rounds (either 4, 8 or 12)
- Shows the leaderboard (top 5 scores)

#### 3. Name Input
- Prompts user to enter a name before gameplay begins
- Starts the timer for the first round upon submission

#### 4. Gameplay
- Each round:
  - Starts with a hard hint (difficulty 10 = 10 points)
  - Offers the option to request new hints (easier ones, i.e. reducing possible score)
  - Allows two guesses per round
  - Includes a real-time countdown (45 sec per round)
- Input is checked using fuzzy string matching (> 85% similarity --> to ensure correct answers even with typos)
- After a correct guess, time-out, or two failed attempts:
  - The round ends with feedback and the correct answer (if wrong/time-out)
  - The next round begins automatically after 2 seconds
 
#### 5. Game Over and Replay
- Shows final score out of maximum possible points (depending on choosen rounds)
- Updates leaderboard, keeping the user's highest score
- Provides an option to replay while preserving leaderboard history

---

## Work procedure
- We used iterative testing to identify and fix issues throughout development
- For example we noticed that minor typos in canton names caused correct answers to be marked wrong. We then integrated the rapidfuzz package for fuzzy matching to allow close-but-not-exact guesses (≥85% similarity)
- Or we also adjusted the scoring system to fairly reflect hint difficulty and attempts used
- Repeated testing helped us balance gameplay and improve user experience

---

## Prerequisites

Install reqiured packages using pip

```bash
pip install streamlit streamlit-autorefresh rapidfuzz
```

Clone this repository onto your local drive with [git](https://git-scm.com/).

```bash
git clone https:/github.com/valentin-s1/Canton-Guessing-Game
```

## Usage

To run the game, simply navigate to the folder containing the source code and execute [game.py](Code/game.py).

``` bash
cd .../Canton-Guessing-Game 
streamlit run Code/game.py
```

Consequently, a game window opens where the user can click the corresponding buttons and tiles to play the game. 

## Authors

- Valentin Schnellmann 21-610-084
- Noé Peterhans 19-617-091
- Claudia Oberhänsli 20-722-468
- Flamur Miskiqi 17-602-269


