"""
Q-CATALYST: Catalyst Materials Database
========================================
12 curated catalytic material models for the Hydrogen Evolution Reaction (HER).
Includes noble metals, transition metals, 2D dichalcogenides, and alloys.
"""

from typing import List, Dict, Any

CATALYSTS: List[Dict[str, str]] = [
    {"id": "Pt", "name": "Platinum", "formula": "Pt", "category": "Noble metal", "reaction": "HER"},
    {"id": "Ru", "name": "Ruthenium", "formula": "Ru", "category": "Noble metal", "reaction": "HER"},
    {"id": "Ir", "name": "Iridium", "formula": "Ir", "category": "Noble metal", "reaction": "HER"},
    {"id": "Pd", "name": "Palladium", "formula": "Pd", "category": "Noble metal", "reaction": "HER"},
    {"id": "Ni", "name": "Nickel", "formula": "Ni", "category": "Transition metal", "reaction": "HER"},
    {"id": "Co", "name": "Cobalt", "formula": "Co", "category": "Transition metal", "reaction": "HER"},
    {"id": "Fe", "name": "Iron", "formula": "Fe", "category": "Transition metal", "reaction": "HER"},
    {"id": "Mo", "name": "Molybdenum", "formula": "Mo", "category": "Transition metal", "reaction": "HER"},
    {"id": "W", "name": "Tungsten", "formula": "W", "category": "Transition metal", "reaction": "HER"},
    {"id": "MoS2", "name": "Molybdenum disulfide", "formula": "MoS₂", "category": "2D dichalcogenide", "reaction": "HER"},
    {"id": "WS2", "name": "Tungsten disulfide", "formula": "WS₂", "category": "2D dichalcogenide", "reaction": "HER"},
    {"id": "NiMo", "name": "Nickel–molybdenum", "formula": "Ni–Mo", "category": "Alloy", "reaction": "HER"},
]


def get_all_catalysts() -> List[Dict[str, str]]:
    """Return list of all 12 catalyst database records."""
    return list(CATALYSTS)


def get_catalyst_map() -> Dict[str, Dict[str, str]]:
    """Return dictionary mapping catalyst_id to record."""
    return {c["id"]: c for c in CATALYSTS}


def get_catalyst(catalyst_id: str) -> Dict[str, str]:
    """Retrieve catalyst record by ID. Raises KeyError if not found."""
    for item in CATALYSTS:
        if item["id"] == catalyst_id:
            return dict(item)
    raise KeyError(f"Catalyst ID '{catalyst_id}' not found in database.")
