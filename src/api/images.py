import os
import replicate
import requests
from PIL import Image
from io import BytesIO
from typing import Optional, Tuple
from src.utils.utils import load_config

IMAGE_STYLES = {
    "Retro": """Beautiful 16-bit anime art in the style of Chrono Trigger and Final Fantasy Tactics. Rich colors with detailed pixel-perfect shading.""",
    "Classic": """Beautiful classic anime art in the style of Dragon Quest or Princess Mononoke, with limited color palette and fewer details.""",
    "Modern": """Beautiful modern anime art in the style of Persona 5 or Violet Evergarden, with clean lines, vibrant colors, and intricate details.""",
    "Chibi": """Beautiful chibi anime art in the style of Theatrhythm or Lucky Star, with exaggerated proportions, large heads and bright, cheerful colors.""",
    "Dark": """Beautiful gothic dark fantasy art in the style of Darkest Dungeon or Demons Souls. Heavy shadows and muted colors with dramatic lighting.""",
}

config = load_config()

IMAGE_STYLE = IMAGE_STYLES[config.get("image_style", "Modern")]
JRPG_BOILERPLATE = (
    f"A Japanese Role Playing Game (JRPG) image in the style: {IMAGE_STYLE}."
)


def load_image_url(url: str) -> Image.Image:
    response = requests.get(url)
    response.raise_for_status()
    return Image.open(BytesIO(response.content))


def generate_image_replicate(
    prompt: str,
    aspect_ratio: Optional[str] = None,
    max_retries: int = 3,
    megapixels: float = 1,
) -> Optional[Image.Image]:
    client = replicate.Client(api_token=config.get("image_api_key"))
    for attempt in range(max_retries):
        try:
            output = client.run(
                config.get("image_model", "black-forest-labs/flux-schnell"),
                input={
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "output_format": "png",
                    "go_fast": False,
                    "megapixels": str(megapixels),
                },
            )[0]
            return load_image_url(output)
        except replicate.exceptions.ModelError as e:
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed: {str(e)}. Retrying...")
                continue
            print(f"Failed after {max_retries} attempts: {str(e)}")
            return None
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return None


def save_image(image: Image.Image, directory: str, filename: str) -> str:
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, filename)
    image.save(file_path, format="PNG")
    return file_path


def save_dummy_image(
    directory: str, filename: str, size: Tuple[int, int] = (64, 64)
) -> str:
    dummy_image = Image.new("RGBA", size, (0, 0, 0, 0))
    return save_image(dummy_image, directory, filename)


def simple_zoom(image: Image.Image, crop_percentage: float = 0.1) -> Image.Image:
    width, height = image.size
    crop_x = int(width * crop_percentage)
    crop_y = int(height * crop_percentage)
    cropped = image.crop(
        (
            crop_x,
            crop_y,
            width - crop_x,
            height - crop_y,
        )
    )
    return cropped.resize((width, height), Image.NEAREST)


def generate_and_save_image(
    prompt: str,
    directory: str,
    filename: str,
    aspect_ratio: str = "3:2",
    dummy_size: Tuple[int, int] = (1280, 720),
    use_dummy: bool = False,
    apply_zoom: float = 0,
    megapixels: float = 1,
) -> Optional[str]:
    if use_dummy:
        return save_dummy_image(directory, filename, dummy_size)

    image = generate_image_replicate(
        prompt, aspect_ratio=aspect_ratio, megapixels=megapixels
    )
    if not image:
        return None

    if apply_zoom > 0:
        image = simple_zoom(image, crop_percentage=apply_zoom)

    return save_image(image, directory, filename)


def generate_title_background(
    world_name: str, world_description: str, use_dummy: bool = False
) -> Optional[str]:
    prompt = f"{JRPG_BOILERPLATE} Image of a game world called {world_name}, which looks like {world_description}. The image should be a single scene that takes up the whole image with no borders."
    return generate_and_save_image(
        prompt=prompt,
        directory="images/title_screens",
        filename=f"{world_name.replace(' ', '_')}.png",
        use_dummy=use_dummy,
        apply_zoom=0.0,
    )


def generate_background_image(
    location_name: str, location_description: str, use_dummy: bool = False
) -> Optional[str]:
    prompt = f"{JRPG_BOILERPLATE} Image of a location background called {location_name}, which looks like {location_description}. The background should be a single scene that takes up the whole image with no borders."
    return generate_and_save_image(
        prompt=prompt,
        directory="images/backgrounds",
        filename=f"{location_name.replace(' ', '_')}.png",
        use_dummy=use_dummy,
        apply_zoom=0.00,
    )


def generate_landmark_image(
    location_name: str,
    location_description: str,
    landmark_name: str,
    landmark_description: str,
    use_dummy: bool = False,
) -> Optional[str]:
    prompt = f"{JRPG_BOILERPLATE} Image of a notable landmark called {landmark_name}, which is {landmark_description}. It is located in {location_name} ({location_description}). The landmark should be centered and rendered as large as possible, taking up most of the image with no borders."
    return generate_and_save_image(
        prompt=prompt,
        directory="images/landmarks",
        filename=f"{landmark_name.replace(' ', '_')}.png",
        dummy_size=(64, 64),
        use_dummy=use_dummy,
        apply_zoom=0.0,
    )


def generate_shop_image(
    location_name: str,
    location_description: str,
    shop_name: str,
    shop_description: str,
    use_dummy: bool = False,
) -> Optional[str]:
    prompt = f"{JRPG_BOILERPLATE} Image of the interior of a shop called {shop_name}, which is {shop_description}. It is located in {location_name} ({location_description}). The shop should be centered and rendered as large as possible, taking up most of the image with no borders."
    return generate_and_save_image(
        prompt=prompt,
        directory="images/shops",
        filename=f"{shop_name.replace(' ', '_')}.png",
        dummy_size=(64, 64),
        use_dummy=use_dummy,
        apply_zoom=0.0,
    )


def generate_npc_portrait(
    npc_name: str,
    npc_description: str,
    job_class: str,
    use_dummy: bool = False,
) -> Optional[str]:
    prompt = f"{JRPG_BOILERPLATE} Portrait image of a character or enemy named {npc_name} ({job_class}), who looks like {npc_description}. The image should be a close-up of the head and rendered as to large as possible, taking up the whole image. The character should be facing forward."
    return generate_and_save_image(
        prompt=prompt,
        directory="images/portraits",
        filename=f"{npc_name.replace(' ', '_')}.png",
        aspect_ratio="1:1",
        dummy_size=(64, 64),
        use_dummy=use_dummy,
        apply_zoom=0.15,
        megapixels=0.25,
    )


def generate_item_portrait(
    item_name: str,
    item_description: str,
    use_dummy: bool = False,
) -> Optional[str]:
    prompt = f"{JRPG_BOILERPLATE} Image of an item called {item_name}, which is described as {item_description}. The item should be centered and rendered as large as possible, taking up the whole image."
    return generate_and_save_image(
        prompt=prompt,
        directory="images/items",
        filename=f"{item_name.replace(' ', '_')}.png",
        aspect_ratio="1:1",
        dummy_size=(64, 64),
        use_dummy=use_dummy,
        apply_zoom=0.15,
        megapixels=0.25,
    )
