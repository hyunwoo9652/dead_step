"""플레이어 담당: 이동 검증, 탐색 범위와 두 지점 검증, 숫자 정보."""
from settings import SIZE, DIRS, neighbors
from board import count

def scan_allowed(game, p):
    return (0 <= p[0] < SIZE and 0 <= p[1] < SIZE and p not in game.walls
            and max(abs(p[0]-game.player[0]), abs(p[1]-game.player[1])) <= 2)

def move(game, dr, dc):
    if game.status != 'playing' or (dr, dc) not in DIRS:
        return False
    q = (game.player[0] + dr, game.player[1] + dc)
    if q not in neighbors(game.player) or q in game.walls:
        game.message = '이동할 수 없는 칸입니다. 턴은 소비되지 않습니다.'
        return False
    game.player = q
    game.visited.add(q)
    game.complete_action('move')
    return True


def reveal_move(game):
    game.hints[game.player] = count(game, game.player, include_center=False)
    game.message = f'이동: 주변 8칸에 감염원 {game.hints[game.player]}개'


def scan(game, points):
    if game.status != 'playing':
        return False
    if len(points) != 2 or len(set(points)) != 2 or not all(scan_allowed(game, p) for p in points):
        game.message = '5×5 범위의 서로 다른 두 지점을 선택하세요.'
        return False
    for p in points:
        game.scans[p] = count(game, p, include_center=True)
    game.message = '탐색 완료: 선택 칸을 포함한 3×3 감염원 수를 표시합니다.'
    game.complete_action('scan')
    return True
