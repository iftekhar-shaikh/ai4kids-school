import base64
# School door image - base64 encoded
b64 = ""
import urllib.request
# Download from the Claude chat outputs
try:
    req = urllib.request.Request(
        'https://cdn-uploads.huggingface.co/production/uploads/noauth/school_gate_cartoon.jpeg',
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    urllib.request.urlretrieve(req, r'C:\Users\iftekhar\ai4kids\school_door.jpeg')
except:
    # Fallback - create a simple placeholder
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new('RGB', (300, 350), '#FFF')
    draw = ImageDraw.Draw(img)
    draw.rectangle([30, 50, 270, 320], outline='#E67E22', width=4)
    draw.arc([80, 10, 220, 100], 0, 180, fill='#3498DB', width=4)
    draw.text((90, 40), "SCHOOL", fill='#E67E22')
    draw.rectangle([100, 120, 200, 320], outline='#2C3E50', width=3)
    draw.ellipse([50, 200, 80, 230], fill='#F39C12')
    draw.ellipse([220, 200, 250, 230], fill='#F39C12')
    img.save(r'C:\Users\iftekhar\ai4kids\school_door.jpeg')
    print("Created placeholder school door image")
