from PIL import Image
import requests
from io import BytesIO
import uuid
from datetime import datetime


def create_playlist_image(BACKGROUND_PATH):
    # --- Configuration ---
    # Replace with your background image file
    OVERLAY_PATH = "cadenceoverlay.png"
    TARGET_SIZE = (1750, 1750)
    OVERLAY_MAX_WIDTH = 750

    try:
        # 1. Open the images
        response = requests.get(BACKGROUND_PATH)
        background = Image.open(BytesIO(response.content)).convert("RGB")
        overlay = Image.open(OVERLAY_PATH).convert("RGBA")

        # 2. Resize the background
        background = background.resize(TARGET_SIZE, Image.Resampling.LANCZOS)

        # 3. Resize overlay if needed
        overlay_width, overlay_height = overlay.size
        if overlay_width > OVERLAY_MAX_WIDTH:
            ratio = OVERLAY_MAX_WIDTH / overlay_width
            new_height = int(overlay_height * ratio)
            overlay = overlay.resize(
                (OVERLAY_MAX_WIDTH, new_height), Image.Resampling.LANCZOS
            )

        # 4. Calculate bottom-right position
        bg_width, bg_height = background.size
        ov_width, ov_height = overlay.size
        margin = 50
        position = (bg_width - ov_width - margin, bg_height - ov_height - margin)

        # 5. Paste overlay onto background
        background.paste(overlay, position, overlay)

        # 6. Save to BytesIO buffer instead of file
        output_buffer = BytesIO()
        background.save(
            output_buffer, format="JPEG", quality=60, optimize=True, progressive=True
        )
        output_buffer.seek(0)  # Reset buffer position to beginning

        # 7. Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        file_path = f"playlists/{timestamp}_{unique_id}.jpg"
        url = create_playlist_image(file_path, output_buffer)
        return url

    except FileNotFoundError:
        print(
            "Error: One of the image files was not found. Please check your file paths."
        )
    except Exception as e:
        print(f"An error occurred: {e}")
