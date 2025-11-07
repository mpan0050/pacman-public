# FIT5222 Assignment 2: Pacman Capture the Flag - AI Context File

## CRITICAL INFORMATION

- **Due Date**: 11:55 PM Monday, November 3rd, 2025 (Week 14)
- **Current Date**: November 1, 2025 - **2 DAYS REMAINING**
- **Contest Server**: https://fit5222a2.contest.pathfinding.ai
- **Student**: Mohit Pandya
- **Course**: FIT5222 - Planning and Automated Reasoning

## PROJECT OVERVIEW

Develop an AI controller for a multiplayer Pacman variant where two teams (Red vs Blue) compete to capture food dots from opposing territory.

### Game Mechanics

- **Multi-agent**: 2 agents per team working cooperatively
- **Discrete**: Grid-based maze with unit time steps
- **Partially observable**: 5-square Manhattan distance observation range
- **Deterministic**: Current state depends only on teams and actions
- **Time limit**: 300 timesteps (1200 total actions across 4 agents)

### Core Rules

- Agents are **ghosts** on home territory, **Pacman** on enemy territory
- Eating food stores it in a virtual backpack; returning home deposits it for points
- Being caught by a ghost returns all backpack food to original positions
- **Power capsules** scare ghosts for 40 timesteps
- **Noisy distance readings**: ±6 steps error for all agents
- Game ends when one team captures all but 2 opponent dots, or after 300 timesteps

## WORKSPACE STRUCTURE

```
/Users/mohitpandya/Monash/FIT5222_PAR/
├── Assignment_1/
├── Assignment_2/               # CURRENT ASSIGNMENT
├── pacman-public/              # Main implementation directory
│   ├── myTeam.py              # Main implementation file (EDIT THIS)
│   ├── myTeam.pddl            # PDDL domain model (EDIT THIS)
│   ├── staffTeam.py           # Baseline to beat
│   ├── berkeleyTeam.py        # UC Berkeley reference
│   ├── capture.py             # Simulator entry point
│   ├── captureAgents.py       # Agent API
│   └── layouts/               # Map files
├── piglet-public/              # PDDL solver
└── flatland/
```

## TECHNICAL REQUIREMENTS

### Installation

1. **Piglet PDDL Solver** (in piglet-public folder):

   ```bash
   cd piglet-public
   git fetch
   git checkout pddl_solver
   python setup.py install
   ```

2. **Update Pacman Code** (in pacman-public folder):
   ```bash
   cd pacman-public
   git fetch
   git reset --hard
   git pull
   ```

### Running the Simulator

**IMPORTANT**: Always use the `pacman` conda environment for this assignment!

```bash
cd /Users/mohitpandya/Monash/FIT5222_PAR/pacman-public
conda run -n pacman python capture.py -r myTeam.py -b staffTeam.py
```

**Key Arguments**:

- `-r [RED.py]`: Red team implementation
- `-b [BLUE.py]`: Blue team implementation
- `-l [LAYOUT]`: Map layout (use `RANDOM` or `RANDOM<seed>` for random maps)
- `-q`: Minimal output, no graphics
- `-Q`: Suppress all output including agent output
- `-n [NUMGAMES]`: Number of games to play
- `-i [MAX_MOVES]`: Maximum total moves (default 1200)
- `-c`: Enable time checking mode (IMPORTANT: test before submission)

**Example Commands** (all using conda environment):

```bash
# Test against baseline with graphics
conda run -n pacman python capture.py -r myTeam.py -b staffTeam.py

# Test 10 games silently
conda run -n pacman python capture.py -r myTeam.py -b staffTeam.py -Q -n 10

# Test with time constraints
conda run -n pacman python capture.py -r myTeam.py -b staffTeam.py -c

# Test on specific map
conda run -n pacman python capture.py -r myTeam.py -b staffTeam.py -l ./layouts/defaultCapture.lay

# Training mode (Q-learning)
conda run -n pacman python capture.py -r myTeam.py -b staffTeam.py -Q -n 100
```

## IMPLEMENTATION ARCHITECTURE

### Core Files to Edit

1. **`myTeam.py`**: Main implementation file containing agent decision-making logic
2. **`myTeam.pddl`**: PDDL domain model for high-level planning

### MixedAgent Class Structure

The baseline uses a two-tier planning approach:

#### 1. High-Level Planning (PDDL-based)

**Key Functions**:

- `get_pddl_state()`: Converts game state to PDDL predicates (tuples)
- `getGoals()`: Returns positive/negative goal state expressions
- `stateSatisfyCurrentPlan()`: Checks if current plan is still valid
- `getHighLevelPlan()`: Solves PDDL problem and returns action sequence

**Distance Constants** (tunable):

- `CLOSE_DISTANCE`
- `MEDIUM_DISTANCE`
- `LONG_DISTANCE`

**PDDL Structure**:

- State expressions: Tuples like `("food_available",)` or `("is_pacman", "a1")`
- Object expressions: Tuples like `("a1", "current_agent")`
- Predicates categorized as **team type** (own agents/score) and **enemy type**

#### 2. Low-Level Planning

**Two Approaches**:

##### A. Q-Learning (Default)

**Key Functions**:

- `getLowLevelPlanQL()`: Computes single-action plan using approximate Q-learning
- `getOffensiveFeatures()`: Feature extraction for offensive strategy
- `getOffensiveReward()`: Reward function for offensive actions
- `getDefensiveFeatures()`: Feature extraction for defensive strategy
- `getDefensiveReward()`: Reward function for defensive actions
- `getEscapeFeatures()`: Feature extraction for escape strategy (when being chased)
- `getEscapeReward()`: Reward function for escape actions

**Q-Learning Parameters**:

- `self.epsilon = 0.1`: Exploration probability
- `self.alpha = 0.1`: Learning rate
- `self.discountRate = 0.9`: Discount rate
- Weights stored in `QLWeights` class variable, persisted to disk

**Weight File Management**:

- Default weights defined in class: `QLWeights = {"offensiveWeights": {...}, "defensiveWeights": {...}, "escapeWeights": {...}}`
- Saved to: `QLWeightsMyTeam.txt` (in pacman-public directory)
- Also possible: `QLWeightsStaffTeam.txt` for staff baseline weights
- To reset training: Delete weight files to use default weights from code
- Weights automatically loaded on startup if file exists

**Training Tips**:

- Set `self.training = True` in `registerInitialState` to enable weight updates
- Use `-Q -n 100` for silent batch training across 100 games
- Train on multiple maps using `-l ./layouts/[mapname].lay`
- Delete weight files to restart training with default weights
- Turn off training before contest submission

##### B. Heuristic Search

**Key Functions**:

- `getLowLevelPlanHS()`: Returns list of (action, location) tuples
- Must implement state-space representation and search strategy
- `posSatisfyLowLevelPlan()`: Validates low-level plan against current position

### Decision-Making Workflow

The `chooseAction()` function implements this cycle:

1. Compute high-level plan if none exists or current action not applicable
2. Select next high-level action from plan
3. Compute low-level plan for that action if needed
4. Execute first low-level action and return to simulator

### Key Initialization Functions

- `registerInitialState()`: Called once at game start; initialize PDDL solver path here
- `createTeam()`: Instantiates two agents (can be different classes)
- `final()`: Called at game end; save training data here

### Environment API

#### GameState Methods

Access game information via `gameState` object:

- `getWalls()`: Returns Grid of obstacles
- `getFood()`, `getBlueFood()`, `getRedFood()`: Returns Grid of food locations
- `getCapsules()`, `getBlueCapsules()`, `getRedCapsules()`: Returns list of capsule positions
- `getAgentState(index)`: Get state for specific agent index
- `getAgentPosition(index)`: Get position for specific agent
- `getScore()`: Current score difference (positive favors red)
- Grid access: `grid[x][y]` where (0,0) is bottom-left
- `asList()`: Converts Grid to list of True coordinates

#### CaptureAgent Convenience Methods

Call these via `self.method(gameState)`:

- `getFood(gameState)`: Returns Grid of food you're trying to eat
- `getFoodYouAreDefending(gameState)`: Returns Grid of food you're defending
- `getCapsules(gameState)`: Returns list of capsules you can eat
- `getCapsulesYouAreDefending(gameState)`: Returns list of capsules you're defending
- `getOpponents(gameState)`: Returns list of opponent agent indices
- `getTeam(gameState)`: Returns list of teammate agent indices
- `getScore(gameState)`: Returns current score
- `getMazeDistance(pos1, pos2)`: Returns actual maze distance between positions
- `getAgentState(index)`: Returns AgentState object (position, scared timer, food carrying, isPacman)
- `getSuccessor(gameState, action)`: Returns successor state after taking action
- `observationHistory`: List of previous observations
- `getCurrentObservation()`: Returns current game state
- See `captureAgents.py` for complete list

#### Path Handling

Always use relative paths from `BASE_FOLDER`:

```python
import os
BASE_FOLDER = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(BASE_FOLDER, "pacman.pddl")
```

## COMPETITION REQUIREMENTS

### Baseline Requirements

Must beat `staffTeam.py` convincingly: **28/49 games** across 7 maps

- **Failing to beat baseline = Fail for Criteria 1 (50/150 marks)**

**Testing Maps**:

- Use random seeds RANDOM1 through RANDOM7 (7 maps)
- Play 7 games on each map = 49 total games
- Win calculation: Count wins across all 49 games, need ≥28 wins

### Scoring System

**Victory Points (VP)** per match against each opponent:

- Convincing win (≥28 games): **3 VP**
- Tie (neither team wins 28): **0.5 VP**
- Loss (≥28 losses): **0 VP**

**Final Score**: `(Your VP / Total Available VP) × 100%`
Where Total Available VP = 3 × (Number of participants - 1)

### Technical Constraints

- **RAM Limit**: 2GB per run
- **Action Time**: 5 seconds per timestep (use `-c` flag to test locally)
- **Total Time**: 2400s per game
- **Submission Limit**: Maximum 2 live submissions at once

### Contest Submission Process

**Server**: https://fit5222a2.contest.pathfinding.ai

**Steps**:

1. Sign in with Bitbucket → Continue with Google (Monash credentials)
2. Create repository on contest site
3. Create Bitbucket API token (Atlassian account settings → Security)
4. Add remote to local repo:
   ```bash
   git remote add personal <your-url>
   git add *
   git commit -m "Description"
   git push personal <branch-name>
   ```
5. Select branch on contest site and submit

**Dependencies**: Request non-standard packages via Ed discussion

**Path Setup for Imports**:

```python
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
```

## DELIVERABLES

### 1. Implementation

**File**: `last_name_student_id_pacman.zip` containing `src/` directory with all code

**Required Files in `src/` directory**:

- `myTeam.py`: Main agent implementation
- `myTeam.pddl`: PDDL domain file
- Any additional Python modules your team uses
- Weight files (if using trained Q-learning weights)
- **Do NOT include**: External libraries, pacman framework files (capture.py, etc.)

### 2. Report (15 pages max, 12pt font)

**Structure**:

- **Approach Description** (15 marks): High/low-level planning strategies, clear links to lectures, theoretical motivation
- **Experiment Discussion** (15 marks): Compare ≥2 strategies with numerical evidence, efficiency analysis vs. benchmarks
- **Reflections** (10 marks): Critical analysis of strengths/weaknesses, implications of findings
- **Communication** (10 marks): Clear narrative, proper structure, accurate citations, supporting materials (tables, pseudo-code)

**File**: `last_name_student_id_report_pacman.pdf`

## MARKING RUBRIC (150 marks total)

### Implementation (100 marks)

#### Criteria 1: Competition (50 marks)

- **N (0-49%)**: Loses to staff baseline
- **P (50-59%)**: 25-49% of available VP
- **C (60-69%)**: 50-74% of available VP
- **D (70-79%)**: 75-100% of available VP
- **HD (80-100%)**: 75-100% of available VP

#### Criteria 2: Agent Strategy (50 marks)

- **N**: Minor updates only (parameter tweaking)
- **P**: Addresses some drawbacks
- **C**: New PDDL actions using more predicates OR new goal functions
- **D**: Dynamic goal switching + improved low-level planner
- **HD**: Customized low-level plans per high-level action + agent cooperation/information sharing

### Report (50 marks)

Detailed rubric in documentation for expectations across Pass/Credit/Distinction/HD levels

## IMPROVEMENT STRATEGIES

### High-Level Planning

1. Add new PDDL actions using "advanced" predicates from `myTeam.pddl`
2. Create new predicates and modify `get_pddl_state()` to track additional game info
3. Implement dynamic goal prioritization based on observations
4. Distinguish team predicates (own agents/score) from enemy predicates

### Low-Level Planning

#### Q-Learning Enhancements

**Feature Design**:

- Normalize feature values across different map sizes
- Ensure smooth feature value changes between states
- Avoid features with sudden value jumps

**Reward Design**:

- Use correlated, non-binary rewards
- Provide informative feedback (avoid sparse rewards)
- Avoid contradictory penalties (e.g., penalizing death equally regardless of food carried)
- Consider context: differentiate being caught with lots vs. little food

**Training Best Practices**:

- Monitor "correction" values during weight updates
- Train strategies independently (disable high-level planner, focus one opponent role)
- Test across multiple maps and random seeds
- Small learning rate stabilizes training but slows convergence

#### Heuristic Search

- Design custom state-space representations
- Implement goal selection strategies per high-level action
- Return plans as `[(action, location), ...]` lists

### Agent Coordination

- Share information between teammates via class variables (e.g., `CURRENT_ACTION = {}`)
- Coordinate low-level actions (e.g., avoid targeting same food)
- Consider teammate's current strategy in decision-making
- Implement cooperative predicates in PDDL:
  - `(eat_enemy ?a - ally)`: Ally is attacking enemy
  - `(go_home ?a - ally)`: Ally is returning home
  - `(go_enemy_land ?a - ally)`: Ally is going to enemy territory
  - `(eat_capsule ?a - ally)`: Ally is eating capsule
  - `(eat_food ?a - ally)`: Ally is collecting food
- Note: Must track ally states in `get_pddl_state()` to use cooperative predicates

## PDDL REFERENCE

### PDDL Workflow in the Agent

1. **Domain File**: `myTeam.pddl` defines types, predicates, and actions
2. **Problem Generation**: `get_pddl_state()` converts game state to PDDL predicates
3. **Goal Setting**: `getGoals()` returns goal predicates to achieve
4. **Planning**: `getHighLevelPlan()` calls Piglet solver to find action sequence
5. **Execution**: `chooseAction()` executes low-level plan for current high-level action

**No Separate Problem File**: Problem is generated dynamically from game state

**When PDDL Solver Fails**:

- If no plan found, agent should have fallback behavior
- Consider using previous plan or simple heuristic
- Check if goal is achievable or too restrictive

### Supported Features

### Supported Features

- `:typing`
- `:strips`
- `:negative-preconditions`

### Syntax Examples

**Types**:

```pddl
(:types
  animal - object
  cat mouse - animal
)
```

**Predicates**:

```pddl
(door_open)
(at_home ?x - animal)
(at ?x - animal ?l - location)
```

**Actions**:

```pddl
(:action catch
  :parameters (?c - cat ?m - mouse)
  :precondition (and (at_home ?m) (at_home ?c))
  :effect (and (not (at_home ?m)))
)
```

**Logical Expressions**:

- `(not Condition)`
- `(and Condition_1 ... Condition_N)`

### Resources

- PDDL Wiki: https://planning.wiki/
- VS Code PDDL extension for syntax highlighting

## IMPORTANT NOTES

### Academic Integrity

- **All work must be your own**
- Do not copy online implementations or share code with peers
- **Plagiarism = Assignment failure and possible unit failure**
- Reference: https://www.monash.edu/students/study-support/academic-integrity

### Submission Strategy

- Submit early and often to contest server
- Don't wait until deadline (server outages/queues possible)
- Test locally against `staffTeam.py` before submitting
- Use `RANDOM<seed>` maps for reproducible testing

### Performance Tips

- Use `-c` flag to ensure actions complete within 5-second limit
- Optimize algorithms to finish games in 2-5 minutes (well under 2400s limit)
- Test RAM usage stays under 2GB

## COMMON TASKS & COMMANDS

### Testing Your Implementation

**IMPORTANT**: All commands must use `conda run -n pacman` to activate the environment!

```bash
# Quick test with graphics
conda run -n pacman python capture.py -r myTeam.py -b staffTeam.py

# Test on specific map layout
conda run -n pacman python capture.py -r myTeam.py -b staffTeam.py -l ./layouts/defaultCapture.lay

# Full baseline test (7 maps, 7 games each = 49 total)
# Need to win 28+ games to pass Criteria 1
conda run -n pacman python capture.py -r myTeam.py -b staffTeam.py -n 7 -l RANDOM1
conda run -n pacman python capture.py -r myTeam.py -b staffTeam.py -n 7 -l RANDOM2
# ... repeat for RANDOM3 through RANDOM7

# Automated testing loop with win counting
wins=0
for i in {1..7}; do
  conda run -n pacman python capture.py -r myTeam.py -b staffTeam.py -n 7 -l RANDOM$i -q | tee -a results.txt
done
# Check results.txt for win count

# Test with reproducible random seed
conda run -n pacman python capture.py -r myTeam.py -b staffTeam.py -l RANDOM42 -n 10
```

### Available Map Layouts

```bash
# List available layouts
ls /Users/mohitpandya/Monash/FIT5222_PAR/pacman-public/layouts/

# Common layouts:
# - defaultCapture.lay
# - alleyCapture.lay
# - bloxCapture.lay
# - crowdedCapture.lay
# - distantCapture.lay
# - fastCapture.lay
# - jumpCapture.lay
# - mediumCapture.lay
# - officeCapture.lay
# - strategicCapture.lay
# - testCapture.lay
```

### Training Q-Learning

```bash
# Train for 100 games
conda run -n pacman python capture.py -r myTeam.py -b staffTeam.py -Q -n 100

# Train on different maps
conda run -n pacman python capture.py -r myTeam.py -b staffTeam.py -Q -n 50 -l ./layouts/defaultCapture.lay
```

### Debugging

```bash
# Run with output to see what's happening
conda run -n pacman python capture.py -r myTeam.py -b staffTeam.py

# Check time constraints
conda run -n pacman python capture.py -r myTeam.py -b staffTeam.py -c
```

## TROUBLESHOOTING

### Common Issues

1. **PDDL solver not found**: Check `registerInitialState()` has correct path to piglet
2. **Timeout errors**: Use `-c` flag to identify slow actions, optimize planning
3. **Low win rate**: Check both high-level goals and low-level features/rewards
4. **Training not improving**: Verify `self.training = True`, check feature/reward design
5. **Import errors**: Ensure `sys.path.append()` is set correctly

### File Locations

- Q-Learning weights: Saved to `QLWeightsMyTeam.txt` in pacman-public directory
- Staff weights example: `QLWeightsStaffTeam.txt`
- PDDL domain: `myTeam.pddl` (must be in same directory as `myTeam.py`)
- Map layouts: `./layouts/*.lay` files
- Logs: Check terminal output for errors

### Strategy-Specific Issues

- **Offensive strategy stuck**: Check if food_available predicate is correct, verify getLowLevelPlanQL for offensive action
- **Defensive strategy weak**: Ensure enemy detection predicates are accurate, improve defensive features/rewards
- **Escape strategy failing**: Check scared timer tracking, improve escape features (distance to safety)
- **Agent coordination failing**: Verify class variables are shared, check cooperative predicate tracking

## AI ASSISTANT INSTRUCTIONS

When helping with this project:

1. **Always** check this context file first
2. **Always** use absolute paths: `/Users/mohitpandya/Monash/FIT5222_PAR/pacman-public/`
3. **Test commands** before suggesting them
4. **Read existing code** before making changes
5. Focus on **beating staffTeam.py** as minimum requirement
6. Consider **both high-level (PDDL) and low-level (Q-learning/search) improvements**
7. Remember the **5-second action limit** when suggesting algorithms
8. Keep **agent coordination** in mind (2 agents per team)

## QUICK REFERENCE

**Conda Environment**: `pacman` (ALWAYS use this!)

**Main Files**:

- Implementation: `/Users/mohitpandya/Monash/FIT5222_PAR/pacman-public/myTeam.py`
- PDDL: `/Users/mohitpandya/Monash/FIT5222_PAR/pacman-public/myTeam.pddl`
- Baseline: `/Users/mohitpandya/Monash/FIT5222_PAR/pacman-public/staffTeam.py`

**Test Command**:

```bash
cd /Users/mohitpandya/Monash/FIT5222_PAR/pacman-public
conda run -n pacman python capture.py -r myTeam.py -b staffTeam.py
```

**Minimum Success**: Beat staffTeam 28/49 games
**Due**: November 3, 2025, 11:55 PM (2 days from now)
