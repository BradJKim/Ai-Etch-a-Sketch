from enum import Enum
import spidev
import lgpio
import time
import re
from PIL import Image, ImageDraw, ImageFont

# --- Pin config (BCM numbering) ---
DC_PIN   = 24
RST_PIN  = 25
BL_PIN   = 18   # backlight, may vary — try 18 or 27

# --- Display config ---
WIDTH    = 320
HEIGHT   = 480
SPI_BUS  = 0
SPI_DEV  = 0
SPI_MHZ  = 32

# --- GPIO setup ---
h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(h, DC_PIN)
lgpio.gpio_claim_output(h, RST_PIN)
lgpio.gpio_claim_output(h, BL_PIN)

# --- SPI setup ---
spi = spidev.SpiDev()
spi.open(SPI_BUS, SPI_DEV)
spi.max_speed_hz = SPI_MHZ * 1000000
spi.mode = 0

class DisplayMode(Enum):
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"

class LCDController:
    def __init__(self, input_file_handler, output_file_handler):
        self.input_file_handler = input_file_handler
        self.output_file_handler = output_file_handler
        init_display()

    def writeToScreen(self, text, position):
        img = render_text(text, position)
        display_image(img)

    def displayScreen(self, displayMode, position):
        try:
            if displayMode not in [m.value for m in DisplayMode]:
                raise ValueError(f"Invalid mode '{displayMode}'. Choose from: {DisplayMode}")
            
            if displayMode == DisplayMode.INPUT.value:
                displayText = self.input_file_handler.readFile()
            elif displayMode == DisplayMode.OUTPUT.value:
                displayText = self.output_file_handler.readFile()

            self.writeToScreen(displayText, position)
            
            
            return True
        except Exception as e:
            print("LCD Controller Error: ", e)
            return False

def reset():
    lgpio.gpio_write(h, RST_PIN, 1)
    time.sleep(0.1)
    lgpio.gpio_write(h, RST_PIN, 0)
    time.sleep(0.1)
    lgpio.gpio_write(h, RST_PIN, 1)
    time.sleep(0.1)

def send_cmd(cmd):
    lgpio.gpio_write(h, DC_PIN, 0)
    spi.writebytes([cmd])

def send_data(data):
    lgpio.gpio_write(h, DC_PIN, 1)
    if isinstance(data, int):
        spi.writebytes([data])
    else:
        # send in chunks to avoid SPI buffer limits
        for i in range(0, len(data), 4096):
            spi.writebytes(data[i:i+4096])

def init_display():
    reset()
    # ILI9486 init sequence
    send_cmd(0x11)  # sleep out
    time.sleep(0.12)
    send_cmd(0x3A); send_data(0x55)   # pixel format: 16bit RGB565
    send_cmd(0x36); send_data(0x48)   # memory access control (landscape)
    send_cmd(0x11)  # sleep out
    send_cmd(0x29)  # display on
    lgpio.gpio_write(h, BL_PIN, 1)    # backlight on

def set_window(x0, y0, x1, y1):
    send_cmd(0x2A)  # column
    send_data([x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF])
    send_cmd(0x2B)  # row
    send_data([y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF])
    send_cmd(0x2C)  # write

def display_image(img):
    img = img.convert("RGB")
    pixels = []
    for r, g, b in img.getdata():
        # convert to RGB565
        color = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        pixels.append(color >> 8)
        pixels.append(color & 0xFF)
    set_window(0, 0, WIDTH - 1, HEIGHT - 1)
    send_data(pixels)
    
def wrap_text(draw, text, font, max_width):
    lines = []

    for paragraph in text.split("\n"):
        words_with_spaces = re.findall(r'\S+\s*', paragraph)  # keeps spaces after words
        current_line = ""

        for chunk in words_with_spaces:
            # Compute width
            bbox = draw.textbbox((0, 0), chunk, font=font)
            chunk_width = bbox[2] - bbox[0]

            # If chunk too wide (long word), break character by character
            if chunk_width > max_width:
                if current_line:
                    lines.append(current_line)
                    current_line = ""

                subchunk = ""
                for char in chunk:
                    test_sub = subchunk + char
                    bbox = draw.textbbox((0,0), test_sub, font=font)
                    if bbox[2] - bbox[0] <= max_width:
                        subchunk = test_sub
                    else:
                        lines.append(subchunk)
                        subchunk = char
                if subchunk:
                    lines.append(subchunk)
                continue

            # Normal wrapping
            test_line = current_line + chunk
            bbox = draw.textbbox((0,0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = chunk

        # Append last line
        if current_line:
            lines.append(current_line)

    return lines

def render_text(text, char_index):
    img = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except:
        font = ImageFont.load_default()

    padding = 12
    bbox = font.getbbox("Ay")
    line_height = (bbox[3] - bbox[1]) + 4

    max_width = WIDTH - 2 * padding
    lines = wrap_text(draw, text.strip(), font, max_width)

    cursor_line, cursor_col = get_cursor_pos(lines, char_index)

    y = padding
    for i, line in enumerate(lines):
        if y + line_height > HEIGHT - padding:
            break
        draw.text((padding, y), line, font=font, fill=(255, 255, 255))

        if i == cursor_line:
            x = get_cursor_x(draw, line, font, cursor_col, padding)
            draw_cursor(draw, line, font, cursor_col, padding, y, line_height)
        y += line_height

    return img

def draw_cursor(draw, line, font, col, padding, y, line_height):
    if col > 0:
        # Measure width of all characters up to col-1
        x = padding + sum(draw.textlength(c, font=font) for c in line[:col])
    else:
        x = padding

    # If cursor is at the end of the line and last char is space
    if col >= len(line) or (line and line[col-1] == " "):
        # Force the cursor to advance by a fixed space width
        x += draw.textlength(" ", font=font)

    draw.line((x, y, x, y + line_height), fill=(255, 255, 255), width=2)

def get_cursor_x(draw, line, font, col, padding):
    x = padding
    for i in range(min(col, len(line))):
        char = line[i]
        if char == " ":
            x += draw.textlength(" ", font=font)
        else:
            x += draw.textlength(char, font=font)
    return x

def get_cursor_pos(lines, char_index):
    count = 0
    for i, line in enumerate(lines):
        if char_index <= count + len(line):
            col = char_index - count
            col = min(col, len(line))
            return i, col
        count += len(line)
    return len(lines) - 1, len(lines[-1])