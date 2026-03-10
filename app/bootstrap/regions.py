from __future__ import annotations

REGION_CONFIGS = {
    "Africa": {
        "gdp_level": "low",
        "security": "low",
        "corruption_rate": 0.24,
        "audit_probability": 0.15,
        "penalty_multiplier": 0.9,
        "bank_risk": 0.35,
        "oracle_success_rate": 0.7,
    },
    "Asia": {
        "gdp_level": "high",
        "security": "high",
        "corruption_rate": 0.12,
        "audit_probability": 0.4,
        "penalty_multiplier": 1.8,
        "bank_risk": 0.15,
        "oracle_success_rate": 0.92,
    },
    "America": {
        "gdp_level": "very_high",
        "security": "high",
        "corruption_rate": 0.18,
        "audit_probability": 0.3,
        "penalty_multiplier": 1.3,
        "bank_risk": 0.22,
        "oracle_success_rate": 0.88,
    },
    "Europe": {
        "gdp_level": "moderate_high",
        "security": "high",
        "corruption_rate": 0.1,
        "audit_probability": 0.33,
        "penalty_multiplier": 1.2,
        "bank_risk": 0.18,
        "oracle_success_rate": 0.9,
    },
    "LatinAmerica": {
        "gdp_level": "medium",
        "security": "medium",
        "corruption_rate": 0.2,
        "audit_probability": 0.22,
        "penalty_multiplier": 1.1,
        "bank_risk": 0.27,
        "oracle_success_rate": 0.8,
    },
}


def load_regions() -> dict[str, dict]:
    return REGION_CONFIGS.copy()
