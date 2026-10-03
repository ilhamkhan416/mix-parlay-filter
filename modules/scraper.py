import asyncio
from datetime import datetime
import zoneinfo
from playwright.async_api import async_playwright

class ParlayScraper:
    def __init__(self, target_url="https://mainbolakaki.pro/_view/odds4.aspx"):
        self.url = target_url

    async def fetch_odds_data(self) -> list:
        scraped_matches = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu"
                ]
            )
            
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1366, "height": 768},
                locale="id-ID",
                timezone_id="Asia/Jakarta"
            )
            
            page = await context.new_page()
            
            try:
                print(f"  [Scraper] Navigating to {self.url}...")
                await page.goto(self.url, wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(5000) # Beri jeda agar iframe/AJAX selesai dimuat

                wib_tz = zoneinfo.ZoneInfo("Asia/Jakarta")
                today_date_str = datetime.now(wib_tz).strftime("%Y-%m-%d")

                # kumpulkan semua frame (main frame + iframe embed)
                all_frames = page.frames
                print(f"  [Scraper] Found {len(all_frames)} frame(s) in page.")

                for frame in all_frames:
                    try:
                        rows = await frame.query_selector_all("tr")
                        for row in rows:
                            text_content = await row.inner_text()
                            lines = [line.strip() for line in text_content.split("\n") if line.strip()]

                            # Parsing umum berdasarkan baris teks jika tabel tidak menggunakan class baku
                            if len(lines) >= 3:
                                # Mencari angka desimal yang bertindak sebagai Odds (misal: 1.35)
                                odds_val = None
                                for item in lines:
                                    clean_item = item.replace(",", ".")
                                    try:
                                        val = float(clean_item)
                                        if 1.01 <= val <= 10.0: # Range odds realistis
                                            odds_val = val
                                            break
                                    except ValueError:
                                        continue

                                if odds_val and len(lines) >= 2:
                                    scraped_matches.append({
                                        "home": lines[0],
                                        "away": lines[1],
                                        "odds_value": odds_val,
                                        "kickoff_iso": f"{today_date_str}T20:00:00"
                                    })
                    except Exception:
                        continue

            except Exception as e:
                print(f"❌ [Scraper Error]: {e}")
            finally:
                await context.close()
                await browser.close()
                
        return scraped_matches
