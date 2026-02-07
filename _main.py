"""
Sora-2 Complete Video Generation Pipeline

This script combines video generation, status monitoring, and download into a single
workflow. It generates a video from a text prompt, monitors the progress showing
elapsed time, and automatically downloads the completed video.

Requirements:
    - Python 3.7+
    - openai library (install via: pip install openai)
    - python-dotenv library (install via: pip install python-dotenv)
    - Valid Azure OpenAI API key and endpoint in .env file

Usage:
    python sora2-generate-and-download.py

Author: Microsoft Corporation
Date: October 2025
"""

import os
import time
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# Configuration
# ============================================================================

# Get configuration from environment variables
api_key = os.getenv("AZURE_API_KEY")
resource_name = os.getenv("AZURE_RESOURCE_NAME")
model_name = os.getenv("AZURE_MODEL_NAME")

if not api_key or not resource_name or not model_name:
    raise ValueError(
        "Missing required environment variables. "
        "Please copy .env.sample to .env and populate with your values."
    )

base_url = f"https://{resource_name}/openai/v1/"
client = OpenAI(
    api_key=api_key,
    base_url=base_url,
)

# Video generation parameters
# NOTE: Avoid copyrighted characters (Elmo, Mickey Mouse, etc.) - they will cause generation to fail
prompt = '''Young woman in her 20s, natural lighting, sitting in a cozy bedroom. She holds up a sleek wireless earbuds case excitedly to the camera. Authentic selfie-style video. She puts the earbuds in her ears, nods to music, and gives a thumbs up with a genuine smile. Casual outfit, messy bun hairstyle. iPhone front camera aesthetic. TikTok style UGC testimonial.'''

size = "720x1280"
seconds = "12"

# Output directory
output_dir = "videos"


def generate_video():
    """
    Start video generation and return the video object.
    """
    print("=" * 60)
    print("STEP 1: Starting Video Generation")
    print("=" * 60)
    print(f"Endpoint URL: {base_url}videos")
    print(f"Prompt: {prompt}")
    print(f"Duration: {seconds} seconds")
    print(f"Resolution: {size}")
    print("-" * 60)
    
    video = client.videos.create(
        model=model_name,
        prompt=prompt,
        size=size,
        seconds=seconds,
    )
    
    print(f"\n✓ Video generation started successfully!")
    print(f"  Video ID: {video.id}")
    print(f"  Status: {video.status}")
    print(f"  Model: {video.model}")
    print(f"  Created At: {video.created_at}")
    
    return video


def wait_for_completion(video_id):
    """
    Poll for video completion, showing elapsed time in seconds.
    Returns the completed video object.
    """
    print("\n" + "=" * 60)
    print("STEP 2: Waiting for Video Generation")
    print("=" * 60)
    print(f"Video ID: {video_id}")
    print("-" * 60)
    
    start_time = time.time()
    poll_interval = 10  # Check every 10 seconds
    
    # Get initial status
    video = client.videos.retrieve(video_id)
    print(f"Initial status: {video.status}")
    
    while video.status not in ["completed", "failed", "cancelled"]:
        elapsed = int(time.time() - start_time)
        print(f"Status: {video.status} | Elapsed: {elapsed} seconds | Waiting {poll_interval}s...")
        time.sleep(poll_interval)
        
        # Retrieve the latest status
        video = client.videos.retrieve(video_id)
    
    # Final elapsed time
    total_elapsed = int(time.time() - start_time)
    
    if video.status == "completed":
        print(f"\n✓ Video generation completed!")
        print(f"  Total time: {total_elapsed} seconds")
    else:
        print(f"\n✗ Video generation ended with status: {video.status}")
        print(f"  Total time: {total_elapsed} seconds")
        # Show failure reason if available
        if hasattr(video, 'error') and video.error:
            print(f"  Error: {video.error}")
        if hasattr(video, 'failure_reason') and video.failure_reason:
            print(f"  Failure reason: {video.failure_reason}")
        # Print full video object for debugging
        print(f"\n  Full response: {video}")
    
    return video


def download_video(video_id):
    """
    Download the completed video to the videos folder using the video ID as filename.
    """
    print("\n" + "=" * 60)
    print("STEP 3: Downloading Video")
    print("=" * 60)
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")
    
    # Use video ID as filename
    output_file_path = os.path.join(output_dir, f"{video_id}.mp4")
    
    print(f"Downloading video...")
    print(f"  Endpoint URL: {base_url}videos/{video_id}/content")
    print(f"  Video ID: {video_id}")
    print(f"  Output Path: {output_file_path}")
    print("-" * 60)
    
    # Download the video content
    content = client.videos.download_content(video_id, variant="video")
    
    # Save to file
    content.write_to_file(output_file_path)
    
    print(f"\n✓ Video saved successfully!")
    print(f"  Location: {os.path.abspath(output_file_path)}")
    print(f"  File size: {os.path.getsize(output_file_path):,} bytes")
    
    return output_file_path


def main():
    """
    Main function that orchestrates the complete video generation pipeline.
    """
    try:
        # Step 1: Generate video
        video = generate_video()
        video_id = video.id
        
        # Step 2: Wait for completion with elapsed time display
        completed_video = wait_for_completion(video_id)
        
        # Step 3: Download if completed successfully
        if completed_video.status == "completed":
            output_path = download_video(video_id)
            
            print("\n" + "=" * 60)
            print("PIPELINE COMPLETE")
            print("=" * 60)
            print(f"Video ID: {video_id}")
            print(f"Saved to: {output_path}")
        else:
            print("\n" + "=" * 60)
            print("PIPELINE FAILED")
            print("=" * 60)
            print(f"Video generation did not complete successfully.")
            print(f"Final status: {completed_video.status}")
            print("\nCommon failure reasons:")
            print("  - Copyrighted characters (Elmo, Mickey Mouse, etc.)")
            print("  - Real celebrities or public figures")
            print("  - Violent or inappropriate content")
            print("  - Trademarked content")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print(f"Error type: {type(e).__name__}")
        print("\nTroubleshooting:")
        print("  - Verify your API key is correct")
        print("  - Check that your Azure resource name is correct")
        print("  - Ensure your Azure subscription has access to Sora-2")
        print("  - Verify the prompt and parameters are valid")


if __name__ == "__main__":
    main()
