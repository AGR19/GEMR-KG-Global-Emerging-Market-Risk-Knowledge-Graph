"""
Builds the evaluation question bank by combining:
  1. Kept hand-written questions whose reference SPARQL we've verified
  2. Auto-generated parametric questions derived from the frontend's
     Home.jsx template (indicator × country × year lookups, time-series,
     cross-country snapshots, superlatives, change queries)
  3. The 7 named analytic templates from SparqlInterface.jsx (paper-validation)

Every reference SPARQL is executed against GraphDB and only kept if it
returns ≥1 row. The output is written as `evaluation/questions.py`.

Run:
    .venv/bin/python -m evaluation.build_questions
"""
from __future__ import annotations

import os
import sys
import textwrap
from dataclasses import dataclass

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(REPO_ROOT, "backend", ".env"))

from evaluation.sparql_utils import execute_sparql


# ── Shared slot vocabulary ───────────────────────────────────────────────

COUNTRIES = ["Brazil", "China", "Mexico", "Philippines", "Poland", "Thailand"]

# (indicator IRI local-name, natural language phrasing)
INDICATORS: list[tuple[str, str]] = [
    ("GDP_at_market_prices_current_US", "GDP at market prices (current US$)"),
    ("GDP_at_market_prices_constant_2010_US", "GDP at market prices (constant 2010 US$)"),
    ("CPI_Price_nominal_seasonally_adjusted", "nominal CPI (seasonally adjusted)"),
    ("CPI_Price_Pct_yearoveryear_seasonally_adjusted", "CPI year-over-year inflation"),
    ("Stock_Market_Index_US", "stock market index (USD)"),
    ("Stock_Market_Index_LCU", "stock market index (local currency)"),
    ("Historical_private_default_rates", "private default rate"),
    ("Historical_public_default_rates", "public default rate"),
    ("Total_Reserves", "total reserves"),
    ("Official_exchange_rate_LCU_per_USD", "official exchange rate (LCU per USD)"),
    ("Real_Effective_Exchange_Rate", "real effective exchange rate"),
    ("Exports_Merchandise_current_US_seasonally_adjusted",
     "exports (current US$, seasonally adjusted)"),
    ("Imports_Merchandise_current_US_seasonally_adjusted",
     "imports (current US$, seasonally adjusted)"),
    ("ControlOfCorruption", "control of corruption score"),
    ("GovernmentEffectiveness", "government effectiveness score"),
    ("PoliticalStability", "political stability score"),
    ("RegulatoryQuality", "regulatory quality score"),
    ("RuleOfLaw", "rule of law score"),
    ("VoiceAndAccountability", "voice and accountability score"),
]


# ── Question record ──────────────────────────────────────────────────────

@dataclass
class Q:
    id: str
    question: str
    tier: str
    result_type: str
    category: str
    reference_sparql: str
    reference_logic: str = ""
    notes: str = ""


# ── Template helpers ─────────────────────────────────────────────────────

PFX = """PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>"""


def _single_cell(country: str, indicator: str, year: int) -> str:
    return f"""{PFX}
SELECT DISTINCT ?value WHERE {{
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:{indicator} ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "{country}" .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "{year}")
}}"""


def _time_series(country: str, indicator: str, y1: int, y2: int) -> str:
    return f"""{PFX}
SELECT DISTINCT ?year ?value WHERE {{
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:{indicator} ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "{country}" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?year)
  FILTER(?year >= {y1} && ?year <= {y2})
}} ORDER BY ?year"""


def _cross_country(indicator: str, year: int) -> str:
    return f"""{PFX}
SELECT DISTINCT ?country ?value WHERE {{
  ?obs a gemr:Observation ;
       gemr:hasCountry ?c ;
       gemr:hasIndicator gemr:{indicator} ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?c gemr:countryName ?country .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "{year}")
}} ORDER BY ?country"""


def _superlative(indicator: str, year: int, direction: str) -> str:
    order = "DESC" if direction == "highest" else "ASC"
    return f"""{PFX}
SELECT DISTINCT ?country ?value WHERE {{
  ?obs a gemr:Observation ;
       gemr:hasCountry ?c ;
       gemr:hasIndicator gemr:{indicator} ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?c gemr:countryName ?country .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "{year}")
}} ORDER BY {order}(?value) LIMIT 1"""


def _change_endpoints(country: str, indicator: str, y1: int, y2: int) -> str:
    return f"""{PFX}
SELECT DISTINCT ?year ?value WHERE {{
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:{indicator} ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "{country}" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?year)
  FILTER(?year = {y1} || ?year = {y2})
}} ORDER BY ?year"""


def _avg_over_range(country: str, indicator: str, y1: int, y2: int) -> str:
    return f"""{PFX}
SELECT (AVG(?value) AS ?avgValue) WHERE {{
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:{indicator} ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "{country}" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?year)
  FILTER(?year >= {y1} && ?year <= {y2})
}}"""


# ── Generation: parametric from Home.jsx-style templates ─────────────────

def gen_lookup_questions() -> list[Q]:
    """Single-cell: ‘What is the X for Y in Z?’"""
    plans = [
        ("Brazil",      "GDP_at_market_prices_current_US",             2010),
        ("China",       "GDP_at_market_prices_current_US",             2015),
        ("Mexico",      "CPI_Price_Pct_yearoveryear_seasonally_adjusted", 2020),
        ("Philippines", "Stock_Market_Index_US",                        2018),
        ("Poland",      "Historical_private_default_rates",             2012),
        ("Thailand",    "Total_Reserves",                               2008),
        ("Brazil",      "Official_exchange_rate_LCU_per_USD",           2022),
        ("China",       "ControlOfCorruption",                          2019),
        ("Mexico",      "GovernmentEffectiveness",                      2021),
        ("Philippines", "PoliticalStability",                           2016),
        ("Poland",      "RegulatoryQuality",                            2015),
        ("Thailand",    "RuleOfLaw",                                    2017),
        ("Brazil",      "VoiceAndAccountability",                       2014),
        ("China",       "Real_Effective_Exchange_Rate",                 2011),
        ("Mexico",      "Exports_Merchandise_current_US_seasonally_adjusted", 2019),
        ("Philippines", "Imports_Merchandise_current_US_seasonally_adjusted", 2020),
    ]
    out = []
    for i, (country, ind, year) in enumerate(plans, 1):
        phrase = _phrase(ind)
        out.append(Q(
            id=f"L{i:02d}",
            question=f"What is the {phrase} for {country} in {year}?",
            tier="simple",
            result_type="single_value",
            category="lookup",
            reference_sparql=_single_cell(country, ind, year),
            reference_logic=(
                f"Looks up the {phrase} observation for {country} in {year}. "
                f"Tests IRI grounding from the phrase to gemr:{ind}."
            ),
        ))
    return out


def gen_timeseries_questions() -> list[Q]:
    """Time series: ‘Show me X for Y from Z1 to Z2.’"""
    plans = [
        ("Brazil",      "GDP_at_market_prices_current_US",         2002, 2023),
        ("China",       "Historical_private_default_rates",         2005, 2020),
        ("Mexico",      "ControlOfCorruption",                      2002, 2023),
        ("Philippines", "GovernmentEffectiveness",                  2005, 2020),
        ("Poland",      "PoliticalStability",                       2002, 2023),
        ("Thailand",    "Real_Effective_Exchange_Rate",             2002, 2023),
        ("Brazil",      "Stock_Market_Index_US",                    2010, 2023),
        ("China",       "Official_exchange_rate_LCU_per_USD",       2002, 2023),
        ("Mexico",      "Total_Reserves",                           2005, 2015),
        ("Poland",      "Historical_public_default_rates",          2002, 2023),
        ("Thailand",    "CPI_Price_Pct_yearoveryear_seasonally_adjusted", 2010, 2020),
        ("Philippines", "Imports_Merchandise_current_US_seasonally_adjusted", 2010, 2023),
    ]
    out = []
    for i, (country, ind, y1, y2) in enumerate(plans, 1):
        phrase = _phrase(ind)
        out.append(Q(
            id=f"T{i:02d}",
            question=f"Show me the {phrase} for {country} from {y1} to {y2}.",
            tier="medium",
            result_type="temporal_series",
            category="temporal_range",
            reference_sparql=_time_series(country, ind, y1, y2),
            reference_logic=(
                f"Returns the time series of {phrase} observations for "
                f"{country} across {y1}–{y2}. Tests temporal range filtering "
                f"and ordering by year."
            ),
        ))
    return out


def gen_cross_country_questions() -> list[Q]:
    plans = [
        ("GDP_at_market_prices_current_US",                2020),
        ("Historical_private_default_rates",               2015),
        ("ControlOfCorruption",                            2019),
        ("PoliticalStability",                             2022),
        ("Stock_Market_Index_US",                          2018),
        ("Total_Reserves",                                 2010),
        ("Real_Effective_Exchange_Rate",                   2021),
        ("Exports_Merchandise_current_US_seasonally_adjusted", 2017),
    ]
    out = []
    for i, (ind, year) in enumerate(plans, 1):
        phrase = _phrase(ind)
        out.append(Q(
            id=f"X{i:02d}",
            question=f"Show the {phrase} for all countries in {year}.",
            tier="medium",
            result_type="list",
            category="cross_country_snapshot",
            reference_sparql=_cross_country(ind, year),
            reference_logic=(
                f"Returns the {phrase} for every country in {year}. Tests "
                f"multi-country enumeration via gemr:countryName variable binding."
            ),
        ))
    return out


def gen_superlative_questions() -> list[Q]:
    plans = [
        ("GDP_at_market_prices_current_US",   2020, "highest"),
        ("Historical_private_default_rates",  2010, "highest"),
        ("ControlOfCorruption",               2022, "highest"),
        ("PoliticalStability",                2015, "lowest"),
        ("Total_Reserves",                    2018, "highest"),
        ("Official_exchange_rate_LCU_per_USD", 2019, "lowest"),
    ]
    out = []
    for i, (ind, year, direction) in enumerate(plans, 1):
        phrase = _phrase(ind)
        out.append(Q(
            id=f"R{i:02d}",
            question=f"Which country had the {direction} {phrase} in {year}?",
            tier="medium",
            result_type="single_value",
            category="superlative",
            reference_sparql=_superlative(ind, year, direction),
            reference_logic=(
                f"Finds the country with the {direction} {phrase} in {year}. "
                f"Tests ORDER BY {('DESC' if direction=='highest' else 'ASC')} + "
                f"LIMIT 1 superlative pattern."
            ),
        ))
    return out


def gen_change_questions() -> list[Q]:
    plans = [
        ("Brazil",      "ControlOfCorruption",            2010, 2020),
        ("China",       "GDP_at_market_prices_current_US", 2008, 2013),
        ("Mexico",      "Historical_private_default_rates", 2010, 2020),
        ("Poland",      "GovernmentEffectiveness",         2005, 2015),
        ("Thailand",    "Official_exchange_rate_LCU_per_USD", 2008, 2012),
        ("Philippines", "Real_Effective_Exchange_Rate",    2010, 2020),
    ]
    out = []
    for i, (country, ind, y1, y2) in enumerate(plans, 1):
        phrase = _phrase(ind)
        out.append(Q(
            id=f"D{i:02d}",
            question=f"How did the {phrase} for {country} change between {y1} and {y2}?",
            tier="medium",
            result_type="comparison",
            category="change_over_time",
            reference_sparql=_change_endpoints(country, ind, y1, y2),
            reference_logic=(
                f"Returns the {phrase} for {country} at the two endpoints "
                f"{y1} and {y2}. Tests the 'change between two years' pattern "
                f"via FILTER(?year = a || ?year = b)."
            ),
        ))
    return out


def gen_avg_questions() -> list[Q]:
    plans = [
        ("Brazil",      "GDP_at_market_prices_current_US",        2015, 2020),
        ("China",       "ControlOfCorruption",                    2010, 2020),
        ("Mexico",      "Historical_private_default_rates",       2005, 2015),
        ("Poland",      "Real_Effective_Exchange_Rate",           2010, 2020),
    ]
    out = []
    for i, (country, ind, y1, y2) in enumerate(plans, 1):
        phrase = _phrase(ind)
        out.append(Q(
            id=f"A{i:02d}",
            question=f"What was the average {phrase} for {country} from {y1} to {y2}?",
            tier="medium",
            result_type="single_value",
            category="aggregation",
            reference_sparql=_avg_over_range(country, ind, y1, y2),
            reference_logic=(
                f"Computes AVG of {phrase} for {country} across {y1}–{y2}. "
                f"Tests aggregation (AVG) combined with temporal filtering."
            ),
        ))
    return out


def _phrase(indicator: str) -> str:
    for name, label in INDICATORS:
        if name == indicator:
            return label
    return indicator.replace("_", " ").lower()


# ── Kept hand-written questions (curated from the current benchmark) ─────
# Only questions whose reference_sparql is confirmed working are kept.
# Paper-validation P01-P07 moved to a separate set since they hit the
# complex frontend templates; the versions below are copied verbatim from
# evaluation/questions.py.

def kept_handwritten() -> list[Q]:
    """Re-use only the lookup/series/aggregate questions that are known-good.
    Skips anything with a hand-wavy reference (e.g. P04 used a class IRI that
    doesn't exist in the KG)."""
    # Import lazily to avoid circular import on first run
    from evaluation.questions import TEST_QUESTIONS
    keep_ids = {"S01","S02","S03","S04","S05","S07","S08",
                "M03","M04","M05","M06",
                "C01","C02","C03","C04","C05"}
    out = []
    for q in TEST_QUESTIONS:
        if q.id in keep_ids:
            out.append(Q(
                id=q.id,
                question=q.question,
                tier=q.tier,
                result_type=q.result_type,
                category=q.category or "lookup",
                reference_sparql=q.reference_sparql,
                reference_logic=q.reference_logic,
                notes=q.notes,
            ))
    return out


# ── Frontend-verified analytical templates (SparqlInterface.jsx) ─────────
# Verbatim SPARQL from frontend/src/components/SparqlInterface.jsx.
# These are the queries the frontend ships as proven working examples.

def frontend_templates() -> list[Q]:
    return [
        Q(
            id="F01",
            question=("What is the comprehensive risk profile for Poland in 2023, "
                      "including total score, risk tier, and component scores?"),
            tier="complex",
            result_type="list",
            category="frontend_risk_profile",
            notes="Verbatim from SparqlInterface.jsx 'Risk Profile Dashboard (2023)'",
            reference_sparql=textwrap.dedent("""\
                PREFIX gemr: <https://gemr-kg.org/ontology#>
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                SELECT ?countryName ?year ?totalScore ?riskTier ?govScore ?econScore ?vulnScore ?contagionScore
                WHERE {
                    BIND("2023"^^xsd:gYear AS ?targetYear)
                    BIND("Poland" AS ?targetCountry)
                    ?scoreObs a gemr:RiskScore ;
                              gemr:hasCountry ?country ;
                              gemr:hasYear ?yearEntity ;
                              gemr:totalRiskScore ?totalScore .
                    ?country gemr:countryName ?countryName .
                    ?yearEntity gemr:yearValue ?year .
                    FILTER (?year = ?targetYear)
                    FILTER (STR(?countryName) = ?targetCountry)
                    OPTIONAL { ?scoreObs gemr:riskTier ?riskTier }
                    OPTIONAL { ?scoreObs gemr:governanceScore ?govScore }
                    OPTIONAL { ?scoreObs gemr:economicHealthScore ?econScore }
                    OPTIONAL { ?scoreObs gemr:externalVulnerabilityScore ?vulnScore }
                    OPTIONAL { ?scoreObs gemr:contagionRiskScore ?contagionScore }
                }"""),
            reference_logic=(
                "Risk Profile Dashboard (2023) — retrieves total risk score plus "
                "all optional component scores and the risk tier for Poland. "
                "Extensive use of OPTIONAL to tolerate missing sub-scores."
            ),
        ),
        Q(
            id="F02",
            question=("Does stock market performance in year T predict private "
                      "default rates in year T+1? Show the average default rate "
                      "following each stock observation."),
            tier="complex",
            result_type="list",
            category="frontend_early_warning",
            notes="Verbatim from SparqlInterface.jsx '1. Early Warning (Stock -> Default)'",
            reference_sparql=textwrap.dedent("""\
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                PREFIX gemr: <https://gemr-kg.org/ontology#>
                SELECT ?countryName ?yearInt ?stockValue ?targetYearInt (AVG(xsd:float(?defaultRate)) AS ?avgDefaultRate)
                WHERE {
                    ?obsStock a gemr:Stock_Market_Index_LCU ;
                              gemr:hasCountry ?c ;
                              gemr:hasYear ?yearEntity ;
                              gemr:observationValue ?stockValue .
                    ?yearEntity gemr:yearValue ?yearLiteral .
                    BIND(xsd:integer(STR(?yearLiteral)) AS ?yearInt)
                    BIND(?yearInt + 1 AS ?targetYearInt)
                    ?targetYearEntity gemr:yearValue ?targetYearLiteral .
                    FILTER(xsd:integer(STR(?targetYearLiteral)) = ?targetYearInt)
                    ?obsDefault a gemr:Observation ;
                                gemr:hasIndicator gemr:Historical_private_default_rates ;
                                gemr:hasCountry ?c ;
                                gemr:hasYear ?targetYearEntity ;
                                gemr:observationValue ?defaultRate .
                    ?c gemr:countryName ?countryName .
                }
                GROUP BY ?countryName ?yearInt ?stockValue ?targetYearInt
                ORDER BY ?countryName ?yearInt
                LIMIT 100"""),
            reference_logic=(
                "Early Warning (Stock → Default): joins stock market observations "
                "at year T with private default rate observations at T+1, "
                "aggregated to an average default rate per stock observation."
            ),
        ),
        Q(
            id="F03",
            question=("How does negative political stability in year T impact "
                      "real-economy GDP in year T+1?"),
            tier="complex",
            result_type="list",
            category="frontend_stability_gdp",
            notes="Verbatim from SparqlInterface.jsx '2. Political Stability -> GDP'",
            reference_sparql=textwrap.dedent("""\
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                PREFIX gemr: <https://gemr-kg.org/ontology#>
                SELECT ?countryName ?yearInt (AVG(xsd:float(?polStability)) AS ?avgPolStability) ?targetYearInt ?gdpValue
                WHERE {
                    ?obsPol a gemr:PoliticalStability ;
                            gemr:hasCountry ?c ;
                            gemr:hasYear ?yearEntity ;
                            gemr:observationValue ?polStability .
                    FILTER(?polStability < 0)
                    ?yearEntity gemr:yearValue ?yearLiteral .
                    BIND(xsd:integer(STR(?yearLiteral)) AS ?yearInt)
                    BIND(?yearInt + 1 AS ?targetYearInt)
                    ?obsEco a gemr:GDP_CONST_2010_USD ;
                            gemr:hasCountry ?c ;
                            gemr:hasYear ?gdpYearRaw ;
                            gemr:observationValue ?gdpValue .
                    OPTIONAL { ?gdpYearRaw gemr:yearValue ?gdpYearVal }
                    BIND(COALESCE(xsd:integer(STR(?gdpYearVal)), ?gdpYearRaw) AS ?gdpYearInt)
                    FILTER(?gdpYearInt = ?targetYearInt)
                    ?c gemr:countryName ?countryName .
                }
                GROUP BY ?countryName ?yearInt ?targetYearInt ?gdpValue
                ORDER BY ?countryName ?yearInt
                LIMIT 50"""),
            reference_logic=(
                "Negative political stability at year T joined to GDP "
                "(constant 2010 USD) at year T+1, averaged per country-year pair."
            ),
        ),
        Q(
            id="F04",
            question=("Show the relationship between stock market performance "
                      "and real-economy GDP in the following year."),
            tier="complex",
            result_type="list",
            category="frontend_default_recovery",
            notes="Verbatim from SparqlInterface.jsx '3. Default -> Recovery'",
            reference_sparql=textwrap.dedent("""\
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                PREFIX gemr: <https://gemr-kg.org/ontology#>
                SELECT ?countryName ?yearT (AVG(xsd:float(?stockValue)) AS ?avgStockValue) ?yearTarget ?gdpValue
                WHERE {
                    ?obsStock a gemr:Stock_Market_Index_LCU ;
                              gemr:hasCountry ?c ;
                              gemr:hasYear ?yearT_Raw ;
                              gemr:observationValue ?stockValue .
                    ?obsGDP a gemr:GDP_CONST_2010_USD ;
                            gemr:hasCountry ?c ;
                            gemr:hasYear ?yearTarget_Raw ;
                            gemr:observationValue ?gdpValue .
                    OPTIONAL { ?yearT_Raw gemr:yearValue ?yValT }
                    OPTIONAL { ?yearTarget_Raw gemr:yearValue ?yValTarget }
                    BIND(COALESCE(xsd:integer(STR(?yValT)), ?yearT_Raw) AS ?yearT)
                    BIND(COALESCE(xsd:integer(STR(?yValTarget)), ?yearTarget_Raw) AS ?yearTarget)
                    FILTER(?yearTarget = ?yearT + 1)
                    ?c gemr:countryName ?countryName .
                }
                GROUP BY ?countryName ?yearT ?yearTarget ?gdpValue
                ORDER BY ?countryName ?yearT"""),
            reference_logic=(
                "Stock market LCU at year T joined to GDP (const 2010 USD) at "
                "year T+1; tolerates either Year IRI subject or typed literal."
            ),
        ),
        Q(
            id="F05",
            question=("Calculate the annual GDP growth rate (percentage) for "
                      "all countries."),
            tier="complex",
            result_type="list",
            category="frontend_gdp_growth",
            notes="Verbatim from SparqlInterface.jsx '4. GDP Growth Tracker'",
            reference_sparql=textwrap.dedent("""\
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                PREFIX gemr: <https://gemr-kg.org/ontology#>
                SELECT ?countryName ?year ?gdpVal_Current ?growthRatePercent
                WHERE {
                    ?obsGDP_T a gemr:GDP_CONST_2010_USD ;
                              gemr:hasCountry ?c ;
                              gemr:hasYear ?yT_Raw ;
                              gemr:observationValue ?gdpVal_Current .
                    ?obsGDP_Prev a gemr:GDP_CONST_2010_USD ;
                                 gemr:hasCountry ?c ;
                                 gemr:hasYear ?yPrev_Raw ;
                                 gemr:observationValue ?gdpVal_Prev .
                    OPTIONAL { ?yT_Raw gemr:yearValue ?yValT }
                    OPTIONAL { ?yPrev_Raw gemr:yearValue ?yValPrev }
                    BIND(COALESCE(xsd:integer(STR(?yValT)), ?yT_Raw) AS ?year)
                    BIND(COALESCE(xsd:integer(STR(?yValPrev)), ?yPrev_Raw) AS ?yearPrev)
                    FILTER(?yearPrev = ?year - 1)
                    BIND(((?gdpVal_Current - ?gdpVal_Prev) / ?gdpVal_Prev) * 100 AS ?growthRatePercent)
                    ?c gemr:countryName ?countryName .
                }
                ORDER BY ?countryName ?year
                LIMIT 100"""),
            reference_logic=(
                "Year-over-year GDP growth rate via self-join on GDP_CONST_2010_USD "
                "at year and year-1, then percentage delta."
            ),
        ),
    ]


# ── Emit the new questions.py file ───────────────────────────────────────

def _python_repr_sparql(s: str) -> str:
    """Emit SPARQL as a triple-quoted string literal preserving newlines."""
    # Use triple-quoted raw string. Escape any triple quotes (none expected).
    if '"""' in s:
        s = s.replace('"""', '\\"\\"\\"')
    return '"""' + s + '"""'


def emit_questions_py(qs: list[Q]) -> str:
    HEADER = '''from dataclasses import dataclass
from typing import Literal

ResultType = Literal["single_value", "list", "temporal_series", "comparison"]


@dataclass
class TestQuestion:
    id: str
    question: str
    tier: Literal["simple", "medium", "complex"]
    result_type: ResultType
    category: str = ""
    reference_sparql: str = ""
    reference_logic: str = ""
    notes: str = ""


# Auto-built by evaluation/build_questions.py — do not hand-edit in place.
# Every reference_sparql was verified to return ≥1 row against GraphDB
# (http://localhost:7200/repositories/GEMR) at the time of generation.
# Questions are drawn from:
#   - frontend/src/components/Home.jsx (parametric country × indicator × year)
#   - frontend/src/components/SparqlInterface.jsx (7 named analytical templates)
#   - curated hand-written questions that passed reference validation.

TEST_QUESTIONS: list[TestQuestion] = [
'''
    body = []
    for q in qs:
        body.append("    TestQuestion(")
        body.append(f"        id={q.id!r},")
        body.append(f"        question={q.question!r},")
        body.append(f"        tier={q.tier!r},")
        body.append(f"        result_type={q.result_type!r},")
        body.append(f"        category={q.category!r},")
        if q.notes:
            body.append(f"        notes={q.notes!r},")
        body.append(f"        reference_logic={q.reference_logic!r},")
        body.append("        reference_sparql=" + _python_repr_sparql(q.reference_sparql) + ",")
        body.append("    ),")
    return HEADER + "\n".join(body) + "\n]\n"


# ── Main ─────────────────────────────────────────────────────────────────

def main() -> None:
    # Note: kept_handwritten() reads the CURRENT questions.py, so we must
    # build our full list BEFORE writing anything.
    all_q: list[Q] = []
    all_q += kept_handwritten()
    all_q += gen_lookup_questions()
    all_q += gen_timeseries_questions()
    all_q += gen_cross_country_questions()
    all_q += gen_superlative_questions()
    all_q += gen_change_questions()
    all_q += gen_avg_questions()
    all_q += frontend_templates()

    # Verify each reference SPARQL returns ≥1 row
    kept: list[Q] = []
    dropped: list[tuple[str, str]] = []
    print(f"Verifying {len(all_q)} candidate questions against GraphDB...\n")
    for q in all_q:
        r = execute_sparql(q.reference_sparql)
        if not r.get("success"):
            dropped.append((q.id, f"exec failed: {str(r.get('error'))[:80]}"))
            continue
        n = len(r["data"].get("results", {}).get("bindings", []))
        if n == 0:
            dropped.append((q.id, "zero rows"))
            continue
        kept.append(q)
        print(f"  {q.id:5s} ✓ {n:4d} rows  [{q.tier:7s}/{q.category}]  {q.question[:70]}")

    print(f"\nKept {len(kept)} / {len(all_q)}.")
    if dropped:
        print("Dropped:")
        for qid, why in dropped:
            print(f"  {qid}: {why}")

    # Write output
    out_path = os.path.join(REPO_ROOT, "evaluation", "questions.py")
    content = emit_questions_py(kept)
    with open(out_path, "w") as f:
        f.write(content)
    print(f"\nWrote {out_path}  ({len(kept)} questions)")

    # Tier breakdown
    tiers: dict[str, int] = {}
    cats: dict[str, int] = {}
    for q in kept:
        tiers[q.tier] = tiers.get(q.tier, 0) + 1
        cats[q.category] = cats.get(q.category, 0) + 1
    print("\nTier counts:")
    for t, n in sorted(tiers.items()):
        print(f"  {t:7s} {n}")
    print("Category counts:")
    for c, n in sorted(cats.items()):
        print(f"  {c:30s} {n}")


if __name__ == "__main__":
    main()
