from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from utils.text_cleaner import clean_team_name

class EntityMatcher:
    def __init__(self, time_window_minutes=30, threshold=0.50):
        self.time_window = time_window_minutes
        self.threshold = threshold

    def _calc_ngram_similarity(self, str1: str, str2: str) -> float:
        s1, s2 = clean_team_name(str1), clean_team_name(str2)
        if not s1 or not s2:
            return 0.0
        
        try:
            vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(3, 3))
            tfidf = vectorizer.fit_transform([s1, s2])
            return float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0])
        except ValueError:
            return 0.0

    def match(self, odds_matches: list, api_fixtures: list) -> list:
        matched_results = []

        for odds in odds_matches:
            best_match = None
            highest_score = 0.0
            odds_time = datetime.fromisoformat(odds['kickoff_iso'])

            for api in api_fixtures:
                api_time = datetime.fromisoformat(api['kickoff_iso'])
                
                # 1. TIME WINDOW FILTER (+/- 30 Menit)
                time_diff = abs((odds_time - api_time).total_seconds()) / 60
                if time_diff > self.time_window:
                    continue

                # 2. N-GRAM MATCHING
                home_score = self._calc_ngram_similarity(odds['home'], api['home'])
                away_score = self._calc_ngram_similarity(odds['away'], api['away'])
                total_score = (home_score + away_score) / 2.0

                if total_score > self.threshold and total_score > highest_score:
                    highest_score = total_score
                    best_match = api

            if best_match:
                matched_results.append({
                    "odds_data": odds,
                    "api_data": best_match,
                    "confidence_score": round(highest_score * 100, 2)
                })

        return matched_results
