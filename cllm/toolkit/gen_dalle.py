import os
from openai import OpenAI
import logging
import json
import argparse
import sys
import asyncio
import aiohttp
import requests

client = OpenAI()

logging.basicConfig(level=os.environ.get("LOGLEVEL", os.getenv("CLLM_LOGLEVEL")))

def validate_args(args):
    valid_sizes = ["256x256", "512x512", "1024x1024"]
    valid_qualities = ["low", "standard", "high"]

    if args.size not in valid_sizes:
        raise ValueError(f"Invalid size '{args.size}'. Valid options are {valid_sizes}.")
    if args.quality not in valid_qualities:
        raise ValueError(f"Invalid quality '{args.quality}'. Valid options are {valid_qualities}.")
    if args.number < 1:
        raise ValueError("Number of images must be at least 1.")

async def fetch_image(session, prompt, style, model, size, quality, n):
    image_prompt = f"{prompt} {style}"
    logging.info(f"Generating image for prompt '{image_prompt}'")
    try:
        response = client.images.generate(
            model=model,
            prompt=image_prompt,
            size=size,
            quality=quality,
            n=n
        )
        url = response.data[0].url
    except Exception as e:
        logging.error(f"Error generating image for prompt '{prompt}': {e}")
        url = None
    return url

async def generate_images(prompts, style, model="dall-e-3", size="1024x1024", quality="standard", n=1):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_image(session, prompt, style, model, size, quality, n) for prompt in prompts]
        image_urls = await asyncio.gather(*tasks)
    return image_urls

def save_images_locally(image_urls, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for i, url in enumerate(image_urls):
        if url:
            image_data = requests.get(url).content
            with open(os.path.join(output_dir, f"image_{i}.png"), 'wb') as f:
                f.write(image_data)
            logging.info(f"Image saved to {os.path.join(output_dir, f'image_{i}.png')}")

def main():
    parser = argparse.ArgumentParser(description="Generate images using OpenAI's DALL-E model")
    parser.add_argument('-m', '--model', type=str, default="dall-e-3", help='Model to use for image generation')
    parser.add_argument('-s', '--size', type=str, default="1024x1024", help='Size of the generated images')
    parser.add_argument('-q', '--quality', type=str, default="standard", help='Quality of the generated images')
    parser.add_argument('-n', '--number', type=int, default=1, help='Number of images to generate per prompt')
    parser.add_argument('-sp', '--style', type=str, default="", help='Additional styling prompt to generate images from')
    parser.add_argument('-o', '--output-dir', type=str, default=None, help='Directory to save generated images')
    args = parser.parse_args()

    try:
        validate_args(args)
        input_data = sys.stdin.read()
        try:
            prompts = json.loads(input_data)
        except json.JSONDecodeError:
            logging.info("Invalid JSON input")
            prompts = [input_data]

        images = asyncio.run(generate_images(prompts, args.style, args.model, args.size, args.quality, args.number))

        if args.output_dir:
            save_images_locally(images, args.output_dir)
        
        print(json.dumps(images))
    except Exception as e:
        logging.error(f"Error: {e}")
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    main()
