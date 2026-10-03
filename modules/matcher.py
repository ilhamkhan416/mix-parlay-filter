from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from utils.text_cleaner import clean_team_name

class EntityMatcher:
    def __init__(self, time_window_minutes=180, threshold=0.35):
        self.time_window = time_window_minutes
        self.threshold = threshold

    def match(self, odds_matches: list, api_fixtures: list) -> list:
        if not odds_matches or not api_fixtures:
            return []

        odds_homes = [clean_team_name(m['home']) for m in odds_matches]
        odds_aways = [clean_team_name(m['away']) for m in odds_matches]
        
        api_homes = [clean_team_name(f['home']) for f in api_fixtures]
        api_aways = [clean_team_name(f['away']) for f in api_fixtures]

        all_names = list(set(odds_homes + odds_aways + api_homes + api_aways))
        if not all_names:
            return []

        vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2, 3))
        vectorizer.fit(all_names)

        vec_odds_h = vectorizer.transform(odds_homes)
        vec_odds_a = vectorizer.transform(odds_aways)
        vec_api_h = vectorizer.transform(api_homes)
        vec_api_a = vectorizer.transform(api_aways)

        sim_h = cosine_similarity(vec_odds_h, vec_api_h)
        sim_a = cosine_similarity(vec_odds_a, vec_api_a)

        matched_results = []

        for i, odds in enumerate(odds_matches):
            best_idx = -1
            best_score = 0.0

            for j, api in enumerate(api_fixtures):
                total_score = float((sim_h[i, j] + sim_a[i, j]) / 2.0)

                if total_score >= self.threshold and total_score > best_score:
                    # Validasi Time Window hanya jika jam kick-off bukan jam default/fallback T20:00:00
                    odds_iso = odds.get('kickoff_iso', '')
                    if not odds_iso.endswith('T20:00:00'):
                        try:
                            odds_time = datetime.fromisoformat(odds_iso)
                            api_time = datetime.fromisoformat(api['kickoff_iso'])
                            time_diff = abs((odds_time - api_time).total_seconds()) / 60.0
                            
                            if time_diff > self.time_window:
                                continue
                        except (ValueError, KeyError):
                            pass

                    best_score = total_score
                    best_idx = j

            if best_idx != -1:
                matched_results.append({
                    "odds_data": odds,
                    "api_data": api_fixtures[best_idx],
                    "confidence_score": round(best_score * 100, 2)
                })

        return matched_results
