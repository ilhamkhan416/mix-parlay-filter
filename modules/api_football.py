import os
import json
import requests
from typing import Dict, List

class APIFootballClient:
    def __init__(self, api_key: str, cache_dir: str = "data/cache"):
        self.api_key = api_key
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {'x-apisports-key': self.api_key}
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def get_fixtures_by_date(self, date_str: str) -> List[Dict]:
        cache_file = os.path.join(self.cache_dir, f"fixtures_{date_str}.json")
        
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                return json.load(f)

        params = {'date': date_str}
        try:
            response = requests.get(f"{self.base_url}/fixtures", headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            res_json = response.json()

            if res_json.get('errors'):
                print(f"  [API Debug Error]: {res_json.get('errors')}")

            data = res_json.get('response', [])
        except Exception as e:
            print(f"❌ Error fetching fixtures: {e}")
            return []

        formatted = []
        for item in data:
            formatted.append({
                "fixture_id": item['fixture']['id'],
                "home": item['teams']['home']['name'],
                "home_id": item['teams']['home']['id'],
                "away": item['teams']['away']['name'],
                "away_id": item['teams']['away']['id'],
                "kickoff_iso": item['fixture']['date'][:19],
                "league": item['league']['name'],
                "league_id": item['league']['id']
            })

        if formatted:
            with open(cache_file, "w") as f:
                json.dump(formatted, f, indent=2)

        return formatted

    def get_h2h_matches(self, team_id_1: int, team_id_2: int, last_n: int = 5) -> List[Dict]:
        sorted_ids = sorted([team_id_1, team_id_2])
        cache_file = os.path.join(self.cache_dir, f"h2h_{sorted_ids[0]}_{sorted_ids[1]}.json")

        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                return json.load(f)[:last_n]

        params = {'h2h': f"{team_id_1}-{team_id_2}", 'last': last_n}
        try:
            response = requests.get(f"{self.base_url}/fixtures/headtohead", headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            res_json = response.json()
            data = res_json.get('response', [])
        except Exception as e:
            print(f"❌ Error fetching H2H: {e}")
            return []

        formatted = []
        for item in data:
            formatted.append({
                "fixture_id": item['fixture']['id'],
                "date": item['fixture']['date'][:10],
                "league": item['league']['name'],
                "teams": {
                    "home": {"id": item['teams']['home']['id'], "name": item['teams']['home']['name'], "winner": item['teams']['home']['winner']},
                    "away": {"id": item['teams']['away']['id'], "name": item['teams']['away']['name'], "winner": item['teams']['away']['winner']}
                },
                "score": item['goals']
            })

        if formatted:
            with open(cache_file, "w") as f:
                json.dump(formatted, f, indent=2)

        return formatted[:last_n]

    def get_team_statistics(self, team_id: int, league_id: int, season: int) -> Dict:
        """
        Mengambil data statistik tim (form, rekor kandang/tandang, dsb.) dari API-Football.
        """
        cache_file = os.path.join(self.cache_dir, f"stats_{team_id}_{league_id}_{season}.json")

        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                return json.load(f)

        params = {
            'team': team_id,
            'league': league_id,
            'season': season
        }
        try:
            response = requests.get(f"{self.base_url}/teams/statistics", headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            res_json = response.json()
            data = res_json.get('response', {})
        except Exception as e:
            print(f"❌ Error fetching team stats: {e}")
            return {}

        formatted = {
            "form": data.get("form", ""),
            "fixtures": {
                "played": data.get("fixtures", {}).get("played", {}),
                "wins": data.get("fixtures", {}).get("wins", {}),
                "draws": data.get("fixtures", {}).get("draws", {}),
                "loses": data.get("fixtures", {}).get("loses", {})
            }
        }

        if formatted["form"]:
            with open(cache_file, "w") as f:
                json.dump(formatted, f, indent=2)

        return formatted
