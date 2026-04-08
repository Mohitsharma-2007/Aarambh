import httpx
import asyncio

async def capture_live_html(name, handle):
    url = f"https://www.youtube.com/@{handle}/live"
    print(f"Capturing HTML for {name} ({url})...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        try:
            res = await client.get(url, headers=headers)
            with open(f"debug_{handle}.html", "w", encoding="utf-8") as f:
                f.write(res.text)
            print(f"Saved debug_{handle}.html (Size: {len(res.text)})")
            
            # Print specific indicators
            print(f"Contains 'isLive': {'isLive' in res.text}")
            print(f"Contains 'LIVE': {'LIVE' in res.text}")
            print(f"Final URL: {res.url}")
        except Exception as e:
            print(f"Error: {e}")

async def main():
    await capture_live_html("Aaj Tak", "aajtak")

if __name__ == "__main__":
    asyncio.run(main())
