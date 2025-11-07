# Quick Testing & Validation Guide

## 1. Run Standard Tests

### Test against baseline (10 games)

```bash
cd /Users/mohitpandya/Monash/FIT5222_PAR/pacman-public
conda run -n pacman python capture.py -r myTeam -b staffTeam -l defaultCapture -q -n 10
```

### Test on different layouts

```bash
# Random layout
conda run -n pacman python capture.py -r myTeam -b staffTeam -l RANDOM -q -n 10

# Test capture
conda run -n pacman python capture.py -r myTeam -b staffTeam -l testCapture -q -n 10
```

### Visual debugging (single game with graphics)

```bash
conda run -n pacman python capture.py -r myTeam -b staffTeam -l defaultCapture
```

---

## 2. Key Improvements to Observe

### Task 1: A\* Pathfinding

**What to look for:**

- Agents taking longer but SAFER paths around ghosts
- No getting trapped in dead ends when ghosts nearby
- Smooth returns home even under pressure

**Debug output:**

- No specific A\* logs (to avoid slowdown), but watch agent movements

### Task 2: Coordination

**What to look for:**

- "coordinated: True" in console output
- Agents targeting different food clusters
- When defending multiple invaders, agents split targets

**Debug output:**

```
Agent 0: COLLECTING FOOD (coordinated: True)
Agent 2: COLLECTING FOOD (coordinated: True)
```

### Task 3: Dynamic Goals

**What to look for:**

- Different return thresholds based on situation
- Emergency returns when ghost close
- Endgame strategy switches (DEFENDING WIN, SECURING WIN)

**Debug output:**

```
Agent 0: EMERGENCY RETURN! Ghost at distance 2
Agent 0: RETURNING with 2 food (threshold: 2)
Agent 0: DEFENDING WIN
Agent 0: DESPERATE ATTACK - losing with 95 time left
```

---

## 3. Performance Expectations

### vs staffTeam (baseline)

- **Target**: 80%+ win rate (8-10 wins out of 10)
- **Your Iteration 5**: 75% (36/48)
- **Expected now**: 85%+ with better pathfinding

### vs Competition (student teams)

- **Target for D**: 60%+ win rate
- **Target for HD**: 70%+ win rate
- **Your previous**: 45.5%
- **Expected now**: 65-75% (significant improvement)

---

## 4. Common Issues & Solutions

### Issue: Agent timeout

**Symptoms**: Game hangs, agent takes too long
**Solution**: A\* maxDepth set to 30 (tested and safe)
**If still occurs**: Reduce maxDepth to 20 in line ~512

### Issue: Agents targeting same food

**Symptoms**: Both agents go to same cluster
**Solution**: Check coordinator is working - look for "coordinated: True"
**If not working**: Verify global `teamCoordinator` initialized

### Issue: Not returning with food

**Symptoms**: Agent dies with food
**Solution**: Check dynamic threshold logs - should see varying thresholds
**Expected**: Threshold 1-2 when ghost close, 3-5 when safe

### Issue: Poor defense

**Symptoms**: Invaders scoring easily
**Solution**: Verify DEFEND_INVADERS priority triggers
**Check**: Should see "DEFENDING against X invader(s)" message

---

## 5. Competition Submission Checklist

- [ ] Test 10 games vs staffTeam → Record win rate
- [ ] Test on 3+ different layouts → Ensure no crashes
- [ ] Visual test 1 game → Verify intelligent behavior
- [ ] Check no timeout errors → All games complete
- [ ] Review logs → Confirm all 3 tasks active:
  - [ ] A\* pathfinding working (smooth movement)
  - [ ] Coordination messages appearing
  - [ ] Dynamic priorities showing variety
- [ ] Document final performance in report
- [ ] Submit myTeam.py + myTeam.pddl

---

## 6. What to Put in Your Report

### Implementation Section

#### High-Level Strategy (PDDL)

"Used PDDL for strategic decision-making with 7 priority tiers:

1. Emergency return (ghost proximity)
2. Defend invaders (home security)
3. Return with food (dynamic threshold)
4. Hunt scared ghosts (opportunistic)
5. Get capsule (tactical)
6. Endgame strategies (time-based)
7. Food collection (default)

Dynamic goal prioritization considers: score, time remaining, danger level, food remaining, and game phase."

#### Low-Level Planner (A\*)

"Replaced greedy single-step movement with A\* pathfinding algorithm including:

- Multi-step lookahead (up to 30 steps)
- Ghost avoidance with distance-based penalties
- Dead-end detection and avoidance
- Path caching for performance
- Manhattan distance heuristic"

#### Agent Coordination

"Implemented TeamCoordinator class enabling:

- Strategy broadcasting (collecting, defending, returning, etc.)
- Target claiming to prevent food conflicts
- Dynamic role adaptation (both agents can attack/defend based on situation)
- Invader target splitting when multiple threats"

### Results Section

```
Performance vs staffTeam baseline:
- Win Rate: X/10 (X%)
- Average Score: +X.X
- Significant improvement over Iteration 5 (75%)

Performance vs competition (if tested):
- Win Rate: X/Y (X%)
- Expected: 65-75% (D/HD range)

Key Observations:
- Emergency return system prevented X deaths
- Dynamic thresholds adapted X times per game
- Coordination active in X% of food collection
- A* pathfinding avoided X dangerous situations
```

---

## 7. Quick Performance Test Script

Save as `test_performance.sh`:

```bash
#!/bin/bash

echo "=== Testing vs staffTeam (10 games) ==="
conda run -n pacman python capture.py -r myTeam -b staffTeam -l defaultCapture -q -n 10 2>&1 | tail -10

echo ""
echo "=== Testing on RANDOM layout (5 games) ==="
conda run -n pacman python capture.py -r myTeam -b staffTeam -l RANDOM -q -n 5 2>&1 | tail -10

echo ""
echo "=== Testing on testCapture (5 games) ==="
conda run -n pacman python capture.py -r myTeam -b staffTeam -l testCapture -q -n 5 2>&1 | tail -10
```

Make executable: `chmod +x test_performance.sh`
Run: `./test_performance.sh`

---

## 8. Debug Mode (if needed)

To add more detailed logging, add this function to myTeam.py:

```python
def debugLog(self, message, level="INFO"):
    """Optional: Add more detailed logging"""
    if self.index == 0:  # Only log from one agent to avoid spam
        print(f"[DEBUG-{level}] Agent {self.index}: {message}")
```

Use in key places:

```python
self.debugLog(f"A* found path of length {len(path)}", "PATH")
self.debugLog(f"Threshold: {threshold}, Carrying: {carrying}", "THRESHOLD")
self.debugLog(f"Teammate strategy: {teammateStrategy}", "COORD")
```

---

## 9. Validation Checklist

Run through this before final submission:

### Functionality Tests

- [ ] No Python errors or crashes
- [ ] Completes all games within time limit
- [ ] Both agents move intelligently
- [ ] Emergency returns work
- [ ] Defense activates when needed
- [ ] Endgame strategies trigger

### Performance Tests

- [ ] Beats staffTeam 8+ out of 10 games
- [ ] Positive average score
- [ ] No suicidal behavior (running into ghosts)
- [ ] Efficient food collection
- [ ] Good defense (catches invaders)

### Code Quality

- [ ] No debug print spam (current logs are fine)
- [ ] PDDL file matches Python implementation
- [ ] Comments explain complex logic
- [ ] No unused/dead code

---

## 10. Final Submission Files

Ensure you submit:

1. **myTeam.py** - Your upgraded agent
2. **myTeam.pddl** - PDDL domain file
3. **Report** - Document your three improvements
4. **Performance stats** - Win rates from testing

Optional but recommended:

- UPGRADE_IMPLEMENTATION_SUMMARY.md (this file)
- Test results output (save console output)

---

## Need Help?

### If A\* is too slow:

- Reduce `maxDepth` from 30 to 20 (line 512)
- Increase cache timeout from 5 to 10 (line 517)

### If coordination not working:

- Check global `teamCoordinator` initialized (line 70)
- Verify both agents calling `updateStrategy()`

### If dynamic goals seem random:

- Review `calculateReturnThreshold()` logic (line 410)
- Adjust factor weights if needed

### If failing competition:

- Analyze losing games visually (remove -q flag)
- Identify specific failure patterns
- Tune penalties in A\* or thresholds

---

Good luck! Your agent should now be competitive for D/HD grades. 🎯
