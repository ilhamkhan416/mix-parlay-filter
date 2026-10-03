import os
import asyncio
from datetime import datetime
import zoneinfo

from config import (
    FOOTBALL_API_KEY, 
    MIN_ODDS, 
    MAX_ODDS, 
    MIN_EXPECTED_VALUE, 
    TIME_WINDOW_MINUTES, 
    FUZZY_THRESHOLD
)
from modules.scraper import ParlayScraper
from modules.api_football import APIFootballClient
from modules.matcher import EntityMatcher
from modules.filter_engine import ParlayFilterEngine


async def run_pipeline():
    print("🚀 Running Mix Parlay High Probability Pipeline...")

    # 1. Web Scraping Odds dari Situs Parlay
    print("\n[1/4] Scraping Odds dari mainbolakaki.pro...")
    scraper = ParlayScraper()
    odds_data = await scraper.fetch_odds_data()
    print(f" -> Berhasil mengikis {len(odds_data)} pertandingan dari situs.")

    # 2. Ambil Jadwal Resmi dari API-Football (Menggunakan Zona Waktu WIB)
    print("\n[2/4] Fetching API-Football Fixtures...")
    wib_tz = zoneinfo.ZoneInfo("Asia/Jakarta")
    today_str = datetime.now(wib_tz).strftime("%Y-%m-%d")
    print(f" -> Tanggal Target (WIB): {today_str}")

    api_key = os.getenv("FOOTBALL_API_KEY", FOOTBALL_API_KEY)
    api_client = APIFootballClient(api_key=api_key)
    api_fixtures = api_client.get_fixtures_by_date(today_str)
    print(f" -> Berhasil mengambil {len(api_fixtures)} pertandingan resmi dari API.")

    # 3. Pencocokan Entitas Tim & Pengayaan Data H2H
    print("\n[3/4] Matching Entities (Time Window + N-Gram TF-IDF)...")
    matcher = EntityMatcher(time_window_minutes=TIME_WINDOW_MINUTES, threshold=FUZZY_THRESHOLD)
    matched_results = matcher.match(odds_data, api_fixtures)
    
    # Enrich data dengan Head-to-Head (H2H) untuk setiap pertandingan yang berhasil cocok
    for item in matched_results:
        api_item = item['api_data']
        item['api_data']['h2h'] = api_client.get_h2h_matches(
            team_id_1=api_item['home_id'],
            team_id_2=api_item['away_id'],
            last_n=5
        )
    print(f" -> Berhasil mencocokkan & memperkaya data {len(matched_results)} pertandingan.")

    # 4. Filter Matematika +EV & High Probability
    print("\n[4/4] Evaluating +EV & High Probability Filter...")
    filter_engine = ParlayFilterEngine(min_odds=MIN_ODDS, max_odds=MAX_ODDS, min_ev=MIN_EXPECTED_VALUE)
    final_picks = filter_engine.evaluate(matched_results)

    print("\n🎯 FINAL HIGH PROBABILITY PARLAY PICKS:")
    if not final_picks:
        print("  [!] Tidak ada pertandingan yang memenuhi kriteria ketat +EV hari ini.")
    else:
        for pick in final_picks:
            print(
                f"  [✓] {pick['match']} | Odds: {pick['selected_odds']} | "
                f"Est. Win: {pick['estimated_real_prob']} | EV: {pick['expected_value']}"
            )

    return final_picks


if __name__ == "__main__":
    asyncio.run(run_pipeline())
