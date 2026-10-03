from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from utils.text_cleaner import clean_team_name

class EntityMatcher:
    def __init__(self, time_window_minutes=180, threshold=0.35): # Diperlonggar ke 3 jam & threshold 35%
        self.time_window = time_window_minutes
        self.threshold = threshold

    def _calc_ngram_similarity(self, str1: str, str2: str) -> float:
        s1, s2 = clean_team_name(str1), clean_team_name(str2)
        if not s1 or not s2:
            return 0.0
        
        try:
            vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2, 3)) # Digabung 2-gram dan 3-gram
            tfidf = vectorizer.fit_transform([s1, s2])
            return float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0])
        except ValueError:
            return 0.0

    def match(self, odds_matches: list, api_fixtures: list) -> list:
        matched_results = []

        for odds in odds_matches:
            best_match = None
            highest_score = 0.0

            for api in api_fixtures:
                # 1. Kalkulasi Similarity Nama Tim
                home_score = self._calc_ngram_similarity(odds['home'], api['home'])
                away_score = self._calc_ngram_similarity(odds['away'], api['away'])
                total_score = (home_score + away_score) / 2.0

                # 2. Hanya proses jika kemiripan nama memenuhi ambang batas
                if total_score >= self.threshold and total_score > highest_score:
                    # Validasi jam jika kedua format ISO valid
                    try:
                        odds_time = datetime.fromisoformat(odds['kickoff_iso'])
                        api_time = datetime.fromisoformat(api['kickoff_iso'])
                        time_diff = abs((odds_time - api_time).total_seconds()) / 60
                        
                        # Lewati jika beda jam pertandingan lebih dari window (default 3 jam)
                        if time_diff > self.time_window:
                            continue
                    except Exception:
                        pass # Jika format tanggal error, utamakan kecocokan nama tim

                    highest_score = total_score
                    best_match = api

            if best_match:
                matched_results.append({
                    "odds_data": odds,
                    "api_data": best_match,
                    "confidence_score": round(highest_score * 100, 2)
                })

        return matched_results
