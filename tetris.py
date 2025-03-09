import pygame
import random
import time
import math

# 색상 정의
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (51, 51, 51)  # #333333에 해당하는 RGB 값
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)

# 테트리미노 모양 정의
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[1, 1, 1], [0, 1, 0]],  # T
    [[1, 1, 1], [1, 0, 0]],  # L
    [[1, 1, 1], [0, 0, 1]],  # J
    [[1, 1, 0], [0, 1, 1]],  # Z
    [[0, 1, 1], [1, 1, 0]]   # S
]

# 테트리미노 색상 정의
SHAPE_COLORS = [CYAN, YELLOW, MAGENTA, ORANGE, BLUE, RED, GREEN]

# 게임 설정
CELL_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
SCREEN_WIDTH = GRID_WIDTH * CELL_SIZE + 200  # 추가 공간
SCREEN_HEIGHT = GRID_HEIGHT * CELL_SIZE
FPS = 60

# 그리드 위치 설정
GRID_X = 0
GRID_Y = 0

# 파티클 클래스 정의
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.uniform(2, 5)
        self.velocity_x = random.uniform(-2, 2)
        self.velocity_y = random.uniform(-5, -1)
        self.gravity = 0.1
        self.life = 1.0  # 수명 (1.0 = 100%)
        self.decay = random.uniform(0.01, 0.03)  # 수명 감소율
    
    def update(self):
        self.x += self.velocity_x
        self.y += self.velocity_y
        self.velocity_y += self.gravity
        self.life -= self.decay
        return self.life > 0
    
    def draw(self, screen):
        alpha = int(self.life * 255)
        color_with_alpha = (*self.color, alpha)
        
        # 파티클 그리기
        s = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(s, color_with_alpha, (int(self.size), int(self.size)), int(self.size))
        screen.blit(s, (int(self.x - self.size), int(self.y - self.size)))

class Tetris:
    def __init__(self):
        # 게임 초기화
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("테트리스")
        self.clock = pygame.time.Clock()
        
        # Mac에서 한글 지원 폰트 설정
        try:
            # MacOS 기본 한글 지원 폰트들
            mac_fonts = ['AppleGothic', 'Apple SD Gothic Neo', 'Nanum Gothic', 'NanumGothic']
            font_found = False
            
            for font_name in mac_fonts:
                try:
                    self.font = pygame.font.SysFont(font_name, 36)
                    # 테스트 렌더링으로 폰트 지원 확인
                    test = self.font.render('테스트', True, WHITE)
                    font_found = True
                    break
                except:
                    continue
            
            if not font_found:
                # 폴백: 기본 폰트 사용
                self.font = pygame.font.SysFont(None, 36)
        except:
            self.font = pygame.font.SysFont(None, 36)
        
        # 더블 버퍼링을 위한 서피스 생성
        self.buffer = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # 게임 변수 초기화
        self.reset_game()
        
        # 게임 시작 화면 표시 여부
        self.show_start_screen = True

    def reset_game(self):
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = self.new_piece()
        self.next_piece = self.new_piece()
        self.game_over = False
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.fall_speed = 0.5  # 초당 한 칸씩 떨어짐
        self.last_fall_time = time.time()
        
        # 줄 제거 효과를 위한 변수 추가
        self.lines_to_clear = []
        self.clear_effect_time = 0
        self.clear_effect_duration = 1.0  # 효과 지속 시간 (초)
        self.clear_effect_flashes = 6  # 깜빡임 횟수
        
        # 파티클 효과
        self.particles = []
        
        # 효과를 위한 변수
        self.glow_intensity = 0.0
        
        # 하드 드롭 애니메이션을 위한 변수
        self.hard_drop_active = False
        self.hard_drop_start_time = 0
        self.hard_drop_duration = 0.15  # 하드 드롭 애니메이션 지속 시간 (초)
        self.hard_drop_start_y = 0
        self.hard_drop_end_y = 0
        self.hard_drop_piece = None

    def new_piece(self):
        # 새로운 테트리미노 생성
        shape_idx = random.randint(0, len(SHAPES) - 1)
        return {
            'shape': SHAPES[shape_idx],
            'color': SHAPE_COLORS[shape_idx],
            'x': GRID_WIDTH // 2 - len(SHAPES[shape_idx][0]) // 2,
            'y': 0
        }

    def valid_position(self, piece, x_offset=0, y_offset=0):
        # 테트리미노가 유효한 위치에 있는지 확인
        for y, row in enumerate(piece['shape']):
            for x, cell in enumerate(row):
                if cell:
                    pos_x = piece['x'] + x + x_offset
                    pos_y = piece['y'] + y + y_offset
                    
                    if (pos_x < 0 or pos_x >= GRID_WIDTH or 
                        pos_y >= GRID_HEIGHT or 
                        (pos_y >= 0 and self.grid[pos_y][pos_x])):
                        return False
        return True

    def rotate_piece(self, piece):
        # 테트리미노 회전
        shape = piece['shape']
        rotated = list(zip(*reversed(shape)))
        return rotated

    def try_rotate(self):
        # 테트리미노 회전 시도
        rotated_shape = self.rotate_piece(self.current_piece)
        old_shape = self.current_piece['shape']
        self.current_piece['shape'] = rotated_shape
        
        if not self.valid_position(self.current_piece):
            self.current_piece['shape'] = old_shape

    def lock_piece(self):
        # 테트리미노를 그리드에 고정
        for y, row in enumerate(self.current_piece['shape']):
            for x, cell in enumerate(row):
                if cell:
                    pos_x = self.current_piece['x'] + x
                    pos_y = self.current_piece['y'] + y
                    if 0 <= pos_y < GRID_HEIGHT and 0 <= pos_x < GRID_WIDTH:
                        self.grid[pos_y][pos_x] = self.current_piece['color']
        
        # 완성된 줄 확인
        self.lines_to_clear = []
        for y in range(GRID_HEIGHT - 1, -1, -1):
            if all(self.grid[y]):
                self.lines_to_clear.append(y)
        
        # 완성된 줄이 있으면 효과 시작
        if self.lines_to_clear:
            self.clear_effect_time = time.time()
            
            # 파티클 효과 생성
            for y in self.lines_to_clear:
                for x in range(GRID_WIDTH):
                    color = self.grid[y][x]
                    center_x = x * CELL_SIZE + CELL_SIZE // 2
                    center_y = y * CELL_SIZE + CELL_SIZE // 2
                    
                    # 각 블록마다 여러 파티클 생성
                    for _ in range(10):
                        self.particles.append(Particle(center_x, center_y, color))
            
            # 다음 테트리미노는 효과가 끝난 후에 설정됨
        else:
            # 완성된 줄이 없으면 바로 다음 테트리미노 설정
            self.current_piece = self.next_piece
            self.next_piece = self.new_piece()
            
            # 게임 오버 확인
            if not self.valid_position(self.current_piece):
                self.game_over = True

    def draw_grid(self):
        # 그리드 그리기 (격자만 그림)
        for x in range(GRID_WIDTH + 1):
            pygame.draw.line(
                self.buffer,
                DARK_GRAY,
                (GRID_X + x * CELL_SIZE, GRID_Y),
                (GRID_X + x * CELL_SIZE, GRID_Y + GRID_HEIGHT * CELL_SIZE),
                1
            )
        for y in range(GRID_HEIGHT + 1):
            pygame.draw.line(
                self.buffer,
                DARK_GRAY,
                (GRID_X, GRID_Y + y * CELL_SIZE),
                (GRID_X + GRID_WIDTH * CELL_SIZE, GRID_Y + y * CELL_SIZE),
                1
            )

    def draw_blocks(self):
        # 고정된 블록 그리기
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.grid[y][x] != 0:
                    color = self.grid[y][x]  # 그리드에 저장된 색상 사용
                    
                    # 줄 제거 효과 (깜빡임)
                    if self.lines_to_clear and y in self.lines_to_clear:
                        effect_progress = (time.time() - self.clear_effect_time) / self.clear_effect_duration
                        flash_count = 5  # 깜빡임 횟수
                        flash_state = int(effect_progress * flash_count * 2) % 2
                        
                        if flash_state == 0:
                            # 블록 확대 효과
                            expand = int(CELL_SIZE * 0.2 * math.sin(effect_progress * math.pi))
                            rect = pygame.Rect(
                                GRID_X + x * CELL_SIZE - expand // 2,
                                GRID_Y + y * CELL_SIZE - expand // 2,
                                CELL_SIZE + expand,
                                CELL_SIZE + expand
                            )
                            pygame.draw.rect(self.buffer, color, rect)
                            
                            # 블록 테두리
                            pygame.draw.rect(self.buffer, WHITE, rect, 1)
                            
                            # 파티클 생성 (일정 간격으로)
                            if random.random() < 0.1:
                                particle_x = GRID_X + x * CELL_SIZE + CELL_SIZE // 2
                                particle_y = GRID_Y + y * CELL_SIZE + CELL_SIZE // 2
                                self.particles.append(Particle(particle_x, particle_y, color))
                        else:
                            # 깜빡임 효과 - 흰색으로 변경
                            rect = pygame.Rect(
                                GRID_X + x * CELL_SIZE,
                                GRID_Y + y * CELL_SIZE,
                                CELL_SIZE,
                                CELL_SIZE
                            )
                            pygame.draw.rect(self.buffer, WHITE, rect)
                    else:
                        # 일반 블록
                        rect = pygame.Rect(
                            GRID_X + x * CELL_SIZE,
                            GRID_Y + y * CELL_SIZE,
                            CELL_SIZE,
                            CELL_SIZE
                        )
                        pygame.draw.rect(self.buffer, color, rect)
                        pygame.draw.rect(self.buffer, WHITE, rect, 1)

    def draw_piece(self, piece, offset_x=0, offset_y=0):
        # 테트리미노 그리기
        shape = piece['shape']
        color = piece['color']  # 이미 색상 튜플이므로 인덱싱 제거
        
        for y in range(len(shape)):
            for x in range(len(shape[y])):
                if shape[y][x]:
                    rect = pygame.Rect(
                        GRID_X + (piece['x'] + x) * CELL_SIZE + offset_x,  # 위치 계산 수정
                        GRID_Y + (piece['y'] + y) * CELL_SIZE + offset_y,  # 위치 계산 수정
                        CELL_SIZE,
                        CELL_SIZE
                    )
                    pygame.draw.rect(self.buffer, color, rect)
                    pygame.draw.rect(self.buffer, WHITE, rect, 1)

    def draw_next_piece(self):
        # 다음 테트리미노 표시
        next_piece = self.next_piece
        shape = next_piece['shape']
        color = next_piece['color']  # 이미 색상 튜플이므로 인덱싱 제거
        
        # 다음 조각 영역 배경
        next_area = pygame.Rect(
            GRID_X + GRID_WIDTH * CELL_SIZE + 20,
            GRID_Y,
            6 * CELL_SIZE,
            6 * CELL_SIZE
        )
        pygame.draw.rect(self.buffer, BLACK, next_area)
        pygame.draw.rect(self.buffer, WHITE, next_area, 1)
        
        # 다음 조각 텍스트
        next_text = self.font.render("다음", True, WHITE)
        self.buffer.blit(
            next_text,
            (GRID_X + GRID_WIDTH * CELL_SIZE + 20 + (6 * CELL_SIZE - next_text.get_width()) // 2,
             GRID_Y - 40)
        )
        
        # 다음 조각 그리기
        for y in range(len(shape)):
            for x in range(len(shape[y])):
                if shape[y][x]:
                    # 중앙에 배치하기 위한 오프셋 계산
                    offset_x = (6 - len(shape[0])) // 2
                    offset_y = (6 - len(shape)) // 2
                    
                    rect = pygame.Rect(
                        GRID_X + GRID_WIDTH * CELL_SIZE + 20 + (offset_x + x) * CELL_SIZE,
                        GRID_Y + (offset_y + y) * CELL_SIZE,
                        CELL_SIZE,
                        CELL_SIZE
                    )
                    pygame.draw.rect(self.buffer, color, rect)
                    pygame.draw.rect(self.buffer, WHITE, rect, 1)

    def draw_info(self):
        # 게임 정보 표시
        info_x = GRID_X + GRID_WIDTH * CELL_SIZE + 20
        info_y = GRID_Y + 6 * CELL_SIZE + 20
        
        # 점수
        score_text = self.font.render(f"점수: {self.score}", True, WHITE)
        self.buffer.blit(score_text, (info_x, info_y))
        
        # 레벨
        level_text = self.font.render(f"레벨: {self.level}", True, WHITE)
        self.buffer.blit(level_text, (info_x, info_y + 40))
        
        # 지운 줄 수
        lines_text = self.font.render(f"줄: {self.lines_cleared}", True, WHITE)
        self.buffer.blit(lines_text, (info_x, info_y + 80))

    def draw_game_over(self):
        # 게임 오버 메시지
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.buffer.blit(overlay, (0, 0))
        
        game_over_font = pygame.font.SysFont(None, 72)
        game_over_text = game_over_font.render("GAME OVER", True, WHITE)
        restart_text = self.font.render("R 키를 눌러 재시작", True, WHITE)
        
        self.buffer.blit(
            game_over_text,
            (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2,
             SCREEN_HEIGHT // 2 - game_over_text.get_height() // 2 - 30)
        )
        
        self.buffer.blit(
            restart_text,
            (SCREEN_WIDTH // 2 - restart_text.get_width() // 2,
             SCREEN_HEIGHT // 2 + game_over_text.get_height() // 2)
        )

    def update_particles(self):
        # 파티클 업데이트
        new_particles = []
        for particle in self.particles:
            if particle.update():
                new_particles.append(particle)
        self.particles = new_particles

    def draw_particles(self):
        # 파티클 그리기
        for particle in self.particles:
            particle.draw(self.buffer)

    def draw_hard_drop_animation(self):
        # 하드 드롭 애니메이션 그리기
        if not self.hard_drop_active:
            return
            
        # 애니메이션 진행 상태 계산 (0.0 ~ 1.0)
        progress = min(1.0, (time.time() - self.hard_drop_start_time) / self.hard_drop_duration)
        
        # 현재 Y 위치 계산 (시작 위치에서 끝 위치로 선형 보간)
        current_y = self.hard_drop_start_y + (self.hard_drop_end_y - self.hard_drop_start_y) * progress
        
        # 애니메이션 중인 조각 그리기
        piece_copy = self.hard_drop_piece.copy()
        piece_copy['y'] = current_y
        
        # 그림자 효과 (반투명)
        shape = piece_copy['shape']
        color = piece_copy['color']  # 이미 색상 튜플이므로 인덱싱 제거
        
        for y in range(len(shape)):
            for x in range(len(shape[y])):
                if shape[y][x]:
                    rect = pygame.Rect(
                        GRID_X + (piece_copy['x'] + x) * CELL_SIZE,  # 위치 계산 수정
                        GRID_Y + (piece_copy['y'] + y) * CELL_SIZE,  # 위치 계산 수정
                        CELL_SIZE,
                        CELL_SIZE
                    )
                    # 속도감을 위한 잔상 효과
                    alpha = int(255 * (1 - progress * 0.5))
                    shadow_color = (*color, alpha)
                    
                    # 반투명 사각형 그리기
                    shadow_surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                    pygame.draw.rect(shadow_surface, shadow_color, (0, 0, CELL_SIZE, CELL_SIZE))
                    pygame.draw.rect(shadow_surface, (255, 255, 255, alpha), (0, 0, CELL_SIZE, CELL_SIZE), 1)
                    self.buffer.blit(shadow_surface, rect)

    def draw_start_screen(self):
        # 시작 화면 그리기
        self.buffer.fill(BLACK)
        title_font = pygame.font.SysFont(None, 48)  # 포인트 크기 줄임
        title_text = title_font.render("BCAI 테트리스", True, WHITE)  # 타이틀 변경
        start_text = self.font.render("시작하려면 스페이스바를 누르세요", True, WHITE)
        
        self.buffer.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, SCREEN_HEIGHT // 2 - 100))
        self.buffer.blit(start_text, (SCREEN_WIDTH // 2 - start_text.get_width() // 2, SCREEN_HEIGHT // 2))

    def run(self):
        # 게임 메인 루프
        running = True
        while running:
            self.clock.tick(60)  # FPS 설정
            
            # 버퍼 초기화
            self.buffer.fill(BLACK)
            
            if self.show_start_screen:
                # 시작 화면 표시
                self.draw_start_screen()
                
                # 이벤트 처리
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                        self.show_start_screen = False
            else:
                # 이벤트 처리
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    
                    if not self.game_over and not self.lines_to_clear and not self.hard_drop_active:  # 효과 중에는 입력 무시
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_LEFT:
                                if self.valid_position(self.current_piece, x_offset=-1):
                                    self.current_piece['x'] -= 1
                            elif event.key == pygame.K_RIGHT:
                                if self.valid_position(self.current_piece, x_offset=1):
                                    self.current_piece['x'] += 1
                            elif event.key == pygame.K_DOWN:
                                if self.valid_position(self.current_piece, y_offset=1):
                                    self.current_piece['y'] += 1
                            elif event.key == pygame.K_UP:
                                self.try_rotate()
                            elif event.key == pygame.K_SPACE:
                                # 하드 드롭 애니메이션 시작
                                self.hard_drop_start_y = float(self.current_piece['y'])
                                
                                # 최종 위치 계산
                                end_y = self.current_piece['y']
                                while self.valid_position(self.current_piece, y_offset=1):
                                    self.current_piece['y'] += 1
                                    end_y = self.current_piece['y']
                                
                                # 원래 위치로 복원
                                self.current_piece['y'] = int(self.hard_drop_start_y)
                                
                                # 하드 드롭 애니메이션 설정
                                self.hard_drop_end_y = float(end_y)
                                self.hard_drop_piece = self.current_piece.copy()
                                self.hard_drop_piece['shape'] = [row[:] for row in self.current_piece['shape']]
                                self.hard_drop_active = True
                                self.hard_drop_start_time = time.time()
                    else:
                        if event.type == pygame.KEYDOWN and event.key == pygame.K_r and self.game_over:
                            self.reset_game()
            
                # 하드 드롭 애니메이션 처리
                if not self.show_start_screen and self.hard_drop_active and time.time() - self.hard_drop_start_time > self.hard_drop_duration:
                    self.hard_drop_active = False
                    # 최종 위치로 이동
                    self.current_piece['y'] = int(self.hard_drop_end_y)
                    self.lock_piece()
                
                # 줄 제거 효과 처리
                if not self.show_start_screen and self.lines_to_clear and time.time() - self.clear_effect_time > self.clear_effect_duration:
                    # 효과 시간이 끝나면 줄 제거 및 점수 계산
                    lines_cleared = len(self.lines_to_clear)
                    
                    # 줄 제거
                    for y in sorted(self.lines_to_clear):
                        for y2 in range(y, 0, -1):
                            self.grid[y2] = self.grid[y2 - 1][:]
                        self.grid[0] = [0] * GRID_WIDTH
                    
                    # 점수 계산
                    self.score += [0, 100, 300, 500, 800][min(lines_cleared, 4)] * self.level
                    self.lines_cleared += lines_cleared
                    self.level = self.lines_cleared // 10 + 1
                    self.fall_speed = max(0.05, 0.5 - (self.level - 1) * 0.05)
                    
                    # 다음 테트리미노 설정
                    self.current_piece = self.next_piece
                    self.next_piece = self.new_piece()
                    
                    # 게임 오버 확인
                    if not self.valid_position(self.current_piece):
                        self.game_over = True
                    
                    # 효과 종료
                    self.lines_to_clear = []
                
                # 자동 낙하 (효과 중에는 낙하 중지)
                if not self.show_start_screen and not self.game_over and not self.lines_to_clear and not self.hard_drop_active and time.time() - self.last_fall_time > self.fall_speed:
                    if self.valid_position(self.current_piece, y_offset=1):
                        self.current_piece['y'] += 1
                    else:
                        self.lock_piece()
                    self.last_fall_time = time.time()
                
                # 파티클 업데이트
                self.update_particles()
                
                # 그리기
                self.draw_grid()
                self.draw_blocks()
                
                # 하드 드롭 애니메이션 또는 현재 조각 그리기
                if self.hard_drop_active:
                    self.draw_hard_drop_animation()
                elif not self.game_over and not self.lines_to_clear:
                    self.draw_piece(self.current_piece)
                
                # 다음 조각 및 게임 정보 그리기
                self.draw_next_piece()
                self.draw_info()
                self.draw_particles()
                
                # 게임 오버 화면
                if self.game_over:
                    self.draw_game_over()
            
            # 버퍼를 화면에 그리기 (한 번에 업데이트)
            self.screen.blit(self.buffer, (0, 0))
            pygame.display.flip()
        
        pygame.quit()

if __name__ == "__main__":
    game = Tetris()
    game.run() 