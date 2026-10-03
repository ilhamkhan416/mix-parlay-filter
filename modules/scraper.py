import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

class ParlayScraper:
    def __init__(self, target_url="https://mainbolakaki.pro/_view/odds4.aspx"):
        self.url = target_url

    async def fetch_odds_data(self) -> list:
        scraped_matches = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Anti-bot User Agent
            await page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            
            try:
                await page.goto(self.url, wait_until="networkidle", timeout=30000)
                rows = await page.query_selector_all("table tr.match-row")
                
                for row in rows:
                    home = await row.eval_on_selector(".home-team", "el => el.innerText")
                    away = await row.eval_on_selector(".away-team", "el => el.innerText")
                    odds = await row.eval_on_selector(".odds-val", "el => el.innerText")
                    time_str = await row.eval_on_selector(".match-time", "el => el.innerText")
                    
                    scraped_matches.append({
                        "home": home.strip(),
                        "away": away.strip(),
                        "odds_value": float(odds.strip()),
                        "kickoff_iso": datetime.now().strftime(f"%Y-%m-%dT{time_str.strip()}:00")
                    })
            except Exception as e:
                print(f"❌ Scraper Warning/Error: {e}")
            finally:
                await browser.close()
                
        return scraped_matches
