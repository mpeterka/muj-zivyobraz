"""Small monochrome moon illustrations; all inputs and assets are local."""
from __future__ import annotations

import io
import math
import re
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance
from PIL.PngImagePlugin import PngInfo

ASSETS = Path(__file__).resolve().parent.parent / 'assets' / 'moon'
REAL_SOURCE = 'https://commons.wikimedia.org/wiki/File:Full_Moon_Luc_Viatour.jpg'
REAL_LICENSE = 'https://creativecommons.org/licenses/by-sa/3.0/'


def parse_options(query: str) -> tuple[int, int, str]:
    if len(query) > 100:
        raise ValueError('Query too long')
    options = {}
    for item in query.split('&') if query else []:
        key, separator, value = item.partition('=')
        if not separator or key not in {'width', 'height', 'style'} or key in options:
            raise ValueError('Only unique width, height and style are allowed')
        if key == 'style':
            if value not in {'voyage', 'real'}:
                raise ValueError('style must be voyage or real')
        else:
            if not re.fullmatch(r'[1-9][0-9]{1,3}', value) or not 32 <= int(value) <= 1024:
                raise ValueError('Dimensions must be integers between 32 and 1024')
            value = int(value)
        options[key] = value
    return options.get('width', 128), options.get('height', 128), options.get('style', 'voyage')


def phase_mask(size: int, degrees: float) -> Image.Image:
    """Orthographic illuminated hemisphere: 0 new, 90 first quarter, 180 full."""
    angle = degrees % 360
    mask = Image.new('L', (size, size), 0)
    if angle == 0:
        return mask
    draw = ImageDraw.Draw(mask)
    radius = (size - 1) / 2
    cosine = math.cos(math.radians(angle))
    for row in range(size):
        extent = math.sqrt(max(0, radius * radius - (row - radius) ** 2))
        left, right = math.ceil(radius - extent), math.floor(radius + extent)
        if angle <= 180:
            left = max(left, math.ceil(radius + cosine * extent - 1e-9))
        else:
            right = min(right, math.floor(radius - cosine * extent + 1e-9))
        if left <= right:
            draw.line((left, row, right, row), fill=255)
    return mask


def render_moon(width: int, height: int, style: str, degrees: float) -> bytes:
    parse_options(f'width={width}&height={height}&style={style}')
    if not math.isfinite(degrees):
        raise ValueError('Phase must be finite')
    size = max(1, int(min(width, height) * .94))
    # Keep Voyage's full silhouette, including the rocket outside the disk.
    if style == 'voyage':
        with Image.open(ASSETS / 'melies-cutout.png') as source:
            texture = source.resize(
                (size, size), Image.Resampling.LANCZOS).convert('RGBA')
        disk = texture.getchannel('A').point(lambda value: 255 if value >= 128 else 0)
        illumination = Image.new('L', (size, size), 0)
        angle = degrees % 360
        if angle:
            draw = ImageDraw.Draw(illumination)
            cx, cy, radius = size * .52, size * .52, size * .455
            cosine = math.cos(math.radians(angle))
            for row in range(size):
                extent = math.sqrt(max(0, radius * radius - (row - cy) ** 2))
                if angle <= 180:
                    left, right = math.ceil(cx + cosine * extent), size - 1
                else:
                    left, right = 0, math.floor(cx - cosine * extent)
                if left <= right:
                    draw.line((left, row, right, row), fill=255)
    else:
        with Image.open(ASSETS / 'real-source.jpg') as source:
            texture = source.crop((82, 90, 1328, 1353)).resize(
                (size, size), Image.Resampling.LANCZOS).convert('RGBA')
        disk = Image.new('L', (size, size), 0)
        ImageDraw.Draw(disk).ellipse((0, 0, size - 1, size - 1), fill=255)
        illumination = phase_mask(size, degrees)
    gray = texture.convert('L')
    # Moderate tones keep the face/craters readable after dithering at 128 px.
    gray = ImageEnhance.Contrast(gray).enhance(.85)
    gray = ImageEnhance.Brightness(gray).enhance(1.18 if style == 'real' else 1.05)
    lit = ImageChops.multiply(gray, illumination)
    canvas = Image.new('L', (width, height), 255)
    canvas.paste(lit, ((width - size) // 2, (height - size) // 2), disk)
    monochrome = canvas.convert('1', dither=Image.Dither.FLOYDSTEINBERG)
    metadata = PngInfo()
    if style == 'real':
        metadata.add_text('Author', 'Luc Viatour / https://lucnix.be')
        metadata.add_text('Source', REAL_SOURCE)
        metadata.add_text('License', REAL_LICENSE)
        metadata.add_text('Description', 'Adapted: crop, phase mask, resize, monochrome dithering.')
    else:
        metadata.add_text('Author', 'Georges Melies, Le Voyage dans la lune (1902)')
        metadata.add_text('Source', 'https://commons.wikimedia.org/wiki/File:Le_Voyage_dans_la_lune.jpg')
        metadata.add_text('License', 'Public domain; background extracted with ImageGen.')
    output = io.BytesIO()
    monochrome.save(output, format='PNG', pnginfo=metadata)
    return output.getvalue()
