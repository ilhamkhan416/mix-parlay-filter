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

                ignored_keywords = ["soccer", "mix parlay", "today", "select league", "odds", "home", "away", "time", "draw"]

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

                                team_pairs = []
                                i = 0
                                while i < len(lines):
                                    item = lines[i]
                                    
                                    # Abaikan label status/jam
                                    if item.upper() in ["LIVE", "TODAY", "CANCEL"] or item.replace(":", "").isdigit():
                                        i += 1
                                        continue

                                    # Cek jika baris ini merupakan nama tim
                                    if len(item) > 2 and item.lower() not in ignored_keywords:
                                        team_name = item
                                        team_odds = None

                                        # Cari odds milik tim tersebut di baris persis setelah nama tim
                                        for lookahead in range(1, 3):
                                            if i + lookahead < len(lines):
                                                possible_odds = lines[i + lookahead].replace(",", ".")
                                                try:
                                                    val = float(possible_odds)
                                                    if 1.01 <= val <= 10.0:
                                                        team_odds = val
                                                        break
                                                except ValueError:
                                                    pass

                                        team_pairs.append({"name": team_name, "odds": team_odds})
                                    i += 1

                                # Pastikan terdeteksi minimal 2 tim (Home dan Away)
                                if len(team_pairs) >= 2:
                                    home_info = team_pairs[0]
                                    away_info = team_pairs[1]

                                    # Default panggil Home, tapi jika Odds Away lebih rendah (favorit) / valid, ambil Away
                                    selected_team = home_info["name"]
                                    selected_odds = home_info["odds"]
                                    pick_type = "Home Win"

                                    # Jika odds Away tersedia dan bernilai favorit/lebih rendah dari Home
                                    if away_info["odds"] and (not home_info["odds"] or away_info["odds"] < home_info["odds"]):
                                        selected_team = away_info["name"]
                                        selected_odds = away_info["odds"]
                                        pick_type = "Away Win"

                                    if selected_odds:
                                        scraped_matches.append({
                                            "home": home_info["name"],
                                            "away": away_info["name"],
                                            "selected_pick": selected_team,
                                            "pick_type": pick_type,
                                            "odds_value": selected_odds,
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
