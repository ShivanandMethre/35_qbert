 # Q*bert Repair Lab

This project is a single-file Q*bert-lite clone using **Pygame**. It introduces students to isometric projection, diagonal hop validation, and enemy chase behavior using a small, readable object-oriented codebase.

---

## What's Provided

A working Q*bert-lite game with:

* A pyramid of cubes the player hops across diagonally, painting each cube toward its target color on landing
* Coily, an enemy that chases the player across the pyramid, and red balls that roll downward
* Falling off the edge of the pyramid (or bumping an enemy while grounded) costs a life
* Levels, lives, and scoring, with a win once every cube reaches its target color
* Different color palettes for different levels
* Cube completion flash effect
* Bonus life every 1000 points
* Sound effects and high-score saving

The project contains **one deliberate bug** and **three optional features**, which are completed using an iterative process involving an AI assistant and critical code review.

### Use an LLM (e.g. ChatGPT or Claude) as your debugging and pair-programming partner for this lab.

---

## Getting Started

### Setup

1. Make sure you have Python 3.10+ installed.

2. Install dependencies:

```bash
pip install pygame
```

3. Run the game:

```bash
python game.py
```

**Controls:** Left/Up/Down/Right to hop diagonally, `R` to reset, Space to continue after clearing a level.

---

## Tasks Completed

Each task was completed using an iterative process involving LLM suggestions and critical code review.

### Task 1: Fix the pyramid projection bug 

The pyramid projection was corrected by using true division (`row / 2`) instead of integer division (`row // 2`) so that the pyramid renders as a symmetric triangle.

### Task 2: Implement `cube_palette(level)` 

Implemented different three-color palettes for different levels.

### Task 3: Implement `on_cube_completed(cell)` 

Implemented a brief visual flash when a cube reaches its target color.

### Task 4: Implement `bonus_life_threshold()` 

Implemented a bonus life every 1000 points.

---

## Expected Behavior

* The pyramid renders as a symmetric triangle of cubes
* Landing on a cube advances its color exactly one stage, only once per hop
* Hopping off the edge of the pyramid makes the player fall and costs a life
* Coily chases **toward** the player's current position rather than away from it
* Painting every cube to its target color wins the level; running out of lives ends the game
* Different levels use different cube color palettes
* Completed cubes briefly flash
* A bonus life is awarded every 1000 points

---

## Folder Structure

```text
qbert/
├── game.py
└── README.md
```

---

## Submission Checklist

Submission is only the following three things:

* [ ] A 10-second video of gameplay **before** your changes, showing the bug/broken behavior
* [ ] A 10-second video of gameplay **after** your changes, showing the bug fixed and the new features working
* [ ] The Chat/LLM used page link, with the complete chat history
