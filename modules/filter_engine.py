from typing import Dict, List

class ParlayFilterEngine:
    def __init__(self, min_odds: float = 1.20, max_odds: float = 1.80, min_ev: float = -0.02):
        self.min_odds = min_odds
        self.max_odds = max_odds
        self.min_ev = min_ev

    @staticmethod
    def calculate_implied_probability(odds: float) -> float:
        if odds <= 1.0:
            return 0.0
        return round(1.0 / odds, 4)

    @staticmethod
    def _parse_form_score(form_str: str) -> float:
        if not form_str:
            return 0.50
        points = 0.0
        clean_form = form_str.upper()[-5:]
        for res in clean_form:
            if res == 'W':
                points += 1.0
            elif res == 'D':
                points += 0.5
        return points / len(clean_form) if clean_form else 0.50

    def estimate_real_probability(self, team_stats: Dict, h2h_matches: List[Dict], is_home: bool = True) -> float:
        form_rate = self._parse_form_score(team_stats.get('form', 'WWDDL'))

        h2h_wins = 0
        total_h2h = len(h2h_matches[:5]) if h2h_matches else 0
        
        if total_h2h > 0:
            for match in h2h_matches[:5]:
                teams = match.get('teams', {})
                winner = teams.get('home', {}) if is_home else teams.get('away', {})
                if winner.get('winner') is True:
                    h2h_wins += 1
            h2h_rate = h2h_wins / total_h2h
        else:
            h2h_rate = form_rate

        venue_stats = team_stats.get('fixtures', {}).get('wins', {})
        played = venue_stats.get('home' if is_home else 'away', 0)
        wins = venue_stats.get('home' if is_home else 'away', 0)
        venue_rate = (wins / played) if played > 0 else form_rate

        # Bobot kalkulasi probabilitas riil: Form (40%), H2H (35%), Venue (25%)
        real_prob = (0.40 * form_rate) + (0.35 * h2h_rate) + (0.25 * venue_rate)
        return round(real_prob, 4)

    def calculate_expected_value(self, odds: float, estimated_prob: float) -> float:
        net_profit = odds - 1.0
        prob_loss = 1.0 - estimated_prob
        return round((estimated_prob * net_profit) - (prob_loss * 1.0), 4)

    def evaluate(self, matched_data: List[Dict]) -> List[Dict]:
        high_prob_picks = []

        for item in matched_data:
            odds_info = item.get('odds_data', {})
            api_info = item.get('api_data', {})
            
            odds_val = float(odds_info.get('odds_value', 0.0))
            if not (self.min_odds <= odds_val <= self.max_odds):
                continue

            h2h_data = api_info.get('h2h', [])
            team_stats = api_info.get('stats', {})
            
            # 1. BACA DINAMIS TIM MANA YANG MEMILIKI ODDS TERSEBUT (HOME ATAU AWAY)
            pick_type = odds_info.get('pick_type', 'Home Win')
            selected_pick = odds_info.get('selected_pick')
            
            is_home_pick = (pick_type == 'Home Win')

            if not selected_pick:
                selected_pick = odds_info.get('home' if is_home_pick else 'away', api_info.get('home' if is_home_pick else 'away', 'Team'))

            # 2. HITUNG PROBABILITAS BERDASARKAN SISI TIM YANG DIPILIH
            estimated_real_prob = self.estimate_real_probability(team_stats, h2h_data, is_home=is_home_pick)
            implied_prob = self.calculate_implied_probability(odds_val)
            ev = self.calculate_expected_value(odds_val, estimated_real_prob)

            if ev < self.min_ev:
                continue

            home_team = odds_info.get('home', api_info.get('home', 'Home Team'))
            away_team = odds_info.get('away', api_info.get('away', 'Away Team'))

            high_prob_picks.append({
                "match": f"{home_team} vs {away_team}",
                "pick": selected_pick,               # Mengembalikan nama tim yang benar (misal: Germany)
                "pick_type": pick_type,               # Mengembalikan "Away Win" atau "Home Win"
                "selected_odds": odds_val,
                "implied_probability": f"{round(implied_prob * 100, 2)}%",
                "estimated_real_prob": f"{round(estimated_real_prob * 100, 2)}%",
                "expected_value": f"{'+' if ev > 0 else ''}{round(ev * 100, 2)}%",
                "league": api_info.get('league_name', 'Unknown')
            })

        return high_prob_picks
