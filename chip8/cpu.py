import numpy as np
import random

from screen import Screen

class CPU():
    def  __init__(self, screen: Screen) -> None:
        """
        Initialize the CPU
        """
        self.screen = screen

        self.v = np.zeros(16, dtype=np.uint8)        # registers (V0-VF)
        self.memory = np.zeros(4096, dtype=np.uint8) # 4kb memory

        self.sp = np.uint16()                        # stack pouinter
        self.stack = np.zeros(16, dtype=np.uint16)   # stack

        self.ir = np.uint16()                        # index register
        self.pc = np.uint16(0x200)                   # program counter

        self.delay_timer = np.uint8()                # delay timer
        self.sound_timer = np.uint8()                # sound timer

        self.gb = np.zeros(64*32, dtype=np.uint8)    # graphics buffer
        self.draw_flag = False                       # indicates a draw has occured

        self.keys = np.zeros(16, dtype=np.uint8)     # stores which keys are pressed

        self.current_opcode = np.uint16()            # the current opcode to execute

    def load_rom(self, rom_path: str, offset: int) -> None:
        """
        Load the ROM into memory
        """
        rom_bytes = open(rom_path, 'rb').read()
        for idx, byte in enumerate(rom_bytes):
            self.memory[offset + idx] = byte

    def print(self) -> None:
        """
        Print the current state of the CPU
        """
        print("pc: {} sp: {} ir: {}".format(hex(self.pc), hex(self.sp), hex(self.ir)))
        print("stack")
        print([hex(s) for s in self.stack[:8]])
        print([hex(s) for s in self.stack[8:]])
        print("registers")
        print([hex(v) for v in self.v[:8]])
        print([hex(v) for v in self.v[8:]])

    def execute(self) -> None:
        self.current_opcode = self.memory[self.pc] << 8 | self.memory[self.pc + 1]  # 2 bytes

        # 00E_
        if self.current_opcode & 0xF000 == 0x0000:
            # 00E0 - Clear screen
            if self.current_opcode & 0x000F == 0x0000:
                self.clear_screen()
            # 00EE - Return from a subroutine
            elif self.current_opcode & 0x000F == 0x000E:
                self.return_from_subroutine()
            else:
                raise Exception("Invalid opcode {}".format(hex(self.current_opcode)))
        # 1NNN - Jump to location nnn
        elif self.current_opcode & 0xF000 == 0x1000:
            self.jump_to_location()
        # 2NNN - Call subroutine at nnn
        elif self.current_opcode & 0xF000 == 0x2000:
            self.call_subroutine()
        # 3NNN - Skip next instruction if Vx = kk
        elif self.current_opcode & 0xF000 == 0x3000:
            self.skip_next_instruction_if_vx_kk()
        # 4XKK - Skip next instruction if Vx != kk
        elif self.current_opcode & 0xF000 == 0x4000:
            self.skip_next_instruction_if_vx_not_kk()
        # 5XY0 - Skip next instruction if Vx = Vy
        elif self.current_opcode & 0xF000 == 0x5000:
            self.skip_next_instruction_if_vx_vy()
        # 6XKK - Set Vx = kk
        elif self.current_opcode & 0xF000 == 0x6000:
            self.set_vx_kk()
        # 7XKK - Set Vx = Vx + kk
        elif self.current_opcode & 0xF000 == 0x7000:
            self.add_vx_kk()
        # 8XY_
        elif self.current_opcode & 0xF000 == 0x8000:
            # 8XY0 - Set Vx = Vy
            if self.current_opcode & 0x000F == 0x0000:
                self.set_vx_vy()
            # 8XY1 - Set Vx = Vx OR Vy
            elif self.current_opcode & 0x000F == 0x0001:
                self.vx_or_vy()
            # 8XY2 - Set Vx = Vx AND Vy
            elif self.current_opcode & 0x000F == 0x0002:
                self.vx_and_vy()
            # 8XY3 - Set Vx = Vx XOR Vy
            elif self.current_opcode & 0x000F == 0x0003:
                self.vx_xor_vy()
            # 8XY4 - Set Vx = Vx + Vy, set VF = carry
            elif self.current_opcode & 0x000F == 0x0004:
                self.vx_add_vy()
            # 8XY5 - Set Vx = Vx - Vy, set VF = NOT borrow
            elif self.current_opcode & 0x000F == 0x0005:
                self.vx_sub_vy()
            # 8XY6 - Set Vx = Vx SHR 1
            elif self.current_opcode & 0x000F == 0x0006:
                self.shift_right_vx()
            # 8XY7 - Set Vx = Vy - Vx, set VF = NOT borrow
            elif self.current_opcode & 0x000F == 0x0007:
                self.vy_sub_vx()
            # 0x000E - Set Vx = Vx SHL 1
            elif self.current_opcode & 0x000F == 0x000E:
                self.shift_left_vx()
            else:
                raise Exception("Invalid opcode {}".format(hex(self.current_opcode)))
        # 9XY0 - Skip next instruction if Vx != Vy
        elif self.current_opcode & 0xF000 == 0x9000:
            self.skip_next_instruction_if_vx_not_vy()
        # ANNN - Set I = nnn
        elif self.current_opcode & 0xF000 == 0xA000:
            self.set_ir_to_nnn()
        # BNNN - Jump to location nnn + V0
        elif self.current_opcode & 0xF000 == 0xB000:
            self.jump_to_location_nnn_plus_v0()
        # CXKK - Set Vx = random byte AND kk
        elif self.current_opcode & 0xF000 == 0xC000:
            self.vx_random_byte_masked_by_kk()
        # DXYN - Display n-byte sprite starting at memory location I at (Vx, Vy), set VF = collision
        elif self.current_opcode & 0xF000 == 0xD000:
            self.display_sprite()
        # EX__
        elif self.current_opcode & 0xF000 == 0xE000:
            # EX9E - Skip next instruction if key with the value of Vx is pressed
            if self.current_opcode & 0x00FF == 0x009E:
                self.skip_next_instruction_if_vx_is_pressed()
            # EXA1 - Skip next instruction if key with the value of Vx is not pressed
            elif self.current_opcode & 0x00FF == 0x00A1:
                self.skip_next_instruction_if_vx_is_not_pressed()
            else:
                raise Exception("Invalid opcode {}".format(hex(self.current_opcode)))
        # FX__
        elif self.current_opcode & 0xF000 == 0xF000:
            # FX07 - Set Vx = delay timer value
            if self.current_opcode & 0x00FF == 0x0007:
                self.set_vx_to_delay_timer_value()
            # FX0A - Wait for a key press, store the value of the key in Vx
            elif self.current_opcode & 0x00FF == 0x000A:
                self.wait_for_key_press_store_in_vx()
            # FX15 - Set delay timer = Vx
            elif self.current_opcode & 0x00FF == 0x0015:
                self.set_delay_time_to_vx()
            # FX18 - Set sound timer = Vx
            elif self.current_opcode & 0x00FF == 0x0018:
                self.set_sound_timer_to_vx()
            # FX1E - Set I = I + Vx
            elif self.current_opcode & 0x00FF == 0x001E:
                self.add_ir_vx()
            # FX29 - Set I = location of sprite for digit Vx
            elif self.current_opcode & 0x00FF == 0x0029:
                self.set_ir_to_sprite_vx()
            # FX33 - Store BCD representation of Vx in memory locations I, I+1, and I+2
            elif self.current_opcode & 0x00FF == 0x0033:
                self.bcd_rep_vx()
            # FX55 - Store registers V0 through Vx in memory starting at location I
            elif self.current_opcode & 0x00FF == 0x0055:
                self.regs_to_memory()
            # FX65 - Read registers V0 through Vx from memory starting at location I
            elif self.current_opcode & 0x00FF == 0x0065:
                self.read_regs_from_memory()
            else:
                raise Exception("Invalid opcode {}".format(hex(self.current_opcode)))
        else:
            raise Exception("Invalid opcode {}".format(hex(self.current_opcode)))

        self.pc += 2 # Increment program counter

        if self.delay_timer > 0:
            self.delay_timer -= 1

        if self.sound_timer > 0:
            # if sound_timer == 1:
            #    TODO: Implement sound
            self.sound_timer -= 1

        if self.screen.debug:
            self.screen.draw_debug(
                self.pc,
                self.sp,
                self.ir,
                self.delay_timer,
                self.sound_timer,
                self.v,
                self.stack,
            )
            self.screen.draw_console(self.current_opcode)

    # Chip 8 Instructions
    # from http://devernay.free.fr/hacks/chip8/C8TECH10.HTM#00EE

    def clear_screen(self) -> None:
        """
        00E0 - CLS
        Clear the display.
        """
        self.gb = np.zeros(64*32, dtype=np.uint8)
        self.draw_flag = True

    def return_from_subroutine(self) -> None:
        """
        00EE - RET
        Return from a subroutine.

        The interpreter sets the program counter to the address at the top of the stack,
        then subtracts 1 from the stack pointer.
        """
        self.sp -= 1
        self.pc = self.stack[self.sp]

    def jump_to_location(self) -> None:
        """
        1NNN - JP addr
        Jump to location nnn.

        The interpreter sets the program counter to nnn.
        """
        self.pc = self.current_opcode & 0x0FFF
        self.pc -= 2 # to make up for us incrementing the pc counter later

    def call_subroutine(self) -> None:
        """
        2NNN - JP addr
        Call subroutine at nnn.


        The interpreter increments the stack pointer, then puts the current PC on the top of the stack.
        The PC is then set to nnn.
        """
        self.stack[self.sp] = self.pc
        self.sp += 1
        self.pc = self.current_opcode & 0x0FFF

    def skip_next_instruction_if_vx_kk(self) -> None:
        """
        3xkk - SE Vx, byte
        Skip next instruction if Vx = kk.

        The interpreter compares register Vx to kk, and if they are equal,
        increments the program counter by 2.
        """
        if self.v[(self.current_opcode & 0x0F00) >> 8] == (self.current_opcode & 0x00FF):
            self.pc += 2

    def skip_next_instruction_if_vx_not_kk(self) -> None:
        """
        4xkk - SNE Vx, byte
        Skip next instruction if Vx != kk.

        The interpreter compares register Vx to kk, and if they are not equal,
        increments the program counter by 2.
        """
        if self.v[(self.current_opcode & 0x0F00) >> 8] != (self.current_opcode & 0x00FF):
            self.pc += 2

    def skip_next_instruction_if_vx_vy(self) -> None:
        """
        5xy0 - SE Vx, Vy
        Skip next instruction if Vx = Vy.

        The interpreter compares register Vx to register Vy, and if they are equal,
        increments the program counter by 2.
        """
        if (self.v[(self.current_opcode & 0x0F00) >> 8] == self.v[(self.current_opcode & 0x00F0) >> 4]):
            self.pc += 2

    def set_vx_kk(self) -> None:
        """
        6xkk - LD Vx, byte
        Set Vx = kk.

        The interpreter puts the value kk into register Vx.
        """
        self.v[(self.current_opcode & 0x0F00) >> 8] = (self.current_opcode & 0x00FF)

    def add_vx_kk(self) -> None:
        """
        7xkk - ADD Vx, byte
        Set Vx = Vx + kk.

        Adds the value kk to the value of register Vx, then stores the result in Vx.
        """
        self.v[(self.current_opcode & 0x0F00) >> 8] += (self.current_opcode & 0x00FF)

    def set_vx_vy(self) -> None:
        """
        8xy0 - LD Vx, Vy
        Set Vx = Vy.

        Stores the value of register Vy in register Vx.
        """
        self.v[(self.current_opcode & 0x0F00) >> 8] = self.v[(self.current_opcode & 0x00F0) >> 4]

    def vx_or_vy(self) -> None:
        """
        8xy1 - OR Vx, Vy
        Set Vx = Vx OR Vy.

        Performs a bitwise OR on the values of Vx and Vy, then stores the result in Vx.
        A bitwise OR compares the corrseponding bits from two values, and if either bit is 1,
        then the same bit in the result is also 1. Otherwise, it is 0.
        """
        self.v[(self.current_opcode & 0x0F00) >> 8] = self.v[(self.current_opcode & 0x0F00) >> 8] or self.v[(self.current_opcode & 0x00F0) >> 4]

    def vx_and_vy(self) -> None:
        """
        8xy2 - AND Vx, Vy
        Set Vx = Vx AND Vy.

        Performs a bitwise AND on the values of Vx and Vy, then stores the result in Vx.
        A bitwise AND compares the corrseponding bits from two values, and if both bits are 1,
        then the same bit in the result is also 1. Otherwise, it is 0.
        """
        self.v[(self.current_opcode & 0x0F00) >> 8] = self.v[(self.current_opcode & 0x0F00) >> 8] and self.v[(self.current_opcode & 0x00F0) >> 4]

    def vx_xor_vy(self) -> None:
        """
        8xy3 - XOR Vx, Vy
        Set Vx = Vx XOR Vy.

        Performs a bitwise exclusive OR on the values of Vx and Vy, then stores the result in Vx.
        An exclusive OR compares the corrseponding bits from two values, and if the bits are not both the same,
        then the corresponding bit in the result is set to 1. Otherwise, it is 0.
        """
        self.v[(self.current_opcode & 0x0F00) >> 8] = self.v[(self.current_opcode & 0x0F00) >> 8] ^ self.v[(self.current_opcode & 0x00F0) >> 4]

    def vx_add_vy(self) -> None:
        """
        8xy4 - ADD Vx, Vy
        Set Vx = Vx + Vy, set VF = carry.

        The values of Vx and Vy are added together.
        If the result is greater than 8 bits (i.e., > 255,) VF is set to 1,
        otherwise 0. Only the lowest 8 bits of the result are kept, and stored in Vx.
        """
        res = self.v[(self.current_opcode & 0x0F00) >> 8] + self.v[(self.current_opcode & 0x00F0) >> 4]
        if res > 0xFF:
            self.v[0xF] = 1
        else:
            self.v[0xF] = 0
        self.v[(self.current_opcode & 0x0F00) >> 8] = res
        
    def vx_sub_vy(self) -> None:
        """
        8xy5 - SUB Vx, Vy
        Set Vx = Vx - Vy, set VF = NOT borrow.

        If Vx > Vy, then VF is set to 1, otherwise 0.
        Then Vy is subtracted from Vx, and the results stored in Vx.
        """
        if self.v[(self.current_opcode & 0x0F00) >> 8] > self.v[(self.current_opcode & 0x00F0) >> 4]:
            self.v[0xF] = 1
        else:
            self.v[0xF] = 0
        self.v[(self.current_opcode & 0x0F00) >> 8] -= self.v[(self.current_opcode & 0x00F0) >> 4]

    def shift_right_vx(self) -> None:
        """
        8xy6 - SHR Vx {, Vy}
        Set Vx = Vx SHR 1.

        If the least-significant bit of Vx is 1, then VF is set to 1, otherwise 0.
        Then Vx is divided by 2.
        """
        if self.v[(self.current_opcode & 0x0F00) >> 8] & 0x1 == 1:
            self.v[0xF] = 1
        else:
            self.v[0xF] = 0
        self.v[(self.current_opcode & 0x0F00) >> 8] >>= 1

    def vy_sub_vx(self) -> None:
        """
        8xy7 - SUBN Vx, Vy
        Set Vx = Vy - Vx, set VF = NOT borrow.

        If Vy > Vx, then VF is set to 1, otherwise 0.
        Then Vx is subtracted from Vy, and the results stored in Vx.
        """
        if self.v[(self.current_opcode & 0x00F0) >> 4] > self.v[(self.current_opcode & 0x0F00) >> 8]:
            self.v[0xF] = 1
        else:
            self.v[0xF] = 0
        self.v[(self.current_opcode & 0x0F00) >> 8] = self.v[(self.current_opcode & 0x00F0) >> 4] - self.v[(self.current_opcode & 0x0F00) >> 8]

    def shift_left_vx(self) -> None:
        """
        8xyE - SHL Vx {, Vy}
        Set Vx = Vx SHL 1.

        If the most-significant bit of Vx is 1, then VF is set to 1, otherwise to 0.
        Then Vx is multiplied by 2.
        """
        if self.v[(self.current_opcode & 0x0F00) >> 8] >> 7 == 1:
            self.v[0xF] = 1
        else:
            self.v[0xF] = 0
        self.v[(self.current_opcode & 0x0F00) >> 8] <<= 1

    def skip_next_instruction_if_vx_not_vy(self) -> None:
        """
        9xy0 - SNE Vx, Vy
        Skip next instruction if Vx != Vy.

        The values of Vx and Vy are compared, and if they are not equal,
        the program counter is increased by 2.
        """
        if self.v[(self.current_opcode & 0x0F00) >> 8] != self.v[(self.current_opcode & 0x00F0) >> 4]:
            self.pc += 2

    def set_ir_to_nnn(self) -> None:
        """
        Annn - LD I, addr
        Set I = nnn.

        The value of register I is set to nnn.
        """
        self.ir = self.current_opcode & 0x0FFF

    def jump_to_location_nnn_plus_v0(self) -> None:
        """
        Bnnn - JP V0, addr
        Jump to location nnn + V0.

        The program counter is set to nnn plus the value of V0.
        """
        self.ir = (self.current_opcode & 0x0FFF) + self.v[0]

    def vx_random_byte_masked_by_kk(self) -> None:
        """
        Cxkk - RND Vx, byte
        Set Vx = random byte AND kk.

        The interpreter generates a random number from 0 to 255, which is then ANDed with the value kk.
        The results are stored in Vx. See instruction 8xy2 for more information on AND.
        """
        self.v[(self.current_opcode & 0x0F00) >> 8] = random.randint(0,255) & (self.current_opcode & 0x00FF)

    def display_sprite(self) -> None:
        """
        Dxyn - DRW Vx, Vy, nibble
        Display n-byte sprite starting at memory location I at (Vx, Vy), set VF = collision.

        The interpreter reads n bytes from memory, starting at the address stored in I.
        These bytes are then displayed as sprites on screen at coordinates (Vx, Vy).
        Sprites are XORed onto the existing screen.
        If this causes any pixels to be erased, VF is set to 1, otherwise it is set to 0.
        If the sprite is positioned so part of it is outside the coordinates of the display,
        it wraps around to the opposite side of the screen.
        See instruction 8xy3 for more information on XOR, and section 2.4,
        Display, for more information on the Chip-8 screen and sprites.
        """
        x = self.v[(self.current_opcode & 0x0F00) >> 8]
        y = self.v[(self.current_opcode & 0x00F0) >> 4]
        n = self.current_opcode & 0x000F

        self.v[0xF] = 0

        for y_pos in range(n):
            pixel = self.memory[self.ir + y_pos]
            for x_pos in range(8):
                if pixel & (0x80 >> x_pos) != 0:
                    x_coord = (x + x_pos) % 64
                    y_coord = (y + y_pos) % 32
                    if self.gb[x_coord + (y_coord * 64)] == 1:
                        self.v[0xF] = 1
                    self.gb[x_coord  + (y_coord * 64)] ^= 1
                    self.screen.draw_pixel(x_coord % 64, y_coord, self.gb[x_coord + (y_coord * 64)])

        self.screen.update()
        self.draw_flag = True

    def skip_next_instruction_if_vx_is_pressed(self) -> None:
        """
        Ex9E - SKP Vx
        Skip next instruction if key with the value of Vx is pressed.

        Checks the keyboard, and if the key corresponding to the value of Vx
        is currently in the down position, PC is increased by 2.
        """
        if self.keys[self.v[(self.current_opcode & 0x0F00) >> 8]] != 0:
            self.pc += 2

    def skip_next_instruction_if_vx_is_not_pressed(self) -> None:
        """
        ExA1 - SKNP Vx
        Skip next instruction if key with the value of Vx is not pressed.

        Checks the keyboard, and if the key corresponding to the value of Vx is currently
        in the up position, PC is increased by 2.
        """
        if self.keys[self.v[(self.current_opcode & 0x0F00) >> 8]] == 0:
            self.pc += 2

    def set_vx_to_delay_timer_value(self) -> None:
        """
        Fx07 - LD Vx, DT
        Set Vx = delay timer value.

        The value of DT is placed into Vx.
        """
        self.v[(self.current_opcode & 0x0F00) >> 8] = self.delay_timer

    def wait_for_key_press_store_in_vx(self) -> None:
        """
        Fx0A - LD Vx, K
        Wait for a key press, store the value of the key in Vx.

        All execution stops until a key is pressed, then the value of that key is
        stored in Vx.
        """
        key_pressed = False
        for i, key in enumerate(self.keys):
            if key != 0:
                self.v[(self.current_opcode & 0x0F00) >> 8] = i
                key_pressed = True
        if not key_pressed:
            self.pc -= 2 # pc will stay at the same value after += 2 later

    def set_delay_time_to_vx(self) -> None:
        """
        Fx15 - LD DT, Vx
        Set delay timer = Vx.

        DT is set equal to the value of Vx.
        """
        self.delay_timer = self.v[(self.current_opcode & 0x0F00) >> 8]

    def set_sound_timer_to_vx(self) -> None:
        """
        Fx18 - LD ST, Vx
        Set sound timer = Vx.

        ST is set equal to the value of Vx.
        """
        self.sound_timer = self.v[(self.current_opcode & 0x0F00) >> 8]

    def add_ir_vx(self) -> None:
        """
        Fx1E - ADD I, Vx
        Set I = I + Vx.

        The values of I and Vx are added, and the results are stored in I.
        """
        # Overflow
        if (self.ir + self.v[(self.current_opcode & 0x0F00) >> 8]) > 0xFFF:
            self.v[0xF] = 1
        else:
            self.v[0xF] = 0
        self.ir += self.v[(self.current_opcode & 0x0F00) >> 8]

    def set_ir_to_sprite_vx(self) -> None:
        """
        Fx29 - LD F, Vx
        Set I = location of sprite for digit Vx.

        The value of I is set to the location for the hexadecimal sprite corresponding
        to the value of Vx. See section 2.4, Display, for more information on the Chip-8
        hexadecimal font.
        """
        self.ir = self.v[(self.current_opcode & 0x0F00) >> 8] * 0x5

    def bcd_rep_vx(self) -> None:
        """
        Fx33 - LD B, Vx
        Store BCD representation of Vx in memory locations I, I+1, and I+2.

        The interpreter takes the decimal value of Vx, and places the hundreds digit in
        memory at location in I, the tens digit at location I+1, and the ones digit at
        location I+2.
        """
        self.memory[self.ir] = self.v[(self.current_opcode & 0x0F00) >> 8] / 100            # hundreds digit
        self.memory[self.ir + 1] = (self.v[(self.current_opcode & 0x0F00) >> 8] / 10) % 10  # tens digit
        self.memory[self.ir + 2] = self.v[(self.current_opcode & 0x0F00) >> 8] % 10         # ones digit

    def regs_to_memory(self) -> None:
        """
        Fx55 - LD [I], Vx
        Store registers V0 through Vx in memory starting at location I.

        The interpreter copies the values of registers V0 through Vx into memory,
        starting at the address in I.
        """
        for i in range((self.current_opcode & 0x0F00) >> 8):
            self.memory[self.ir + i] = self.v[i]

    def read_regs_from_memory(self) -> None:
        """
        Fx65 - LD Vx, [I]
        Read registers V0 through Vx from memory starting at location I.

        The interpreter reads values from memory starting at location I into registers
        V0 through Vx.
        """
        for i in range((self.current_opcode & 0x0F00) >> 8):
            self.v[i] = self.memory[self.ir + i]
