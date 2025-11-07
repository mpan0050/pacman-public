# Quick Reference: Implementation Iterations

**Student:** Mohit Pandya (35295252)  
**Assignment:** FIT5222 Assignment 2 - Pacman Capture the Flag  
**Date:** November 7, 2025

## Overview

This document provides a quick visual reference for the 5 implementation iterations.

---

## Iteration Timeline

```
Nov 1-2: Iteration 1 (Old Backup) → FAILED (Timeout)
         ↓
Nov 2:   Iteration 2 (Simple Backup) → FAILED (Too Weak)
         ↓
Nov 2-3: Iteration 3 (Simple Enhanced) → FAILED (Timeout)
         ↓
Nov 3:   Iteration 4 (New Hybrid) → SUCCESS (Viable)
         ↓
Nov 3:   Iteration 5 (Final) → SUBMITTED (45.5% win rate)
```

---

## Architecture Evolution

### Iteration 1: Complex PDDL + Q-Learning

```
GameState → PDDL Solver → High-Level Action
                              ↓
                        Q-Learning Planner
                              ↓
                      Feature Extraction
                              ↓
                         Low-Level Action
```

**Result:** Too slow, timeout failures

---

### Iteration 2: Pure Greedy

```
GameState → Greedy Heuristics → Action
```

**Result:** Too simple, ~35% win rate

---

### Iteration 3: Enhanced PDDL + Q-Learning

```
GameState → PDDL Solver → High-Level Action
                              ↓
                   Enhanced Q-Learning (5 weight sets)
                              ↓
                      40+ Features
                              ↓
                         Low-Level Action
```

**Result:** Even slower than Iteration 1

---

### Iteration 4 & 5: PDDL + Greedy (Final)

```
GameState → PDDL Solver → High-Level Action
                              ↓
                      Greedy Heuristics
                              ↓
                           Action
```

**Result:** Fast, reliable, 45.5% win rate

---

## Complexity Metrics

| Iteration | Lines | Components  | Complexity | Speed | Win Rate |
| --------- | ----- | ----------- | ---------- | ----- | -------- |
| 1         | 708   | PDDL + QL   | High       | Slow  | N/A      |
| 2         | 175   | Greedy      | Low        | Fast  | ~35%     |
| 3         | 1,299 | PDDL + QL++ | Very High  | Slow  | N/A      |
| 4         | 402   | PDDL + G    | Medium     | Fast  | ~42%     |
| 5         | 513   | PDDL + G+   | Medium     | Fast  | 45.5%    |

**Legend:** QL = Q-Learning, G = Greedy

---

## Key Differences

### Iteration 1 vs 2

- **Removed:** PDDL, Q-Learning, Training
- **Added:** Simple greedy heuristics
- **Outcome:** Speed ↑, Performance ↓

### Iteration 2 vs 3

- **Added:** PDDL back, Enhanced Q-Learning, 5 weight sets, 40+ features
- **Outcome:** Complexity ↑↑, Still timeout

### Iteration 3 vs 4

- **Removed:** Q-Learning entirely (saved 897 lines!)
- **Kept:** PDDL for strategy
- **Added:** Simple greedy heuristics
- **Outcome:** Speed ↑↑, Reliability ↑

### Iteration 4 vs 5

- **Refined:** PDDL state representation
- **Improved:** Ghost avoidance, Return triggers, Food selection
- **Added:** Better error handling, More predicates
- **Outcome:** Performance +3.5%

---

## Code Snippets

### Iteration 1: Q-Learning Weights

```python
QLWeights = {
    "offensiveWeights": {
        'closest-food': -3,
        '#-of-ghosts-1-step-away': -100,
        'successorScore': 100,
    },
    "defensiveWeights": {...},
    "escapeWeights": {...}
}
```

### Iteration 2: Pure Greedy

```python
def chooseAction(self, gameState):
    if myState.numCarrying > 0 and ghostNearby:
        return self.escapeHome(gameState, actions)
    elif myState.numCarrying >= 5:
        return self.escapeHome(gameState, actions)
    else:
        return self.attackFood(gameState, actions)
```

### Iteration 5: PDDL + Greedy (Final)

```python
def chooseAction(self, gameState):
    if self.shouldReplan(gameState):
        self.updatePlan(gameState)  # PDDL planning

    # Execute with greedy heuristics
    return self.executeAction(gameState, actions, self.currentAction)
```

---

## Performance Summary

### Measured Results

- **Iteration 2:** ~35% (estimated from testing)
- **Iteration 4:** ~42% (estimated)
- **Iteration 5:** 45.5% (actual: 10W 12L 0T)

### Theoretical Performance

- **Iteration 1 & 3:** Could be 50-55% IF no timeout
- But timeout = 0% effective win rate

---

## What Each Iteration Taught Us

### Iteration 1

**Lesson:** Two-layer planning is too expensive for real-time games

### Iteration 2

**Lesson:** Strategic planning is necessary for competitive play

### Iteration 3

**Lesson:** More complexity doesn't solve the speed problem

### Iteration 4

**Lesson:** PDDL + greedy is the right balance

### Iteration 5

**Lesson:** Small refinements can improve performance

---

## Files Location

```
Assignment_2/backup_files/
├── myTeam_old_backup.py      # Iteration 1
├── myTeam_simple_backup.py   # Iteration 2
├── myTeam_simple.py          # Iteration 3
├── myTeam_new.py             # Iteration 4
└── myTeam_pddl.pddl          # Alternative PDDL

pacman-public/
├── myTeam.py                 # Iteration 5 (FINAL)
└── myTeam.pddl              # Final PDDL domain
```

---

## For Your Report

### Best Figures to Include

1. **Architecture Evolution Diagram** (showing all 5 iterations)
2. **Line Count vs Performance Chart**
3. **Complexity/Speed Trade-off Graph**
4. **Win Rate Progression** (where measured)

### Best Code Comparisons

1. Show chooseAction() method evolution
2. Compare PDDL integration approaches
3. Highlight Q-Learning removal

### Best Tables

1. Iteration Comparison Table (see IMPLEMENTATION_SUMMARY.txt)
2. Performance Metrics Table
3. Feature Count Comparison

---

## Quick Stats for Report

- **Total Iterations:** 5
- **Development Time:** ~3 days (Nov 1-3)
- **Final Performance:** 45.5% win rate (below 57% target)
- **Final Grade Estimate:** CREDIT (60-69%)
- **Code Reduction:** From 1,299 lines (worst) to 513 lines (final)
- **Speed Improvement:** From timeout to reliable execution
- **Key Insight:** Simplicity > Complexity for real-time constraints

---

## End of Quick Reference

For detailed explanations, see:

- `IMPLEMENTATION_LOG.txt` - Full technical details
- `IMPLEMENTATION_SUMMARY.txt` - Complete summary with all sections
- `CONTEXT_FOR_AI.md` - Assignment requirements and context
