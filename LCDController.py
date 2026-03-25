from enum import Enum
import spidev
import lgpio
import time
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
SPI_MHZ  = 16

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

    def writeToScreen(self, text):
        img = render_text(text)
        display_image(img)

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
        words = paragraph.split(" ")
        current_line = ""

        for word in words:
            # Check if the word itself is too long
            bbox = draw.textbbox((0, 0), word, font=font)
            word_width = bbox[2] - bbox[0]

            if word_width > max_width:
                # First, flush any existing line
                if current_line:
                    lines.append(current_line)
                    current_line = ""

                # Now break the long word
                chunk = ""
                for char in word:
                    test_chunk = chunk + char
                    bbox = draw.textbbox((0, 0), test_chunk, font=font)
                    chunk_width = bbox[2] - bbox[0]

                    if chunk_width <= max_width:
                        chunk = test_chunk
                    else:
                        lines.append(chunk)
                        chunk = char

                if chunk:
                    lines.append(chunk)

                continue

            # Normal word wrapping
            test_line = current_line + (" " if current_line else "") + word
            bbox = draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]

            if line_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)
        else:
            lines.append("")

    return lines

def render_text(text):
    img = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except:
        font = ImageFont.load_default()

    padding = 12
    line_height = 26

    max_width = WIDTH - 2 * padding
    lines = wrap_text(draw, text.strip(), font, max_width)

    y = padding
    for line in lines:
        if y + line_height > HEIGHT - padding:
            break
        draw.text((padding, y), line, font=font, fill=(255, 255, 255))
        y += line_height

    return img
