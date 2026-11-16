"""공통 실행 진입점. Tk 화면이 없으면 로컬 브라우저 화면을 사용합니다."""
import sys


def main():
    if '--web' not in sys.argv:
        try:
            import tkinter as tk
            from ui import App
        except ImportError as exc:
            print(f'Tk 화면을 불러올 수 없습니다: {exc}')
        else:
            try:
                root = tk.Tk()
            except tk.TclError as exc:
                print(f'Tk 화면을 열 수 없습니다: {exc}')
            else:
                App(root)
                root.mainloop()
                return

    from web_ui import serve
    try:
        serve(open_browser='--no-browser' not in sys.argv)
    except OSError as exc:
        print(f'로컬 브라우저 화면도 열 수 없습니다: {exc}')
        print('진행보고서의 콘솔 화면으로 전환합니다.')
        from terminal_ui import serve as serve_terminal
        serve_terminal()


if __name__ == '__main__':
    main()
