import os

# API Configurations
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "")

# Filter Engine Tuning Parameters (Diperluas untuk menjaring lebih banyak rekomendasi)
MIN_ODDS = 1.20              # Menjangkau odds yang lebih rendah (favorit kuat)
MAX_ODDS = 1.75              # Menjangkau odds hingga 1.75
MIN_EXPECTED_VALUE = -0.05   # Toleransi nilai EV diperlonggar dari +0.02 ke -0.05

# Matcher Settings
TIME_WINDOW_MINUTES = 180
FUZZY_THRESHOLD = 0.15
