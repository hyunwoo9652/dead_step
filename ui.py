"""Offline desktop interface using the Python standard library."""
import json
import os
from pathlib import Path
import random
import tkinter as tk
from tkinter import messagebox, font as tkfont
from game import Game
from settings import SIZE

BG = '#101722'
PANEL = '#192435'
TEXT = '#e6edf7'
MUTED = '#a2b2c8'
CELL = 38
PAD = 12

class App:
    def __init__(self, root):
        self.root = root
        root.title('DEAD STEP · 데드 스텝')
        root.configure(bg=BG)
        root.resizable(False, False)
        # Use an installed Korean outline font instead of relying on a Windows-only name.
        families = set(tkfont.families(root))
        self.ui_font = next((name for name in (
            'Noto Sans CJK KR', 'Noto Sans KR', 'Malgun Gothic', '맑은 고딕',
            'NanumGothic', 'DejaVu Sans'
        ) if name in families), 'TkDefaultFont')
        root.option_add('*Font', (self.ui_font, 10))
        self.records_path = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'DeadStep' / 'records.json'
        self.records = self.load_records()
        self.difficulty = tk.StringVar(value='normal')
        self.selected = []
        self.scan_mode = False
        self.logged_result = False
        outer = tk.Frame(root, bg=BG, padx=20, pady=15)
        outer.pack()
        tk.Label(outer, text='DEAD STEP', fg=TEXT, bg=BG, font=(self.ui_font, 25, 'bold')).grid(row=0,column=0,sticky='w')
        tk.Label(outer, text='정보를 모으고, 추격을 피해 탈출하세요.', fg=MUTED, bg=BG, font=(self.ui_font,10)).grid(row=1,column=0,sticky='w',pady=(0,12))
        self.canvas = tk.Canvas(outer, width=SIZE*CELL+PAD*2, height=SIZE*CELL+PAD*2, bg=BG, highlightthickness=0)
        self.canvas.grid(row=2,column=0)
        side = tk.Frame(outer, bg=PANEL, padx=16,pady=16,width=275)
        side.grid(row=0,column=1,rowspan=3,sticky='ns',padx=(18,0))
        tk.Label(side,text='탈출 작전',bg=PANEL,fg=TEXT,font=(self.ui_font,17,'bold')).pack(anchor='w')
        self.stats = tk.Label(side,bg=PANEL,fg=TEXT,justify='left',font=(self.ui_font,11))
        self.stats.pack(anchor='w',pady=15)
        for label, key in [('쉬움 · 감염원 5개','easy'),('보통 · 감염원 8개','normal'),('어려움 · 감염원 10개','hard')]:
            tk.Radiobutton(side,text=label,variable=self.difficulty,value=key,bg=PANEL,fg=TEXT,selectcolor=BG,activebackground=PANEL,activeforeground=TEXT,command=self.new_game).pack(anchor='w')
        self.button(side,'새 게임  [R]',self.new_game)
        self.button(side,'같은 맵 다시 도전',self.retry)
        self.scan_button = self.button(side,'탐색 시작 / 취소  [S]',self.toggle_scan)
        self.button(side,'게임 방법',self.help)
        tk.Label(side,text='P  플레이어     E  출구\nZ  감염체       ■  벽\n우클릭: 위험 예상 칸 표시\n\n흰 숫자: 이동 정보 (주변 8칸)\n파란 s숫자: 탐색 정보 (중심 포함 9칸)\n\n탐색 중 서로 다른 두 칸을 클릭하면\n한 턴이 진행됩니다.\nS / Esc로 탐색을 취소할 수 있습니다.',bg=PANEL,fg=MUTED,justify='left',font=(self.ui_font,10)).pack(anchor='w',pady=16)
        self.record_label = tk.Label(side,bg=PANEL,fg='#77dcc4',justify='left',font=(self.ui_font,10))
        self.record_label.pack(anchor='w')
        self.message = tk.Label(outer,bg=BG,fg=TEXT,anchor='w',justify='left',wraplength=850,font=(self.ui_font,10))
        self.message.grid(row=3,column=0,columnspan=2,sticky='w',pady=(12,0))
        root.bind('<KeyPress>',self.key)
        self.canvas.bind('<Button-1>',self.click)
        self.canvas.bind('<Button-3>',self.flag)
        self.new_game()

    def button(self,parent,text,command):
        b=tk.Button(parent,text=text,command=command,bg='#2a3c55',fg=TEXT,activebackground='#39577a',activeforeground=TEXT,relief='flat',padx=12,pady=9,font=(self.ui_font,10))
        b.pack(fill='x',pady=4)
        return b

    def load_records(self):
        try:
            data=json.loads(self.records_path.read_text(encoding='utf-8'))
            return {k:v for k,v in data.items() if k in ('easy','normal','hard') and isinstance(v,int) and v>0}
        except (OSError,ValueError,AttributeError):
            return {}

    def new_game(self,seed=None):
        self.seed = seed if seed is not None else random.randrange(2**32)
        self.game=Game(self.difficulty.get(),self.seed)
        self.scan_mode=False
        self.selected=[]
        self.logged_result=False
        self.render()

    def retry(self):
        self.new_game(self.seed)

    def toggle_scan(self):
        if self.game.status!='playing': return
        self.scan_mode=not self.scan_mode
        self.selected=[]
        self.game.message='범위 안의 두 칸을 클릭하세요. 선택 완료 전에는 턴이 진행되지 않습니다.' if self.scan_mode else '탐색 취소. 방향키로 이동하세요.'
        self.render()

    def key(self,event):
        k=event.keysym.lower()
        if k=='r': self.new_game(); return 'break'
        if k=='s': self.toggle_scan(); return 'break'
        if k=='escape' and self.scan_mode: self.toggle_scan(); return 'break'
        directions={'up':(-1,0),'down':(1,0),'left':(0,-1),'right':(0,1),'w':(-1,0),'a':(0,-1),'d':(0,1)}
        if k in directions:
            if not self.scan_mode:
                self.game.move(*directions[k])
                self.render()
            return 'break'

    def cell_at(self,event):
        return ((event.y-PAD)//CELL,(event.x-PAD)//CELL)

    def click(self,event):
        if not self.scan_mode or self.game.status!='playing': return
        p=self.cell_at(event)
        if not self.game.scan_allowed(p):
            self.game.message='강조된 5×5 범위의 벽이 아닌 칸을 선택하세요.'
        elif p in self.selected:
            self.selected.remove(p)
        else:
            self.selected.append(p)
        if len(self.selected)==2:
            self.game.scan(self.selected)
            self.scan_mode=False
            self.selected=[]
        self.render()

    def flag(self,event):
        p=self.cell_at(event)
        if self.game.status!='playing' or not(0<=p[0]<SIZE and 0<=p[1]<SIZE) or p in self.game.walls: return
        if p in self.game.flags: self.game.flags.remove(p)
        else: self.game.flags.add(p)
        self.render()

    def render(self):
        g=self.game
        self.canvas.delete('all')
        for r in range(SIZE):
            for c in range(SIZE):
                p=(r,c); x=PAD+c*CELL; y=PAD+r*CELL
                color='#243246' if p in g.visited else '#182232'
                if p in g.walls: color='#526074'
                if self.scan_mode and g.scan_allowed(p): color='#253d55'
                if p in self.selected: color='#356b80'
                if g.status!='playing' and p in g.sources: color='#6d2b3d'
                self.canvas.create_rectangle(x+1,y+1,x+CELL-1,y+CELL-1,fill=color,outline='#304055')
                if p in g.hints:
                    self.canvas.create_text(x+11,y+11,text=str(g.hints[p]),fill=TEXT,font=(self.ui_font,10,'bold'))
                if p in g.scans:
                    self.canvas.create_text(x+CELL-12,y+CELL-10,text='s'+str(g.scans[p]),fill='#7fcfff',font=(self.ui_font,9,'bold'))
                if p in g.flags:
                    self.canvas.create_text(x+CELL//2,y+CELL//2,text='!',fill='#f3c76d',font=(self.ui_font,16,'bold'))
                if g.status!='playing' and p in g.sources:
                    self.canvas.create_text(x+CELL//2,y+CELL//2,text='×',fill='#ffa1b0',font=(self.ui_font,18,'bold'))
                for pos,label,fill in [(g.exit,'E','#71e4b7'),(g.enemy,'Z','#ff7287'),(g.player,'P','#f8d578')]:
                    if p==pos:
                        self.canvas.create_oval(x+9,y+8,x+CELL-8,y+CELL-9,fill=fill,outline='')
                        self.canvas.create_text(x+CELL/2,y+CELL/2-1,text=label,fill=BG,font=(self.ui_font,11,'bold'))
        if g.status!='playing' and not self.logged_result:
            self.logged_result=True
            if g.status=='won':
                old=self.records.get(g.difficulty)
                if old is None or g.turn<old:
                    self.records[g.difficulty]=g.turn
                    try:
                        self.records_path.parent.mkdir(parents=True,exist_ok=True)
                        self.records_path.write_text(json.dumps(self.records),encoding='utf-8')
                    except OSError:
                        g.message='기록을 파일에 저장하지 못했습니다. 이번 실행 중에는 유지됩니다.'
        status={'playing':'진행 중','won':'탈출 성공','lost':'탈출 실패'}[g.status]
        self.stats.config(text=f'상태  {status}\n턴 수  {g.turn}\n감염원  {len(g.sources)}개\n다음 감염체 행동  {g.next_enemy_mode if g.status=="playing" else "종료"}\n맵 번호  {self.seed}')
        self.scan_button.config(text=f'탐색 취소  [S] · {len(self.selected)}/2' if self.scan_mode else '탐색 시작  [S]')
        record=self.records.get(g.difficulty)
        self.record_label.config(text='현재 난이도 최고 기록\n'+(f'{record}턴 탈출' if record is not None else '아직 탈출 기록이 없습니다.'))
        self.message.config(text=(g.reason+'  R: 새 게임 / 같은 맵 다시 도전' if g.status!='playing' else g.message))

    def help(self):
        messagebox.showinfo('게임 방법',
            '목표: 감염원과 감염체를 피해 E 출구로 이동합니다.\n\n'
            '방향키: 상하좌우 한 칸 이동. 벽과 맵 밖 이동은 턴을 소비하지 않습니다.\n'
            'S: 탐색 모드. 현재 위치 중심 5×5 범위의 서로 다른 두 칸을 클릭합니다.\n'
            '탐색 두 칸을 확정하면 플레이어는 제자리에 있고 감염체가 한 번 이동합니다.\n\n'
            '흰 숫자: 해당 칸 주변 8칸의 감염원 개수입니다.\n'
            '파란 s숫자: 해당 칸을 포함한 3×3 영역의 감염원 개수입니다.\n'
            's0은 선택 칸과 주변 8칸에 감염원이 없다는 뜻입니다.\n'
            's숫자가 1 이상이면 선택 칸 자체도 위험할 수 있습니다.\n'
            '우클릭 ! 표시는 메모일 뿐, 이동을 막거나 안전을 보장하지 않습니다.\n\n'
            '감염체는 한 턴씩 BFS 추격 → 랜덤 이동을 반복하며 벽을 피합니다.\n'
            '감염체는 감염원에 영향을 받지 않습니다. 출구 도착은 즉시 승리입니다.\n'
            '처음 3×3 구역은 안전하며, 탈출 가능한 경로가 있는 맵만 생성합니다.\n'
            '경로 존재가 숫자만으로 풀 수 있는 맵임을 보장하지는 않습니다.\n\n'
            'R: 새 맵 / 같은 맵 다시 도전: 동일 배치 / 최고 기록: 적은 탈출 턴 수')

