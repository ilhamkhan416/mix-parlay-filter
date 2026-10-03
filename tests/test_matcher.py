import pytest
from modules.matcher import EntityMatcher

@pytest.fixture
def matcher():
    # Menggunakan time_window 30 menit untuk unit testing
    return EntityMatcher(time_window_minutes=30, threshold=0.20)

def test_exact_and_fuzzy_team_matching(matcher):
    odds_data = [{"home": "Bayern München", "away": "Leverkusen", "kickoff_iso": "2026-10-04T22:30:00"}]
    api_data = [{"home": "FC Bayern Munich", "away": "Bayer 04 Leverkusen", "kickoff_iso": "2026-10-04T22:30:00", "league_name": "Bundesliga"}]

    matched = matcher.match(odds_data, api_data)

    assert len(matched) == 1
    assert matched[0]["confidence_score"] >= 20.0
    assert matched[0]["api_data"]["home"] == "FC Bayern Munich"

def test_match_fails_on_time_window_exceeded(matcher):
    # Selisih jam 22:30 vs 23:45 adalah 75 menit (> 30 menit), harus mengembalikan 0 match
    odds_data = [{"home": "Arsenal", "away": "Chelsea", "kickoff_iso": "2026-10-04T22:30:00"}]
    api_data = [{"home": "Arsenal FC", "away": "Chelsea FC", "kickoff_iso": "2026-10-04T23:45:00"}]

    matched = matcher.match(odds_data, api_data)

    assert len(matched) == 0
