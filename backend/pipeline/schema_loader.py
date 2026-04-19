"""
Schema Loader — Parses the OWL ontology and TTL data to extract the GEMR-KG vocabulary.

Extracts:
  - Classes with labels and hierarchy
  - Object properties with domains, ranges, and labels
  - Datatype properties with domains, ranges, and labels
  - All indicator IRIs from the TTL data
  - All country names from the TTL data

This information is used downstream for embedding enrichment and prompt construction.
"""
import xml.etree.ElementTree as ET
from pathlib import Path
from dataclasses import dataclass, field


# XML namespaces used in OWL files
NS = {
    "rdf":  "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "owl":  "http://www.w3.org/2002/07/owl#",
    "gemr": "https://gemr-kg.org/ontology#",
}

GEMR_PREFIX = "https://gemr-kg.org/ontology#"


@dataclass
class OntologyProperty:
    """Represents an OWL property (object or datatype)."""
    iri: str
    local_name: str
    label: str
    domain: str = ""
    range: str = ""
    prop_type: str = "object"  # "object" or "datatype"

    @property
    def description(self) -> str:
        """Rich text description for embedding — combines label, domain, range."""
        parts = [f"{self.label}"]
        if self.domain:
            parts.append(f"connects {self.domain}")
        if self.range:
            parts.append(f"to {self.range}")
        parts.append(f"({self.prop_type} property)")
        return " — ".join(parts)


@dataclass
class OntologyClass:
    """Represents an OWL class."""
    iri: str
    local_name: str
    label: str
    parent: str = ""


@dataclass
class GEMRSchema:
    """Complete extracted schema for the GEMR-KG ontology."""
    classes: list[OntologyClass] = field(default_factory=list)
    properties: list[OntologyProperty] = field(default_factory=list)
    indicators: list[str] = field(default_factory=list)
    countries: list[str] = field(default_factory=list)
    observation_types: list[str] = field(default_factory=list)


def _local_name(uri: str) -> str:
    """Extract local name from a full URI (after # or last /)."""
    if "#" in uri:
        return uri.split("#")[-1]
    return uri.rsplit("/", 1)[-1]


def parse_owl(owl_path: Path) -> tuple[list[OntologyClass], list[OntologyProperty]]:
    """Parse the OWL file and extract classes and properties."""
    tree = ET.parse(owl_path)
    root = tree.getroot()

    classes = []
    properties = []

    # --- Extract Classes ---
    for cls_elem in root.findall(".//owl:Class", NS):
        iri = cls_elem.get(f"{{{NS['rdf']}}}about", "")
        if not iri:
            continue

        local = _local_name(iri)
        label = local  # default to local name

        label_elem = cls_elem.find("rdfs:label", NS)
        if label_elem is not None and label_elem.text:
            label = label_elem.text

        parent = ""
        parent_elem = cls_elem.find("rdfs:subClassOf", NS)
        if parent_elem is not None:
            parent_ref = parent_elem.get(f"{{{NS['rdf']}}}resource", "")
            if parent_ref:
                parent = _local_name(parent_ref)

        classes.append(OntologyClass(iri=iri, local_name=local, label=label, parent=parent))

    # --- Extract Object Properties ---
    for prop_elem in root.findall(".//owl:ObjectProperty", NS):
        iri = prop_elem.get(f"{{{NS['rdf']}}}about", "")
        if not iri:
            continue

        local = _local_name(iri)
        label = local

        label_elem = prop_elem.find("rdfs:label", NS)
        if label_elem is not None and label_elem.text:
            label = label_elem.text

        domain = ""
        domain_elem = prop_elem.find("rdfs:domain", NS)
        if domain_elem is not None:
            domain = _local_name(domain_elem.get(f"{{{NS['rdf']}}}resource", ""))

        range_ = ""
        range_elem = prop_elem.find("rdfs:range", NS)
        if range_elem is not None:
            range_ = _local_name(range_elem.get(f"{{{NS['rdf']}}}resource", ""))

        properties.append(OntologyProperty(
            iri=iri, local_name=local, label=label,
            domain=domain, range=range_, prop_type="object"
        ))

    # --- Extract Datatype Properties ---
    for prop_elem in root.findall(".//owl:DatatypeProperty", NS):
        iri = prop_elem.get(f"{{{NS['rdf']}}}about", "")
        if not iri:
            continue

        local = _local_name(iri)
        label = local

        label_elem = prop_elem.find("rdfs:label", NS)
        if label_elem is not None and label_elem.text:
            label = label_elem.text

        domain = ""
        domain_elem = prop_elem.find("rdfs:domain", NS)
        if domain_elem is not None:
            domain = _local_name(domain_elem.get(f"{{{NS['rdf']}}}resource", ""))

        range_ = ""
        range_elem = prop_elem.find("rdfs:range", NS)
        if range_elem is not None:
            range_ = _local_name(range_elem.get(f"{{{NS['rdf']}}}resource", ""))

        properties.append(OntologyProperty(
            iri=iri, local_name=local, label=label,
            domain=domain, range=range_, prop_type="datatype"
        ))

    return classes, properties


def parse_ttl(ttl_path: Path) -> tuple[list[str], list[str], list[str]]:
    """
    Parse the TTL file to extract indicators, countries, and observation types.
    Uses lightweight string parsing (not a full RDF parser) for speed.
    """
    indicators = set()
    countries = set()
    observation_types = set()

    lines = ttl_path.read_text(errors="replace").splitlines()
    in_type_block = False

    for line in lines:
        stripped = line.strip()

        # Extract indicator URIs:  gemr:hasIndicator gemr:SomeThing
        if "gemr:hasIndicator gemr:" in stripped:
            token = stripped.split("gemr:hasIndicator gemr:")[1].strip().rstrip(" ;.")
            indicators.add(token)

        # Extract country names:  gemr:countryName "Brazil"
        if 'gemr:countryName' in stripped and '"' in stripped:
            name = stripped.split('"')[1]
            countries.add(name)

        # Detect observation type blocks: lines like "a gemr:Observation,"
        if stripped.startswith("a gemr:Observation"):
            in_type_block = True
            # Check for inline types: a gemr:Observation, gemr:PrivateDefaultRate ;
            if "," in stripped:
                for part in stripped.split(",")[1:]:
                    part = part.strip().rstrip(" ;.")
                    if part.startswith("gemr:"):
                        observation_types.add(part.replace("gemr:", ""))
            continue

        # Continuation of type block: "        gemr:PrivateDefaultRate ;"
        if in_type_block and stripped.startswith("gemr:") and ":" in stripped and not " " in stripped.split(";")[0].strip() or (in_type_block and stripped.startswith("gemr:") and stripped.endswith(";")):
            type_name = stripped.rstrip(" ;.").replace("gemr:", "")
            if type_name and not " " in type_name:
                observation_types.add(type_name)
            continue

        # End of type block when we hit a property line
        if in_type_block and ("gemr:has" in stripped or stripped.startswith("gemr:observation")):
            in_type_block = False

    return sorted(indicators), sorted(countries), sorted(observation_types)


def load_schema(owl_path: Path, ttl_path: Path) -> GEMRSchema:
    """Load and return the complete GEMR-KG schema."""
    classes, properties = parse_owl(owl_path)
    indicators, countries, observation_types = parse_ttl(ttl_path)

    return GEMRSchema(
        classes=classes,
        properties=properties,
        indicators=indicators,
        countries=countries,
        observation_types=observation_types,
    )
