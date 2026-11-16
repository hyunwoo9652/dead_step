"""그래픽 화면과 로컬 서버를 쓸 수 없는 환경을 위한 콘솔 화면."""
from web_ui import WebState


def draw(state):
    g = state.game
    cells = []
    for r in range(15):
        row = []
        for c in range(15):
            p = (r, c)
            if p == g.player:
                mark = 'P'
            elif p == g.enemy:
                mark = 'Z'
            elif p == g.exit:
                mark = 'E'
            elif p in g.walls:
                mark = '##'
            elif g.status != 'playing' and p in g.sources:
                mark = 'XX'
            elif p in g.flags:
                mark = '!'
            elif p in g.scans and p in g.hints:
                mark = f'{g.hints[p]}/s{g.scans[p]}'
            elif p in g.scans:
                mark = f's{g.scans[p]}'
            elif p in g.hints:
                mark = str(g.hints[p])
            else:
                mark = '.'
            row.append(f'{mark:>4}')
        cells.append(''.join(row))
    print('\n' + '\n'.join(cells))
    print(f'상태: {g.status} | 턴: {g.turn} | 다음 감염체 행동: {g.next_enemy_mode}')
    print(g.reason if g.status != 'playing' else g.message)
    print('이동 w/a/s/d | 탐색 scan 행1 열1 행2 열2 | 표시 flag 행 열 | new [easy/normal/hard] | retry | quit')
    print('좌표는 0부터 시작합니다. 흰 숫자는 주변 8칸, s숫자는 중심 포함 3×3 감염원 수입니다.')


def serve():
    state = WebState()
    moves = {'w': (-1, 0), 'a': (0, -1), 's': (1, 0), 'd': (0, 1)}
    while True:
        draw(state)
        try:
            parts = input('> ').strip().lower().split()
        except (EOFError, KeyboardInterrupt):
            print('\n게임을 종료합니다.')
            return
        if not parts:
            continue
        try:
            if parts[0] in ('quit', 'q', 'exit'):
                return
            if parts[0] in moves and len(parts) == 1:
                state.action({'action': 'move', 'direction': list(moves[parts[0]])})
            elif parts[0] == 'scan' and len(parts) == 5:
                values = list(map(int, parts[1:]))
                state.action({'action': 'scan', 'points': [values[:2], values[2:]]})
            elif parts[0] == 'flag' and len(parts) == 3:
                state.action({'action': 'flag', 'point': list(map(int, parts[1:]))})
            elif parts[0] == 'new' and len(parts) <= 2:
                state.action({'action': 'new', 'difficulty': parts[1] if len(parts) == 2 else state.difficulty})
            elif parts == ['retry']:
                state.action({'action': 'retry'})
            else:
                print('명령을 다시 입력하세요.')
        except ValueError as exc:
            print(f'입력 오류: {exc}')


if __name__ == '__main__':
    serve()
