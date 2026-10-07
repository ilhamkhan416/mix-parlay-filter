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
                await page.wait_for_timeout(3000)

                wib_tz = zoneinfo.ZoneInfo("Asia/Jakarta")
                today_date_str = datetime.now(wib_tz).strftime("%Y-%m-%d")

                ignored_keywords = ["soccer", "mix parlay", "today", "select league", "odds", "home", "away", "time", "draw"]

                for frame in page.frames:
                    try:
                        rows = await frame.query_selector_all("tr")
                        for row in rows:
                            cells = await row.query_selector_all("td")
                            
                            # Jika struktur berbasis sel tabel (td)
                            if len(cells) >= 5:
                                time_txt = (await cells[0].inner_text()).strip()
                                home_txt = (await cells[1].inner_text()).strip()
                                away_txt = (await cells[2].inner_text()).strip()
                                home_odds_txt = (await cells[3].inner_text()).replace(",", ".").strip()
                                away_odds_txt = (await cells[4].inner_text()).replace(",", ".").strip()

                                if any(kw in home_txt.lower() or kw in away_txt.lower() for kw in ignored_keywords):
                                    continue

                                try:
                                    h_odds = float(home_odds_txt) if home_odds_txt else None
                                    a_odds = float(away_odds_txt) if away_odds_txt else None
                                except ValueError:
                                    continue

                                if not h_odds and not a_odds:
                                    continue

                                # Evaluasi Dinamis Home Win vs Away Win
                                if h_odds and a_odds:
                                    if h_odds <= a_odds:
                                        selected_team = home_txt
                                        selected_odds = h_odds
                                        pick_type = "Home Win"
                                    else:
                                        selected_team = away_txt
                                        selected_odds = a_odds
                                        pick_type = "Away Win"
                                elif h_odds:
                                    selected_team = home_txt
                                    selected_odds = h_odds
                                    pick_type = "Home Win"
                                else:
                                    selected_team = away_txt
                                    selected_odds = a_odds
                                    pick_type = "Away Win"

                                match_time = time_txt if len(time_txt) == 5 and ":" in time_txt else "20:00"

                                scraped_matches.append({
                                    "home": home_txt,
                                    "away": away_txt,
                                    "selected_pick": selected_team,
                                    "pick_type": pick_type,
                                    "odds_value": selected_odds,
                                    "kickoff_iso": f"{today_date_str}T{match_time}:00"
                                })
                            
                            # Fallback jika struktur berupa text-lines tunggal di dalam 1 baris
                            else:
                                text_content = await row.inner_text()
                                lines = [line.strip() for line in text_content.split("\n") if line.strip()]

                                if len(lines) >= 4:
                                    if any(kw in lines[0].lower() or kw in lines[1].lower() for kw in ignored_keywords):
                                        continue

                                    teams = []
                                    odds = []

                                    for line in lines:
                                        cleaned = line.replace(",", ".")
                                        try:
                                            val = float(cleaned)
                                            if 1.01 <= val <= 15.0:
                                                odds.append(val)
                                        except ValueError:
                                            if len(line) > 2 and line.upper() not in ["LIVE", "TODAY", "CANCEL"] and not line.replace(":", "").isdigit():
                                                teams.append(line)

                                    if len(teams) >= 2 and len(odds) >= 2:
                                        home_name, away_name = teams[0], teams[1]
                                        h_odds, a_odds = odds[0], odds[1]

                                        if h_odds <= a_odds:
                                            selected_team = home_name
                                            selected_odds = h_odds
                                            pick_type = "Home Win"
                                        else:
                                            selected_team = away_name
                                            selected_odds = a_odds
                                            pick_type = "Away Win"

                                        scraped_matches.append({
                                            "home": home_name,
                                            "away": away_name,
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
