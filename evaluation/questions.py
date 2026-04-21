from dataclasses import dataclass
from typing import Literal

ResultType = Literal["single_value", "list", "temporal_series", "comparison"]


@dataclass
class TestQuestion:
    id: str
    question: str
    tier: Literal["simple", "medium", "complex"]
    result_type: ResultType
    notes: str = ""


TEST_QUESTIONS: list[TestQuestion] = [
    # ── SIMPLE (8) ──────────────────────────────────────────────────────────
    TestQuestion(
        id="S01",
        question="What is the total risk score for Poland in 2023?",
        tier="simple",
        result_type="single_value",
        notes="RiskScore pattern; single country, single year",
    ),
    TestQuestion(
        id="S02",
        question="What is the governance score for Brazil in 2020?",
        tier="simple",
        result_type="single_value",
        notes="RiskScore.governanceScore; single lookup",
    ),
    TestQuestion(
        id="S03",
        question="What is the private default rate for China in 2015?",
        tier="simple",
        result_type="single_value",
        notes="Observation pattern; HistoricalPrivateDefaultRate type",
    ),
    TestQuestion(
        id="S04",
        question="List all countries that have risk score data in 2023.",
        tier="simple",
        result_type="list",
        notes="RiskScore pattern; DISTINCT countries for a given year",
    ),
    TestQuestion(
        id="S05",
        question="What is the economic health score for Mexico in 2019?",
        tier="simple",
        result_type="single_value",
        notes="RiskScore.economicHealthScore; single country, single year",
    ),
    TestQuestion(
        id="S06",
        question="Show me the private default rates for Brazil from 2002 to 2023.",
        tier="simple",
        result_type="temporal_series",
        notes="Observation time series; full range for one country",
    ),
    TestQuestion(
        id="S07",
        question="What is the total risk score for Thailand in 2010?",
        tier="simple",
        result_type="single_value",
        notes="RiskScore; mid-range year",
    ),
    TestQuestion(
        id="S08",
        question="Which country had the highest total risk score in 2023?",
        tier="simple",
        result_type="single_value",
        notes="RiskScore; MAX aggregate with ORDER BY DESC LIMIT 1",
    ),

    # ── MEDIUM / TEMPORAL (7) ────────────────────────────────────────────────
    TestQuestion(
        id="M01",
        question="What is the GDP growth rate for each country year over year from 2010 to 2020?",
        tier="medium",
        result_type="temporal_series",
        notes="GDP Observation; year-over-year requires temporal lag pattern",
    ),
    TestQuestion(
        id="M02",
        question="How did the governance score for Poland change between 2005 and 2023?",
        tier="medium",
        result_type="temporal_series",
        notes="RiskScore.governanceScore time series; single country range",
    ),
    TestQuestion(
        id="M03",
        question="Did stock market performance in China in 2008 predict default rates in 2009?",
        tier="medium",
        result_type="comparison",
        notes="Cross-indicator join; StockMarkets obs + PrivateDefaultRate obs; temporal lag",
    ),
    TestQuestion(
        id="M04",
        question="How did governance scores in Brazil change between 2015 and 2020?",
        tier="medium",
        result_type="temporal_series",
        notes="RiskScore.governanceScore; 6-year window; tests FILTER on yearValue",
    ),
    TestQuestion(
        id="M05",
        question="Show me how private default rates and risk scores for the Philippines co-evolved from 2010 to 2023.",
        tier="medium",
        result_type="temporal_series",
        notes="Multi-observation join; two observation types aligned by year",
    ),
    TestQuestion(
        id="M06",
        question="What were the annual total reserves for Mexico from 2005 to 2015?",
        tier="medium",
        result_type="temporal_series",
        notes="TotalReserves Observation; 11-year range; tests FILTER range",
    ),
    TestQuestion(
        id="M07",
        question="How did exchange rates change in Thailand between 2008 and 2012?",
        tier="medium",
        result_type="temporal_series",
        notes="OfficialExchangeRate Observation; tests IRI grounding for exchange rate indicator",
    ),

    # ── COMPLEX (5) ─────────────────────────────────────────────────────────
    TestQuestion(
        id="C01",
        question="Which countries had private default rates above 5% between 2010 and 2020?",
        tier="complex",
        result_type="list",
        notes="Observation FILTER on observationValue; multi-country, range FILTER on year",
    ),
    TestQuestion(
        id="C02",
        question="Rank all countries by their average total risk score from 2015 to 2023.",
        tier="complex",
        result_type="list",
        notes="RiskScore aggregation; AVG over year range; ORDER BY; multi-country",
    ),
    TestQuestion(
        id="C03",
        question="For each country, what year had the highest private default rate, and what was that rate?",
        tier="complex",
        result_type="list",
        notes="Aggregation with MAX per country group; tests GROUP BY + ORDER BY",
    ),
    TestQuestion(
        id="C04",
        question="Which countries had improving governance scores AND declining private default rates between 2015 and 2020?",
        tier="complex",
        result_type="list",
        notes="Multi-condition join: RiskScore + Observation; comparing year endpoints",
    ),
    TestQuestion(
        id="C05",
        question="Show me all economic health scores and governance scores for all countries in 2018, ordered by economic health score descending.",
        tier="complex",
        result_type="list",
        notes="Multi-property RiskScore projection; all countries; ORDER BY; tests OPTIONAL usage",
    ),
]
