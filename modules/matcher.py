from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from utils.text_cleaner import clean_team_name

class EntityMatcher:
    def __init__(self, time_window_minutes=180, threshold=0.15):
        self.time_window = time_window_minutes
        self.threshold = threshold

    def match(self, odds_matches: list, api_fixtures: list) -> list:
        if not odds_matches or not api_fixtures:
            return []

        odds_match_strings = [
            f"{clean_team_name(m['home'])} {clean_team_name(m['away'])}" 
            for m in odds_matches
        ]
        api_match_strings = [
            f"{clean_team_name(f['home'])} {clean_team_name(f['away'])}" 
            for f in api_fixtures
        ]

        all_strings = list(set(odds_match_strings + api_match_strings))
        all_strings = [s for s in all_strings if s.strip()]

        if not all_strings:
            return []

        vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 3))
        vectorizer.fit(all_strings)

        vec_odds = vectorizer.transform(odds_match_strings)
        vec_api = vectorizer.transform(api_match_strings)

        sim_matrix = cosine_similarity(vec_odds, vec_api)

        matched_results = []

        for i, odds in enumerate(odds_matches):
            best_idx = -1
            best_score = 0.0

            for j, api in enumerate(api_fixtures):
                score = float(sim_matrix[i, j])

                if score >= self.threshold and score > best_score:
                    # Validasi Time Window (Abaikan hanya jika kickoff memakai jam fallback T20:00:00)
                    odds_iso = odds.get('kickoff_iso', '')
                    api_iso = api.get('kickoff_iso', '')

                    if odds_iso and api_iso and not odds_iso.endswith('T20:00:00'):
                        try:
                            odds_time = datetime.fromisoformat(odds_iso)
                            api_time = datetime.fromisoformat(api_iso)
                            time_diff = abs((odds_time - api_time).total_seconds()) / 60.0
                            
                            # Jika selisih waktu melebihi batas window, lewati matching
                            if time_diff > self.time_window:
                                continue
                        except (ValueError, KeyError):
                            pass

                    best_score = score
                    best_idx = j

            if best_idx != -1:
                matched_results.append({
                    "odds_data": odds,
                    "api_data": api_fixtures[best_idx],
                    "confidence_score": round(best_score * 100, 2)
                })

        return matched_results
