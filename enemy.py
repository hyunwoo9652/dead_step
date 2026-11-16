"""감염체 담당: deque Queue 기반 BFS, 랜덤 이동, 다음 행동 표시."""
from collections import deque
from settings import neighbors

def path(start, goal, blocked):
    queue = deque([start])
    previous = {start: None}
    while queue:
        p = queue.popleft()
        if p == goal:
            result = []
            while p is not None:
                result.append(p)
                p = previous[p]
            return result[::-1]
        for q in neighbors(p):
            if q not in blocked and q not in previous:
                previous[q] = p
                queue.append(q)
    return []

def step(game):
    if game.turn % 2 == 1:
        route = path(game.enemy, game.player, game.walls)
        if len(route) > 1:
            game.enemy = route[1]
    else:
        options = [p for p in neighbors(game.enemy) if p not in game.walls]
        if options:
            game.enemy = game.rng.choice(options)


def next_mode(game):
    return 'BFS 추격' if game.turn % 2 == 0 else '랜덤 이동'
