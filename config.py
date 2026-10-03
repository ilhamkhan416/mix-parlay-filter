import os

# API Key & API-Football Settings
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "311363def3f6531198c08527522c296e")
API_FOOTBALL_URL = "https://v3.football.api-sports.io"

# Filter Engine Settings
MIN_ODDS = 1.25
MAX_ODDS = 1.60
MIN_EXPECTED_VALUE = 0.02 # +2% ROI Minimum
TIME_WINDOW_MINUTES = 30  # Selisih maksimal kickoff WIB/UTC
FUZZY_THRESHOLD = 0.50    # Minimal similarity score N-Gram (50%)
