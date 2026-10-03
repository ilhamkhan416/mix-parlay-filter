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
                await page.wait_for_timeout(5000)

                wib_tz = zoneinfo.ZoneInfo("Asia/Jakarta")
                today_date_str = datetime.now(wib_tz).strftime("%Y-%m-%d")

                # Filter kata kunci header / noise tabel
                ignored_keywords = ["soccer", "mix parlay", "today", "select league", "odds", "home", "away", "time"]

                for frame in page.frames:
                    try:
                        rows = await frame.query_selector_all("tr")
                        for row in rows:
                            text_content = await row.inner_text()
                            lines = [line.strip() for line in text_content.split("\n") if line.strip()]

                            if len(lines) >= 3:
                                # Abaikan jika merupakan header tabel
                                if any(kw in lines[0].lower() or kw in lines[1].lower() for kw in ignored_keywords):
                                    continue

                                # Cari elemen tim yang sah (bukan kata 'LIVE' atau jam '00:00')
                                valid_team_names = []
                                odds_val = None

                                for item in lines:
                                    clean_item = item.replace(",", ".")
                                    # Cari angka Odds
                                    try:
                                        val = float(clean_item)
                                        if 1.01 <= val <= 10.0 and odds_val is None:
                                            odds_val = val
                                            continue
                                    except ValueError:
                                        pass

                                    # Saring nama tim (abaikan LIVE, jam format 00:00, atau teks pendek noise)
                                    if item.upper() not in ["LIVE", "TODAY", "CANCEL"] and not item.replace(":", "").isdigit():
                                        if len(item) > 2 and item.lower() not in ignored_keywords:
                                            valid_team_names.append(item)

                                # Pastikan ditemukan 2 nama tim (Home & Away) dan nilai Odds
                                if len(valid_team_names) >= 2 and odds_val:
                                    scraped_matches.append({
                                        "home": valid_team_names[0],
                                        "away": valid_team_names[1],
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
