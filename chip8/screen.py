import numpy as np
import pygame
from pygame import display, draw, Color, font, Surface

PIXEL_COLORS = {
    0: Color(0, 0, 0, 255),
    1: Color(250, 250, 250, 255)
}

class Screen():
    def __init__(self, debug=False) -> None:
        self.debug = debug
        self.main_surface = None
        self.game_surface = None

        if self.debug:
            self.height = 640
            self.width = 1000

            self.console_surface = None
            self.registers_surface = None

            self.register_text = None
            self.stack_text = None
        else:
            self.height = 320
            self.width = 640

        self.init_display()

    def init_display(self) -> None:
        pygame.init()
        display.init()
        self.init_main_surface()
        self.init_game_surface()
        # debug is pretty sketch tbh but it's helpful
        if self.debug:
            self.init_console_surface()
            self.init_registers_surface()

    def init_main_surface(self) -> None:
        self.main_surface = display.set_mode((self.width, self.height))
        self.main_surface.fill(PIXEL_COLORS[0])
        display.update()

    def init_game_surface(self) -> None:
        self.game_surface = Surface((640,320))
        self.game_surface.fill((0,0,0))
        self.main_surface.blit(self.game_surface, (0,0))
        display.update()

    def init_console_surface(self) -> None:
        self.console_surface = Surface((630,310))
        self.console_surface.fill((189,189,189))
        self.main_surface.blit(self.console_surface, (10,320))
        display.update()

    def init_registers_surface(self) -> None:
        self.registers_surface = Surface((340,620))
        self.registers_surface.fill((189,189,189))
        self.main_surface.blit(self.registers_surface, (650,10))

        display.update()

    def draw_console(self, current_opcode: np.uint16) -> None:
        font = pygame.font.Font('freesansbold.ttf', 24)
        self.console_text = font.render(hex(current_opcode), True, (0,255,0), (0,0,128) )
        self.main_surface.blit(self.console_text,(20,360))

    def draw_debug(self, pc: np.uint16, sp: np.uint16, ir: np.uint16, dt: np.uint8, st: np.uint8, v: np.ndarray, stack: np.ndarray) -> None:
        font = pygame.font.Font('freesansbold.ttf', 24)

        self.pc_text = font.render(hex(pc), True, (0,255,0), (0,0,128) )
        self.main_surface.blit(self.pc_text,(660,20))
        self.sp_text = font.render(hex(sp), True, (0,255,0), (0,0,128) )
        self.main_surface.blit(self.sp_text,(660, 20 + 24))
        self.ir_text = font.render(hex(ir), True, (0,255,0), (0,0,128) )
        self.main_surface.blit(self.ir_text,(660, 20 + 24*2))
        self.dt_text = font.render(hex(dt), True, (0,255,0), (0,0,128) )
        self.main_surface.blit(self.dt_text,(660, 20 + 24*3))
        self.st_text = font.render(hex(st), True, (0,255,0), (0,0,128) )
        self.main_surface.blit(self.st_text,(660, 20 + 24*4))

        if not self.register_text:
            self.register_text = [0] * len(v)
        if not self.stack_text:
            self.stack_text = [0] * len(stack)

        for i, r in enumerate(v):
            self.register_text[i] = font.render(hex(r), True, (0,255,0), (0,0,128) )
            self.main_surface.blit(self.register_text[i],(660,20 + i * 24 + (24*6)))

        for i, s in enumerate(stack):
            self.stack_text[i] = font.render(hex(s), True, (0,255,0), (0,0,128) )
            self.main_surface.blit(self.stack_text[i],(660 + 100, 20 + i * 24 + (24*6)))

    def draw_pixel(self, x_pos, y_pos, pixel_color) -> None:
            x_base = x_pos * 10
            y_base = y_pos * 10
            draw.rect(self.main_surface, PIXEL_COLORS[pixel_color], (x_base, y_base, 10, 10))

    def update(self) -> None:
        display.update()
