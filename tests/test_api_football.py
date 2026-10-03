import os
import json
import pytest
from unittest.mock import patch
from modules.api_football import APIFootballClient

@pytest.fixture
def api_client(tmp_path):
    """ Membuat client API-Football menggunakan direktori cache sementara """
    return APIFootballClient(api_key="TEST_KEY", cache_dir=str(tmp_path))

def test_get_h2h_matches_with_mock_api(api_client):
    mock_response = {
        "response": [
            {
                "fixture": {"id": 1001, "date": "2026-10-04T20:00:00+00:00"},
                "league": {"name": "Bundesliga"},
                "teams": {
                    "home": {"id": 157, "name": "Bayern Munich", "winner": True},
                    "away": {"id": 168, "name": "Bayer Leverkusen", "winner": False}
                },
                "goals": {"home": 3, "away": 1}
            }
        ]
    }

    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        h2h = api_client.get_h2h_matches(team_id_1=157, team_id_2=168, last_n=5)

        assert len(h2h) == 1
        assert h2h[0]["teams"]["home"]["name"] == "Bayern Munich"
        assert h2h[0]["teams"]["home"]["winner"] is True
        assert h2h[0]["score"]["home"] == 3

def test_h2h_cache_creation(api_client, tmp_path):
    # Menyediakan mock response yang valid agar data ter-format dan file cache dibuat
    mock_response = {
        "response": [
            {
                "fixture": {"id": 2002, "date": "2026-10-04T20:00:00+00:00"},
                "league": {"name": "Premier League"},
                "teams": {
                    "home": {"id": 10, "name": "Team A", "winner": True},
                    "away": {"id": 20, "name": "Team B", "winner": False}
                },
                "goals": {"home": 1, "away": 0}
            }
        ]
    }
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        api_client.get_h2h_matches(team_id_1=10, team_id_2=20)
        
        cache_file = tmp_path / "h2h_10_20.json"
        assert os.path.exists(cache_file) is True
