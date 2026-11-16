"""Linux 데스크톱에서 실제 Tk 창을 자동 조작하고 창 영역만 캡처합니다."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime

from enemy import path
from game import Game


def winning_route():
    """화면 검증용 경로. 감염원 정보를 사용하므로 사용자 추론 평가가 아닙니다."""
    for seed in range(100):
        game = Game(seed=seed)
        route = path(game.player, game.exit, game.walls | game.sources)
        directions = [(b[0] - a[0], b[1] - a[1]) for a, b in zip(route, route[1:])]
        for direction in directions:
            game.move(*direction)
            if game.status != 'playing':
                break
        if game.status == 'won':
            return seed, directions
    raise RuntimeError('자동 검증용 승리 경로를 찾지 못했습니다.')


def main():
    if not os.environ.get('DISPLAY'):
        raise RuntimeError('그래픽 데스크톱의 터미널에서 실행하세요. DISPLAY가 없습니다.')
    capture_command = shutil.which('import')
    if not capture_command:
        raise RuntimeError('창 캡처에 필요한 ImageMagick의 import 명령을 찾지 못했습니다.')
    import tkinter as tk
    from ui import App, CELL, PAD

    root = tk.Tk()
    output = Path(__file__).resolve().parent.parent / '제작보고서' / '실행화면' / datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    output.mkdir(parents=True)
    # 자동 승리 검증이 사용자의 개인 기록에 섞이지 않도록 별도 경로 사용.
    os.environ['LOCALAPPDATA'] = str(output / '_test_records')
    app = App(root)
    root.geometry('+30+30')
    records = {
        'started_at': datetime.now().isoformat(), 'python': sys.version,
        'method': '실제 ui.App 창에 Tk 키/마우스 이벤트를 생성하고 ImageMagick으로 해당 창만 캡처',
        'limitations': '합성 입력에 의한 기능 검증. 사용자 플레이 평가가 아님. 승리 경로는 감염원 정보를 사용해 사전 선택.',
        'complete': False, 'screenshots': [], 'checks': [],
        'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in Path(__file__).parent.glob('*.py')},
    }

    def write_log():
        (output / 'capture_log.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')

    def check(condition, description):
        records['checks'].append({'description': description, 'passed': bool(condition)})
        write_log()
        if not condition:
            raise AssertionError(description)

    def key(name):
        root.focus_force()
        root.event_generate('<KeyPress-' + name + '>', when='now')

    def click(point, button=1):
        r, c = point
        app.canvas.event_generate('<Button-' + str(button) + '>',
                                  x=PAD + c * CELL + CELL // 2,
                                  y=PAD + r * CELL + CELL // 2, when='now')

    def capture(name, caption):
        root.update_idletasks()
        target = output / (name + '.png')
        subprocess.run([capture_command, '-window', str(root.winfo_id()), str(target)],
                       check=True, capture_output=True, timeout=15)
        check(target.is_file() and target.stat().st_size > 0, name + ': 캡처 파일 생성')
        records['screenshots'].append({
            'file': target.name, 'caption': caption, 'captured_at': datetime.now().isoformat(),
            'seed': app.seed, 'turn': app.game.turn, 'status': app.game.status,
            'player': app.game.player, 'enemy': app.game.enemy,
            'stats_text': app.stats.cget('text'), 'message_text': app.message.cget('text'),
        })
        write_log()
        print('저장:', target, flush=True)

    def scenario():
        app.new_game(7)
        yield ('01_start', '보통 난이도 시작 화면. 플레이어·감염체·출구와 턴 0 표시.')
        key('Down')
        check(app.game.turn == 0 and app.game.player == (14, 0), '맵 밖 이동은 턴을 소비하지 않음')
        key('Right')
        check(app.game.turn == 1 and app.game.player == (14, 1), '방향키 이동 후 한 칸 이동·턴 1 증가')
        yield ('02_move', '이동 후 주변 8칸 정보 및 다음 감염체 행동 표시.')
        key('s')
        click((14, 1))
        check(app.scan_mode and len(app.selected) == 1 and app.game.turn == 1, '탐색 한 지점 선택은 턴 유지')
        yield ('03_scan_selection', '탐색 범위와 첫 번째 선택 지점 표시. 아직 턴을 소비하지 않음.')
        click((13, 1))
        check(not app.scan_mode and len(app.game.scans) == 2 and app.game.turn == 2, '두 지점 확정 후 탐색 결과 공개·턴 증가')
        yield ('04_scan_result', '두 지점의 중심 포함 3×3 감염원 수가 s숫자로 표시됨.')
        key('s')
        key('Escape')
        check(not app.scan_mode and app.game.turn == 2, '탐색 취소는 턴 유지')
        click((14, 2), 3)
        check((14, 2) in app.game.flags and app.game.turn == 2, '우클릭 위험 표시도 턴 유지')
        yield ('05_flag', '위험 예상 칸 표시. 메모 기능은 턴을 소비하지 않음.')
        walls, sources = app.game.walls.copy(), app.game.sources.copy()
        app.retry()
        check(app.game.turn == 0 and app.game.walls == walls and app.game.sources == sources, '같은 맵 재도전의 배치 유지·상태 초기화')
        yield ('06_retry', '같은 맵 재도전 후 턴과 정보 초기화.')
        # 일반 행동만 반복하여 패배 화면에 도달. 상태 값을 직접 바꾸지 않음.
        for _ in range(200):
            key('s')
            click((14, 0))
            click((14, 1))
            if app.game.status == 'lost':
                break
            yield None
        check(app.game.status == 'lost', '반복 탐색 중 감염체 접촉으로 패배 판정')
        yield ('07_loss', '반복 탐색 자동 시나리오의 패배 화면. 종료 후 감염원 위치 공개.')
        seed, directions = winning_route()
        app.new_game(seed)
        yield None
        keynames = {(-1, 0): 'Up', (1, 0): 'Down', (0, -1): 'Left', (0, 1): 'Right'}
        for direction in directions:
            key(keynames[direction])
            yield None
        check(app.game.status == 'won', '실제 이동 입력으로 출구 도착·승리 판정')
        yield ('08_win', '자동 경로 시나리오의 승리 화면. 감염원 정보를 사용한 검증 경로이며 사용자 추론 성공의 증거는 아님.')

    steps = scenario()
    failed = False

    def fail(exc):
        nonlocal failed
        failed = True
        records['error'] = str(exc)
        write_log()
        print('캡처 중단:', exc, file=sys.stderr, flush=True)
        root.destroy()

    def advance():
        try:
            item = next(steps)
            if item:
                root.after(300, lambda: save_and_continue(item))
            else:
                root.after(60, advance)
        except StopIteration:
            records['complete'] = True
            write_log()
            print('캡처 완료:', output, flush=True)
            root.after(500, root.destroy)
        except Exception as exc:
            fail(exc)

    def save_and_continue(item):
        try:
            capture(*item)
            root.after(60, advance)
        except Exception as exc:
            fail(exc)

    root.after(600, advance)
    root.mainloop()
    return 1 if failed or not records['complete'] else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print('실행 불가:', exc, file=sys.stderr)
        sys.exit(1)
