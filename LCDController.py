from enum import Enum
from PIL import Image, ImageDraw, ImageFont
import subprocess, textwrap, time

WIDTH, HEIGHT = 480, 320
FONT_SIZE = 18
BG_COLOR = (0, 0, 0)
TEXT_COLOR = (255, 255, 255)
PADDING = 10
FB = "/dev/fb1"

class DisplayMode(Enum):
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"

class LCDController:
    def __init__(self, input_file_handler, output_file_handler):
        self.input_file_handler = input_file_handler
        self.output_file_handler = output_file_handler

    def writeToScreen(self, text):
        img = self.render_text(text)
        self.write_to_framebuffer(img)

    def displayScreen(self, displayMode):
        try:
            if displayMode not in [m.value for m in DisplayMode]:
                raise ValueError(f"Invalid mode '{displayMode}'. Choose from: {DisplayMode}")
            
            if displayMode == DisplayMode.INPUT.value:
                displayText = self.input_file_handler.readFile()
            elif displayMode == DisplayMode.OUTPUT.value:
                displayText = self.output_file_handler.readFile()

            self.writeToScreen(displayText)
            
            return True
        except Exception as e:
            print("LCD Controller Error: ", e)
            return False
        
    def render_text(self, text):
        img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", FONT_SIZE)
        except:
            font = ImageFont.load_default()

        # Wrap text to fit width
        chars_per_line = (WIDTH - 2 * PADDING) // (FONT_SIZE // 2)
        lines = []
        for paragraph in text.strip().split("\n"):
            lines += textwrap.wrap(paragraph, width=chars_per_line) or [""]

        y = PADDING
        for line in lines:
            if y + FONT_SIZE > HEIGHT - PADDING:
                break
            draw.text((PADDING, y), line, font=font, fill=TEXT_COLOR)
            y += FONT_SIZE + 4

        return img

    def write_to_framebuffer(self, img):
        # Convert to RGB565 for the TFT
        raw = img.convert("RGB").tobytes()
        with open(FB, "wb") as f:
            f.write(raw)
