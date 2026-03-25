import spidev
import lgpio
import time
import textwrap
from PIL import Image, ImageDraw, ImageFont

# --- Pin config (BCM numbering) ---
DC_PIN   = 24
RST_PIN  = 25
BL_PIN   = 18   # backlight, may vary — try 18 or 27

# --- Display config ---
WIDTH    = 480
HEIGHT   = 320
SPI_BUS  = 0
SPI_DEV  = 0
SPI_MHZ  = 16

# --- Your text ---
TEXT = """
Hello from Raspberry Pi 5.
This paragraph is rendered directly over SPI
without any kernel framebuffer driver.
You can put anything here — sensor data,
news, notes, or status updates.
"""

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
    send_cmd(0x36); send_data(0x28)   # memory access control (landscape)
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
    chars_per_line = (WIDTH - 2 * padding) // 12

    lines = []
    for para in text.strip().split("\n"):
        wrapped = textwrap.wrap(para, width=chars_per_line)
        lines += wrapped if wrapped else [""]

    y = padding
    for line in lines:
        if y + line_height > HEIGHT - padding:
            break
        draw.text((padding, y), line, font=font, fill=(255, 255, 255))
        y += line_height

    return img

# --- Main ---
init_display()

while True:
    img = render_text(TEXT)
    display_image(img)
    time.sleep(10)