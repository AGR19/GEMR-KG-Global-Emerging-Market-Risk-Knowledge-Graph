# GEMR-KG Ground Truth Questions

> **20 benchmark questions** with gold-standard SPARQL queries verified against live GraphDB.  
> Every query returns real data. These serve as the reference for Answer Accuracy (AA) evaluation.

---

## Simple (8 queries)

| ID | Question | Category | What It Tests | Expected |
|---|---|---|---|---|
| **S01** | Total risk score for Poland 2023 | Lookup | Basic RiskScore entity match | 82 |
| **S02** | Control of corruption for Brazil 2020 | Lookup | Governance indicator IRI grounding | -0.43 |
| **S03** | Private default rate for China 2015 | Lookup | Default rate indicator grounding | 6.67% |
| **S04** | Countries with risk score data in 2023 | Lookup | DISTINCT enumeration | Brazil, Poland |
| **S05** | GDP (current US$) for Mexico 2019 | Lookup | Economic indicator IRI grounding | ~$1.3T |
| **S06** | Private defaults for Brazil 2002-2023 | Temporal range | Time series + year filtering | 22 years |
| **S07** | Political stability for Thailand 2010 | Lookup | Governance sub-indicator grounding | -1.44 |
| **S08** | Country with highest risk score 2023 | Superlative | ORDER BY DESC + LIMIT 1 | Poland (82) |

---

## Medium (7 queries)

| ID | Question | Category | What It Tests | Rows |
|---|---|---|---|---|
| **M01** | GDP for all countries 2010-2020 | Temporal range | Multi-country + year range | 176 |
| **M02** | Corruption score Poland 2005-2023 | Temporal range | Long time series | 76 |
| **M03** | Stock market 2008 vs defaults 2009 (China) | Cross-indicator | Two indicators, temporal lag join | 1 |
| **M04** | Gov effectiveness Brazil 2015-2020 | Temporal range | Governance sub-indicator time series | 24 |
| **M05** | Default rates + risk scores Philippines | Cross-indicator | OPTIONAL join (missing data) | 28 |
| **M06** | Total reserves Mexico 2005-2015 | Temporal range | Economic indicator grounding | 22 |
| **M07** | Exchange rates Thailand 2008-2012 | Temporal range | Disambiguating multiple exchange rate IRIs | 10 |

---

## Complex (5 queries)

| ID | Question | Category | What It Tests | Rows |
|---|---|---|---|---|
| **C01** | Countries with default rates > 5% (2010-2020) | Filter | Compound FILTER (numeric + temporal) | 17 |
| **C02** | Rank countries by avg risk score 2015-2023 | Aggregation | GROUP BY + AVG + ORDER BY | 2 |
| **C03** | Highest default rate ever per country | Aggregation | GROUP BY + MAX | 6 |
| **C04** | Improving governance AND declining defaults 2015-2020 | Compositional | 4 observation patterns + endpoint comparison | 4 |
| **C05** | Health + governance scores for all 2023 | Optional paths | OPTIONAL multi-property projection | 2 |

---

## Reference SPARQL Queries

### S01 — Total risk score for Poland in 2023

**Logic:** Retrieves the composite totalRiskScore from the RiskScore entity for Poland in 2023. Tests the most basic KG access pattern: match a typed entity (`gemr:RiskScore`) filtered by country name and a specific year entity (`gemr:Year2023`). Expected: 82.

```sparql
PREFIX gemr: <https://gemr-kg.org/ontology#>
SELECT ?total WHERE {
  ?rs a gemr:RiskScore ;
      gemr:hasCountry ?country ;
      gemr:hasYear gemr:Year2023 ;
      gemr:totalRiskScore ?total .
  ?country gemr:countryName "Poland" .
}
```

---

### S02 — Control of corruption score for Brazil in 2020

**Logic:** Retrieves the ControlOfCorruption governance indicator observation for Brazil in 2020. Tests the Observation query pattern with `gemr:hasIndicator` pointing to a specific governance metric. The system must ground "control of corruption" to the exact IRI `gemr:ControlOfCorruption` rather than hallucinating an IRI.

```sparql
PREFIX gemr: <https://gemr-kg.org/ontology#>
SELECT ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:ControlOfCorruption ;
       gemr:hasYear gemr:Year2020 ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Brazil" .
}
```

---

### S03 — Private default rate for China in 2015

**Logic:** Retrieves the private default rate observation for China in 2015. Tests IRI grounding: the system must map "private default rate" to `gemr:Historical_private_default_rates` (not a hallucinated IRI like `gemr:PrivateDefaultRate`). Expected: ~6.67%.

```sparql
PREFIX gemr: <https://gemr-kg.org/ontology#>
SELECT ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:Historical_private_default_rates ;
       gemr:hasYear gemr:Year2015 ;
       gemr:observationValue ?value .
  ?country gemr:countryName "China" .
}
```

---

### S04 — List all countries that have risk score data in 2023

**Logic:** Finds all countries that have a RiskScore entity for 2023. Tests DISTINCT projection and the ability to enumerate across multiple entities. Only Brazil and Poland have RiskScore data in the KG, so the expected result is exactly 2 countries.

```sparql
PREFIX gemr: <https://gemr-kg.org/ontology#>
SELECT DISTINCT ?name WHERE {
  ?rs a gemr:RiskScore ;
      gemr:hasCountry ?country ;
      gemr:hasYear gemr:Year2023 .
  ?country gemr:countryName ?name .
} ORDER BY ?name
```

---

### S05 — GDP at market prices (current US$) for Mexico in 2019

**Logic:** Retrieves the GDP at market prices (current US$) observation for Mexico in 2019. Tests IRI grounding for economic indicators: the system must map "GDP at market prices" to `gemr:GDP_at_market_prices_current_US`. Expected: ~$1.3 trillion.

```sparql
PREFIX gemr: <https://gemr-kg.org/ontology#>
SELECT ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:GDP_at_market_prices_current_US ;
       gemr:hasYear gemr:Year2019 ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Mexico" .
}
```

---

### S06 — Private default rates for Brazil from 2002 to 2023

**Logic:** Retrieves all private default rate observations for Brazil across the full time range (2002-2023). Tests temporal filtering with BIND/FILTER on yearValue, and the ability to produce an ordered time series. Expected: 22 rows, one per year.

```sparql
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
} ORDER BY ?yearInt
```

---

### S07 — Political stability score for Thailand in 2010

**Logic:** Retrieves the Political Stability governance indicator for Thailand in 2010. Tests IRI grounding for governance sub-indicators: the system must map "political stability" to `gemr:PoliticalStability`.

```sparql
PREFIX gemr: <https://gemr-kg.org/ontology#>
SELECT ?value WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:PoliticalStability ;
       gemr:hasYear gemr:Year2010 ;
       gemr:observationValue ?value .
  ?country gemr:countryName "Thailand" .
}
```

---

### S08 — Country with highest total risk score in 2023

**Logic:** Finds the country with the highest totalRiskScore in 2023. Tests superlative query pattern (`ORDER BY DESC` + `LIMIT 1`). Expected: Poland (82), since only Brazil (47) and Poland (82) have RiskScore data.

```sparql
PREFIX gemr: <https://gemr-kg.org/ontology#>
SELECT ?name ?total WHERE {
  ?rs a gemr:RiskScore ;
      gemr:hasCountry ?country ;
      gemr:hasYear gemr:Year2023 ;
      gemr:totalRiskScore ?total .
  ?country gemr:countryName ?name .
} ORDER BY DESC(?total) LIMIT 1
```

---

### M01 — GDP at market prices (current US$) for each country from 2010 to 2020

**Logic:** Retrieves GDP (current US$) observations for ALL countries across 2010-2020. Tests multi-country enumeration combined with temporal range filtering. The system must correctly ground "GDP at market prices" to `gemr:GDP_at_market_prices_current_US` and apply integer year filtering via BIND/FILTER.

```sparql
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
} ORDER BY ?name ?yearInt
```

---

### M02 — Control of corruption score for Poland from 2005 to 2023

**Logic:** Retrieves the ControlOfCorruption governance indicator for Poland from 2005 to 2023. Tests long temporal range filtering on a governance sub-indicator. Shows how Poland's corruption control evolved over nearly two decades.

```sparql
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
} ORDER BY ?yearInt
```

---

### M03 — Stock market performance in China 2008 vs default rates 2009

**Logic:** Joins two different indicator observations for China across consecutive years: stock market performance (2008) vs private default rate (2009). Tests cross-indicator pattern with a temporal lag — the system must generate two separate Observation triple patterns joined on the same country but different years and indicators. This is a causal/predictive analysis query.

```sparql
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
}
```

---

### M04 — Government effectiveness scores in Brazil from 2015 to 2020

**Logic:** Retrieves the GovernmentEffectiveness WGI indicator for Brazil from 2015 to 2020. Tests IRI grounding for a specific governance sub-indicator (not the composite governanceScore on RiskScore, but the raw WGI observation). Shows Brazil's institutional quality trajectory during a period of political instability.

```sparql
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
} ORDER BY ?yearInt
```

---

### M05 — Private default rates and risk scores for the Philippines 2010-2023

**Logic:** Retrieves private default rate observations for the Philippines (2010-2023) with an OPTIONAL join to RiskScore totalRiskScore. Tests the OPTIONAL pattern — since RiskScore data only exists for 2023 for some countries, riskTotal will be NULL for most years. The system must correctly use OPTIONAL to avoid losing default rate rows that have no matching RiskScore.

```sparql
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
} ORDER BY ?yearInt
```

---

### M06 — Annual total reserves for Mexico from 2005 to 2015

**Logic:** Retrieves Total_Reserves observations for Mexico from 2005 to 2015. Tests IRI grounding for economic indicators — the system must map "total reserves" to `gemr:Total_Reserves` (not `RESERVES_TOTAL` or `Foreign_Reserves_Months_Import_Cover`).

```sparql
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
} ORDER BY ?yearInt
```

---

### M07 — Exchange rates in Thailand between 2008 and 2012

**Logic:** Retrieves Official_exchange_rate_LCU_per_USD observations for Thailand from 2008 to 2012. Tests IRI grounding for exchange rate indicators — multiple exchange rate IRIs exist in the KG (`Official_exchange_rate_LCU_per_USD`, `Exchange_rate_new_LCU_per_USD`, `Exchange_rate_old_LCU_per_USD`, `XRATE_OFFICIAL`, etc.) and the system must pick the correct one.

```sparql
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
} ORDER BY ?yearInt
```

---

### C01 — Countries with private default rates above 5% between 2010 and 2020

**Logic:** Finds all country-year combinations where the private default rate exceeded 5% between 2010 and 2020. Tests compound filtering: FILTER on both observationValue (> 5.0) AND year range. The system must combine temporal and numeric constraints in a single query. Expected results include Brazil (2014, 2016) and others.

```sparql
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
} ORDER BY ?name ?yearInt
```

---

### C02 — Rank all countries by average total risk score from 2015 to 2023

**Logic:** Computes the average totalRiskScore per country over 2015-2023 and ranks them. Tests GROUP BY + AVG aggregation combined with temporal filtering and ORDER BY. Note: only Brazil and Poland have RiskScore data (both only for 2023), so the AVG equals their single-year score. Poland (82) ranks above Brazil (47).

```sparql
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
} GROUP BY ?name ORDER BY DESC(?avgRisk)
```

---

### C03 — Highest private default rate ever recorded per country

**Logic:** Finds the maximum private default rate for each country across the entire time range. Tests GROUP BY with MAX aggregation — the system must group observations by country and compute the peak default rate. Expected: 6 countries, each with their historical peak (e.g., Brazil ~7.94%, China ~6.67%).

```sparql
PREFIX gemr: <https://gemr-kg.org/ontology#>
SELECT ?name (MAX(?value) AS ?maxRate) WHERE {
  ?obs a gemr:Observation ;
       gemr:hasCountry ?country ;
       gemr:hasIndicator gemr:Historical_private_default_rates ;
       gemr:observationValue ?value .
  ?country gemr:countryName ?name .
} GROUP BY ?name ORDER BY ?name
```

---

### C04 — Countries with improving governance AND declining defaults (2015-2020)

**Logic:** Finds countries where: (1) GovernmentEffectiveness in 2020 > 2015, AND (2) private default rate in 2020 < 2015. Tests compositional query with four separate Observation triple patterns joined on the same country but different years and indicators, plus a FILTER comparing endpoint values. This is the most structurally complex query in the benchmark.

```sparql
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
}
```

---

### C05 — Economic health and governance scores for all countries in 2023

**Logic:** Retrieves economicHealthScore and governanceScore from RiskScore entities for all countries in 2023, using OPTIONAL patterns since not all RiskScore entities have all sub-scores populated. Tests OPTIONAL join pattern and multi-property projection. Only Poland has full sub-scores; Brazil has only totalRiskScore.

```sparql
PREFIX gemr: <https://gemr-kg.org/ontology#>
SELECT ?name ?econ ?gov WHERE {
  ?rs a gemr:RiskScore ;
      gemr:hasCountry ?country ;
      gemr:hasYear gemr:Year2023 .
  ?country gemr:countryName ?name .
  OPTIONAL { ?rs gemr:economicHealthScore ?econ }
  OPTIONAL { ?rs gemr:governanceScore ?gov }
} ORDER BY DESC(?econ)
```

---

## Questions Changed from Original Set

| ID | Original Question | New Question | Reason |
|---|---|---|---|
| S02 | Governance score for Brazil in 2020 | Control of corruption for Brazil in 2020 | RiskScore only exists for Brazil/Poland in 2023; no sub-scores for Brazil |
| S05 | Economic health score for Mexico in 2019 | GDP (current US$) for Mexico in 2019 | No RiskScore entity exists for Mexico at all |
| S07 | Total risk score for Thailand in 2010 | Political stability for Thailand in 2010 | No RiskScore entity exists for Thailand at all |
