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
from modules.wa_notifier import send_whatsapp_parlay_picks


async def run_pipeline():
    print("🚀 Running Mix Parlay High Probability Pipeline...")

    # Step 1: Web Scraping Odds dari Situs Parlay
    print("\n[1/4] Scraping Odds dari mainbolakaki.pro...")
    scraper = ParlayScraper()
    odds_data = await scraper.fetch_odds_data()
    print(f" -> Berhasil mengikis {len(odds_data)} pertandingan dari situs.")

    if not odds_data:
        print("  [!] Tidak ada data odds yang di-scrape. Menghentikan pipeline.")
        return []

    # Step 2: Ambil Jadwal Resmi dari API-Football (Zona Waktu WIB)
    print("\n[2/4] Fetching API-Football Fixtures...")
    wib_tz = zoneinfo.ZoneInfo("Asia/Jakarta")
    today_str = datetime.now(wib_tz).strftime("%Y-%m-%d")
    print(f" -> Tanggal Target (WIB): {today_str}")

    api_key = os.getenv("FOOTBALL_API_KEY", FOOTBALL_API_KEY)
    api_client = APIFootballClient(api_key=api_key)
    api_fixtures = api_client.get_fixtures_by_date(today_str)
    print(f" -> Berhasil mengambil {len(api_fixtures)} pertandingan resmi dari API.")

    if not api_fixtures:
        print("  [!] Tidak ada jadwal pertandingan resmi dari API. Menghentikan pipeline.")
        return []

    # Sampel Debug untuk Memantau Struktur Data
    print(f"  🔍 [Debug Sample Scraped]: {odds_data[0]}")
    print(f"  🔍 [Debug Sample API]: {api_fixtures[0]}")

    # Step 3: Pencocokan Entitas Tim (Vectorized TF-IDF)
    print("\n[3/4] Matching Entities (Vectorized TF-IDF)...")
    matcher = EntityMatcher(time_window_minutes=TIME_WINDOW_MINUTES, threshold=FUZZY_THRESHOLD)
    matched_results = matcher.match(odds_data, api_fixtures)
    print(f" -> Berhasil mencocokkan {len(matched_results)} pertandingan.")

    # Step 4: Selective H2H Ingestion & +EV Filtering
    print("\n[4/4] Ingesting H2H & Evaluating +EV Filter...")
    filtered_matched = []
    
    for item in matched_results:
        odds_val = float(item['odds_data'].get('odds_value', 0.0))
        if MIN_ODDS <= odds_val <= MAX_ODDS:
            api_item = item['api_data']
            # Ambil data H2H secara selektif
            item['api_data']['h2h'] = api_client.get_h2h_matches(
                team_id_1=api_item['home_id'],
                team_id_2=api_item['away_id'],
                last_n=5
            )
            filtered_matched.append(item)

    print(f" -> {len(filtered_matched)} pertandingan masuk dalam evaluasi EV mendalam.")

    # Evaluasi menggunakan Filter Engine Dinamis
    filter_engine = ParlayFilterEngine(min_odds=MIN_ODDS, max_odds=MAX_ODDS, min_ev=MIN_EXPECTED_VALUE)
    final_picks = filter_engine.evaluate(filtered_matched)

    print("\n🎯 FINAL HIGH PROBABILITY PARLAY PICKS:")
    if not final_picks:
        print("  [!] Tidak ada pertandingan yang memenuhi kriteria ketat +EV hari ini.")
    else:
        for pick in final_picks:
            print(
                f"  [✓] LAGA: {pick['match']} | "
                f"👉 PASANG: {pick['pick']} | "
                f"Odds: {pick['selected_odds']} | "
                f"Est. Win: {pick['estimated_real_prob']} | "
                f"EV: {pick['expected_value']}"
            )

    # Pengiriman Notifikasi Otomatis ke WhatsApp
    send_whatsapp_parlay_picks(final_picks)

    return final_picks


if __name__ == "__main__":
    asyncio.run(run_pipeline())
