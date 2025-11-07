# myTeam.py
# ---------------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


# myTeam.py
# ---------------
# Licensing Information: Please do not distribute or publish solutions to this
# project. You are free to use and extend these projects for educational
# purposes. The Pacman AI projects were developed at UC Berkeley, primarily by
# John DeNero (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# For more info, see http://inst.eecs.berkeley.edu/~cs188/sp09/pacman.html

from captureAgents import CaptureAgent
import random, time, util, os
from game import Directions, Actions
from util import nearestPoint

# Import PDDL solver
BASE_FOLDER = os.path.dirname(os.path.abspath(__file__))
from lib_piglet.utils.pddl_solver import pddl_solver

#################
# Team Coordination #
#################

class TeamCoordinator:
    """
    Maintains shared state between agents to coordinate strategies and avoid conflicts.
    """
    def __init__(self):
        self.agentStrategies = {}
        self.agentTargets = {}
        self.claimedFood = set()
        
    def updateStrategy(self, agentIndex, strategy, target=None):
        self.agentStrategies[agentIndex] = strategy
        if target:
            self.agentTargets[agentIndex] = target
    
    def getTeammateStrategy(self, myIndex, teamIndices):
        for idx in teamIndices:
            if idx != myIndex and idx in self.agentStrategies:
                return self.agentStrategies[idx]
        return None
    
    def getTeammateTarget(self, myIndex, teamIndices):
        for idx in teamIndices:
            if idx != myIndex and idx in self.agentTargets:
                return self.agentTargets[idx]
        return None
    
    def claimFood(self, food):
        self.claimedFood.add(food)
    
    def isClaimedByTeammate(self, food, myIndex):
        return food in self.claimedFood

teamCoordinator = TeamCoordinator()

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first='HybridAgent', second='HybridAgent'):
    """
    Creates a team using PDDL for high-level planning and greedy heuristics for low-level actions.
    """
    return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########

class HybridAgent(CaptureAgent):
    """
    Hybrid agent that uses PDDL for strategic planning and reactive heuristics for execution.
    """

    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)
        self.start = gameState.getAgentPosition(self.index)
        
        # PDDL solver setup
        self.pddl_solver = pddl_solver(BASE_FOLDER + '/myTeam.pddl')
        self.currentPlan = []
        self.currentAction = None
        
        # Position tracking for loop detection
        self.lastPositions = []
        self.planExecutionSteps = 0
        self.MAX_PLAN_STEPS = 15
        
        # Caching for performance
        self.deadEndCache = {}
        self.pathCache = {}
        self.pathCacheTime = {}
        
        # Register with team coordinator
        global teamCoordinator
        self.coordinator = teamCoordinator
        self.coordinator.updateStrategy(self.index, "initializing")
        
    def chooseAction(self, gameState):
        """
        Main decision loop: uses PDDL for strategic planning and heuristics for tactical execution.
        """
        # Track current position
        myPos = gameState.getAgentPosition(self.index)
        self.lastPositions.append(myPos)
        if len(self.lastPositions) > 5:
            self.lastPositions.pop(0)
        
        # Get legal actions, avoid stopping
        actions = gameState.getLegalActions(self.index)
        if 'Stop' in actions and len(actions) > 1:
            actions.remove('Stop')
        
        # Break loops if detected
        if len(self.lastPositions) == 5 and len(set(self.lastPositions)) <= 2:
            return random.choice(actions)
        
        # Replan when necessary
        if self.shouldReplan(gameState):
            self.updatePlan(gameState)
            self.planExecutionSteps = 0
        
        self.planExecutionSteps += 1
        
        # Execute current high-level action
        if self.currentAction:
            return self.executeAction(gameState, actions, self.currentAction)
        else:
            return self.executeAction(gameState, actions, "collect-food")
    
    def shouldReplan(self, gameState):
        """
        Determines when to generate a new PDDL plan based on execution progress and threat changes.
        """
        if not self.currentPlan or not self.currentAction:
            return True
        
        if self.planExecutionSteps >= self.MAX_PLAN_STEPS:
            return True
        
        # Check for significant state changes
        myState = gameState.getAgentState(self.index)
        enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        ghosts = [a for a in enemies if not a.isPacman and a.getPosition() != None]
        
        # Replan if threat level changed drastically
        if self.currentAction == "collect-food" and len(ghosts) > 0:
            myPos = gameState.getAgentPosition(self.index)
            minDist = min([self.getMazeDistance(myPos, g.getPosition()) for g in ghosts])
            if minDist <= 3:
                return True
        
        return False
    
    def updatePlan(self, gameState):
        """
        Generates a new PDDL plan based on current game state.
        """
        objects, initState, positiveGoals, negativeGoals = self.getPDDLState(gameState)
        
        self.pddl_solver.parser_.reset_problem()
        self.pddl_solver.parser_.set_objects(objects)
        self.pddl_solver.parser_.set_state(initState)
        self.pddl_solver.parser_.set_positive_goals(positiveGoals)
        self.pddl_solver.parser_.set_negative_goals(negativeGoals)
        
        try:
            plan = self.pddl_solver.solve()
            if plan and len(plan) > 0:
                self.currentPlan = plan
                self.currentAction = plan[0][0].name
                print(f"Agent {self.index}: PDDL chose action '{self.currentAction}' from plan of length {len(plan)}")
            else:
                self.currentAction = "collect-food"
                print(f"Agent {self.index}: No PDDL plan found, using default 'collect-food'")
        except Exception as e:
            self.currentAction = "collect-food"
            print(f"Agent {self.index}: PDDL solver error: {e}")
    
    def getPDDLState(self, gameState):
        """
        Converts game state to PDDL representation with dynamic goal prioritization.
        """
        myState = gameState.getAgentState(self.index)
        myPos = gameState.getAgentPosition(self.index)
        
        # Define objects
        team_indices = self.getTeam(gameState)
        ally_index = [i for i in team_indices if i != self.index][0]
        
        objects = [
            ('a{}'.format(self.index), 'current_agent'),
            ('a{}'.format(ally_index), 'ally'),
        ]
        
        enemies = self.getOpponents(gameState)
        objects.append(('e{}'.format(enemies[0]), 'enemy1'))
        objects.append(('e{}'.format(enemies[1]), 'enemy2'))
        
        # Build predicates
        initState = []
        
        # Food availability
        foodList = self.getFood(gameState).asList()
        if len(foodList) > 0:
            initState.append(('food_available',))
        
        # Food carrying status
        if myState.numCarrying > 0:
            initState.append(('food_in_backpack', 'a{}'.format(self.index)))
            if myState.numCarrying >= 2:
                initState.append(('2_food_in_backpack', 'a{}'.format(self.index)))
            if myState.numCarrying >= 3:
                initState.append(('3_food_in_backpack', 'a{}'.format(self.index)))
            if myState.numCarrying >= 5:
                initState.append(('5_food_in_backpack', 'a{}'.format(self.index)))
        
        if myState.isPacman:
            initState.append(('is_pacman', 'a{}'.format(self.index)))
        
        # Enemy states
        enemyStates = [gameState.getAgentState(i) for i in enemies]
        for i, enemyState in enumerate(enemyStates):
            enemy_obj = 'e{}'.format(enemies[i])
            
            if enemyState.isPacman:
                initState.append(('is_pacman', enemy_obj))
                initState.append(('invaders_present',))
            
            if enemyState.scaredTimer > 0:
                initState.append(('is_scared', enemy_obj))
                initState.append(('can_hunt_ghosts',))
            
            if enemyState.getPosition() is not None:
                dist = self.getMazeDistance(myPos, enemyState.getPosition())
                if dist <= 4:
                    initState.append(('enemy_around', enemy_obj, 'a{}'.format(self.index)))
                    if enemyState.scaredTimer > 0:
                        initState.append(('scared_ghost_near', 'a{}'.format(self.index)))
        
        # Capsule availability and proximity
        capsules = self.getCapsules(gameState)
        if len(capsules) > 0:
            initState.append(('capsule_available',))
            for cap in capsules:
                if self.getMazeDistance(myPos, cap) <= 4:
                    initState.append(('near_capsule', 'a{}'.format(self.index)))
                    break
        
        # Food proximity
        if len(foodList) > 0:
            minFoodDist = min([self.getMazeDistance(myPos, food) for food in foodList])
            if minFoodDist <= 4:
                initState.append(('near_food', 'a{}'.format(self.index)))
        
        # Check teammate coordination
        teammateStrategy = self.coordinator.getTeammateStrategy(self.index, team_indices)
        
        # Assign roles
        if self.index == min(team_indices):
            initState.append(('is_attacker', 'a{}'.format(self.index)))
        else:
            initState.append(('is_defender', 'a{}'.format(self.index)))
        
        # Dynamic goal prioritization based on game state
        positiveGoals = []
        negativeGoals = []
        
        # Gather game metrics for strategic decisions
        currentScore = gameState.getScore()
        timeRemaining = gameState.data.timeleft if gameState.data.timeleft else 1200
        foodRemaining = len(foodList)
        foodDefending = len(self.getFoodYouAreDefending(gameState).asList())
        
        # Assess threats
        enemyStatesVisible = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        ghosts = [a for a in enemyStatesVisible if not a.isPacman and a.getPosition() != None and a.scaredTimer == 0]
        invaders = [a for a in enemyStatesVisible if a.isPacman and a.getPosition() != None]
        scaredGhosts = [a for a in enemyStatesVisible if a.scaredTimer > 5 and a.getPosition() != None]
        
        # Calculate proximity to threats
        nearbyGhosts = []
        if len(ghosts) > 0:
            for g in ghosts:
                dist = self.getMazeDistance(myPos, g.getPosition())
                if dist <= 5:
                    nearbyGhosts.append((g, dist))
        
        minGhostDist = min([d for g, d in nearbyGhosts]) if nearbyGhosts else 999
        
        # Determine game phase
        totalGameTime = 1200
        timeProgress = 1.0 - (timeRemaining / totalGameTime)
        
        strategy = None
        
        # Priority 1: Emergency return if ghost too close while carrying food
        if minGhostDist <= 2 and myState.numCarrying >= 1 and myState.isPacman:
            strategy = "EMERGENCY_RETURN"
            negativeGoals.append(('is_pacman', 'a{}'.format(self.index)))
            self.coordinator.updateStrategy(self.index, "emergency_return", self.start)
            print(f"Agent {self.index}: EMERGENCY RETURN! Ghost at distance {minGhostDist}")
        
        # Priority 2: Defend against invaders
        elif len(invaders) > 0 and not myState.isPacman:
            if teammateStrategy == "defending":
                # Coordinate with defending teammate
                if minGhostDist > 5 or len(scaredGhosts) > 0:
                    strategy = "COORDINATED_ATTACK"
                else:
                    strategy = "DEFEND_INVADERS"
            else:
                strategy = "DEFEND_INVADERS"
            
            if strategy == "DEFEND_INVADERS":
                for obj in objects:
                    if obj[1] in ['enemy1', 'enemy2']:
                        negativeGoals.append(('is_pacman', obj[0]))
                self.coordinator.updateStrategy(self.index, "defending", invaders[0].getPosition())
                print(f"Agent {self.index}: DEFENDING against {len(invaders)} invader(s)")
        
        # Priority 3: Return home with enough food
        elif myState.numCarrying > 0 and myState.isPacman:
            returnThreshold = self.calculateReturnThreshold(
                gameState, currentScore, timeRemaining, foodRemaining, 
                minGhostDist, timeProgress
            )
            
            if myState.numCarrying >= returnThreshold:
                strategy = "RETURN_WITH_FOOD"
                negativeGoals.append(('is_pacman', 'a{}'.format(self.index)))
                self.coordinator.updateStrategy(self.index, "returning", self.start)
                print(f"Agent {self.index}: RETURNING with {myState.numCarrying} food (threshold: {returnThreshold})")
        
        # Priority 4: Hunt scared ghosts for bonus points
        elif len(scaredGhosts) > 0 and myState.isPacman:
            closestScared = min(scaredGhosts, key=lambda g: self.getMazeDistance(myPos, g.getPosition()))
            distToScared = self.getMazeDistance(myPos, closestScared.getPosition())
            
            if closestScared.scaredTimer > distToScared + 3:
                strategy = "HUNT_SCARED"
                negativeGoals.append(('can_hunt_ghosts',))
                self.coordinator.updateStrategy(self.index, "hunting", closestScared.getPosition())
                print(f"Agent {self.index}: HUNTING scared ghost at distance {distToScared}")
        
        # Priority 5: Get capsule when ghosts are blocking
        elif len(capsules) > 0 and len(nearbyGhosts) > 0 and myState.isPacman:
            closestCapsule = min(capsules, key=lambda c: self.getMazeDistance(myPos, c))
            distToCapsule = self.getMazeDistance(myPos, closestCapsule)
            
            if distToCapsule <= 5 and minGhostDist <= 7:
                strategy = "GET_CAPSULE"
                negativeGoals.append(('capsule_available',))
                self.coordinator.updateStrategy(self.index, "getting_capsule", closestCapsule)
                print(f"Agent {self.index}: GETTING CAPSULE to handle nearby ghosts")
        
        # Priority 6: Endgame strategies
        elif timeRemaining < 100:
            if currentScore < 0:
                strategy = "DESPERATE_ATTACK"
                negativeGoals.append(('food_available',))
                self.coordinator.updateStrategy(self.index, "desperate_attack")
                print(f"Agent {self.index}: DESPERATE ATTACK - losing with {timeRemaining} time left")
            elif myState.numCarrying > 0:
                strategy = "SECURE_WIN"
                negativeGoals.append(('is_pacman', 'a{}'.format(self.index)))
                self.coordinator.updateStrategy(self.index, "securing_win")
                print(f"Agent {self.index}: SECURING WIN - returning all food")
            else:
                strategy = "DEFEND_WIN"
                for obj in objects:
                    if obj[1] in ['enemy1', 'enemy2']:
                        negativeGoals.append(('is_pacman', obj[0]))
                self.coordinator.updateStrategy(self.index, "defending_win")
                print(f"Agent {self.index}: DEFENDING WIN")
        
        # Default: Standard food collection with coordination
        else:
            teammateTarget = self.coordinator.getTeammateTarget(self.index, team_indices)
            
            if teammateStrategy == "collecting_food" and teammateTarget:
                strategy = "COORDINATED_COLLECT"
            else:
                strategy = "COLLECT_FOOD"
            
            negativeGoals.append(('food_available',))
            self.coordinator.updateStrategy(self.index, "collecting_food")
            print(f"Agent {self.index}: COLLECTING FOOD (coordinated: {strategy == 'COORDINATED_COLLECT'})")
        
        # Fallback
        if not positiveGoals and not negativeGoals:
            negativeGoals.append(('food_available',))
            print(f"Agent {self.index}: FALLBACK to food collection")
        
        return objects, initState, positiveGoals, negativeGoals
    
    def calculateReturnThreshold(self, gameState, score, timeRemaining, foodRemaining, minGhostDist, timeProgress):
        """
        Calculates how much food to carry before returning home based on current game conditions.
        """
        baseThreshold = 3
        
        # Adjust for ghost proximity
        if minGhostDist <= 3:
            baseThreshold = 1
        elif minGhostDist <= 5:
            baseThreshold = 2
        elif minGhostDist <= 7:
            baseThreshold = 3
        else:
            baseThreshold = 5
        
        # Adjust for time pressure
        if timeRemaining < 100:
            baseThreshold = min(baseThreshold, 1)
        elif timeRemaining < 200:
            baseThreshold = min(baseThreshold, 2)
        elif timeRemaining < 400:
            baseThreshold = min(baseThreshold, 3)
        
        # Adjust for score
        if score < -5:
            baseThreshold = min(baseThreshold + 2, 6)
        elif score > 10:
            baseThreshold = max(baseThreshold - 1, 1)
        
        # Adjust for remaining food
        if foodRemaining <= 2:
            baseThreshold = 1
        elif foodRemaining <= 5:
            baseThreshold = min(baseThreshold, 2)
        
        # Adjust for game phase
        if timeProgress < 0.3:
            baseThreshold = min(baseThreshold + 1, 6)
        elif timeProgress > 0.8:
            baseThreshold = max(baseThreshold - 1, 1)
        
        return max(1, baseThreshold)
    
    def executeAction(self, gameState, actions, highLevelAction):
        """
        Maps PDDL actions to specific implementations.
        """
        if highLevelAction in ["attack", "attack_aggressive"]:
            return self.collectFood(gameState, actions)
        elif highLevelAction in ["return_food", "go_home"]:
            return self.returnHome(gameState, actions)
        elif highLevelAction in ["hunt_invader", "defence"]:
            return self.defendHome(gameState, actions)
        elif highLevelAction == "get_capsule":
            return self.getCapsule(gameState, actions)
        elif highLevelAction == "hunt_scared":
            return self.huntGhost(gameState, actions)
        elif highLevelAction == "patrol":
            return self.patrol(gameState, actions)
        else:
            return self.collectFood(gameState, actions)
    
    # Low-level helper methods for strategic decisions
    
    def isDeadEnd(self, gameState, position):
        """
        Returns True if position has only one exit.
        """
        if position in self.deadEndCache:
            return self.deadEndCache[position]
        
        walls = gameState.getWalls()
        x, y = int(position[0]), int(position[1])
        
        neighbors = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
        openNeighbors = 0
        for nx, ny in neighbors:
            if 0 <= nx < walls.width and 0 <= ny < walls.height:
                if not walls[nx][ny]:
                    openNeighbors += 1
        
        isDeadEnd = openNeighbors <= 1
        self.deadEndCache[position] = isDeadEnd
        return isDeadEnd
    
    def hasEscapeRoute(self, gameState, position, ghosts):
        """
        Uses BFS to check if there's a safe path back to home territory.
        """
        if len(ghosts) == 0:
            return True
        
        walls = gameState.getWalls()
        homeX = gameState.data.layout.width // 2 - 1 if self.red else gameState.data.layout.width // 2
        
        from util import Queue
        queue = Queue()
        queue.push(position)
        visited = set([position])
        
        maxDepth = 10
        depth = 0
        
        while not queue.isEmpty() and depth < maxDepth:
            size = len(queue.list)
            for _ in range(size):
                pos = queue.pop()
                x, y = int(pos[0]), int(pos[1])
                
                if (self.red and x <= homeX) or (not self.red and x >= homeX):
                    return True
                
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    nx, ny = x + dx, y + dy
                    nextPos = (nx, ny)
                    
                    if (0 <= nx < walls.width and 0 <= ny < walls.height and 
                        not walls[nx][ny] and nextPos not in visited):
                        
                        tooClose = False
                        for ghost in ghosts:
                            if ghost.scaredTimer == 0:
                                gPos = ghost.getPosition()
                                if self.getMazeDistance(nextPos, gPos) <= 2:
                                    tooClose = True
                                    break
                        
                        if not tooClose:
                            visited.add(nextPos)
                            queue.push(nextPos)
            
            depth += 1
        
        return False
    
    def evaluateFoodTarget(self, gameState, food, ghosts):
        """
        Scores food pellets based on distance, safety, and strategic value.
        """
        myPos = gameState.getAgentPosition(self.index)
        myState = gameState.getAgentState(self.index)
        score = 0
        
        distToFood = self.getMazeDistance(myPos, food)
        score -= distToFood * 1.5
        
        if len(ghosts) > 0:
            minGhostDist = min([self.getMazeDistance(food, g.getPosition()) for g in ghosts])
            if minGhostDist <= 2:
                score -= 100
            elif minGhostDist <= 4:
                score -= 30
            
            if not self.hasEscapeRoute(gameState, food, ghosts):
                score -= 50
        
        if myState.numCarrying > 0 and self.isDeadEnd(gameState, food):
            score -= 40
        
        homeX = gameState.data.layout.width // 2 - 1 if self.red else gameState.data.layout.width // 2
        distToHome = abs(food[0] - homeX)
        score -= distToHome * 0.5 * myState.numCarrying
        
        foodList = self.getFood(gameState).asList()
        nearbyFood = sum(1 for f in foodList if self.getMazeDistance(food, f) <= 3)
        score += nearbyFood * 3
        
        return score
    
    def predictGhostPositions(self, gameState, ghosts, steps=3):
        """
        Predicts ghost positions for safer pathing. Currently conservative - assumes ghosts stay near current position.
        """
        myPos = gameState.getAgentPosition(self.index)
        predictions = []
        walls = gameState.getWalls()
        
        for ghost in ghosts:
            if ghost.scaredTimer > 0:
                predictions.append(ghost.getPosition())
            else:
                gPos = ghost.getPosition()
                predictions.append(gPos)
        
        return predictions
    
    # A* pathfinding with ghost avoidance
    
    def aStarSearch(self, gameState, start, goal, ghosts, maxDepth=30):
        """
        A* search that finds paths avoiding ghost positions. Caches paths for efficiency.
        """
        from util import PriorityQueue
        
        # Check cache
        cacheKey = (start, goal, tuple(sorted([g.getPosition() for g in ghosts if g.getPosition()])))
        currentTime = gameState.data.timeleft if gameState.data.timeleft else 0
        
        if cacheKey in self.pathCache:
            cachedTime = self.pathCacheTime.get(cacheKey, 0)
            if abs(currentTime - cachedTime) < 5:
                return self.pathCache[cacheKey]
        
        walls = gameState.getWalls()
        
        frontier = PriorityQueue()
        frontier.push((start, [start]), 0)
        
        explored = set()
        
        while not frontier.isEmpty():
            currentPos, path = frontier.pop()
            
            if currentPos == goal:
                self.pathCache[cacheKey] = path
                self.pathCacheTime[cacheKey] = currentTime
                return path
            
            if len(path) > maxDepth:
                continue
            
            if currentPos in explored:
                continue
            explored.add(currentPos)
            
            x, y = int(currentPos[0]), int(currentPos[1])
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                nextPos = (nx, ny)
                
                if not (0 <= nx < walls.width and 0 <= ny < walls.height):
                    continue
                if walls[nx][ny]:
                    continue
                
                if nextPos in explored:
                    continue
                
                cost = len(path)
                
                # Penalize positions near ghosts
                ghostPenalty = 0
                for ghost in ghosts:
                    if ghost.scaredTimer == 0 and ghost.getPosition():
                        gPos = ghost.getPosition()
                        distToGhost = abs(nx - gPos[0]) + abs(ny - gPos[1])
                        
                        if distToGhost <= 1:
                            ghostPenalty += 1000
                        elif distToGhost == 2:
                            ghostPenalty += 100
                        elif distToGhost == 3:
                            ghostPenalty += 20
                        elif distToGhost <= 5:
                            ghostPenalty += 5
                
                if len(ghosts) > 0 and self.isDeadEnd(gameState, nextPos):
                    ghostPenalty += 50
                
                totalCost = cost + ghostPenalty
                
                heuristic = abs(nx - goal[0]) + abs(ny - goal[1])
                
                priority = totalCost + heuristic
                
                newPath = path + [nextPos]
                frontier.push((nextPos, newPath), priority)
        
        return None
    
    def getNextActionFromPath(self, gameState, path):
        """
        Converts a path into the next directional action.
        """
        if not path or len(path) < 2:
            return Directions.STOP
        
        myPos = gameState.getAgentPosition(self.index)
        nextPos = path[1]
        
        dx = nextPos[0] - myPos[0]
        dy = nextPos[1] - myPos[1]
        
        if dx == 1:
            return Directions.EAST
        elif dx == -1:
            return Directions.WEST
        elif dy == 1:
            return Directions.NORTH
        elif dy == -1:
            return Directions.SOUTH
        else:
            return Directions.STOP
    
    # Tactical implementations
    
    def collectFood(self, gameState, actions):
        """
        Selects and approaches food pellets using A* pathfinding and coordination.
        """
        myPos = gameState.getAgentPosition(self.index)
        myState = gameState.getAgentState(self.index)
        foodList = self.getFood(gameState).asList()
        
        if len(foodList) == 0:
            return self.returnHome(gameState, actions)
        
        enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        ghosts = [a for a in enemies if not a.isPacman and a.getPosition() != None and a.scaredTimer == 0]
        
        # Emergency retreat if carrying food and ghost nearby
        if len(ghosts) > 0 and myState.numCarrying > 0:
            minGhostDist = min([self.getMazeDistance(myPos, g.getPosition()) for g in ghosts])
            if minGhostDist <= 2:
                return self.returnHome(gameState, actions)
        
        # Filter out food claimed by teammate
        availableFood = [f for f in foodList if not self.coordinator.isClaimedByTeammate(f, self.index)]
        if len(availableFood) == 0:
            availableFood = foodList
        
        # Evaluate and select best food target
        bestFood = None
        bestScore = -999999
        
        for food in availableFood:
            score = self.evaluateFoodTarget(gameState, food, ghosts)
            if score > bestScore:
                bestScore = score
                bestFood = food
        
        if bestScore < -80 and myState.numCarrying >= 1:
            return self.returnHome(gameState, actions)
        
        # Use A* for safe path
        path = self.aStarSearch(gameState, myPos, bestFood, ghosts, maxDepth=30)
        
        if path and len(path) > 1:
            self.coordinator.claimFood(bestFood)
            self.coordinator.updateStrategy(self.index, "collecting_food", bestFood)
            
            action = self.getNextActionFromPath(gameState, path)
            if action in actions:
                return action
        
        return self.moveTowardsSmart(gameState, actions, bestFood, ghosts)
    
    def returnHome(self, gameState, actions):
        """
        Returns to home territory using A* to find the safest entry point.
        """
        myPos = gameState.getAgentPosition(self.index)
        
        enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        ghosts = [a for a in enemies if not a.isPacman and a.getPosition() != None and a.scaredTimer == 0]
        
        # Determine home boundary
        if self.red:
            homeX = gameState.data.layout.width // 2 - 1
        else:
            homeX = gameState.data.layout.width // 2
        
        # Find all valid entry points
        walls = gameState.getWalls()
        validHomePositions = []
        for y in range(walls.height):
            if not walls[homeX][y]:
                validHomePositions.append((homeX, y))
        
        # Select safest entry point
        bestHomePos = None
        bestScore = -999999
        
        for homePos in validHomePositions:
            score = 0
            
            dist = self.getMazeDistance(myPos, homePos)
            score -= dist * 10
            
            if len(ghosts) > 0:
                minGhostDist = min([self.getMazeDistance(homePos, g.getPosition()) for g in ghosts])
                score += minGhostDist * 20
            
            if score > bestScore:
                bestScore = score
                bestHomePos = homePos
        
        if bestHomePos is None:
            bestHomePos = self.start
        
        # Use A* for safe path
        path = self.aStarSearch(gameState, myPos, bestHomePos, ghosts, maxDepth=50)
        
        if path and len(path) > 1:
            action = self.getNextActionFromPath(gameState, path)
            if action in actions:
                return action
        
        return self.moveTowardsSmart(gameState, actions, bestHomePos, ghosts)
    
    def getCapsule(self, gameState, actions):
        """
        Approaches power capsules when strategic.
        """
        myPos = gameState.getAgentPosition(self.index)
        capsules = self.getCapsules(gameState)
        
        if len(capsules) == 0:
            return self.collectFood(gameState, actions)
        
        enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        ghosts = [a for a in enemies if not a.isPacman and a.getPosition() != None and a.scaredTimer == 0]
        
        if len(ghosts) > 0:
            bestCapsule = min(capsules, key=lambda c: self.getMazeDistance(myPos, c))
            return self.moveTowardsSmart(gameState, actions, bestCapsule, ghosts)
        
        target = capsules[0]
        return self.moveTowards(gameState, actions, target, avoidGhosts=True)
    
    def huntGhost(self, gameState, actions):
        """
        Pursues scared ghosts for bonus points.
        """
        myPos = gameState.getAgentPosition(self.index)
        enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        scaredGhosts = [a for a in enemies if a.scaredTimer > 0 and a.getPosition() != None]
        
        if len(scaredGhosts) == 0:
            return self.collectFood(gameState, actions)
        
        target = scaredGhosts[0].getPosition()
        return self.moveTowards(gameState, actions, target, avoidGhosts=False)
    
    def defendHome(self, gameState, actions):
        """
        Intercepts invaders using A* pathfinding and coordination to split targets.
        """
        myPos = gameState.getAgentPosition(self.index)
        enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
        ghosts = []
        
        if len(invaders) > 0:
            minDist = 999999
            closestInvader = None
            for invader in invaders:
                dist = self.getMazeDistance(myPos, invader.getPosition())
                if dist < minDist:
                    minDist = dist
                    closestInvader = invader
            
            targetPos = closestInvader.getPosition()
            
            # Coordinate with teammate if multiple invaders
            if len(invaders) > 1:
                teammateStrategy = self.coordinator.getTeammateStrategy(self.index, self.getTeam(gameState))
                if teammateStrategy == "defending":
                    teammateTarget = self.coordinator.getTeammateTarget(self.index, self.getTeam(gameState))
                    if teammateTarget and len(invaders) > 1:
                        for inv in invaders:
                            if inv.getPosition() != teammateTarget:
                                targetPos = inv.getPosition()
                                break
            
            # Use A* for interception
            path = self.aStarSearch(gameState, myPos, targetPos, ghosts, maxDepth=40)
            
            if path and len(path) > 1:
                self.coordinator.updateStrategy(self.index, "defending", targetPos)
                action = self.getNextActionFromPath(gameState, path)
                if action in actions:
                    return action
            
            return self.moveTowards(gameState, actions, targetPos, avoidGhosts=False)
        else:
            return self.patrol(gameState, actions)
    
    def patrol(self, gameState, actions):
        """
        Guards territory by positioning near vulnerable food and entry points.
        """
        myPos = gameState.getAgentPosition(self.index)
        
        foodDefending = self.getFoodYouAreDefending(gameState).asList()
        
        if len(foodDefending) > 0:
            walls = gameState.getWalls()
            width = walls.width
            height = walls.height
            
            if self.red:
                boundary = width // 2 - 1
            else:
                boundary = width // 2
            
            # Find most vulnerable food
            vulnerableFood = None
            minDistToBoundary = 999999
            
            for food in foodDefending:
                distToBoundary = abs(food[0] - boundary)
                if distToBoundary < minDistToBoundary:
                    minDistToBoundary = distToBoundary
                    vulnerableFood = food
            
            if vulnerableFood:
                fx, fy = vulnerableFood
                
                if self.red:
                    targetX = boundary - 2
                else:
                    targetX = boundary + 2
                
                targetY = fy
                
                # Find nearby valid position
                bestPos = myPos
                minDist = 999999
                
                for dy in range(-3, 4):
                    for dx in range(-2, 3):
                        testPos = (targetX + dx, targetY + dy)
                        if (0 <= testPos[0] < width and 0 <= testPos[1] < height):
                            if not walls[testPos[0]][testPos[1]]:
                                dist = self.getMazeDistance(myPos, testPos)
                                if dist < minDist:
                                    minDist = dist
                                    bestPos = testPos
                
                return self.moveTowards(gameState, actions, bestPos, avoidGhosts=False)
        
        # Default to center position
        centerY = walls.height // 2
        if self.red:
            centerX = width // 2 - 3
        else:
            centerX = width // 2 + 3
        
        return self.moveTowards(gameState, actions, (centerX, centerY), avoidGhosts=False)
    
    def moveTowardsSmart(self, gameState, actions, target, ghosts):
        """
        Movement with ghost prediction and multi-step safety evaluation.
        """
        myPos = gameState.getAgentPosition(self.index)
        bestAction = random.choice(actions)
        bestScore = -999999
        
        ghostPredictions = self.predictGhostPositions(gameState, ghosts, steps=2)
        
        for action in actions:
            successor = self.getSuccessor(gameState, action)
            pos2 = successor.getAgentPosition(self.index)
            
            score = 0
            
            distToTarget = self.getMazeDistance(pos2, target)
            score -= distToTarget * 10
            
            if len(ghosts) > 0:
                dangerousGhosts = [g for g in ghosts if g.scaredTimer == 0]
                
                for ghost in dangerousGhosts:
                    gPos = ghost.getPosition()
                    ghostDist = self.getMazeDistance(pos2, gPos)
                    
                    if ghostDist <= 1:
                        score -= 10000
                    elif ghostDist == 2:
                        score -= 500
                    elif ghostDist == 3:
                        score -= 200
                    elif ghostDist <= 5:
                        score -= 50
                
                for predPos in ghostPredictions:
                    predDist = self.getMazeDistance(pos2, predPos)
                    if predDist <= 2:
                        score -= 300
            
            if len(ghosts) > 0 and len([g for g in ghosts if self.getMazeDistance(myPos, g.getPosition()) <= 5]) > 0:
                homeX = gameState.data.layout.width // 2 - 1 if self.red else gameState.data.layout.width // 2
                distToHome = abs(pos2[0] - homeX)
                score -= distToHome * 5
            
            if len(ghosts) > 0 and self.isDeadEnd(gameState, pos2):
                score -= 400
            
            if len(self.lastPositions) > 0 and pos2 == self.lastPositions[-1]:
                score -= 5
            
            if score > bestScore:
                bestScore = score
                bestAction = action
        
        return bestAction
    
    def moveTowards(self, gameState, actions, target, avoidGhosts=True):
        """
        Basic movement toward target with optional ghost avoidance.
        """
        myPos = gameState.getAgentPosition(self.index)
        bestDist = 999999
        bestAction = random.choice(actions)
        
        enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        ghosts = [a for a in enemies if not a.isPacman and a.getPosition() != None]
        
        for action in actions:
            successor = self.getSuccessor(gameState, action)
            pos2 = successor.getAgentPosition(self.index)
            
            dist = self.getMazeDistance(pos2, target)
            
            if avoidGhosts and len(ghosts) > 0:
                scaredGhosts = [g for g in ghosts if g.scaredTimer > 0]
                dangerousGhosts = [g for g in ghosts if g.scaredTimer == 0]
                
                if len(dangerousGhosts) > 0:
                    ghostDist = min([self.getMazeDistance(pos2, g.getPosition()) for g in dangerousGhosts])
                    if ghostDist <= 1:
                        continue
                    elif ghostDist <= 3:
                        dist += (4 - ghostDist) * 30
            
            if dist < bestDist:
                bestDist = dist
                bestAction = action
        
        return bestAction
    
    def getSuccessor(self, gameState, action):
        """
        Generates successor state after taking an action.
        """
        successor = gameState.generateSuccessor(self.index, action)
        pos = successor.getAgentState(self.index).getPosition()
        if pos != nearestPoint(pos):
            return successor.generateSuccessor(self.index, action)
        else:
            return successor


