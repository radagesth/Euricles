from PIL import Image, ImageDraw, ImageFont
import io, struct, os

SIZES = [16, 32, 48, 64, 128, 256]
GREEN = (22, 163, 74)
WHITE = (255, 255, 255)
OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "euricles.ico")


def _draw_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    r = max(size // 8, 2)
    draw.rounded_rectangle([(0, 0), (size - 1, size - 1)], radius=r, fill=GREEN)
    font_size = int(size * 0.6)
    try:
        font = ImageFont.truetype("segoeui.ttf", font_size)
    except (IOError, OSError):
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except (IOError, OSError):
            font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), "E", font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (size - tw) / 2 - bbox[0]
    ty = (size - th) / 2 - bbox[1]
    draw.text((tx, ty), "E", fill=WHITE, font=font)
    return img


def _png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _build_ico(images: list) -> bytes:
    png_data = [_png_bytes(img) for img in images]
    count = len(images)
    header = struct.pack("<HHH", 0, 1, count)
    offset = 6 + count * 16
    entries = b""
    for i, (img, png) in enumerate(zip(images, png_data)):
        w = img.width if img.width < 256 else 0
        h = img.height if img.height < 256 else 0
        bpp = 32
        size = len(png)
        entries += struct.pack("<BBBBHHII", w, h, 0, 0, 1, bpp, size, offset)
        offset += size
    return header + entries + b"".join(png_data)


def main():
    images = [_draw_icon(s) for s in SIZES]
    ico_data = _build_ico(images)
    with open(OUTPUT, "wb") as f:
        f.write(ico_data)
    print(f"Icono generado: {OUTPUT} ({len(ico_data)} bytes, {len(SIZES)} tamaños: {SIZES})")


if __name__ == "__main__":
    main()
