#!/usr/bin/env python3
"""
nano-banana-2 Image Generator
Generate images from text prompts using fal.ai's nano-banana-2 model.
Supports both text-to-image and image-to-image (edit) modes.
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from typing import Optional, List

try:
    import requests
except ImportError:
    print("Installing requests...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests


# fal.ai API endpoints
FAL_API_URL = "https://queue.fal.run/fal-ai/nano-banana-2"
FAL_EDIT_API_URL = "https://queue.fal.run/fal-ai/nano-banana-2/edit"
FAL_RESULT_URL = "https://queue.fal.run/fal-ai/nano-banana-2/requests"


def get_api_key() -> str:
    """Get FAL API key from environment or file."""
    # Try environment variable first
    api_key = os.environ.get("FAL_KEY")
    if api_key:
        return api_key

    # Try workspace directory
    key_file = Path(__file__).parent.parent.parent / "fal-key.txt"
    if key_file.exists():
        return key_file.read_text().strip()

    # Try home directory
    key_file = Path.home() / "fal-key.txt"
    if key_file.exists():
        return key_file.read_text().strip()

    raise ValueError(
        "FAL API key not found. Set FAL_KEY environment variable "
        "or create fal-key.txt in workspace or home directory."
    )


def image_to_data_url(image_path: str) -> str:
    """Convert a local image file to a data URL."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    # Determine MIME type
    suffix = path.suffix.lower()
    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    mime_type = mime_types.get(suffix, "application/octet-stream")
    
    # Read and encode
    with open(path, "rb") as f:
        image_data = f.read()
    
    encoded = base64.b64encode(image_data).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def process_image_urls(image_paths: List[str]) -> List[str]:
    """Process image paths/URLs into usable URLs for the API."""
    urls = []
    for img in image_paths:
        if img.startswith("http://") or img.startswith("https://"):
            # Already a URL
            urls.append(img)
        else:
            # Local file - convert to data URL
            data_url = image_to_data_url(img)
            urls.append(data_url)
    return urls


def submit_request(
    api_key: str,
    prompt: str,
    num_images: int = 1,
    aspect_ratio: str = "auto",
    resolution: str = "1K",
    output_format: str = "png",
    seed: Optional[int] = None,
    enable_web_search: bool = False,
    image_urls: Optional[List[str]] = None,
) -> tuple:
    """Submit image generation request to fal.ai.
    
    Returns:
        tuple: (request_id, is_edit_mode)
    """
    headers = {
        "Authorization": f"Key {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "prompt": prompt,
        "num_images": num_images,
        "aspect_ratio": aspect_ratio,
        "resolution": resolution,
        "output_format": output_format,
        "enable_web_search": enable_web_search,
    }

    if seed is not None:
        payload["seed"] = seed

    # Determine endpoint based on whether images are provided
    # Note: edit endpoint returns same status/result URLs as regular endpoint
    if image_urls:
        payload["image_urls"] = image_urls
        api_url = FAL_EDIT_API_URL
        is_edit = True
        print(f"Mode: Image-to-Image (Edit)")
    else:
        api_url = FAL_API_URL
        is_edit = False
        print(f"Mode: Text-to-Image")

    response = requests.post(
        api_url,
        headers=headers,
        json=payload,
    )

    if response.status_code != 200:
        raise Exception(f"API request failed: {response.status_code} - {response.text}")

    data = response.json()
    return data["request_id"], is_edit


def get_status(api_key: str, request_id: str) -> dict:
    """Get the status of a submitted request."""
    headers = {
        "Authorization": f"Key {api_key}",
    }

    response = requests.get(
        f"{FAL_RESULT_URL}/{request_id}/status",
        headers=headers,
    )

    # 200 = completed, 202 = in progress
    if response.status_code not in (200, 202):
        raise Exception(f"Failed to get status: {response.status_code} - {response.text}")

    return response.json()


def get_result(api_key: str, request_id: str) -> dict:
    """Get the result of a submitted request (only call when status is COMPLETED)."""
    headers = {
        "Authorization": f"Key {api_key}",
    }

    response = requests.get(
        f"{FAL_RESULT_URL}/{request_id}",
        headers=headers,
    )

    if response.status_code != 200:
        raise Exception(f"Failed to get result: {response.status_code} - {response.text}")

    return response.json()


def wait_for_result(
    api_key: str,
    request_id: str,
    timeout: int = 300,
    poll_interval: int = 2,
) -> dict:
    """Wait for the request to complete and return the result."""
    import time

    start_time = time.time()

    while time.time() - start_time < timeout:
        status = get_status(api_key, request_id)

        if status.get("status") == "COMPLETED":
            # Now fetch the actual result
            return get_result(api_key, request_id)

        if status.get("status") == "FAILED":
            raise Exception(f"Request failed: {status}")

        time.sleep(poll_interval)

    raise TimeoutError(f"Request timed out after {timeout} seconds")


def download_image(url: str, output_path: Path) -> Path:
    """Download image from URL to local file."""
    response = requests.get(url, stream=True)
    response.raise_for_status()

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate images from text prompts using fal.ai nano-banana-2"
    )
    parser.add_argument(
        "--prompt", "-p",
        required=True,
        help="Text prompt for image generation",
    )
    parser.add_argument(
        "--image", "-i",
        action="append",
        dest="images",
        help="Input image for edit mode (can be URL or local path). Can be used multiple times.",
    )
    parser.add_argument(
        "--num-images", "-n",
        type=int,
        default=1,
        help="Number of images to generate (default: 1)",
    )
    parser.add_argument(
        "--aspect-ratio", "-a",
        default="auto",
        choices=["auto", "21:9", "16:9", "3:2", "4:3", "5:4", "1:1", "4:5", "3:4", "2:3", "9:16"],
        help="Aspect ratio (default: auto)",
    )
    parser.add_argument(
        "--resolution", "-r",
        default="1K",
        choices=["0.5K", "1K", "2K", "4K"],
        help="Resolution (default: 1K)",
    )
    parser.add_argument(
        "--output-format", "-f",
        default="png",
        choices=["jpeg", "png", "webp"],
        help="Output format (default: png)",
    )
    parser.add_argument(
        "--seed", "-s",
        type=int,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--enable-web-search",
        action="store_true",
        help="Enable web search for up-to-date info",
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=Path("."),
        help="Output directory for downloaded images (default: current directory)",
    )
    parser.add_argument(
        "--download", "-d",
        action="store_true",
        help="Download generated images to local files",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON",
    )

    args = parser.parse_args()

    try:
        api_key = get_api_key()
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Process input images if provided
    image_urls = None
    if args.images:
        print(f"Processing {len(args.images)} input image(s)...")
        image_urls = process_image_urls(args.images)

    print(f"Submitting request: {args.prompt[:50]}...")

    request_id, is_edit = submit_request(
        api_key=api_key,
        prompt=args.prompt,
        num_images=args.num_images,
        aspect_ratio=args.aspect_ratio,
        resolution=args.resolution,
        output_format=args.output_format,
        seed=args.seed,
        enable_web_search=args.enable_web_search,
        image_urls=image_urls,
    )

    print(f"Request ID: {request_id}")
    print("Waiting for result...")

    result = wait_for_result(api_key, request_id)

    images = result.get("images", [])
    description = result.get("description", "")

    if args.json:
        output = {
            "request_id": request_id,
            "prompt": args.prompt,
            "mode": "edit" if is_edit else "generate",
            "images": images,
            "description": description,
        }
        print(json.dumps(output, indent=2))
    else:
        mode_str = "(Edit)" if is_edit else ""
        print(f"\nGenerated {len(images)} image(s) {mode_str}:")
        for i, img in enumerate(images, 1):
            print(f"  {i}. {img['url']}")

        if description:
            print(f"\nDescription: {description}")

    if args.download and images:
        args.output_dir.mkdir(parents=True, exist_ok=True)

        print(f"\nDownloading images to {args.output_dir}...")
        for i, img in enumerate(images, 1):
            url = img["url"]
            ext = args.output_format
            mode_prefix = "edit" if is_edit else "gen"
            filename = f"nano-banana-2-{mode_prefix}-{request_id[:8]}-{i}.{ext}"
            output_path = args.output_dir / filename

            download_image(url, output_path)
            print(f"  Downloaded: {output_path}")


if __name__ == "__main__":
    main()
