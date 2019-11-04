import argparse
import numpy as np

import pygame as pg

from cpu import CPU
from screen import Screen

KEY_MAP = {
    pg.K_0: 0x0,
    pg.K_1: 0x1,
    pg.K_2: 0x2,
    pg.K_3: 0x3,
    pg.K_4: 0x4,
    pg.K_5: 0x5,
    pg.K_6: 0x6,
    pg.K_7: 0x7,
    pg.K_8: 0x8,
    pg.K_9: 0x9,
    pg.K_q: 0xA,
    pg.K_w: 0xB,
    pg.K_e: 0xC,
    pg.K_r: 0xD,
    pg.K_t: 0xE,
    pg.K_y: 0xF,
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rom-path", help="Path to ROM file to run")
    parser.add_argument("--debug", default=False, action='store_true', help="Run in debug mode")
    parser.add_argument("--stepper", default=False, action='store_true', help="Run with stepper")
    args = parser.parse_args()

    screen = Screen(debug=args.debug)
    cpu = CPU(screen)
    cpu.load_rom(args.rom_path, 0x200)

    while True:
        # Pretty hacky way to step through each instruction
        if args.stepper:
            input()

        cpu.execute()

        for event in pg.event.get():
            if event.type == pg.KEYDOWN:
                if event.key in KEY_MAP:
                    cpu.keys[KEY_MAP[event.key]] = 1
            elif event.type == pg.KEYUP:
                if event.key in KEY_MAP:
                    cpu.keys[KEY_MAP[event.key]] = 0

if __name__ == "__main__":
    main()
