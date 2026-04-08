import httpx
import asyncio
import re

TEST_CHANNELS = [
    {"name": "Aaj Tak", "id": "UCZFMm1mW0Z81r3j3rN5cA"},
    {"name": "CNN", "id": "UCupvZG-5koHEi_75aLxfV0A"},
    {"name": "BBC News", "id": "UCK8sQmJBp8GCxrOtXWBpyEA"}
]

async def check_live_scrape(name, channel_id):
    url = f"https://www.youtube.com/channel/{channel_id}/live"
    print(f"\n--- Checking {name} via scrape ({url}) ---")
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
        try:
            # YouTube redirects /live to the current live video or the channel home
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            res = await client.get(url, headers=headers)
            content = res.text
            
            # Look for "videoID" or "canonical" link
            # If it's live, the page contains "isLive": true and the videoId
            is_live = '"isLive":true' in content
            video_id_match = re.search(r'vi/([a-zA-Z0-9_-]{11})/', content)
            video_id_match_v2 = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', content)
            
            video_id = video_id_match_v2.group(1) if video_id_match_v2 else (video_id_match.group(1) if video_id_match else None)
            
            if is_live and video_id:
                print(f"✅ DETECTED LIVE: {video_id}")
                return video_id
            else:
                print(f"❌ Not Live (is_live={is_live}, video_id={video_id})")
                return None
        except Exception as e:
            print(f"Error: {e}")
            return None

async def main():
    for chan in TEST_CHANNELS:
        await check_live_scrape(chan["name"], chan["id"])

if __name__ == "__main__":
    asyncio.run(main())
