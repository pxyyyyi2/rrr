"""
Enhanced Image Generation Backend
Improved error handling, logging, and reliability
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from random import randint
from time import sleep
from typing import Optional, Tuple

import requests
from PIL import Image
from dotenv import get_key

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('image_generation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ImageGenerator:
    """Enhanced image generation class with multiple API support"""
    
    def __init__(self):
        self.data_folder = Path("Data")
        self.data_folder.mkdir(exist_ok=True)
        
        # Multiple API options for fallback
        self.huggingface_apis = [
            "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5",
            "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1", 
            "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
            "https://api-inference.huggingface.co/models/CompVis/stable-diffusion-v1-4"
        ]
        
        self.api_key = self._load_api_key()
        self.headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else None
        
    def _load_api_key(self) -> Optional[str]:
        """Load and validate API key"""
        try:
            api_key = get_key('.env', 'HuggingFaceAPIKey')
            if api_key:
                logger.info(f"✅ API key loaded: {api_key[:10]}...")
                return api_key
            else:
                logger.warning("⚠️  No Hugging Face API key found. Will use free alternatives.")
                return None
        except Exception as e:
            logger.error(f"Error loading API key: {e}")
            return None
    
    def _clean_filename(self, prompt: str) -> str:
        """Clean prompt for safe filename usage"""
        # Replace spaces and remove problematic characters
        cleaned = prompt.replace(" ", "_")
        # Remove or replace problematic characters
        problematic_chars = '<>:"/\\|?*'
        for char in problematic_chars:
            cleaned = cleaned.replace(char, "_")
        # Limit length
        return cleaned[:50]
    
    async def _query_huggingface(self, payload: dict, api_url: str) -> Optional[bytes]:
        """Make async request to Hugging Face API"""
        try:
            response = await asyncio.to_thread(
                requests.post, 
                api_url, 
                headers=self.headers, 
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.content
            elif response.status_code == 503:
                logger.warning(f"Model loading for {api_url.split('/')[-1]}, retrying...")
                await asyncio.sleep(5)
                return None
            else:
                logger.error(f"API error ({api_url.split('/')[-1]}): {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Request failed for {api_url}: {e}")
            return None
    
    async def _generate_with_huggingface(self, prompt: str) -> int:
        """Generate images using Hugging Face APIs with fallback"""
        if not self.headers:
            return 0
            
        successful_images = 0
        
        for api_url in self.huggingface_apis:
            if successful_images >= 4:
                break
                
            model_name = api_url.split('/')[-1]
            logger.info(f"🔄 Trying model: {model_name}")
            
            # Create tasks for remaining images
            remaining_images = 4 - successful_images
            tasks = []
            
            for i in range(remaining_images):
                payload = {
                    "inputs": f"{prompt}, high quality, detailed, 4k, masterpiece",
                    "parameters": {
                        "seed": randint(0, 1000000),
                        "num_inference_steps": 25,
                        "guidance_scale": 7.5
                    }
                }
                task = asyncio.create_task(self._query_huggingface(payload, api_url))
                tasks.append(task)
            
            # Wait for all tasks to complete
            image_bytes_list = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Save successful images
            for i, image_bytes in enumerate(image_bytes_list):
                if isinstance(image_bytes, bytes) and image_bytes:
                    try:
                        filename = f"{self._clean_filename(prompt)}{successful_images + 1}.jpg"
                        filepath = self.data_folder / filename
                        
                        with open(filepath, "wb") as f:
                            f.write(image_bytes)
                        
                        logger.info(f"✅ Generated: {filepath}")
                        successful_images += 1
                        
                        if successful_images >= 4:
                            break
                            
                    except Exception as e:
                        logger.error(f"Error saving image: {e}")
            
            # If we got some images from this model, we can stop
            if successful_images > 0:
                break
                
        return successful_images
    
    async def _generate_with_pollinations(self, prompt: str) -> int:
        """Generate images using free Pollinations.ai API"""
        logger.info("🔄 Using Pollinations.ai (Free alternative)...")
        successful_images = 0
        
        for i in range(4):
            try:
                # Clean prompt for URL
                url_prompt = prompt.replace(' ', '%20').replace(',', '%2C')
                seed = randint(0, 1000000)
                
                url = f"https://image.pollinations.ai/prompt/{url_prompt}?seed={seed}&width=512&height=512&enhance=true"
                
                response = await asyncio.to_thread(requests.get, url, timeout=30)
                
                if response.status_code == 200 and response.content:
                    filename = f"{self._clean_filename(prompt)}{i+1}.jpg"
                    filepath = self.data_folder / filename
                    
                    with open(filepath, "wb") as f:
                        f.write(response.content)
                    
                    logger.info(f"✅ Generated: {filepath}")
                    successful_images += 1
                else:
                    logger.warning(f"❌ Failed to generate image {i+1} - Status: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Error generating image {i+1} with Pollinations: {e}")
                
        return successful_images
    
    def open_generated_images(self, prompt: str):
        """Open and display generated images"""
        cleaned_prompt = self._clean_filename(prompt)
        
        # Find all generated images for this prompt
        image_files = list(self.data_folder.glob(f"{cleaned_prompt}*.jpg"))
        
        if not image_files:
            logger.warning(f"No images found for prompt: {prompt}")
            return
        
        for image_path in sorted(image_files):
            try:
                logger.info(f"Opening image: {image_path}")
                img = Image.open(image_path)
                img.show()
                sleep(1)  # Small delay between opening images
            except Exception as e:
                logger.error(f"Unable to open {image_path}: {e}")
    
    async def generate_images(self, prompt: str) -> bool:
        """Main image generation function with fallback strategies"""
        logger.info(f"🎨 Starting image generation for: '{prompt}'")
        
        total_generated = 0
        
        # Try Hugging Face first if API key is available
        if self.api_key:
            total_generated = await self._generate_with_huggingface(prompt)
            logger.info(f"Hugging Face generated {total_generated} images")
        
        # If we don't have enough images, try Pollinations
        if total_generated < 4:
            additional_images = await self._generate_with_pollinations(prompt)
            total_generated += additional_images
            logger.info(f"Pollinations generated {additional_images} additional images")
        
        if total_generated > 0:
            logger.info(f"✅ Successfully generated {total_generated} images total!")
            return True
        else:
            logger.error("❌ Failed to generate any images with all available methods")
            return False


class ImageGenerationService:
    """Service to monitor and handle image generation requests"""
    
    def __init__(self):
        self.generator = ImageGenerator()
        self.request_file = Path("Frontend/Files/ImageGeneration.data")
        self.request_file.parent.mkdir(parents=True, exist_ok=True)
        
    def parse_request_data(self, data: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse request data with improved error handling"""
        try:
            # Handle different possible formats
            data = data.strip()
            
            if not data:
                return None, None
            
            # Split by comma and clean up
            parts = data.split(",")
            
            if len(parts) >= 2:
                prompt = parts[0].strip()
                status = parts[1].strip()
                return prompt, status
            else:
                logger.error(f"Invalid data format: {data}")
                return None, None
                
        except Exception as e:
            logger.error(f"Error parsing request data '{data}': {e}")
            return None, None
    
    def mark_request_complete(self):
        """Mark the current request as completed"""
        try:
            with open(self.request_file, "w") as f:
                f.write("False,False")
            logger.info("Request marked as complete")
        except Exception as e:
            logger.error(f"Error marking request complete: {e}")
    
    async def process_generation_request(self, prompt: str):
        """Process a single image generation request"""
        logger.info(f"🎨 Processing generation request: '{prompt}'")
        
        try:
            # Generate images
            success = await self.generator.generate_images(prompt)
            
            if success:
                # Open images for display
                self.generator.open_generated_images(prompt)
                logger.info("✅ Image generation completed successfully")
            else:
                logger.error("❌ Image generation failed")
                
        except Exception as e:
            logger.error(f"Error during image generation: {e}")
        finally:
            # Always mark as complete
            self.mark_request_complete()
    
    async def monitor_requests(self):
        """Monitor for image generation requests"""
        logger.info("🚀 Image Generation Service Started")
        
        while True:
            try:
                if not self.request_file.exists():
                    await asyncio.sleep(1)
                    continue
                
                with open(self.request_file, "r", encoding='utf-8') as f:
                    data = f.read()
                
                prompt, status = self.parse_request_data(data)
                
                if prompt and status and status.lower() == "true":
                    await self.process_generation_request(prompt)
                    break  # Exit after processing one request
                else:
                    await asyncio.sleep(1)
                    
            except FileNotFoundError:
                # File doesn't exist yet, keep waiting
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error monitoring requests: {e}")
                await asyncio.sleep(1)


async def main():
    """Main entry point"""
    service = ImageGenerationService()
    await service.monitor_requests()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Image generation service stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Image generation service shutdown complete")