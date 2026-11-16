"""진행 담당: 게임 상태 초기화, 턴 순서, 승패 판정, 기능 통합."""
import random
import board
import player
import enemy

class Game:
    def __init__(self, difficulty='normal', seed=None):
        self.rng = random.Random(seed)
        self.seed = seed
        self.difficulty = difficulty
        self.player, self.exit, self.enemy = (14, 0), (0, 14), (0, 0)
        self.turn = 0
        self.status = 'playing'
        self.reason = ''
        self.hints = {}
        self.scans = {}
        self.flags = set()
        self.visited = {self.player}
        self.message = '출구까지 탈출하세요. S: 탐색 / 방향키: 이동'
        board.initialize(self)
        self.hints[self.player] = board.count(self, self.player, include_center=False)

    def check_player(self):
        if self.player in self.sources:
            self.status, self.reason = 'lost', '숨겨진 감염원을 밟았습니다.'
        elif self.player == self.enemy:
            self.status, self.reason = 'lost', '감염체와 접촉했습니다.'
        elif self.player == self.exit:
            self.status, self.reason = 'won', f'{self.turn}턴 만에 탈출했습니다!'
        return self.status != 'playing'

    def complete_action(self, kind):
        """유효 행동 한 번 = 턴 하나. 출구 및 즉시 패배를 추격보다 먼저 판정."""
        self.turn += 1
        if self.check_player():
            return
        if kind == 'move':
            player.reveal_move(self)
        self.enemy_step()

    def move(self, dr, dc):
        return player.move(self, dr, dc)

    def scan(self, points):
        return player.scan(self, points)

    def scan_allowed(self, p):
        return player.scan_allowed(self, p)

    def count(self, p, include_center):
        return board.count(self, p, include_center)

    def enemy_step(self):
        enemy.step(self)
        self.check_player()

    @property
    def next_enemy_mode(self):
        return enemy.next_mode(self)
