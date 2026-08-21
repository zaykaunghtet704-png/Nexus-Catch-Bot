from PIL import Image, ImageDraw, ImageFont
import io

def generate_card_canvas(card_name: str, rarity_name: str, mint: float, serial: int, dye_hex: str = "#FFFFFF") -> io.BytesIO:
    img = Image.new('RGB', (350, 500), color='#100C1A')
    draw = ImageDraw.Draw(img)
    
    # Card Frames
    draw.rectangle([10, 10, 340, 490], outline=dye_hex, width=4)
    draw.rectangle([20, 20, 330, 300], outline="#FFD700", width=2)
    
    font = ImageFont.load_default()
    draw.text((30, 320), f"Name: {card_name}", fill="#FFFFFF", font=font)
    draw.text((30, 350), f"Rarity: [{rarity_name}]", fill="#FFD700", font=font)
    draw.text((30, 380), f"Mint: {mint:.1f}% | #{serial}", fill="#00FFFF", font=font)
    
    output = io.BytesIO()
    img.save(output, format='PNG')
    output.seek(0)
    return output
