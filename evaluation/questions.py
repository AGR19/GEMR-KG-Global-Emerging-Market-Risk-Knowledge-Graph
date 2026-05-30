from dataclasses import dataclass
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
    TestQuestion(
        id='S01',
        question='What is the total risk score for Poland in 2023?',
        tier='simple',
        result_type='single_value',
        category='lookup',
        notes='RiskScore pattern; single country, single year',
        reference_logic='Retrieves the composite totalRiskScore from the RiskScore entity for Poland in 2023. Tests the most basic KG access pattern: match a typed entity (gemr:RiskScore) filtered by country name and a specific year entity (gemr:Year2023). Expected: 82.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
SELECT ?total WHERE {
  ?rs a gemr:RiskScore ;
      gemr:hasCountry ?country ;
      gemr:hasYear gemr:Year2023 ;
      gemr:totalRiskScore ?total .
  ?country gemr:countryName "Poland" .
}""",
    ),
    TestQuestion(
        id='S02',
        question='What is the control of corruption score for Brazil in 2020?',
        tier='simple',
        result_type='single_value',
        category='lookup',
        notes='Governance Observation; tests indicator IRI grounding for ControlOfCorruption',
        reference_logic="Retrieves the ControlOfCorruption governance indicator observation for Brazil in 2020. Tests the Observation query pattern with gemr:hasIndicator pointing to a specific governance metric. The system must ground 'control of corruption' to the exact IRI gemr:ControlOfCorruption rather than hallucinating an IRI.",
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
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
        id='S03',
        question='What is the private default rate for China in 2015?',
        tier='simple',
        result_type='single_value',
        category='lookup',
        notes='Observation pattern; Historical_private_default_rates indicator',
        reference_logic="Retrieves the private default rate observation for China in 2015. Tests IRI grounding: the system must map 'private default rate' to gemr:Historical_private_default_rates (not a hallucinated IRI like gemr:PrivateDefaultRate). Expected: ~6.67%.",
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
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
        id='S04',
        question='List all countries that have risk score data in 2023.',
        tier='simple',
        result_type='list',
        category='lookup',
        notes='RiskScore pattern; DISTINCT countries for a given year',
        reference_logic='Finds all countries that have a RiskScore entity for 2023. Tests DISTINCT projection and the ability to enumerate across multiple entities. Only Brazil and Poland have RiskScore data in the KG, so the expected result is exactly 2 countries.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
SELECT DISTINCT ?name WHERE {
  ?rs a gemr:RiskScore ;
      gemr:hasCountry ?country ;
      gemr:hasYear gemr:Year2023 .
  ?country gemr:countryName ?name .
} ORDER BY ?name""",
    ),
    TestQuestion(
        id='S05',
        question='What is the GDP at market prices (current US$) for Mexico in 2019?',
        tier='simple',
        result_type='single_value',
        category='lookup',
        notes='GDP Observation; tests grounding GDP indicator to correct IRI',
        reference_logic="Retrieves the GDP at market prices (current US$) observation for Mexico in 2019. Tests IRI grounding for economic indicators: the system must map 'GDP at market prices' to gemr:GDP_at_market_prices_current_US. Expected: ~$1.3 trillion.",
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
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
        id='S07',
        question='What is the political stability score for Thailand in 2010?',
        tier='simple',
        result_type='single_value',
        category='lookup',
        notes='Governance Observation; PoliticalStability indicator for a mid-range year',
        reference_logic="Retrieves the Political Stability governance indicator for Thailand in 2010. Tests IRI grounding for governance sub-indicators: the system must map 'political stability' to gemr:PoliticalStability.",
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
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
        id='S08',
        question='Which country had the highest total risk score in 2023?',
        tier='simple',
        result_type='single_value',
        category='superlative',
        notes='RiskScore; MAX aggregate with ORDER BY DESC LIMIT 1',
        reference_logic='Finds the country with the highest totalRiskScore in 2023. Tests superlative query pattern (ORDER BY DESC + LIMIT 1). Expected: Poland (82), since only Brazil (47) and Poland (82) have RiskScore data.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
SELECT ?name ?total WHERE {
  ?rs a gemr:RiskScore ;
      gemr:hasCountry ?country ;
      gemr:hasYear gemr:Year2023 ;
      gemr:totalRiskScore ?total .
  ?country gemr:countryName ?name .
} ORDER BY DESC(?total) LIMIT 1""",
    ),
    TestQuestion(
        id='M03',
        question='Did stock market performance in China in 2008 predict default rates in 2009?',
        tier='medium',
        result_type='comparison',
        category='cross_indicator',
        notes='Cross-indicator join; Stock_Market_Index_US + Historical_private_default_rates; temporal lag',
        reference_logic='Joins two different indicator observations for China across consecutive years: stock market performance (2008) vs private default rate (2009). Tests cross-indicator pattern with a temporal lag — the system must generate two separate Observation triple patterns joined on the same country but different years and indicators. This is a causal/predictive analysis query.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
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
        id='M04',
        question='How did government effectiveness scores in Brazil change between 2015 and 2020?',
        tier='medium',
        result_type='temporal_series',
        category='temporal_range',
        notes='GovernmentEffectiveness governance indicator; 6-year window',
        reference_logic="Retrieves the GovernmentEffectiveness WGI indicator for Brazil from 2015 to 2020. Tests IRI grounding for a specific governance sub-indicator (not the composite governanceScore on RiskScore, but the raw WGI observation). Shows Brazil's institutional quality trajectory during a period of political instability.",
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
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
        id='M05',
        question='Show me how private default rates and risk scores for the Philippines co-evolved from 2010 to 2023.',
        tier='medium',
        result_type='temporal_series',
        category='cross_indicator',
        notes='Multi-observation join; default rate + OPTIONAL RiskScore aligned by year',
        reference_logic='Retrieves private default rate observations for the Philippines (2010-2023) with an OPTIONAL join to RiskScore totalRiskScore. Tests the OPTIONAL pattern — since RiskScore data only exists for 2023 for some countries, riskTotal will be NULL for most years. The system must correctly use OPTIONAL to avoid losing default rate rows that have no matching RiskScore.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
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
        id='M06',
        question='What were the annual total reserves for Mexico from 2005 to 2015?',
        tier='medium',
        result_type='temporal_series',
        category='temporal_range',
        notes='Total_Reserves indicator; 11-year range; tests IRI grounding for reserves',
        reference_logic="Retrieves Total_Reserves observations for Mexico from 2005 to 2015. Tests IRI grounding for economic indicators — the system must map 'total reserves' to gemr:Total_Reserves (not RESERVES_TOTAL or Foreign_Reserves_Months_Import_Cover).",
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
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
        id='C01',
        question='Which countries had private default rates above 5% between 2010 and 2020?',
        tier='complex',
        result_type='list',
        category='filter',
        notes='Observation FILTER on observationValue > 5.0; multi-country, year range',
        reference_logic='Finds all country-year combinations where the private default rate exceeded 5% between 2010 and 2020. Tests compound filtering: FILTER on both observationValue (> 5.0) AND year range. The system must combine temporal and numeric constraints in a single query. Expected results include Brazil (2014, 2016) and others.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
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
        id='C02',
        question='Rank all countries by their average total risk score from 2015 to 2023.',
        tier='complex',
        result_type='list',
        category='aggregation',
        notes='RiskScore aggregation; AVG over year range; ORDER BY; multi-country',
        reference_logic='Computes the average totalRiskScore per country over 2015-2023 and ranks them. Tests GROUP BY + AVG aggregation combined with temporal filtering and ORDER BY. Note: only Brazil and Poland have RiskScore data (both only for 2023), so the AVG equals their single-year score. Poland (82) ranks above Brazil (47).',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
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
        id='C03',
        question='For each country, what is the highest private default rate ever recorded?',
        tier='complex',
        result_type='list',
        category='aggregation',
        notes='Aggregation with MAX per country group; tests GROUP BY + MAX',
        reference_logic='Finds the maximum private default rate for each country across the entire time range. Tests GROUP BY with MAX aggregation — the system must group observations by country and compute the peak default rate. Expected: 6 countries, each with their historical peak (e.g., Brazil ~7.94%, China ~6.67%).',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
SELECT ?name (MAX(?value) AS ?maxRate) WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:Historical_private_default_rates ;
       gemr:observationValue ?value .
  ?country gemr:countryName ?name .
} GROUP BY ?name ORDER BY ?name""",
    ),
    TestQuestion(
        id='C04',
        question='Which countries had improving government effectiveness AND declining private default rates between 2015 and 2020?',
        tier='complex',
        result_type='list',
        category='compositional',
        notes='Multi-condition join: GovernmentEffectiveness + Historical_private_default_rates; endpoint comparison',
        reference_logic='Finds countries where: (1) GovernmentEffectiveness in 2020 > 2015, AND (2) private default rate in 2020 < 2015. Tests compositional query with four separate Observation triple patterns joined on the same country but different years and indicators, plus a FILTER comparing endpoint values. This is the most structurally complex query in the benchmark.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
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
        id='C05',
        question='Show me the economic health score and governance score for all countries in 2023, ordered by economic health score descending.',
        tier='complex',
        result_type='list',
        category='optional_paths',
        notes='Multi-property RiskScore projection; all countries; ORDER BY; OPTIONAL usage',
        reference_logic='Retrieves economicHealthScore and governanceScore from RiskScore entities for all countries in 2023, using OPTIONAL patterns since not all RiskScore entities have all sub-scores populated. Tests OPTIONAL join pattern and multi-property projection. Only Poland has full sub-scores; Brazil has only totalRiskScore.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
SELECT ?name ?econ ?gov WHERE {
  ?rs a gemr:RiskScore ;
      gemr:hasCountry ?country ;
      gemr:hasYear gemr:Year2023 .
  ?country gemr:countryName ?name .
  OPTIONAL { ?rs gemr:economicHealthScore ?econ }
  OPTIONAL { ?rs gemr:governanceScore ?gov }
} ORDER BY DESC(?econ)""",
    ),
    TestQuestion(
        id='L01',
        question='What is the GDP at market prices (current US$) for Brazil in 2010?',
        tier='simple',
        result_type='single_value',
        category='lookup',
        reference_logic='Looks up the GDP at market prices (current US$) observation for Brazil in 2010. Tests IRI grounding from the phrase to gemr:GDP_at_market_prices_current_US.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:GDP_at_market_prices_current_US ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Brazil" .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "2010")
}""",
    ),
    TestQuestion(
        id='L02',
        question='What is the GDP at market prices (current US$) for China in 2015?',
        tier='simple',
        result_type='single_value',
        category='lookup',
        reference_logic='Looks up the GDP at market prices (current US$) observation for China in 2015. Tests IRI grounding from the phrase to gemr:GDP_at_market_prices_current_US.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:GDP_at_market_prices_current_US ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "China" .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "2015")
}""",
    ),
    TestQuestion(
        id='L03',
        question='What is the CPI year-over-year inflation for Mexico in 2020?',
        tier='simple',
        result_type='single_value',
        category='lookup',
        reference_logic='Looks up the CPI year-over-year inflation observation for Mexico in 2020. Tests IRI grounding from the phrase to gemr:CPI_Price_Pct_yearoveryear_seasonally_adjusted.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:CPI_Price_Pct_yearoveryear_seasonally_adjusted ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Mexico" .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "2020")
}""",
    ),
    TestQuestion(
        id='L04',
        question='What is the stock market index (USD) for Philippines in 2018?',
        tier='simple',
        result_type='single_value',
        category='lookup',
        reference_logic='Looks up the stock market index (USD) observation for Philippines in 2018. Tests IRI grounding from the phrase to gemr:Stock_Market_Index_US.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:Stock_Market_Index_US ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Philippines" .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "2018")
}""",
    ),
    TestQuestion(
        id='L05',
        question='What is the private default rate for Poland in 2012?',
        tier='simple',
        result_type='single_value',
        category='lookup',
        reference_logic='Looks up the private default rate observation for Poland in 2012. Tests IRI grounding from the phrase to gemr:Historical_private_default_rates.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:Historical_private_default_rates ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Poland" .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "2012")
}""",
    ),
    TestQuestion(
        id='L06',
        question='What is the total reserves for Thailand in 2008?',
        tier='simple',
        result_type='single_value',
        category='lookup',
        reference_logic='Looks up the total reserves observation for Thailand in 2008. Tests IRI grounding from the phrase to gemr:Total_Reserves.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:Total_Reserves ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Thailand" .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "2008")
}""",
    ),
    TestQuestion(
        id='L07',
        question='What is the official exchange rate (LCU per USD) for Brazil in 2022?',
        tier='simple',
        result_type='single_value',
        category='lookup',
        reference_logic='Looks up the official exchange rate (LCU per USD) observation for Brazil in 2022. Tests IRI grounding from the phrase to gemr:Official_exchange_rate_LCU_per_USD.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:Official_exchange_rate_LCU_per_USD ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Brazil" .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "2022")
}""",
    ),
    TestQuestion(
        id='L08',
        question='What is the control of corruption score for China in 2019?',
        tier='simple',
        result_type='single_value',
        category='lookup',
        reference_logic='Looks up the control of corruption score observation for China in 2019. Tests IRI grounding from the phrase to gemr:ControlOfCorruption.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:ControlOfCorruption ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "China" .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "2019")
}""",
    ),
    TestQuestion(
        id='L09',
        question='What is the government effectiveness score for Mexico in 2021?',
        tier='simple',
        result_type='single_value',
        category='lookup',
        reference_logic='Looks up the government effectiveness score observation for Mexico in 2021. Tests IRI grounding from the phrase to gemr:GovernmentEffectiveness.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:GovernmentEffectiveness ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Mexico" .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "2021")
}""",
    ),
    TestQuestion(
        id='L10',
        question='What is the political stability score for Philippines in 2016?',
        tier='simple',
        result_type='single_value',
        category='lookup',
        reference_logic='Looks up the political stability score observation for Philippines in 2016. Tests IRI grounding from the phrase to gemr:PoliticalStability.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:PoliticalStability ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Philippines" .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "2016")
}""",
    ),
    TestQuestion(
        id='L11',
        question='What is the regulatory quality score for Poland in 2015?',
        tier='simple',
        result_type='single_value',
        category='lookup',
        reference_logic='Looks up the regulatory quality score observation for Poland in 2015. Tests IRI grounding from the phrase to gemr:RegulatoryQuality.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:RegulatoryQuality ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Poland" .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "2015")
}""",
    ),
    TestQuestion(
        id='L12',
        question='What is the rule of law score for Thailand in 2017?',
        tier='simple',
        result_type='single_value',
        category='lookup',
        reference_logic='Looks up the rule of law score observation for Thailand in 2017. Tests IRI grounding from the phrase to gemr:RuleOfLaw.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:RuleOfLaw ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Thailand" .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "2017")
}""",
    ),
    TestQuestion(
        id='L13',
        question='What is the voice and accountability score for Brazil in 2014?',
        tier='simple',
        result_type='single_value',
        category='lookup',
        reference_logic='Looks up the voice and accountability score observation for Brazil in 2014. Tests IRI grounding from the phrase to gemr:VoiceAndAccountability.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:VoiceAndAccountability ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Brazil" .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "2014")
}""",
    ),
    TestQuestion(
        id='L14',
        question='What is the real effective exchange rate for China in 2011?',
        tier='simple',
        result_type='single_value',
        category='lookup',
        reference_logic='Looks up the real effective exchange rate observation for China in 2011. Tests IRI grounding from the phrase to gemr:Real_Effective_Exchange_Rate.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:Real_Effective_Exchange_Rate ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "China" .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "2011")
}""",
    ),
    TestQuestion(
        id='L15',
        question='What is the exports (current US$, seasonally adjusted) for Mexico in 2019?',
        tier='simple',
        result_type='single_value',
        category='lookup',
        reference_logic='Looks up the exports (current US$, seasonally adjusted) observation for Mexico in 2019. Tests IRI grounding from the phrase to gemr:Exports_Merchandise_current_US_seasonally_adjusted.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:Exports_Merchandise_current_US_seasonally_adjusted ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Mexico" .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "2019")
}""",
    ),
    TestQuestion(
        id='L16',
        question='What is the imports (current US$, seasonally adjusted) for Philippines in 2020?',
        tier='simple',
        result_type='single_value',
        category='lookup',
        reference_logic='Looks up the imports (current US$, seasonally adjusted) observation for Philippines in 2020. Tests IRI grounding from the phrase to gemr:Imports_Merchandise_current_US_seasonally_adjusted.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:Imports_Merchandise_current_US_seasonally_adjusted ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Philippines" .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "2020")
}""",
    ),
    TestQuestion(
        id='T01',
        question='Show me the GDP at market prices (current US$) for Brazil from 2002 to 2023.',
        tier='medium',
        result_type='temporal_series',
        category='temporal_range',
        reference_logic='Returns the time series of GDP at market prices (current US$) observations for Brazil across 2002–2023. Tests temporal range filtering and ordering by year.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?year ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:GDP_at_market_prices_current_US ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Brazil" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?year)
  FILTER(?year >= 2002 && ?year <= 2023)
} ORDER BY ?year""",
    ),
    TestQuestion(
        id='T02',
        question='Show me the private default rate for China from 2005 to 2020.',
        tier='medium',
        result_type='temporal_series',
        category='temporal_range',
        reference_logic='Returns the time series of private default rate observations for China across 2005–2020. Tests temporal range filtering and ordering by year.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?year ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:Historical_private_default_rates ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "China" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?year)
  FILTER(?year >= 2005 && ?year <= 2020)
} ORDER BY ?year""",
    ),
    TestQuestion(
        id='T03',
        question='Show me the control of corruption score for Mexico from 2002 to 2023.',
        tier='medium',
        result_type='temporal_series',
        category='temporal_range',
        reference_logic='Returns the time series of control of corruption score observations for Mexico across 2002–2023. Tests temporal range filtering and ordering by year.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?year ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:ControlOfCorruption ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Mexico" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?year)
  FILTER(?year >= 2002 && ?year <= 2023)
} ORDER BY ?year""",
    ),
    TestQuestion(
        id='T04',
        question='Show me the government effectiveness score for Philippines from 2005 to 2020.',
        tier='medium',
        result_type='temporal_series',
        category='temporal_range',
        reference_logic='Returns the time series of government effectiveness score observations for Philippines across 2005–2020. Tests temporal range filtering and ordering by year.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?year ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:GovernmentEffectiveness ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Philippines" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?year)
  FILTER(?year >= 2005 && ?year <= 2020)
} ORDER BY ?year""",
    ),
    TestQuestion(
        id='T05',
        question='Show me the political stability score for Poland from 2002 to 2023.',
        tier='medium',
        result_type='temporal_series',
        category='temporal_range',
        reference_logic='Returns the time series of political stability score observations for Poland across 2002–2023. Tests temporal range filtering and ordering by year.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?year ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:PoliticalStability ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Poland" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?year)
  FILTER(?year >= 2002 && ?year <= 2023)
} ORDER BY ?year""",
    ),
    TestQuestion(
        id='T06',
        question='Show me the real effective exchange rate for Thailand from 2002 to 2023.',
        tier='medium',
        result_type='temporal_series',
        category='temporal_range',
        reference_logic='Returns the time series of real effective exchange rate observations for Thailand across 2002–2023. Tests temporal range filtering and ordering by year.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?year ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:Real_Effective_Exchange_Rate ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Thailand" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?year)
  FILTER(?year >= 2002 && ?year <= 2023)
} ORDER BY ?year""",
    ),
    TestQuestion(
        id='T07',
        question='Show me the stock market index (USD) for Brazil from 2010 to 2023.',
        tier='medium',
        result_type='temporal_series',
        category='temporal_range',
        reference_logic='Returns the time series of stock market index (USD) observations for Brazil across 2010–2023. Tests temporal range filtering and ordering by year.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?year ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:Stock_Market_Index_US ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Brazil" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?year)
  FILTER(?year >= 2010 && ?year <= 2023)
} ORDER BY ?year""",
    ),
    TestQuestion(
        id='T08',
        question='Show me the official exchange rate (LCU per USD) for China from 2002 to 2023.',
        tier='medium',
        result_type='temporal_series',
        category='temporal_range',
        reference_logic='Returns the time series of official exchange rate (LCU per USD) observations for China across 2002–2023. Tests temporal range filtering and ordering by year.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?year ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:Official_exchange_rate_LCU_per_USD ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "China" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?year)
  FILTER(?year >= 2002 && ?year <= 2023)
} ORDER BY ?year""",
    ),
    TestQuestion(
        id='T09',
        question='Show me the total reserves for Mexico from 2005 to 2015.',
        tier='medium',
        result_type='temporal_series',
        category='temporal_range',
        reference_logic='Returns the time series of total reserves observations for Mexico across 2005–2015. Tests temporal range filtering and ordering by year.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?year ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:Total_Reserves ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Mexico" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?year)
  FILTER(?year >= 2005 && ?year <= 2015)
} ORDER BY ?year""",
    ),
    TestQuestion(
        id='T10',
        question='Show me the public default rate for Poland from 2002 to 2023.',
        tier='medium',
        result_type='temporal_series',
        category='temporal_range',
        reference_logic='Returns the time series of public default rate observations for Poland across 2002–2023. Tests temporal range filtering and ordering by year.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?year ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:Historical_public_default_rates ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Poland" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?year)
  FILTER(?year >= 2002 && ?year <= 2023)
} ORDER BY ?year""",
    ),
    TestQuestion(
        id='T11',
        question='Show me the CPI year-over-year inflation for Thailand from 2010 to 2020.',
        tier='medium',
        result_type='temporal_series',
        category='temporal_range',
        reference_logic='Returns the time series of CPI year-over-year inflation observations for Thailand across 2010–2020. Tests temporal range filtering and ordering by year.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?year ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:CPI_Price_Pct_yearoveryear_seasonally_adjusted ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Thailand" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?year)
  FILTER(?year >= 2010 && ?year <= 2020)
} ORDER BY ?year""",
    ),
    TestQuestion(
        id='T12',
        question='Show me the imports (current US$, seasonally adjusted) for Philippines from 2010 to 2023.',
        tier='medium',
        result_type='temporal_series',
        category='temporal_range',
        reference_logic='Returns the time series of imports (current US$, seasonally adjusted) observations for Philippines across 2010–2023. Tests temporal range filtering and ordering by year.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?year ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:Imports_Merchandise_current_US_seasonally_adjusted ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Philippines" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?year)
  FILTER(?year >= 2010 && ?year <= 2023)
} ORDER BY ?year""",
    ),
    TestQuestion(
        id='X01',
        question='Show the GDP at market prices (current US$) for all countries in 2020.',
        tier='medium',
        result_type='list',
        category='cross_country_snapshot',
        reference_logic='Returns the GDP at market prices (current US$) for every country in 2020. Tests multi-country enumeration via gemr:countryName variable binding.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?country ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?c ;
       gemr:hasIndicator gemr:GDP_at_market_prices_current_US ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?c gemr:countryName ?country .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "2020")
} ORDER BY ?country""",
    ),
    TestQuestion(
        id='X02',
        question='Show the private default rate for all countries in 2015.',
        tier='medium',
        result_type='list',
        category='cross_country_snapshot',
        reference_logic='Returns the private default rate for every country in 2015. Tests multi-country enumeration via gemr:countryName variable binding.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?country ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?c ;
       gemr:hasIndicator gemr:Historical_private_default_rates ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?c gemr:countryName ?country .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "2015")
} ORDER BY ?country""",
    ),
    TestQuestion(
        id='X03',
        question='Show the control of corruption score for all countries in 2019.',
        tier='medium',
        result_type='list',
        category='cross_country_snapshot',
        reference_logic='Returns the control of corruption score for every country in 2019. Tests multi-country enumeration via gemr:countryName variable binding.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?country ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?c ;
       gemr:hasIndicator gemr:ControlOfCorruption ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?c gemr:countryName ?country .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "2019")
} ORDER BY ?country""",
    ),
    TestQuestion(
        id='X04',
        question='Show the political stability score for all countries in 2022.',
        tier='medium',
        result_type='list',
        category='cross_country_snapshot',
        reference_logic='Returns the political stability score for every country in 2022. Tests multi-country enumeration via gemr:countryName variable binding.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?country ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?c ;
       gemr:hasIndicator gemr:PoliticalStability ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?c gemr:countryName ?country .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "2022")
} ORDER BY ?country""",
    ),
    TestQuestion(
        id='X05',
        question='Show the stock market index (USD) for all countries in 2018.',
        tier='medium',
        result_type='list',
        category='cross_country_snapshot',
        reference_logic='Returns the stock market index (USD) for every country in 2018. Tests multi-country enumeration via gemr:countryName variable binding.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?country ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?c ;
       gemr:hasIndicator gemr:Stock_Market_Index_US ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?c gemr:countryName ?country .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "2018")
} ORDER BY ?country""",
    ),
    TestQuestion(
        id='X06',
        question='Show the total reserves for all countries in 2010.',
        tier='medium',
        result_type='list',
        category='cross_country_snapshot',
        reference_logic='Returns the total reserves for every country in 2010. Tests multi-country enumeration via gemr:countryName variable binding.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?country ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?c ;
       gemr:hasIndicator gemr:Total_Reserves ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?c gemr:countryName ?country .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "2010")
} ORDER BY ?country""",
    ),
    TestQuestion(
        id='X07',
        question='Show the real effective exchange rate for all countries in 2021.',
        tier='medium',
        result_type='list',
        category='cross_country_snapshot',
        reference_logic='Returns the real effective exchange rate for every country in 2021. Tests multi-country enumeration via gemr:countryName variable binding.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?country ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?c ;
       gemr:hasIndicator gemr:Real_Effective_Exchange_Rate ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?c gemr:countryName ?country .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "2021")
} ORDER BY ?country""",
    ),
    TestQuestion(
        id='X08',
        question='Show the exports (current US$, seasonally adjusted) for all countries in 2017.',
        tier='medium',
        result_type='list',
        category='cross_country_snapshot',
        reference_logic='Returns the exports (current US$, seasonally adjusted) for every country in 2017. Tests multi-country enumeration via gemr:countryName variable binding.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?country ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?c ;
       gemr:hasIndicator gemr:Exports_Merchandise_current_US_seasonally_adjusted ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?c gemr:countryName ?country .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "2017")
} ORDER BY ?country""",
    ),
    TestQuestion(
        id='R01',
        question='Which country had the highest GDP at market prices (current US$) in 2020?',
        tier='medium',
        result_type='single_value',
        category='superlative',
        reference_logic='Finds the country with the highest GDP at market prices (current US$) in 2020. Tests ORDER BY DESC + LIMIT 1 superlative pattern.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?country ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?c ;
       gemr:hasIndicator gemr:GDP_at_market_prices_current_US ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?c gemr:countryName ?country .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "2020")
} ORDER BY DESC(?value) LIMIT 1""",
    ),
    TestQuestion(
        id='R02',
        question='Which country had the highest private default rate in 2010?',
        tier='medium',
        result_type='single_value',
        category='superlative',
        reference_logic='Finds the country with the highest private default rate in 2010. Tests ORDER BY DESC + LIMIT 1 superlative pattern.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?country ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?c ;
       gemr:hasIndicator gemr:Historical_private_default_rates ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?c gemr:countryName ?country .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "2010")
} ORDER BY DESC(?value) LIMIT 1""",
    ),
    TestQuestion(
        id='R03',
        question='Which country had the highest control of corruption score in 2022?',
        tier='medium',
        result_type='single_value',
        category='superlative',
        reference_logic='Finds the country with the highest control of corruption score in 2022. Tests ORDER BY DESC + LIMIT 1 superlative pattern.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?country ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?c ;
       gemr:hasIndicator gemr:ControlOfCorruption ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?c gemr:countryName ?country .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "2022")
} ORDER BY DESC(?value) LIMIT 1""",
    ),
    TestQuestion(
        id='R04',
        question='Which country had the lowest political stability score in 2015?',
        tier='medium',
        result_type='single_value',
        category='superlative',
        reference_logic='Finds the country with the lowest political stability score in 2015. Tests ORDER BY ASC + LIMIT 1 superlative pattern.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?country ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?c ;
       gemr:hasIndicator gemr:PoliticalStability ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?c gemr:countryName ?country .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "2015")
} ORDER BY ASC(?value) LIMIT 1""",
    ),
    TestQuestion(
        id='R05',
        question='Which country had the highest total reserves in 2018?',
        tier='medium',
        result_type='single_value',
        category='superlative',
        reference_logic='Finds the country with the highest total reserves in 2018. Tests ORDER BY DESC + LIMIT 1 superlative pattern.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?country ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?c ;
       gemr:hasIndicator gemr:Total_Reserves ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?c gemr:countryName ?country .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "2018")
} ORDER BY DESC(?value) LIMIT 1""",
    ),
    TestQuestion(
        id='R06',
        question='Which country had the lowest official exchange rate (LCU per USD) in 2019?',
        tier='medium',
        result_type='single_value',
        category='superlative',
        reference_logic='Finds the country with the lowest official exchange rate (LCU per USD) in 2019. Tests ORDER BY ASC + LIMIT 1 superlative pattern.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?country ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?c ;
       gemr:hasIndicator gemr:Official_exchange_rate_LCU_per_USD ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?c gemr:countryName ?country .
  ?yearEntity gemr:yearValue ?yLit .
  FILTER(STR(?yLit) = "2019")
} ORDER BY ASC(?value) LIMIT 1""",
    ),
    TestQuestion(
        id='D01',
        question='How did the control of corruption score for Brazil change between 2010 and 2020?',
        tier='medium',
        result_type='comparison',
        category='change_over_time',
        reference_logic="Returns the control of corruption score for Brazil at the two endpoints 2010 and 2020. Tests the 'change between two years' pattern via FILTER(?year = a || ?year = b).",
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?year ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:ControlOfCorruption ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Brazil" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?year)
  FILTER(?year = 2010 || ?year = 2020)
} ORDER BY ?year""",
    ),
    TestQuestion(
        id='D02',
        question='How did the GDP at market prices (current US$) for China change between 2008 and 2013?',
        tier='medium',
        result_type='comparison',
        category='change_over_time',
        reference_logic="Returns the GDP at market prices (current US$) for China at the two endpoints 2008 and 2013. Tests the 'change between two years' pattern via FILTER(?year = a || ?year = b).",
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?year ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:GDP_at_market_prices_current_US ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "China" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?year)
  FILTER(?year = 2008 || ?year = 2013)
} ORDER BY ?year""",
    ),
    TestQuestion(
        id='D03',
        question='How did the private default rate for Mexico change between 2010 and 2020?',
        tier='medium',
        result_type='comparison',
        category='change_over_time',
        reference_logic="Returns the private default rate for Mexico at the two endpoints 2010 and 2020. Tests the 'change between two years' pattern via FILTER(?year = a || ?year = b).",
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?year ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:Historical_private_default_rates ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Mexico" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?year)
  FILTER(?year = 2010 || ?year = 2020)
} ORDER BY ?year""",
    ),
    TestQuestion(
        id='D04',
        question='How did the government effectiveness score for Poland change between 2005 and 2015?',
        tier='medium',
        result_type='comparison',
        category='change_over_time',
        reference_logic="Returns the government effectiveness score for Poland at the two endpoints 2005 and 2015. Tests the 'change between two years' pattern via FILTER(?year = a || ?year = b).",
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?year ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:GovernmentEffectiveness ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Poland" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?year)
  FILTER(?year = 2005 || ?year = 2015)
} ORDER BY ?year""",
    ),
    TestQuestion(
        id='D05',
        question='How did the official exchange rate (LCU per USD) for Thailand change between 2008 and 2012?',
        tier='medium',
        result_type='comparison',
        category='change_over_time',
        reference_logic="Returns the official exchange rate (LCU per USD) for Thailand at the two endpoints 2008 and 2012. Tests the 'change between two years' pattern via FILTER(?year = a || ?year = b).",
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?year ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:Official_exchange_rate_LCU_per_USD ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Thailand" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?year)
  FILTER(?year = 2008 || ?year = 2012)
} ORDER BY ?year""",
    ),
    TestQuestion(
        id='D06',
        question='How did the real effective exchange rate for Philippines change between 2010 and 2020?',
        tier='medium',
        result_type='comparison',
        category='change_over_time',
        reference_logic="Returns the real effective exchange rate for Philippines at the two endpoints 2010 and 2020. Tests the 'change between two years' pattern via FILTER(?year = a || ?year = b).",
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?year ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:Real_Effective_Exchange_Rate ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Philippines" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?year)
  FILTER(?year = 2010 || ?year = 2020)
} ORDER BY ?year""",
    ),
    TestQuestion(
        id='A01',
        question='What was the average GDP at market prices (current US$) for Brazil from 2015 to 2020?',
        tier='medium',
        result_type='single_value',
        category='aggregation',
        reference_logic='Computes AVG of GDP at market prices (current US$) for Brazil across 2015–2020. Tests aggregation (AVG) combined with temporal filtering.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT (AVG(?value) AS ?avgValue) WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:GDP_at_market_prices_current_US ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Brazil" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?year)
  FILTER(?year >= 2015 && ?year <= 2020)
}""",
    ),
    TestQuestion(
        id='A02',
        question='What was the average control of corruption score for China from 2010 to 2020?',
        tier='medium',
        result_type='single_value',
        category='aggregation',
        reference_logic='Computes AVG of control of corruption score for China across 2010–2020. Tests aggregation (AVG) combined with temporal filtering.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT (AVG(?value) AS ?avgValue) WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:ControlOfCorruption ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "China" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?year)
  FILTER(?year >= 2010 && ?year <= 2020)
}""",
    ),
    TestQuestion(
        id='A03',
        question='What was the average private default rate for Mexico from 2005 to 2015?',
        tier='medium',
        result_type='single_value',
        category='aggregation',
        reference_logic='Computes AVG of private default rate for Mexico across 2005–2015. Tests aggregation (AVG) combined with temporal filtering.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT (AVG(?value) AS ?avgValue) WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:Historical_private_default_rates ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Mexico" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?year)
  FILTER(?year >= 2005 && ?year <= 2015)
}""",
    ),
    TestQuestion(
        id='A04',
        question='What was the average real effective exchange rate for Poland from 2010 to 2020?',
        tier='medium',
        result_type='single_value',
        category='aggregation',
        reference_logic='Computes AVG of real effective exchange rate for Poland across 2010–2020. Tests aggregation (AVG) combined with temporal filtering.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT (AVG(?value) AS ?avgValue) WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:Real_Effective_Exchange_Rate ;
       gemr:hasYear ?yearEntity ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Poland" .
  ?yearEntity gemr:yearValue ?yLit .
  BIND(xsd:integer(STR(?yLit)) AS ?year)
  FILTER(?year >= 2010 && ?year <= 2020)
}""",
    ),
    TestQuestion(
        id='F01',
        question='What is the comprehensive risk profile for Poland in 2023, including total score, risk tier, and component scores?',
        tier='complex',
        result_type='list',
        category='frontend_risk_profile',
        notes="Verbatim from SparqlInterface.jsx 'Risk Profile Dashboard (2023)'",
        reference_logic='Risk Profile Dashboard (2023) — retrieves total risk score plus all optional component scores and the risk tier for Poland. Extensive use of OPTIONAL to tolerate missing sub-scores.',
        reference_sparql="""PREFIX gemr: <https://gemr-kg.org/ontology#>
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
}""",
    ),
    TestQuestion(
        id='F02',
        question='Does stock market performance in year T predict private default rates in year T+1? Show the average default rate following each stock observation.',
        tier='complex',
        result_type='list',
        category='frontend_early_warning',
        notes="Verbatim from SparqlInterface.jsx '1. Early Warning (Stock -> Default)'",
        reference_logic='Early Warning (Stock → Default): joins stock market observations at year T with private default rate observations at T+1, aggregated to an average default rate per stock observation.',
        reference_sparql="""PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
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
LIMIT 100""",
    ),
    TestQuestion(
        id='F03',
        question='How does negative political stability in year T impact real-economy GDP in year T+1?',
        tier='complex',
        result_type='list',
        category='frontend_stability_gdp',
        notes="Verbatim from SparqlInterface.jsx '2. Political Stability -> GDP'",
        reference_logic='Negative political stability at year T joined to GDP (constant 2010 USD) at year T+1, averaged per country-year pair.',
        reference_sparql="""PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
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
LIMIT 50""",
    ),
    TestQuestion(
        id='F04',
        question='Show the relationship between stock market performance and real-economy GDP in the following year.',
        tier='complex',
        result_type='list',
        category='frontend_default_recovery',
        notes="Verbatim from SparqlInterface.jsx '3. Default -> Recovery'",
        reference_logic='Stock market LCU at year T joined to GDP (const 2010 USD) at year T+1; tolerates either Year IRI subject or typed literal.',
        reference_sparql="""PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
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
ORDER BY ?countryName ?yearT""",
    ),
    TestQuestion(
        id='F05',
        question='Calculate the annual GDP growth rate (percentage) for all countries.',
        tier='complex',
        result_type='list',
        category='frontend_gdp_growth',
        notes="Verbatim from SparqlInterface.jsx '4. GDP Growth Tracker'",
        reference_logic='Year-over-year GDP growth rate via self-join on GDP_CONST_2010_USD at year and year-1, then percentage delta.',
        reference_sparql="""PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
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
LIMIT 100""",
    ),
]
