import asyncio
import os
import shutil
import subprocess
from playwright.async_api import async_playwright

async def record_agent_demo():
    video_dir = "/config/Desktop/Session1/plant-care-shop/demo_video"
    os.makedirs(video_dir, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path="/usr/bin/google-chrome",
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--window-size=1280,800"
            ]
        )

        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir=video_dir,
            record_video_size={"width": 1280, "height": 800}
        )

        page = await context.new_page()

        print("Navigating to VerdantCare Chat UI (http://localhost:8080)...")
        await page.goto("http://localhost:8080")
        await page.wait_for_timeout(2500)

        # 1. Primary prompt: Show what the app does best (Greenhouse Catalog Search)
        prompt_1 = "Hi! What indoor plants do you have in stock that are easy to care for and under $50?"
        print("Sending Prompt 1:", prompt_1)

        input_box = await page.wait_for_selector("#input")
        # Type smoothly to look like a realistic demo
        await input_box.type(prompt_1, delay=35)
        await page.wait_for_timeout(800)

        await page.keyboard.press("Enter")

        print("Waiting for response to Prompt 1...")
        # Wait until typing indicator disappears and response bubble appears
        await page.wait_for_timeout(10000)

        # 2. Richer prompt: Show off botanical taxonomy lookup + video generation tool
        prompt_2 = "Can you look up the botanical taxonomy for Monstera Deliciosa and generate a short video of a flourishing Monstera plant?"
        print("Sending Prompt 2:", prompt_2)

        await input_box.type(prompt_2, delay=35)
        await page.wait_for_timeout(800)

        await page.keyboard.press("Enter")

        print("Waiting for response to Prompt 2 (tool call + video generation)...")
        await page.wait_for_timeout(42000)

        # Pause on final response to showcase the rich results
        await page.wait_for_timeout(4000)

        video_obj = page.video
        await page.close()
        await context.close()
        await browser.close()

        video_file = await video_obj.path()
        print("Playwright recorded raw video file at:", video_file)

        # Copy raw video to agent_demo.webm in project root
        target_path = "/config/Desktop/Session1/plant-care-shop/agent_demo.webm"
        shutil.copy(video_file, target_path)
        print("Demo video saved to:", target_path)

        # If ffmpeg/imageio is available, convert to mp4 for universal viewing
        try:
            mp4_target = "/config/Desktop/Session1/plant-care-shop/agent_demo.mp4"
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            cmd = [ffmpeg_exe, "-y", "-i", target_path, "-c:v", "libx264", "-pix_fmt", "yuv420p", mp4_target]
            subprocess.run(cmd, check=True)
            print("Converted MP4 demo video saved to:", mp4_target)
        except Exception as e:
            print("MP4 conversion note:", str(e))

        return target_path

if __name__ == "__main__":
    asyncio.run(record_agent_demo())
