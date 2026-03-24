#!/usr/bin/env python3
"""Generate a simple diagram for Claude Computer Use announcement."""

from PIL import Image, ImageDraw, ImageFont
import os

# Create image
width, height = 1200, 675
img = Image.new('RGB', (width, height), color='#1a1a2e')
draw = ImageDraw.Draw(img)

# Colors
red_accent = '#C41E3A'
white = '#FFFFFF'
gray = '#8B8B8B'
light_gray = '#E0E0E0'

# Try to load a font
try:
    font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
    font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
except:
    font_large = ImageFont.load_default()
    font_medium = ImageFont.load_default()
    font_small = ImageFont.load_default()

# Title
title = "Claude Computer Use"
bbox = draw.textbbox((0, 0), title, font=font_large)
title_width = bbox[2] - bbox[0]
draw.text(((width - title_width) / 2, 40), title, fill=white, font=font_large)

# Subtitle
subtitle = "AI Operating Your Desktop"
bbox = draw.textbbox((0, 0), subtitle, font=font_medium)
subtitle_width = bbox[2] - bbox[0]
draw.text(((width - subtitle_width) / 2, 100), subtitle, fill=gray, font=font_medium)

# Draw three boxes with icons
box_width = 280
box_height = 200
start_y = 200
gap = 60
start_x = (width - (3 * box_width + 2 * gap)) / 2

boxes = [
    ("1", "Open Apps", "🚀"),
    ("2", "Browse Web", "🌐"),
    ("3", "Fill Sheets", "📊"),
]

for i, (num, label, icon) in enumerate(boxes):
    x = start_x + i * (box_width + gap)
    
    # Draw box
    draw.rectangle([x, start_y, x + box_width, start_y + box_height], 
                   outline=red_accent, width=3)
    
    # Draw number circle
    circle_x = x + box_width / 2
    circle_y = start_y + 50
    circle_r = 25
    draw.ellipse([circle_x - circle_r, circle_y - circle_r,
                  circle_x + circle_r, circle_y + circle_r],
                 fill=red_accent)
    draw.text((circle_x - 8, circle_y - 15), num, fill=white, font=font_medium)
    
    # Draw label
    bbox = draw.textbbox((0, 0), label, font=font_small)
    label_width = bbox[2] - bbox[0]
    draw.text((x + (box_width - label_width) / 2, start_y + 120), 
              label, fill=light_gray, font=font_small)

# Draw arrows between boxes
arrow_y = start_y + box_height / 2
for i in range(2):
    x1 = start_x + (i + 1) * box_width + i * gap + 10
    x2 = start_x + (i + 1) * (box_width + gap) - 10
    draw.line([(x1, arrow_y), (x2 - 15, arrow_y)], fill=red_accent, width=3)
    # Arrow head
    draw.polygon([(x2 - 15, arrow_y - 10), (x2 - 15, arrow_y + 10), (x2, arrow_y)], 
                 fill=red_accent)

# Bottom text
footer = "Natural Language → Desktop Automation"
bbox = draw.textbbox((0, 0), footer, font=font_small)
footer_width = bbox[2] - bbox[0]
draw.text(((width - footer_width) / 2, 480), footer, fill=gray, font=font_small)

# ONIZUKA branding
brand = "$" + "ONIAGI"
bbox = draw.textbbox((0, 0), brand, font=font_medium)
brand_width = bbox[2] - bbox[0]
draw.text(((width - brand_width) / 2, 560), brand, fill=red_accent, font=font_medium)

# Save
output_path = 'memory/docs/public/claude-computer-use-diagram.png'
os.makedirs(os.path.dirname(output_path), exist_ok=True)
img.save(output_path)
print(f"Generated: {output_path}")
