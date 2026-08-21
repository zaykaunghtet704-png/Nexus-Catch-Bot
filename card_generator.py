from PIL import Image, ImageDraw, ImageFont
import io
import requests

def generate_custom_card(card_title, rarity_name, print_no, atk, def_val, hp, dye_hex="#FF0055", frame_style="Gold"):
    # Create base canvas
    width, height = 400, 600
    image = Image.new("RGB", (width, height), color=(15, 15, 25))
    draw = ImageDraw.Draw(image)

    # Frame Color Mapping
    frame_color = (255, 215, 0) if frame_style == "Gold" else (0, 255, 255)

    # Outer Decorative Border (Gilded/Neon Frame)
    draw.rectangle([10, 10, width - 10, height - 10], outline=frame_color, width=6)
    draw.rectangle([18, 18, width - 18, height - 18], outline=(50, 50, 70), width=2)

    # Header Stats
    draw.text((25, 25), f"[{rarity_name.upper()}]", fill=frame_color)
    draw.text((width - 120, 25), f"Print #{print_no:04d}", fill=(200, 200, 200))

    # Inner Card Image Placeholder Box
    draw.rectangle([30, 60, width - 30, 380], outline=(100, 100, 150), fill=(30, 30, 45))
    draw.text((120, 200), "[ CHARACTER VISUAL ]", fill=(150, 150, 180))

    # Details Section
    draw.text((30, 400), f"Character: {card_title}", fill=(255, 255, 255))
    draw.text((30, 430), f"Frame: {frame_style} | Dye: {dye_hex}", fill=dye_hex)
    draw.text((30, 460), f"Condition: Mint 100%", fill=(0, 255, 150))
    
    # Stats Line
    stats_text = f"HP: {hp:,} | ATK: {atk:,} | DEF: {def_val:,}"
    draw.text((30, 500), stats_text, fill=(255, 215, 0))

    # Save to IO Stream
    bio = io.BytesIO()
    bio.name = 'card.png'
    image.save(bio, 'PNG')
    bio.seek(0)
    return bio
