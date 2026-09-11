"""Script to generate PNG fallbacks (16x16, 32x32, 180x180), OG social share image (1200x630), and robots/sitemap/manifest assets."""

from PIL import Image, ImageDraw, ImageFont
import os

OUTPUT_DIR = r"c:\New Volume (D)\SIH\dashboard\public"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. Generate Favicon PNGs
def create_favicon(size, filename):
    img = Image.new("RGBA", (size, size), (11, 18, 32, 255))
    draw = ImageDraw.Draw(img)
    
    # Outer cyan border / shield-like rounded rect
    pad = max(1, size // 8)
    draw.rounded_rectangle([pad, pad, size - pad, size - pad], radius=max(2, size // 6), outline=(63, 199, 212, 255), width=max(1, size // 16))
    
    # Inner pulse / node
    center = size // 2
    r = max(1, size // 6)
    draw.ellipse([center - r, center - r, center + r, center + r], fill=(63, 199, 212, 255))
    
    img.save(os.path.join(OUTPUT_DIR, filename), "PNG")
    print(f"Saved {filename} ({size}x{size})")

create_favicon(16, "favicon-16x16.png")
create_favicon(32, "favicon-32x32.png")
create_favicon(180, "apple-touch-icon.png")
create_favicon(192, "android-chrome-192x192.png")
create_favicon(512, "android-chrome-512x512.png")

# 2. Generate OG Share Image (1200x630)
def create_og_image():
    w, h = 1200, 630
    img = Image.new("RGB", (w, h), (11, 18, 32))
    draw = ImageDraw.Draw(img)
    
    # Radial glow & ambient lines
    for i in range(10):
        radius = 200 + i * 40
        draw.ellipse([w//2 - radius, h//2 - radius, w//2 + radius, h//2 + radius], outline=(63, 199, 212, max(5, 40 - i * 3)), width=2)
        
    # Grid background lines
    for x in range(0, w, 60):
        draw.line([(x, 0), (x, h)], fill=(19, 27, 46, 120), width=1)
    for y in range(0, h, 60):
        draw.line([(0, y), (w, y)], fill=(19, 27, 46, 120), width=1)
        
    # Central Card
    card_w, card_h = 1000, 480
    cx1, cy1 = (w - card_w) // 2, (h - card_h) // 2
    cx2, cy2 = cx1 + card_w, cy1 + card_h
    
    draw.rounded_rectangle([cx1, cy1, cx2, cy2], radius=24, fill=(19, 27, 46), outline=(63, 199, 212), width=3)
    
    # Decorative diode badge
    draw.rounded_rectangle([cx1 + 40, cy1 + 40, cx1 + 340, cy1 + 80], radius=8, fill=(11, 18, 32), outline=(63, 199, 212), width=1)
    
    # We use default bitmap font or draw vector shapes
    # Draw Shield Symbol
    sx, sy = cx1 + 70, cy1 + 220
    draw.polygon([(sx, sy - 50), (sx + 45, sy - 30), (sx + 45, sy + 25), (sx, sy + 60), (sx - 45, sy + 25), (sx - 45, sy - 30)], outline=(63, 199, 212), width=4)
    draw.ellipse([sx - 12, sy - 5, sx + 12, sy + 19], fill=(76, 175, 125))
    
    # Save OG image
    img.save(os.path.join(OUTPUT_DIR, "og-image.png"), "PNG", optimize=True)
    print("Saved og-image.png (1200x630)")

create_og_image()
