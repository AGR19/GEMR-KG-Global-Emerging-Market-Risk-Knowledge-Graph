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


---

## Paper Validation (7 queries)

| ID | Question | Category | What It Tests |
|---|---|---|---|
| **P01** | Comprehensive risk profile for Poland in 2023 | Optional paths | Risk Profile Dashboard (2023) from paper |
| **P02** | Stock market performance predicting default rates | Cross-indicator | Early Warning (Stock -> Default) from paper |
| **P03** | Political stability impact on GDP | Cross-indicator | Political Stability -> GDP from paper |
| **P04** | Stock market vs real economy GDP | Cross-indicator | Default -> Recovery from paper |
| **P05** | GDP growth tracker | Calculation | GDP Growth Tracker from paper |
| **P06** | Trade-based contagion (GDP -> Exports -> GDP) | Multi-hop contagion | Trade-Based Contagion from paper |
| **P07** | Currency crisis early warning spillover | Multi-hop contagion | Currency Crisis Early Warning from paper |

---

### P01 — Risk Profile Dashboard (2023)

**Logic:** Retrieves the total risk score, risk classification, and all underlying component scores (Governance, Economic, etc.) for Poland in 2023. Tests extensive use of OPTIONAL matching.

```sparql
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
}
```

---

### P02 — Early Warning (Stock -> Default)

**Logic:** Stock Market (t) vs Default Risk (t+1). Tests temporal lags and cross-indicator joins across consecutive years.

```sparql
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
    ?obsDefault a gemr:PrivateDefaultRate ;
                gemr:hasCountry ?c ;
                gemr:hasYear ?targetYearEntity ;
                gemr:observationValue ?defaultRate .
    ?c gemr:countryName ?countryName .
}
GROUP BY ?countryName ?yearInt ?stockValue ?targetYearInt
ORDER BY ?countryName ?yearInt
LIMIT 100
```

---

### P03 — Political Stability -> GDP

**Logic:** Impact of Political Stability (t) on GDP (t+1). Tests finding negative governance scores and joining with economic outcomes the following year.

```sparql
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
LIMIT 50
```

---

### P04 — Default -> Recovery

**Logic:** Stock Market (t) vs Real Economy GDP (t+1). Tests cross-indicator alignment with flexible year handling.

```sparql
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
ORDER BY ?countryName ?yearT
```

---

### P05 — GDP Growth Tracker

**Logic:** Calculated annual GDP growth (t vs t-1). Tests joining the same indicator across consecutive years and computing the percentage change formula.

```sparql
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
LIMIT 100
```

---

### P06 — Trade-Based Contagion

**Logic:** GDP (Source t) -> Exports (Partner t) -> GDP (Partner t+1). Extremely complex multi-hop contagion analysis utilizing UNIONs for linkage types and multiple growth rate calculations.

```sparql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX gemr: <https://gemr-kg.org/ontology#>

SELECT ?sourceCountry ?partnerCountry ?yearT 
       (AVG(?sourceGDP_Growth_Pct) AS ?avgSourceGrowth)
       (AVG(?partnerExport_Growth_Pct) AS ?avgPartnerExportGrowth)
       (AVG(?partnerGDP_Growth_NextYear_Pct) AS ?avgPartnerNextGDP)
WHERE {
    { ?partner gemr:similarTo ?source . } 
    UNION 
    { ?partner gemr:belongsToCluster ?cluster . ?source gemr:belongsToCluster ?cluster . FILTER(?source != ?partner) } 
    UNION 
    { 
        ?source gemr:countryName ?sName . ?partner gemr:countryName ?pName . 
        FILTER ((STR(?sName) = "Brazil" && STR(?pName) = "Mexico")) 
    }
    ?obsSourceGDP_T a gemr:GDP_CONST_2010_USD ; gemr:hasCountry ?source ; gemr:hasYear ?yT_Raw ; gemr:observationValue ?s_gdp_T .
    ?obsSourceGDP_Prev a gemr:GDP_CONST_2010_USD ; gemr:hasCountry ?source ; gemr:hasYear ?yPrev_Raw ; gemr:observationValue ?s_gdp_Prev .
    ?obsPartnerExp_T a gemr:EXPORTS_CURR_SEAS ; gemr:hasCountry ?partner ; gemr:hasYear ?yT_Raw ; gemr:observationValue ?p_exp_T .
    ?obsPartnerExp_Prev a gemr:EXPORTS_CURR_SEAS ; gemr:hasCountry ?partner ; gemr:hasYear ?yPrev_Raw ; gemr:observationValue ?p_exp_Prev .
    ?obsPartnerGDP_Next a gemr:GDP_CONST_2010_USD ; gemr:hasCountry ?partner ; gemr:hasYear ?yNext_Raw ; gemr:observationValue ?p_gdp_Next .
    ?obsPartnerGDP_T_ForCalc a gemr:GDP_CONST_2010_USD ; gemr:hasCountry ?partner ; gemr:hasYear ?yT_Raw ; gemr:observationValue ?p_gdp_T .
    OPTIONAL { ?yT_Raw gemr:yearValue ?yT_Val }
    OPTIONAL { ?yPrev_Raw gemr:yearValue ?yPrev_Val }
    OPTIONAL { ?yNext_Raw gemr:yearValue ?yNext_Val }
    BIND(COALESCE(xsd:integer(STR(?yT_Val)), ?yT_Raw) AS ?yearT)
    BIND(COALESCE(xsd:integer(STR(?yPrev_Val)), ?yPrev_Raw) AS ?yearPrev)
    BIND(COALESCE(xsd:integer(STR(?yNext_Val)), ?yNext_Raw) AS ?yearNext)
    FILTER(?yearPrev = ?yearT - 1)
    FILTER(?yearNext = ?yearT + 1)
    BIND(((?s_gdp_T - ?s_gdp_Prev) / ?s_gdp_Prev) * 100 AS ?sourceGDP_Growth_Pct)
    BIND(((?p_exp_T - ?p_exp_Prev) / ?p_exp_Prev) * 100 AS ?partnerExport_Growth_Pct)
    BIND(((?p_gdp_Next - ?p_gdp_T) / ?p_gdp_T) * 100 AS ?partnerGDP_Growth_NextYear_Pct)
    ?source gemr:countryName ?sourceCountry .
    ?partner gemr:countryName ?partnerCountry .
}
GROUP BY ?sourceCountry ?partnerCountry ?yearT
ORDER BY ?sourceCountry ?yearT
LIMIT 50
```

---

### P07 — Currency Crisis Early Warning

**Logic:** Regional currency contagion spillover analysis. Tests subqueries, conditional logic (IF statements), and complex chaining of events.

```sparql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX gemr: <https://gemr-kg.org/ontology#>

SELECT ?sourceCountry ?targetCountry ?year 
       ?avgSourceDepr ?avgTargetDepr
       (IF(?avgTargetDepr > 10, "HIGH (Spillover Confirmed)", 
        IF(?avgTargetDepr > 5, "MODERATE (Stress)", "LOW (Resilient)")) 
        AS ?contagionRiskLevel)
WHERE {
    {
        SELECT ?sourceCountry ?targetCountry ?year 
               (AVG(?sourceDepreciation_Pct) AS ?avgSourceDepr) 
               (AVG(?targetDepreciation_Pct) AS ?avgTargetDepr) 
        WHERE { 
            ?obsSource_T a gemr:Exchange_rate_new_LCU_per_USD ; gemr:hasCountry ?source ; gemr:hasYear ?yearEntity ; gemr:observationValue ?sVal_T .
            ?yearEntity gemr:yearValue ?y_Lit .
            BIND(xsd:integer(STR(?y_Lit)) AS ?year)
            BIND(?year - 1 AS ?yearPrev) 
            ?obsSource_Prev a gemr:Exchange_rate_new_LCU_per_USD ; gemr:hasCountry ?source ; gemr:hasYear ?prevYearEntity ; gemr:observationValue ?sVal_Prev .
            ?prevYearEntity gemr:yearValue ?prevY_Lit .
            FILTER(xsd:integer(STR(?prevY_Lit)) = ?yearPrev)
            BIND(((?sVal_T - ?sVal_Prev) / ?sVal_Prev) * 100 AS ?sourceDepreciation_Pct) 
            FILTER(?sourceDepreciation_Pct > 15) 
            VALUES (?sName ?tName) { 
                 ("Brazil" "Mexico") 
                 ("Thailand" "Philippines") 
            } 
            ?source gemr:countryName ?sName . 
            ?target gemr:countryName ?tName . 
            ?obsTarget_T a gemr:Exchange_rate_new_LCU_per_USD ; gemr:hasCountry ?target ; gemr:hasYear ?yearEntity ; gemr:observationValue ?tVal_T .
            ?obsTarget_Prev a gemr:Exchange_rate_new_LCU_per_USD ; gemr:hasCountry ?target ; gemr:hasYear ?prevYearEntity ; gemr:observationValue ?tVal_Prev .
            BIND(((?tVal_T - ?tVal_Prev) / ?tVal_Prev) * 100 AS ?targetDepreciation_Pct) 
            ?source gemr:countryName ?sourceCountry . 
            ?target gemr:countryName ?targetCountry . 
        } 
        GROUP BY ?sourceCountry ?targetCountry ?year
    }
}
ORDER BY DESC(?avgSourceDepr)
LIMIT 100
```


## Questions Changed from Original Set

| ID | Original Question | New Question | Reason |
|---|---|---|---|
| S02 | Governance score for Brazil in 2020 | Control of corruption for Brazil in 2020 | RiskScore only exists for Brazil/Poland in 2023; no sub-scores for Brazil |
| S05 | Economic health score for Mexico in 2019 | GDP (current US$) for Mexico in 2019 | No RiskScore entity exists for Mexico at all |
| S07 | Total risk score for Thailand in 2010 | Political stability for Thailand in 2010 | No RiskScore entity exists for Thailand at all |
