# Elo-Predictions

This project focuses on the statistical analysis of chess games to predict a player's Elo rating. By processing a large dataset of online chess games, the goal is to build a regression model that estimates a player's rating based on various in-game performance metrics and to identify which features are most indicative of a player's skill level.

## 1. Data Source

The dataset for this project was built from the Lichess Open Database, a public repository of chess games played on the platform.

* **Data Scope**: The analysis uses standard rated games played in **March 2025**.
* **Volume**: This specific monthly dump contains over **97 million games** , totaling approximately **31.8 GB** of data in the PGN (Portable Game Notation) format.
* **License**: The database is released under the **Creative Commons CC0 license**, which allows for free use, modification, and redistribution.

## 2. Data Processing Pipeline

### Custom PGN Parser

To efficiently process the massive volume of game data (~97 million games), a custom, high-performance PGN parser was developed. Standard solutions, such as the parser in the `python-chess` library, were found to be too slow for a dataset of this scale. The new parser was implemented in **C++** for maximum speed, with **Pybind11** used to create Python bindings for easy integration into the data analysis workflow.

### Preprocessing and Selection

1.  **Game Selection**: To ensure consistency and representativeness, the project focuses exclusively on games played with a **rapid 10+0 time control** (10 minutes per player). This format was chosen as it is a highly popular and representative time control, providing a good basis for analysis.

2.  **Player Selection**: A total of **15,000 players** who played a sufficient number of games meeting the criteria were selected for the final dataset. The sampling strategy was designed to create a balanced dataset:
    * **67%** of players were chosen randomly, resulting in a dataset that mirrors the natural (approximately normal) distribution of ratings on Lichess.
    * **33%** of players were selected to ensure a uniform distribution of ratings across the entire spectrum, from beginner to master level. This prevents the model from being biased toward the most common rating brackets.

### Dataset Creation

The final dataset was split into:
* A **training set** containing **10,000** players.
* A **testing set** containing **5,000** players.

Each record in the dataset corresponds to one player and includes a variety of numerical features calculated from at least 10 of their games. The target variable is the player's `elo` rating. Key features include:
* `avg_cp_loss`: Average centipawn loss per move, measuring inaccuracy against the Stockfish 16 engine.
* `avg_inacc`, `avg_mist`, `avg_blund`: Average number of inaccuracies, mistakes, and blunders per game.
* `frac_time_win`, `frac_time_loss`: The fraction of total game time a player uses on moves in their won vs. lost games.
* `avg_book_moves`: The average number of opening moves that follow established chess theory.

## 3. Statistical Analysis

The primary objective is to perform a comprehensive statistical analysis and build a regression model to predict player Elo ratings based on the engineered features[cite: 869]. The analysis will be conducted in accordance with the laboratory assignments for the "Statistics in Artificial Intelligence and Data Analysis" course. The goal of the model is to predict the ELO value based on game style and decision quality statistics, which allows for an analysis of which features most significantly influence a player's chess level.
