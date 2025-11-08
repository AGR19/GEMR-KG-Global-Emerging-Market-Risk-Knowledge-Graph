# GEMR:KG - Global Emerging Markets Risk Knowledge Graph
The Goal of the project is to construct a knowledge graph and publish a research paper out of it.

# Datasets

1. World Bank : Global Economic Monitor
```
https://datacatalog.worldbank.org/search/dataset/0037798/Global-Economic-Monitor

```
2. World Bank : Global Emerging Markets Risk Database
```
https://data360.worldbank.org/en/dataset/IFC_GEM
```

3. World Bank : Worldwide Governance Indicators
```
https://www.worldbank.org/en/publication/worldwide-governance-indicators

```

# Goal

The World Bank provides the Global Economic Monitor (GEM) dataset. Existing visualizations for the GEM dataset can be found at the following link: [https://databank.worldbank.org/source/global-economic-monitor-(gem)](https://databank.worldbank.org/source/global-economic-monitor-(gem)).

Similarly, another dataset exists called the Global Emerging Markets (GEMs) Risk Database. However, visualizations for this emerging market risk dataset are not currently available.

Our tool is designed to combine both datasets, facilitate visualization, and answer analytical questions.

### Practical Value

The shared dimensions of **country** and **year** within these datasets enable users to:

* Link the datasets for correlation analysis (e.g., "Does inflation correlate with default rates?").
* Build predictive models using macroeconomic indicators to forecast credit risk.
* Conduct country-specific studies over the 29-year overlapping period.
* Perform regional analyses comparing economic conditions with credit risk patterns.

The primary value of this tool lies in its ability to combine these different data types using "country" and "year" as the joining keys.

# Documentation

## Dataset Analysis Documents

Comprehensive analysis documents have been created to understand the datasets and plan the knowledge graph construction:

### 0. [Executive Summary](analysis/EXECUTIVE_SUMMARY.md) ⭐ **Start Here!**
**Purpose**: 5-minute overview of the entire project

**Contents**:
- Quick dataset snapshot
- What's in each dataset (summarized)
- Key relationships at a glance
- Top 10 research questions
- Implementation roadmap
- How to use the documentation

### 1. [Dataset Analysis and Research Questions](analysis/DATASET_ANALYSIS_AND_RESEARCH_QUESTIONS.md)
**Purpose**: Complete overview of both datasets with detailed research questions

**Contents**:
- Complete fields and labels from both datasets
- 12 categories of economic research questions (120+ specific questions)
- Knowledge graph structure and entity/relationship definitions
- Expected outcomes and implementation priorities
- Data quality considerations

### 2. [Data Relationship Mapping](analysis/DATA_RELATIONSHIP_MAPPING.md)
**Purpose**: Explicit mappings between risk and economic indicators for knowledge graph construction

**Contents**:
- Geographic mapping (risk codes ↔ economic country names)
- Temporal alignment strategies
- Risk indicators ↔ Economic indicators relationships with hypothesized correlations
- Sector-specific mappings
- Currency type and exchange rate relationships
- Time lag structures (leading/lagging indicators)
- Cypher query examples for graph database
- Data integration checklist

### 3. [Fields and Labels Reference Guide](analysis/FIELDS_AND_LABELS_REFERENCE.md)
**Purpose**: Quick reference for all fields, codes, and labels in both datasets

**Contents**:
- Complete 45-column structure of risk dataset
- All 132 geographic entities with code mappings
- All 12 risk indicators (default and recovery rates)
- All 37 economic indicator files with descriptions
- Complete label mappings for all categorical fields
- 187 individual countries coverage
- Data structure and joining dimensions

### 4. [Visual Relationships](analysis/VISUAL_RELATIONSHIPS.md)
**Purpose**: Visual diagrams showing data structures and relationships

**Contents**:
- Dataset overview diagrams
- Risk and economic data structure visualizations
- Geographic hierarchy
- Risk indicator taxonomy
- Economic → Risk relationship flows
- Sector-specific mappings
- Currency type analysis diagrams
- Knowledge graph schema visualization
- Time lag structure charts
- Regional risk profiles
- Implementation timeline (Gantt chart)

## Key Findings from Analysis

### Dataset Coverage
- **Risk Dataset**: 23,155 observations across 132 geographic entities (1984-2024, annual)
- **Economic Dataset**: 37 indicators across up to 199 entities (1996-2025, annual)
- **Overlap Period**: 1996-2024 (28 years of common data for analysis)

### Risk Data Dimensions
The risk dataset captures multiple dimensions:
- **Geographic**: 132 entities (6 regions + income-based groups + individual countries)
- **Risk Types**: Default rates and Recovery rates for Public, Private, and Sovereign borrowers
- **Sectors**: 20+ sectors (GICS classification + functional categories)
- **Project Types**: Corporate Finance, Project Finance, Financial Institutions, Structured Finance, etc.
- **Currency Types**: Foreign, Local, Mixed
- **Contract Sizes**: 7 size bands (< 1M EUR to > 25M EUR)
- **Seniority**: Senior, Senior-Secured, Senior-Unsecured, Subordinated

### Economic Data Categories
The economic dataset covers 9 major categories:
1. **GDP and Growth** (5 indicators)
2. **Inflation and Prices** (6 indicators)
3. **Exchange Rates** (4 indicators)
4. **Exports** (6 indicators)
5. **Imports** (7 indicators)
6. **Trade Balance** (1 indicator)
7. **Monetary/Financial** (3 indicators)
8. **Real Sector** (3 indicators)
9. **Labor Market** (1 indicator)

### Sample Research Questions the Knowledge Graph Will Answer

1. **Macroeconomic Drivers**: How does GDP growth volatility correlate with private sector default rates across different regions?

2. **Currency Risk**: What is the relationship between exchange rate depreciation and foreign currency default rates versus local currency default rates?

3. **Sectoral Vulnerability**: How do banking sector default rates correlate with stock market performance versus real economy indicators?

4. **Regional Patterns**: Which economic indicators best predict sovereign default rates in Sub-Saharan Africa compared to other regions?

5. **Early Warning**: How do leading economic indicators (Industrial Production, Retail Sales) predict future default rates across different sectors?

6. **Recovery Analysis**: How do sovereign recovery rates vary with total reserves levels and foreign reserves measured in months of import cover?

7. **Stress Testing**: Under scenarios of 10%, 20%, 30% exchange rate depreciation, what are the predicted changes in foreign currency default rates?

8. **Size Effects**: Do larger contract sizes show different default rate sensitivities to GDP shocks compared to smaller contracts?

9. **Time Dynamics**: What is the duration of elevated default rates following exchange rate crises across different currency types?

10. **Contagion**: Do default rates in one region lead default rates in another region after controlling for regional economic indicators?

*See [DATASET_ANALYSIS_AND_RESEARCH_QUESTIONS.md](analysis/DATASET_ANALYSIS_AND_RESEARCH_QUESTIONS.md) for 120+ detailed research questions organized into 12 categories.*

## Data Relationships

### Primary Linking Keys
1. **Geographic**: Risk dataset REF_AREA codes map to Economic dataset country names
2. **Temporal**: TIME_PERIOD (risk) aligns with year column (economic) for 1996-2024
3. **Regional**: Both datasets share 6 main regional classifications (East Asia & Pacific, Europe & Central Asia, Latin America & Caribbean, Middle East & North Africa, South Asia, Sub-Saharan Africa)

### Key Relationships Identified
- **GDP ↔ Default Rates**: Negative correlation expected (higher GDP → lower defaults)
- **Exchange Rate ↔ Foreign Currency Defaults**: Positive correlation (depreciation → higher defaults)
- **Unemployment ↔ Private Defaults**: Positive correlation with 1-2 year lag
- **Industrial Production ↔ Industrial Sector Defaults**: Negative correlation with 1-2 year lag
- **Stock Markets ↔ Recovery Rates**: Positive correlation (better markets → higher recovery)
- **Reserves ↔ Sovereign Defaults**: Negative correlation (higher reserves → lower sovereign risk)

*See [DATA_RELATIONSHIP_MAPPING.md](analysis/DATA_RELATIONSHIP_MAPPING.md) for comprehensive relationship mappings and Cypher query examples.*
