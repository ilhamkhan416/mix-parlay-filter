import pytest
from modules.filter_engine import ParlayFilterEngine

@pytest.fixture
def engine():
    return ParlayFilterEngine(min_odds=1.25, max_odds=1.60, min_ev=0.02)

def test_implied_probability_calculation(engine):
    ip = engine.calculate_implied_probability(1.40)
    assert ip == 0.7143

def test_expected_value_positive_and_negative(engine):
    ev_pos = engine.calculate_expected_value(odds=1.40, estimated_prob=0.80)
    assert ev_pos == 0.12

    ev_neg = engine.calculate_expected_value(odds=1.40, estimated_prob=0.50)
    assert ev_neg == -0.30

def test_evaluate_parlay_filters_h2h_and_odds(engine):
    matched_input = [
        {
            "odds_data": {"home": "Bayern Munich", "away": "Leverkusen", "odds_value": 1.40},
            "api_data": {
                "league_name": "Bundesliga",
                "stats": {"form": "WWWDW"},
                "h2h": [
                    {"teams": {"home": {"winner": True}, "away": {"winner": False}}},
                    {"teams": {"home": {"winner": True}, "away": {"winner": False}}}
                ]
            },
            "confidence_score": 90.0
        },
        {
            "odds_data": {"home": "Real Madrid", "away": "Getafe", "odds_value": 1.95},
            "api_data": {"stats": {"form": "WWWWW"}, "h2h": []},
            "confidence_score": 85.0
        }
    ]

    picks = engine.evaluate(matched_input)

    assert len(picks) == 1
    assert picks[0]["match"] == "Bayern Munich vs Leverkusen"
    assert "+" in picks[0]["expected_value"]
