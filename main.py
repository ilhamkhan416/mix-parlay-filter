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
    print("==================================================")
    print("🚀 STARTING MIX PARLAY DETAILED DEBUG PIPELINE")
    print("==================================================")

    # ----------------------------------------------------
    # STEP 1: SCRAPING ODDS
    # ----------------------------------------------------
    print("\n[STEP 1/4] Scraping Odds dari mainbolakaki.pro...")
    scraper = ParlayScraper()
    odds_data = await scraper.fetch_odds_data()
    print(f"  └─ Total Scraped Matches: {len(odds_data)}")

    if not odds_data:
        print("  ❌ [ABORT] Tidak ada data odds yang di-scrape. Pipeline dihentikan.")
        return []

    print(f"  🔍 [Sample Scraped Item #1]: {odds_data[0]}")

    # ----------------------------------------------------
    # STEP 2: FETCH API FIXTURES
    # ----------------------------------------------------
    print("\n[STEP 2/4] Fetching API-Football Fixtures...")
    wib_tz = zoneinfo.ZoneInfo("Asia/Jakarta")
    today_str = datetime.now(wib_tz).strftime("%Y-%m-%d")
    print(f"  └─ Target Date (WIB): {today_str}")

    api_key = os.getenv("FOOTBALL_API_KEY", FOOTBALL_API_KEY)
    print(f"  └─ Using API Key: {'***' + api_key[-4:] if api_key else 'MISSING'}")

    api_client = APIFootballClient(api_key=api_key)
    api_fixtures = api_client.get_fixtures_by_date(today_str)
    print(f"  └─ Total API Fixtures Returned: {len(api_fixtures)}")

    if not api_fixtures:
        print("  ❌ [ABORT] API-Football tidak mengembalikan fixture. Pipeline dihentikan.")
        return []

    print(f"  🔍 [Sample API Fixture #1]: {api_fixtures[0]}")

    # ----------------------------------------------------
    # STEP 3: ENTITY MATCHING (VECTORIZED TF-IDF)
    # ----------------------------------------------------
    print("\n[STEP 3/4] Matching Scraped Teams with Official API Entities...")
    matcher = EntityMatcher(time_window_minutes=TIME_WINDOW_MINUTES, threshold=FUZZY_THRESHOLD)
    matched_results = matcher.match(odds_data, api_fixtures)
    print(f"  └─ Total Successfully Matched Fixtures: {len(matched_results)}")

    if not matched_results:
        print("  ❌ [ABORT] Tidak ada pertandingan yang berhasil dicocokkan (Matched = 0).")
        return []

    # Print log untuk 5 pencocokan pertama
    print("  🔍 [Detail Matched Samples (Top 5)]:")
    for idx, m in enumerate(matched_results[:5], 1):
        o = m['odds_data']
        a = m['api_data']
        print(f"     {idx}. Scraped: '{o.get('home')} vs {o.get('away')}' ({o.get('selected_pick')})")
        print(f"        Matched API: '{a.get('home')} (ID:{a.get('home_id')}) vs {a.get('away')} (ID:{a.get('away_id')})' | League ID: {a.get('league_id')}")

    # ----------------------------------------------------
    # STEP 4: API INGESTION (H2H & STATS) & EVALUATION
    # ----------------------------------------------------
    print("\n[STEP 4/4] Ingesting Deep Stats & H2H from API-Football...")
    filtered_matched = []
    
    for idx, item in enumerate(matched_results, 1):
        odds_val = float(item['odds_data'].get('odds_value', 0.0))
        home_team = item['odds_data'].get('home')
        away_team = item['odds_data'].get('away')

        if not (MIN_ODDS <= odds_val <= MAX_ODDS):
            print(f"  [Skip Item #{idx}] {home_team} vs {away_team} -> Odds {odds_val} di luar range ({MIN_ODDS}-{MAX_ODDS})")
            continue

        api_item = item['api_data']
        home_id = api_item.get('home_id')
        away_id = api_item.get('away_id')
        league_id = api_item.get('league_id')

        print(f"\n  ► Processing [{idx}/{len(matched_results)}] {home_team} vs {away_team} (Odds: {odds_val})")
        print(f"     └─ Home ID: {home_id} | Away ID: {away_id} | League ID: {league_id}")

        # Ingest H2H
        h2h_data = []
        if home_id and away_id:
            h2h_data = api_client.get_h2h_matches(team_id_1=home_id, team_id_2=away_id, last_n=5)
            print(f"     └─ H2H Matches Found: {len(h2h_data)}")
            if h2h_data:
                print(f"        Sample H2H #1: {h2h_data[0]['teams']['home']['name']} {h2h_data[0]['score']['home']}-{h2h_data[0]['score']['away']} {h2h_data[0]['teams']['away']['name']}")

        item['api_data']['h2h'] = h2h_data

        # Ingest Stats
        stats_data = {}
        if home_id and league_id:
            stats_data = api_client.get_team_statistics(team_id=home_id, league_id=league_id)
            form_res = stats_data.get('form', 'N/A')
            print(f"     └─ Team Stats Fetched: Form = '{form_res}'")

        item['api_data']['stats'] = stats_data
        filtered_matched.append(item)

    print(f"\n  └─ Total Matches Passed to EV Evaluator: {len(filtered_matched)}")

    # ----------------------------------------------------
    # EVALUATE WITH FILTER ENGINE
    # ----------------------------------------------------
    print("\n[EVALUATION] Calculating Real Probabilities & Expected Values...")
    filter_engine = ParlayFilterEngine(min_odds=MIN_ODDS, max_odds=MAX_ODDS, min_ev=MIN_EXPECTED_VALUE)
    final_picks = filter_engine.evaluate(filtered_matched)

    print("\n==================================================")
    print(f"🎯 FINAL EVALUATION RESULTS ({len(final_picks)} PICKS):")
    print("==================================================")

    if not final_picks:
        print("  ⚠️ [!] Tidak ada pertandingan yang lolos kriteria EV.")
    else:
        for idx, pick in enumerate(final_picks, 1):
            print(f"  {idx}. {pick['match']}")
            print(f"     👉 PASANG: {pick['pick']} ({pick['pick_type']}) | Odds: {pick['selected_odds']}")
            print(f"     📈 Form: {pick['form_history']} | Est. Win: {pick['estimated_real_prob']} | EV: {pick['expected_value']}")
            print(f"     💡 Rationale: {pick['rationale']}\n")

    # ----------------------------------------------------
    # WHATSAPP NOTIFICATION
    # ----------------------------------------------------
    print("[NOTIFIER] Sending WhatsApp Notification via Fonnte...")
    send_whatsapp_parlay_picks(final_picks)

    print("\n✅ PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    return final_picks


if __name__ == "__main__":
    asyncio.run(run_pipeline())
