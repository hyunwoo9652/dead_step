"""공용 상수: 변경 사항은 팀 전체와 합의하세요."""
SIZE = 15
DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))

def neighbors(p):
    r, c = p
    return [(r+dr, c+dc) for dr, dc in DIRS if 0 <= r+dr < SIZE and 0 <= c+dc < SIZE]
