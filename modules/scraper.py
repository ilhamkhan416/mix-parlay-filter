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
            # Launch Chromium dengan opsi stabilitas untuk lingkungan Linux/GitHub Actions
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-accelerated-2d-canvas",
                    "--disable-gpu"
                ]
            )
            
            # Buat konteks browser dengan User-Agent & Viewport seperti browser desktop asli
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1366, "height": 768},
                locale="id-ID",
                timezone_id="Asia/Jakarta"
            )
            
            page = await context.new_page()
            
            try:
                # Navigasi ke target URL
                print(f"  [Scraper] Navigating to {self.url}...")
                response = await page.goto(self.url, wait_until="domcontentloaded", timeout=60000)
                
                if response and response.status != 200:
                    print(f"  [Scraper] Warning: Server returned status code {response.status}")

                # Beri jeda 5 detik untuk memastikan skrip AJAX/JavaScript odds selesai merefresh tabel
                await page.wait_for_timeout(5000)

                # Ambil semua elemen baris tabel pertandingan
                # Mendukung elemen tr standar maupun class match-row
                rows = await page.query_selector_all("table tr")
                
                wib_tz = zoneinfo.ZoneInfo("Asia/Jakarta")
                today_date_str = datetime.now(wib_tz).strftime("%Y-%m-%d")

                for row in rows:
                    # Ambil teks mentah dari setiap baris
                    text_content = await row.inner_text()
                    lines = [line.strip() for line in text_content.split("\n") if line.strip()]

                    # Tentukan elemen selector spesifik jika ada
                    home_el = await row.query_selector(".home-team, td.home, td:nth-child(2)")
                    away_el = await row.query_selector(".away-team, td.away, td:nth-child(4)")
                    odds_el = await row.query_selector(".odds-val, td.odds, td:nth-child(5)")
                    time_el = await row.query_selector(".match-time, td.time, td:nth-child(1)")

                    if home_el and away_el and odds_el:
                        home_text = (await home_el.inner_text()).strip()
                        away_text = (await away_el.inner_text()).strip()
                        odds_raw = (await odds_el.inner_text()).strip()
                        time_raw = (await time_el.inner_text()).strip() if time_el else "20:00"

                        # Validasi nilai odds (harus berupa angka/desimal)
                        try:
                            odds_val = float(odds_raw.replace(",", "."))
                        except ValueError:
                            continue

                        # Bersihkan format waktu kick-off (HH:MM)
                        clean_time = time_raw if ":" in time_raw else "20:00"
                        if len(clean_time) == 4 and clean_time[1] == ":":
                            clean_time = "0" + clean_time

                        kickoff_iso = f"{today_date_str}T{clean_time[:5]}:00"

                        if home_text and away_text and odds_val > 1.0:
                            scraped_matches.append({
                                "home": home_text,
                                "away": away_text,
                                "odds_value": odds_val,
                                "kickoff_iso": kickoff_iso
                            })

            except Exception as e:
                print(f"❌ [Scraper Error]: {e}")
            finally:
                await context.close()
                await browser.close()
                
        return scraped_matches


# ==========================================
# SIMULASI PENGUJIAN LOKAL
# ==========================================
if __name__ == "__main__":
    async def main():
        scraper = ParlayScraper()
        results = await scraper.fetch_odds_data()
        print(f"\n✅ Total Scraped Matches: {len(results)}")
        for m in results[:5]:
            print(f"  - {m['home']} vs {m['away']} | Odds: {m['odds_value']} | Kickoff: {m['kickoff_iso']}")

    asyncio.run(main())
