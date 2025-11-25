from PIL import Image
import requests
from io import BytesIO

def create_playlist_image(BACKGROUND_PATH):
    # --- Configuration ---
    # Replace with your background image file
    OVERLAY_PATH = 'cadenceoverlay.png'        # Replace with your overlay image file (PNG recommended for transparency)
    OUTPUT_PATH = 'composite_image.jpg' # Output file name
    TARGET_SIZE = (1750, 1750)
    OVERLAY_MAX_WIDTH = 750             # Max width for the overlay (adjust as needed)

    try:
        # 1. Open the images
        response = requests.get(BACKGROUND_PATH)
        background = Image.open(BytesIO(response.content)).convert("RGB")
        overlay = Image.open(OVERLAY_PATH).convert("RGBA") # Use RGBA to handle transparency
        
        # 2. Resize the background to 3000x3000
        background = background.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
        
        # Optional: Resize the overlay to a sensible size (e.g., max width 500 pixels)
        # This maintains the aspect ratio of the overlay.
        overlay_width, overlay_height = overlay.size
        if overlay_width > OVERLAY_MAX_WIDTH:
            ratio = OVERLAY_MAX_WIDTH / overlay_width
            new_height = int(overlay_height * ratio)
            overlay = overlay.resize((OVERLAY_MAX_WIDTH, new_height), Image.Resampling.LANCZOS)
        
        # 3. Calculate the bottom-right position
        bg_width, bg_height = background.size
        ov_width, ov_height = overlay.size
        
        # Set a small margin from the bottom and right edges
        margin = 50 
        
        # Coordinates for the top-left corner of the pasted overlay
        # (x, y) = (background_width - overlay_width - margin, background_height - overlay_height - margin)
        position = (
            bg_width - ov_width - margin,
            bg_height - ov_height - margin
        )
        
        # 4. Paste the overlay onto the background
        # The third argument (overlay) acts as a mask, ensuring any transparency 
        # in the overlay image is respected (no blend).
        background.paste(overlay, position, overlay)
        
        # Save the final image
        # Save JPEG with slightly lower quality to reduce file size
        background.save(OUTPUT_PATH, format='JPEG', quality=60, optimize=True, progressive=True)
        print(f"Success! Image saved to {OUTPUT_PATH} with dimensions {background.size}.")
        return True
        

    except FileNotFoundError:
        print("Error: One of the image files was not found. Please check your file paths.")
    except Exception as e:
        print(f"An error occurred: {e}")