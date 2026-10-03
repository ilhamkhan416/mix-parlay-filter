import os
import asyncio
from datetime import datetime
from config import FOOTBALL_API_KEY, MIN_ODDS, MAX_ODDS, MIN_EXPECTED_VALUE, TIME_WINDOW_MINUTES, FUZZY_THRESHOLD
from modules.scraper import ParlayScraper
from modules.api_football import APIFootballClient
from modules.matcher import EntityMatcher
from modules.filter_engine import ParlayFilterEngine

async def run_pipeline():
    print("🚀 Running Mix Parlay High Probability Pipeline...")

    # Step 1: Web Scraping Odds
    print("\n[1/4] Scraping Odds from mainbolakaki.pro...")
    scraper = ParlayScraper()
    odds_data = await scraper.fetch_odds_data()
    print(f" -> Scraped {len(odds_data)} matches.")

    # Step 2: Fetch Official Fixtures API-Football
    print("\n[2/4] Fetching API-Football Fixtures...")
    today_str = datetime.now().strftime("%Y-%m-%d")
    api_client = APIFootballClient(api_key=FOOTBALL_API_KEY)
    api_fixtures = api_client.get_fixtures_by_date(today_str)
    print(f" -> Fetched {len(api_fixtures)} official fixtures.")

    # Step 3: Match Entities & Ingest H2H
    print("\n[3/4] Matching Entities (Time Window + N-Gram)...")
    matcher = EntityMatcher(time_window_minutes=TIME_WINDOW_MINUTES, threshold=FUZZY_THRESHOLD)
    matched_results = matcher.match(odds_data, api_fixtures)
    
    # Ingest Data H2H
    for item in matched_results:
        api_item = item['api_data']
        item['api_data']['h2h'] = api_client.get_h2h_matches(
            team_id_1=api_item['home_id'],
            team_id_2=api_item['away_id'],
            last_n=5
        )
    print(f" -> Successfully matched & enriched {len(matched_results)} matches.")

    # Step 4: +EV & Parlay Filter Engine
    print("\n[4/4] Evaluating +EV & High Probability Filter...")
    filter_engine = ParlayFilterEngine(min_odds=MIN_ODDS, max_odds=MAX_ODDS, min_ev=MIN_EXPECTED_VALUE)
    final_picks = filter_engine.evaluate(matched_results)

    print("\n🎯 FINAL HIGH PROBABILITY PARLAY PICKS:")
    if not final_picks:
        print("  [!] No matches passed the strict +EV criteria today.")
    for pick in final_picks:
        print(f"  [✓] {pick['match']} | Odds: {pick['selected_odds']} | Est. Win: {pick['estimated_real_prob']} | EV: {pick['expected_value']}")

if __name__ == "__main__":
    asyncio.run(run_pipeline())
