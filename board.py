"""맵 담당: 맵 생성, 요소 배치, 주변 감염원 수 계산. 좌표는 (행, 열)."""
from settings import SIZE
from enemy import path

def initialize(game):
    """공유 Game 상태에 맵 데이터를 구성합니다."""
    count, wall_count = {'easy': (5, 22), 'normal': (8, 32), 'hard': (10, 40)}[game.difficulty]
    cells = {(r,c) for r in range(SIZE) for c in range(SIZE)}
    # Keep a small starting area safe. This is a fairness addition to the documents.
    safe = {(r,c) for r in range(12,15) for c in range(3)} | {game.exit, game.enemy}
    candidates = sorted(cells - safe)
    for _ in range(2000):
        game.walls = set(game.rng.sample(candidates, wall_count))
        game.sources = set(game.rng.sample(sorted(cells - safe - game.walls), count))
        if path(game.player, game.exit, game.walls | game.sources) and path(game.enemy, game.player, game.walls):
            break
    else:
        raise RuntimeError('유효한 맵을 생성할 수 없습니다.')
    game.terrain = [[{'wall': (r,c) in game.walls, 'source': (r,c) in game.sources}
                     for c in range(SIZE)] for r in range(SIZE)]

def count(game, p, include_center):
    r,c = p
    return sum((r+dr,c+dc) in game.sources for dr in (-1,0,1) for dc in (-1,0,1)
               if include_center or (dr,dc) != (0,0))
