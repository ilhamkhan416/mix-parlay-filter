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

    def get_team_statistics(self, team_id: int, league_id: int, season: int = None) -> Dict:
        from datetime import datetime
        if not season:
            season = datetime.now().year - 1

        cache_file = os.path.join(self.cache_dir, f"stats_{team_id}_{league_id}_{season}.json")

        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                return json.load(f)

        params = {'team': team_id, 'league': league_id, 'season': season}
        data = {}
        try:
            response = requests.get(f"{self.base_url}/teams/statistics", headers=self.headers, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json().get('response', {})
        except Exception as e:
            print(f"❌ Error fetching stats for team {team_id}: {e}")

        raw_form = data.get("form", "")

        # Fallback 1: Coba season alternatif (2026 / international)
        if not raw_form:
            try:
                alt_params = {'team': team_id, 'league': league_id, 'season': season + 1}
                res_alt = requests.get(f"{self.base_url}/teams/statistics", headers=self.headers, params=alt_params, timeout=15)
                if res_alt.status_code == 200:
                    data_alt = res_alt.json().get('response', {})
                    raw_form = data_alt.get("form", "")
            except Exception:
                pass

        # Fallback 2: Ambil 5 laga terakhir tim jika data liga kosong
        if not raw_form:
            try:
                fix_resp = requests.get(
                    f"{self.base_url}/fixtures", 
                    headers=self.headers, 
                    params={'team': team_id, 'last': 5}, 
                    timeout=15
                )
                if fix_resp.status_code == 200:
                    last_fixtures = fix_resp.json().get('response', [])
                    form_chars = []
                    for fix in last_fixtures:
                        home_id = fix['teams']['home']['id']
                        winner_home = fix['teams']['home']['winner']
                        winner_away = fix['teams']['away']['winner']
                        
                        if (team_id == home_id and winner_home) or (team_id != home_id and winner_away):
                            form_chars.append('W')
                        elif winner_home is None or winner_away is None:
                            form_chars.append('D')
                        else:
                            form_chars.append('L')
                    raw_form = "".join(form_chars)
            except Exception as ex:
                print(f"⚠ Fallback fixture fetch error: {ex}")

        formatted = {
            "form": raw_form,
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
