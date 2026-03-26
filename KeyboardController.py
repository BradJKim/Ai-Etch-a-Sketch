import sys
import tty
import termios

class KeyboardController:
    def __init__(self):
        pass

    def grabInputChar(self):
        try:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)

            try:
                tty.setraw(fd)
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

            return ch

        except Exception as e:
            print("Keyboard Controller Error:", e)
            return False