"""추가 패키지 없이 실행하는 로컬 브라우저 화면과 게임 API."""
import json
import os
from pathlib import Path
import random
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from game import Game
from settings import SIZE


DIFFICULTIES = ('easy', 'normal', 'hard')
HTML_PATH = Path(__file__).with_name('web_ui.html')


class WebState:
    def __init__(self):
        self.records_path = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'DeadStep' / 'records.json'
        self.records = self.load_records()
        self.difficulty = 'normal'
        self.new_game()

    def load_records(self):
        try:
            data = json.loads(self.records_path.read_text(encoding='utf-8'))
            return {k: v for k, v in data.items()
                    if k in DIFFICULTIES and isinstance(v, int) and not isinstance(v, bool) and v > 0}
        except (OSError, ValueError, AttributeError):
            return {}

    def new_game(self, difficulty=None, seed=None):
        if difficulty is not None:
            if difficulty not in DIFFICULTIES:
                raise ValueError('지원하지 않는 난이도입니다.')
            self.difficulty = difficulty
        self.seed = random.randrange(2**32) if seed is None else seed
        self.game = Game(self.difficulty, self.seed)
        self.logged_result = False

    def save_result(self):
        g = self.game
        if self.logged_result or g.status == 'playing':
            return
        self.logged_result = True
        if g.status != 'won':
            return
        old = self.records.get(g.difficulty)
        if old is None or g.turn < old:
            self.records[g.difficulty] = g.turn
            try:
                self.records_path.parent.mkdir(parents=True, exist_ok=True)
                self.records_path.write_text(json.dumps(self.records), encoding='utf-8')
            except OSError:
                g.message = '기록을 파일에 저장하지 못했습니다. 이번 실행 중에는 유지됩니다.'

    @staticmethod
    def point(value):
        if not isinstance(value, list) or len(value) != 2 or any(type(x) is not int for x in value):
            raise ValueError('좌표는 정수 두 개로 입력해야 합니다.')
        return tuple(value)

    def action(self, data):
        if not isinstance(data, dict):
            raise ValueError('잘못된 요청입니다.')
        kind = data.get('action')
        if kind == 'new':
            self.new_game(data.get('difficulty', self.difficulty))
        elif kind == 'retry':
            self.new_game(seed=self.seed)
        elif kind == 'move':
            dr, dc = self.point(data.get('direction'))
            self.game.move(dr, dc)
        elif kind == 'scan':
            points = data.get('points')
            if not isinstance(points, list) or len(points) != 2:
                raise ValueError('서로 다른 두 칸을 선택해야 합니다.')
            self.game.scan([self.point(p) for p in points])
        elif kind == 'flag':
            p = self.point(data.get('point'))
            g = self.game
            if (g.status == 'playing' and 0 <= p[0] < SIZE and 0 <= p[1] < SIZE
                    and p not in g.walls):
                if p in g.flags:
                    g.flags.remove(p)
                else:
                    g.flags.add(p)
        else:
            raise ValueError('알 수 없는 행동입니다.')
        self.save_result()
        return self.snapshot()

    def snapshot(self):
        g = self.game
        self.save_result()
        def points(values):
            return [list(p) for p in sorted(values)]
        def counts(values):
            return [[p[0], p[1], value] for p, value in sorted(values.items())]
        return {
            'size': SIZE,
            'difficulty': g.difficulty,
            'seed': self.seed,
            'status': g.status,
            'turn': g.turn,
            'message': g.reason if g.status != 'playing' else g.message,
            'next_enemy_mode': g.next_enemy_mode if g.status == 'playing' else '종료',
            'player': list(g.player),
            'enemy': list(g.enemy),
            'exit': list(g.exit),
            'walls': points(g.walls),
            'sources': points(g.sources) if g.status != 'playing' else [],
            'source_count': len(g.sources),
            'visited': points(g.visited),
            'flags': points(g.flags),
            'hints': counts(g.hints),
            'scans': counts(g.scans),
            'scan_allowed': points((r, c) for r in range(SIZE) for c in range(SIZE)
                                   if g.scan_allowed((r, c))) if g.status == 'playing' else [],
            'record': self.records.get(g.difficulty),
        }


def create_server():
    state = WebState()

    class Handler(BaseHTTPRequestHandler):
        def respond(self, status, body, content_type):
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == '/':
                self.respond(200, HTML_PATH.read_bytes(), 'text/html; charset=utf-8')
            elif self.path == '/api/state':
                body = json.dumps(state.snapshot(), ensure_ascii=False).encode('utf-8')
                self.respond(200, body, 'application/json; charset=utf-8')
            elif self.path == '/favicon.ico':
                self.respond(204, b'', 'image/x-icon')
            else:
                self.respond(404, b'Not found', 'text/plain; charset=utf-8')

        def do_POST(self):
            if self.path != '/api/action':
                self.respond(404, b'Not found', 'text/plain; charset=utf-8')
                return
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if length < 1 or length > 4096:
                    raise ValueError('요청 크기가 올바르지 않습니다.')
                data = json.loads(self.rfile.read(length).decode('utf-8'))
                result = state.action(data)
                status = 200
            except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
                result = {'error': str(exc)}
                status = 400
            body = json.dumps(result, ensure_ascii=False).encode('utf-8')
            self.respond(status, body, 'application/json; charset=utf-8')

    return ThreadingHTTPServer(('127.0.0.1', 0), Handler)


def serve(open_browser=True):
    server = create_server()
    url = f'http://127.0.0.1:{server.server_port}/'
    print(f'데드 스텝 화면: {url}', flush=True)
    print('종료하려면 이 터미널에서 Ctrl+C를 누르세요.', flush=True)
    has_desktop = os.name == 'nt' or sys.platform == 'darwin' or bool(
        os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'))
    if open_browser and has_desktop:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    serve()
