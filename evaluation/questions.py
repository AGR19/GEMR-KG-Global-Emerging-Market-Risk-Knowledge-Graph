from dataclasses import dataclass
from typing import Literal

ResultType = Literal["single_value", "list", "temporal_series", "comparison"]


@dataclass
class TestQuestion:
    id: str
    question: str
    tier: Literal["simple", "medium", "complex"]
    result_type: ResultType
    category: str = ""            # Query pattern category (paper-style)
    reference_sparql: str = ""    # Gold-standard SPARQL verified against GraphDB
    reference_logic: str = ""     # What the query is meant to identify / how it works
    notes: str = ""


TEST_QUESTIONS: list[TestQuestion] = [

    # ══════════════════════════════════════════════════════════════════════
    #  SIMPLE (8) — Single-hop lookups, basic filters, single entity
    # ══════════════════════════════════════════════════════════════════════

    TestQuestion(
        id="S01",
        question="What is the total risk score for Poland in 2023?",
        tier="simple",
        result_type="single_value",
        category="lookup",
        notes="RiskScore pattern; single country, single year",
        reference_logic=(
            "Retrieves the composite totalRiskScore from the RiskScore entity "
            "for Poland in 2023. Tests the most basic KG access pattern: "
            "match a typed entity (gemr:RiskScore) filtered by country name "
            "and a specific year entity (gemr:Year2023). Expected: 82."
        ),
        reference_sparql="""\
PREFIX gemr: <https://gemr-kg.org/ontology#>
SELECT ?total WHERE {
  ?rs a gemr:RiskScore ;
      gemr:hasCountry ?country ;
      gemr:hasYear gemr:Year2023 ;
      gemr:totalRiskScore ?total .
  ?country gemr:countryName "Poland" .
}""",
    ),

    TestQuestion(
        id="S02",
        question="What is the control of corruption score for Brazil in 2020?",
        tier="simple",
        result_type="single_value",
        category="lookup",
        notes="Governance Observation; tests indicator IRI grounding for ControlOfCorruption",
        reference_logic=(
            "Retrieves the ControlOfCorruption governance indicator observation "
            "for Brazil in 2020. Tests the Observation query pattern with "
            "gemr:hasIndicator pointing to a specific governance metric. "
            "The system must ground 'control of corruption' to the exact IRI "
            "gemr:ControlOfCorruption rather than hallucinating an IRI."
        ),
        reference_sparql="""\
PREFIX gemr: <https://gemr-kg.org/ontology#>
SELECT ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:ControlOfCorruption ;
       gemr:hasYear gemr:Year2020 ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Brazil" .
}""",
    ),

    TestQuestion(
        id="S03",
        question="What is the private default rate for China in 2015?",
        tier="simple",
        result_type="single_value",
        category="lookup",
        notes="Observation pattern; Historical_private_default_rates indicator",
        reference_logic=(
            "Retrieves the private default rate observation for China in 2015. "
            "Tests IRI grounding: the system must map 'private default rate' "
            "to gemr:Historical_private_default_rates (not a hallucinated IRI "
            "like gemr:PrivateDefaultRate). Expected: ~6.67%."
        ),
        reference_sparql="""\
PREFIX gemr: <https://gemr-kg.org/ontology#>
SELECT ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:Historical_private_default_rates ;
       gemr:hasYear gemr:Year2015 ;
       gemr:observationValue ?value .
  ?country gemr:countryName "China" .
}""",
    ),

    TestQuestion(
        id="S04",
        question="List all countries that have risk score data in 2023.",
        tier="simple",
        result_type="list",
        category="lookup",
        notes="RiskScore pattern; DISTINCT countries for a given year",
        reference_logic=(
            "Finds all countries that have a RiskScore entity for 2023. "
            "Tests DISTINCT projection and the ability to enumerate across "
            "multiple entities. Only Brazil and Poland have RiskScore data "
            "in the KG, so the expected result is exactly 2 countries."
        ),
        reference_sparql="""\
PREFIX gemr: <https://gemr-kg.org/ontology#>
SELECT DISTINCT ?name WHERE {
  ?rs a gemr:RiskScore ;
      gemr:hasCountry ?country ;
      gemr:hasYear gemr:Year2023 .
  ?country gemr:countryName ?name .
} ORDER BY ?name""",
    ),

    TestQuestion(
        id="S05",
        question="What is the GDP at market prices (current US$) for Mexico in 2019?",
        tier="simple",
        result_type="single_value",
        category="lookup",
        notes="GDP Observation; tests grounding GDP indicator to correct IRI",
        reference_logic=(
            "Retrieves the GDP at market prices (current US$) observation for "
            "Mexico in 2019. Tests IRI grounding for economic indicators: the "
            "system must map 'GDP at market prices' to "
            "gemr:GDP_at_market_prices_current_US. Expected: ~$1.3 trillion."
        ),
        reference_sparql="""\
PREFIX gemr: <https://gemr-kg.org/ontology#>
SELECT ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:GDP_at_market_prices_current_US ;
       gemr:hasYear gemr:Year2019 ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Mexico" .
}""",
    ),

    TestQuestion(
        id="S06",
        question="Show me the private default rates for Brazil from 2002 to 2023.",
        tier="simple",
        result_type="temporal_series",
        category="temporal_range",
        notes="Observation time series; full range for one country",
        reference_logic=(
            "Retrieves all private default rate observations for Brazil across "
            "the full time range (2002-2023). Tests temporal filtering with "
            "BIND/FILTER on yearValue, and the ability to produce an ordered "
            "time series. Expected: 22 rows, one per year."
        ),
        reference_sparql="""\
PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ?yearInt ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:Historical_private_default_rates ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Brazil" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?yearInt)
  FILTER(?yearInt >= 2002 && ?yearInt <= 2023)
} ORDER BY ?yearInt""",
    ),

    TestQuestion(
        id="S07",
        question="What is the political stability score for Thailand in 2010?",
        tier="simple",
        result_type="single_value",
        category="lookup",
        notes="Governance Observation; PoliticalStability indicator for a mid-range year",
        reference_logic=(
            "Retrieves the Political Stability governance indicator for "
            "Thailand in 2010. Tests IRI grounding for governance sub-indicators: "
            "the system must map 'political stability' to gemr:PoliticalStability."
        ),
        reference_sparql="""\
PREFIX gemr: <https://gemr-kg.org/ontology#>
SELECT ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:PoliticalStability ;
       gemr:hasYear gemr:Year2010 ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Thailand" .
}""",
    ),

    TestQuestion(
        id="S08",
        question="Which country had the highest total risk score in 2023?",
        tier="simple",
        result_type="single_value",
        category="superlative",
        notes="RiskScore; MAX aggregate with ORDER BY DESC LIMIT 1",
        reference_logic=(
            "Finds the country with the highest totalRiskScore in 2023. "
            "Tests superlative query pattern (ORDER BY DESC + LIMIT 1). "
            "Expected: Poland (82), since only Brazil (47) and Poland (82) "
            "have RiskScore data."
        ),
        reference_sparql="""\
PREFIX gemr: <https://gemr-kg.org/ontology#>
SELECT ?name ?total WHERE {
  ?rs a gemr:RiskScore ;
      gemr:hasCountry ?country ;
      gemr:hasYear gemr:Year2023 ;
      gemr:totalRiskScore ?total .
  ?country gemr:countryName ?name .
} ORDER BY DESC(?total) LIMIT 1""",
    ),

    # ══════════════════════════════════════════════════════════════════════
    #  MEDIUM (7) — Multi-hop, temporal range, cross-indicator joins
    # ══════════════════════════════════════════════════════════════════════

    TestQuestion(
        id="M01",
        question="What is the GDP at market prices (current US$) for each country from 2010 to 2020?",
        tier="medium",
        result_type="temporal_series",
        category="temporal_range",
        notes="GDP Observation; multi-country, 11-year window with year filtering",
        reference_logic=(
            "Retrieves GDP (current US$) observations for ALL countries across "
            "2010-2020. Tests multi-country enumeration combined with temporal "
            "range filtering. The system must correctly ground 'GDP at market "
            "prices' to gemr:GDP_at_market_prices_current_US and apply integer "
            "year filtering via BIND/FILTER."
        ),
        reference_sparql="""\
PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ?name ?yearInt ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:GDP_at_market_prices_current_US ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName ?name .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?yearInt)
  FILTER(?yearInt >= 2010 && ?yearInt <= 2020)
} ORDER BY ?name ?yearInt""",
    ),

    TestQuestion(
        id="M02",
        question="How did the control of corruption score for Poland change between 2005 and 2023?",
        tier="medium",
        result_type="temporal_series",
        category="temporal_range",
        notes="Governance time series; single country, 19-year window",
        reference_logic=(
            "Retrieves the ControlOfCorruption governance indicator for Poland "
            "from 2005 to 2023. Tests long temporal range filtering on a "
            "governance sub-indicator. Shows how Poland's corruption control "
            "evolved over nearly two decades."
        ),
        reference_sparql="""\
PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ?yearInt ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:ControlOfCorruption ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Poland" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?yearInt)
  FILTER(?yearInt >= 2005 && ?yearInt <= 2023)
} ORDER BY ?yearInt""",
    ),

    TestQuestion(
        id="M03",
        question="Did stock market performance in China in 2008 predict default rates in 2009?",
        tier="medium",
        result_type="comparison",
        category="cross_indicator",
        notes="Cross-indicator join; Stock_Market_Index_US + Historical_private_default_rates; temporal lag",
        reference_logic=(
            "Joins two different indicator observations for China across "
            "consecutive years: stock market performance (2008) vs private "
            "default rate (2009). Tests cross-indicator pattern with a temporal "
            "lag — the system must generate two separate Observation triple "
            "patterns joined on the same country but different years and "
            "indicators. This is a causal/predictive analysis query."
        ),
        reference_sparql="""\
PREFIX gemr: <https://gemr-kg.org/ontology#>
SELECT ?stockVal ?defaultVal WHERE {
  ?obs1 a gemr:Observation ;
        gemr:hasCountry ?country ;
        gemr:hasIndicator gemr:Stock_Market_Index_US ;
        gemr:hasYear gemr:Year2008 ;
        gemr:observationValue ?stockVal .
  ?obs2 a gemr:Observation ;
        gemr:hasCountry ?country ;
        gemr:hasIndicator gemr:Historical_private_default_rates ;
        gemr:hasYear gemr:Year2009 ;
        gemr:observationValue ?defaultVal .
  ?country gemr:countryName "China" .
}""",
    ),

    TestQuestion(
        id="M04",
        question="How did government effectiveness scores in Brazil change between 2015 and 2020?",
        tier="medium",
        result_type="temporal_series",
        category="temporal_range",
        notes="GovernmentEffectiveness governance indicator; 6-year window",
        reference_logic=(
            "Retrieves the GovernmentEffectiveness WGI indicator for Brazil "
            "from 2015 to 2020. Tests IRI grounding for a specific governance "
            "sub-indicator (not the composite governanceScore on RiskScore, "
            "but the raw WGI observation). Shows Brazil's institutional "
            "quality trajectory during a period of political instability."
        ),
        reference_sparql="""\
PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ?yearInt ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:GovernmentEffectiveness ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Brazil" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?yearInt)
  FILTER(?yearInt >= 2015 && ?yearInt <= 2020)
} ORDER BY ?yearInt""",
    ),

    TestQuestion(
        id="M05",
        question="Show me how private default rates and risk scores for the Philippines co-evolved from 2010 to 2023.",
        tier="medium",
        result_type="temporal_series",
        category="cross_indicator",
        notes="Multi-observation join; default rate + OPTIONAL RiskScore aligned by year",
        reference_logic=(
            "Retrieves private default rate observations for the Philippines "
            "(2010-2023) with an OPTIONAL join to RiskScore totalRiskScore. "
            "Tests the OPTIONAL pattern — since RiskScore data only exists "
            "for 2023 for some countries, riskTotal will be NULL for most years. "
            "The system must correctly use OPTIONAL to avoid losing default "
            "rate rows that have no matching RiskScore."
        ),
        reference_sparql="""\
PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ?yearInt ?defaultVal ?riskTotal WHERE {
  ?obs1 a gemr:Observation ;
        gemr:hasCountry ?country ;
        gemr:hasIndicator gemr:Historical_private_default_rates ;
        gemr:hasYear ?yearEntity ;
        gemr:observationValue ?defaultVal .
  ?country gemr:countryName "Philippines" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?yearInt)
  FILTER(?yearInt >= 2010 && ?yearInt <= 2023)
  OPTIONAL {
    ?rs a gemr:RiskScore ;
        gemr:hasCountry ?country ;
        gemr:hasYear ?yearEntity ;
        gemr:totalRiskScore ?riskTotal .
  }
} ORDER BY ?yearInt""",
    ),

    TestQuestion(
        id="M06",
        question="What were the annual total reserves for Mexico from 2005 to 2015?",
        tier="medium",
        result_type="temporal_series",
        category="temporal_range",
        notes="Total_Reserves indicator; 11-year range; tests IRI grounding for reserves",
        reference_logic=(
            "Retrieves Total_Reserves observations for Mexico from 2005 to "
            "2015. Tests IRI grounding for economic indicators — the system "
            "must map 'total reserves' to gemr:Total_Reserves (not "
            "RESERVES_TOTAL or Foreign_Reserves_Months_Import_Cover)."
        ),
        reference_sparql="""\
PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ?yearInt ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:Total_Reserves ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Mexico" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?yearInt)
  FILTER(?yearInt >= 2005 && ?yearInt <= 2015)
} ORDER BY ?yearInt""",
    ),

    TestQuestion(
        id="M07",
        question="How did exchange rates change in Thailand between 2008 and 2012?",
        tier="medium",
        result_type="temporal_series",
        category="temporal_range",
        notes="Official_exchange_rate_LCU_per_USD; tests IRI grounding for exchange rate indicator",
        reference_logic=(
            "Retrieves Official_exchange_rate_LCU_per_USD observations for "
            "Thailand from 2008 to 2012. Tests IRI grounding for exchange "
            "rate indicators — multiple exchange rate IRIs exist in the KG "
            "(Official_exchange_rate_LCU_per_USD, Exchange_rate_new_LCU_per_USD, "
            "Exchange_rate_old_LCU_per_USD, XRATE_OFFICIAL, etc.) and the "
            "system must pick the correct one."
        ),
        reference_sparql="""\
PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ?yearInt ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:Official_exchange_rate_LCU_per_USD ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Thailand" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?yearInt)
  FILTER(?yearInt >= 2008 && ?yearInt <= 2012)
} ORDER BY ?yearInt""",
    ),

    # ══════════════════════════════════════════════════════════════════════
    #  COMPLEX (5) — Aggregation, multi-condition, cross-indicator joins
    # ══════════════════════════════════════════════════════════════════════

    TestQuestion(
        id="C01",
        question="Which countries had private default rates above 5% between 2010 and 2020?",
        tier="complex",
        result_type="list",
        category="filter",
        notes="Observation FILTER on observationValue > 5.0; multi-country, year range",
        reference_logic=(
            "Finds all country-year combinations where the private default "
            "rate exceeded 5% between 2010 and 2020. Tests compound filtering: "
            "FILTER on both observationValue (> 5.0) AND year range. The "
            "system must combine temporal and numeric constraints in a single "
            "query. Expected results include Brazil (2014, 2016) and others."
        ),
        reference_sparql="""\
PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?name ?yearInt ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:Historical_private_default_rates ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName ?name .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?yearInt)
  FILTER(?yearInt >= 2010 && ?yearInt <= 2020 && ?value > 5.0)
} ORDER BY ?name ?yearInt""",
    ),

    TestQuestion(
        id="C02",
        question="Rank all countries by their average total risk score from 2015 to 2023.",
        tier="complex",
        result_type="list",
        category="aggregation",
        notes="RiskScore aggregation; AVG over year range; ORDER BY; multi-country",
        reference_logic=(
            "Computes the average totalRiskScore per country over 2015-2023 "
            "and ranks them. Tests GROUP BY + AVG aggregation combined with "
            "temporal filtering and ORDER BY. Note: only Brazil and Poland "
            "have RiskScore data (both only for 2023), so the AVG equals "
            "their single-year score. Poland (82) ranks above Brazil (47)."
        ),
        reference_sparql="""\
PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ?name (AVG(?total) AS ?avgRisk) WHERE {
  ?rs a gemr:RiskScore ;
      gemr:hasCountry ?country ;
      gemr:hasYear ?yearEntity ;
      gemr:totalRiskScore ?total .
  ?country gemr:countryName ?name .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?yearInt)
  FILTER(?yearInt >= 2015 && ?yearInt <= 2023)
} GROUP BY ?name ORDER BY DESC(?avgRisk)""",
    ),

    TestQuestion(
        id="C03",
        question="For each country, what is the highest private default rate ever recorded?",
        tier="complex",
        result_type="list",
        category="aggregation",
        notes="Aggregation with MAX per country group; tests GROUP BY + MAX",
        reference_logic=(
            "Finds the maximum private default rate for each country across "
            "the entire time range. Tests GROUP BY with MAX aggregation — "
            "the system must group observations by country and compute the "
            "peak default rate. Expected: 6 countries, each with their "
            "historical peak (e.g., Brazil ~7.94%, China ~6.67%)."
        ),
        reference_sparql="""\
PREFIX gemr: <https://gemr-kg.org/ontology#>
SELECT ?name (MAX(?value) AS ?maxRate) WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:Historical_private_default_rates ;
       gemr:observationValue ?value .
  ?country gemr:countryName ?name .
} GROUP BY ?name ORDER BY ?name""",
    ),

    TestQuestion(
        id="C04",
        question="Which countries had improving government effectiveness AND declining private default rates between 2015 and 2020?",
        tier="complex",
        result_type="list",
        category="compositional",
        notes="Multi-condition join: GovernmentEffectiveness + Historical_private_default_rates; endpoint comparison",
        reference_logic=(
            "Finds countries where: (1) GovernmentEffectiveness in 2020 > 2015, "
            "AND (2) private default rate in 2020 < 2015. Tests compositional "
            "query with four separate Observation triple patterns joined on "
            "the same country but different years and indicators, plus a "
            "FILTER comparing endpoint values. This is the most structurally "
            "complex query in the benchmark."
        ),
        reference_sparql="""\
PREFIX gemr: <https://gemr-kg.org/ontology#>
SELECT ?name WHERE {
  ?obs2015 a gemr:Observation ;
           gemr:hasCountry ?country ;
           gemr:hasIndicator gemr:GovernmentEffectiveness ;
           gemr:hasYear gemr:Year2015 ;
           gemr:observationValue ?gov2015 .
  ?obs2020 a gemr:Observation ;
           gemr:hasCountry ?country ;
           gemr:hasIndicator gemr:GovernmentEffectiveness ;
           gemr:hasYear gemr:Year2020 ;
           gemr:observationValue ?gov2020 .
  ?def2015 a gemr:Observation ;
           gemr:hasCountry ?country ;
           gemr:hasIndicator gemr:Historical_private_default_rates ;
           gemr:hasYear gemr:Year2015 ;
           gemr:observationValue ?defRate2015 .
  ?def2020 a gemr:Observation ;
           gemr:hasCountry ?country ;
           gemr:hasIndicator gemr:Historical_private_default_rates ;
           gemr:hasYear gemr:Year2020 ;
           gemr:observationValue ?defRate2020 .
  ?country gemr:countryName ?name .
  FILTER(?gov2020 > ?gov2015 && ?defRate2020 < ?defRate2015)
}""",
    ),

    TestQuestion(
        id="C05",
        question="Show me the economic health score and governance score for all countries in 2023, ordered by economic health score descending.",
        tier="complex",
        result_type="list",
        category="optional_paths",
        notes="Multi-property RiskScore projection; all countries; ORDER BY; OPTIONAL usage",
        reference_logic=(
            "Retrieves economicHealthScore and governanceScore from RiskScore "
            "entities for all countries in 2023, using OPTIONAL patterns "
            "since not all RiskScore entities have all sub-scores populated. "
            "Tests OPTIONAL join pattern and multi-property projection. "
            "Only Poland has full sub-scores; Brazil has only totalRiskScore."
        ),
        reference_sparql="""\
PREFIX gemr: <https://gemr-kg.org/ontology#>
SELECT ?name ?econ ?gov WHERE {
  ?rs a gemr:RiskScore ;
      gemr:hasCountry ?country ;
      gemr:hasYear gemr:Year2023 .
  ?country gemr:countryName ?name .
  OPTIONAL { ?rs gemr:economicHealthScore ?econ }
  OPTIONAL { ?rs gemr:governanceScore ?gov }
} ORDER BY DESC(?econ)""",
    ),
]
