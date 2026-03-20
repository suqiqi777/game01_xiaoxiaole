import pygame
import random
import sys
import asyncio  # 网页版核心

# --- 1. 设置区 ---
WIDTH, HEIGHT = 600, 750
GRID_SIZE = 5
CELL_SIZE = 100
FPS = 30 
GAME_TIME = 60 

# 颜色
WHITE = (255, 255, 255)
GRAY = (220, 220, 220)
DARK_BROWN = (90, 50, 30)
DEEP_RED = (200, 50, 50)
BLACK = (0, 0, 0)

class Game:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
        except:
            pass
            
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("My Portrait Match-3 Web")
        self.clock = pygame.time.Clock()
        
        self.load_assets()
        self.reset_game()

    def load_assets(self):
        self.gem_images = []
        try:
            for i in range(1, 5):
                # 网页版路径直接用文件名
                img = pygame.image.load(f'gem{i}.png').convert_alpha()
                img = pygame.transform.scale(img, (CELL_SIZE - 20, CELL_SIZE - 20))
                self.gem_images.append(img)
            
            self.match_sound = None
            try:
                self.match_sound = pygame.mixer.Sound('match.wav')
            except:
                pass
        except Exception as e:
            print(f"Asset loading error: {e}")

        self.font = pygame.font.SysFont("arial", 40, bold=True)
        self.big_font = pygame.font.SysFont("arial", 70, bold=True)

    def reset_game(self):
        self.board = [[random.randint(0, 3) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.selected = None
        self.score = 0
        self.game_over = False
        self.counting_down = True
        self.ready_timer = 4
        self.last_ready_tick = pygame.time.get_ticks()
        self.game_start_time = None
        
        # 初始去重
        while self.find_matches():
            matches = self.find_matches()
            for r, c in matches: self.board[r][c] = -1
            self.drop_and_fill()

    def drop_and_fill(self):
        for c in range(GRID_SIZE):
            col = [self.board[r][c] for r in range(GRID_SIZE) if self.board[r][c] != -1]
            while len(col) < GRID_SIZE: col.insert(0, random.randint(0, 3))
            for r in range(GRID_SIZE): self.board[r][c] = col[r]

    def draw(self):
        self.screen.fill(WHITE)
        now = pygame.time.get_ticks()
        
        # 1. 计时逻辑
        seconds_left = GAME_TIME
        if self.counting_down:
            if now - self.last_ready_tick > 1000:
                self.ready_timer -= 1
                self.last_ready_tick = now
                if self.ready_timer <= 0:
                    self.counting_down = False
                    self.game_start_time = pygame.time.get_ticks()
            seconds_left = GAME_TIME
        elif not self.game_over:
            passed_time = (now - self.game_start_time) // 1000
            seconds_left = max(0, GAME_TIME - passed_time)
            if seconds_left == 0: self.game_over = True

        # 2. UI 绘制
        t_color = DEEP_RED if seconds_left < 10 else (50, 50, 50)
        time_txt = self.font.render(f"TIME: {seconds_left}s", True, t_color)
        score_txt = self.font.render(f"SCORE: {self.score}", True, (50, 50, 50))
        self.screen.blit(time_txt, (30, 25))
        self.screen.blit(score_txt, score_txt.get_rect(topright=(WIDTH - 30, 25)))

        # 3. 棋盘绘制
        off_x, off_y = (WIDTH - 500) // 2, 120
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                rect = pygame.Rect(c*CELL_SIZE + off_x, r*CELL_SIZE + off_y, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(self.screen, GRAY, rect, 1)
                if self.board[r][c] != -1:
                    img_rect = self.gem_images[self.board[r][c]].get_rect(center=rect.center)
                    self.screen.blit(self.gem_images[self.board[r][c]], img_rect)
                if self.selected == (r, c):
                    pygame.draw.rect(self.screen, BLACK, rect, 6, border_radius=10)

        # 4. 状态层
        if self.counting_down:
            # ✨ 关键修复：加了 str() 确保数字能被渲染
            display_text = "START" if self.ready_timer == 4 else str(self.ready_timer)
            self.draw_overlay(display_text, DARK_BROWN)
        elif self.game_over:
            self.draw_overlay("TIME UP!", DEEP_RED, f"Final: {self.score}", "Click to Restart")

        pygame.display.flip()

    def draw_overlay(self, main_txt, color, sub_txt=None, hint_txt=None):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, 180))
        self.screen.blit(overlay, (0,0))
        
        # ✨ 关键修复：确保渲染内容是字符串
        m_txt = self.big_font.render(str(main_txt), True, color)
        self.screen.blit(m_txt, m_txt.get_rect(center=(WIDTH//2, HEIGHT//2 - 40)))
        
        if sub_txt:
            s_txt = self.font.render(str(sub_txt), True, BLACK)
            self.screen.blit(s_txt, s_txt.get_rect(center=(WIDTH//2, HEIGHT//2 + 50)))
        if hint_txt:
            h_txt = self.font.render(str(hint_txt), True, (100, 100, 100))
            self.screen.blit(h_txt, h_txt.get_rect(center=(WIDTH//2, HEIGHT//2 + 120)))

    def find_matches(self):
        to_del = set()
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE - 2):
                if self.board[r][c] == self.board[r][c+1] == self.board[r][c+2] and self.board[r][c] != -1:
                    to_del.update([(r, c), (r, c+1), (r, c+2)])
        for r in range(GRID_SIZE - 2):
            for c in range(GRID_SIZE):
                if self.board[r][c] == self.board[r+1][c] == self.board[r+2][c] and self.board[r][c] != -1:
                    to_del.update([(r, c), (r+1, c), (r+2, c)])
        return list(to_del)

    async def process_eliminations(self):
        while True:
            matches = self.find_matches()
            if not matches: break
            if self.match_sound: self.match_sound.play()
            self.score += len(matches) * 10
            for r, c in matches: self.board[r][c] = -1
            self.draw()
            await asyncio.sleep(0.2) # 网页版停顿
            self.drop_and_fill()
            self.draw()

    async def run(self):
        while True:
            self.draw()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.game_over:
                        self.reset_game()
                    elif not self.counting_down:
                        mx, my = pygame.mouse.get_pos()
                        off_x, off_y = (WIDTH - 500) // 2, 120
                        c, r = (mx - off_x) // CELL_SIZE, (my - off_y) // CELL_SIZE
                        if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
                            if self.selected is None: self.selected = (r, c)
                            else:
                                r1, c1 = self.selected
                                if abs(r1-r) + abs(c1-c) == 1:
                                    self.board[r1][c1], self.board[r][c] = self.board[r][c], self.board[r1][c1]
                                    if self.find_matches(): 
                                        await self.process_eliminations()
                                    else: self.board[r1][c1], self.board[r][c] = self.board[r][c], self.board[r1][c1]
                                self.selected = None
            
            self.clock.tick(FPS)
            await asyncio.sleep(0) # 👈 确保浏览器不挂起

if __name__ == "__main__":
    asyncio.run(Game().run())
