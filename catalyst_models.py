"""
Q-CATALYST: Active-Site Surrogate Models
=========================================
Transparent reduced active-site models for 12 HER catalyst candidates.
IMPORTANT SCIENTIFIC HONESTY:
These parameters are transparent reduced-model parameters for exploratory computational
pre-screening. They are NOT experimental measurements, DFT-fitted constants, or ab-initio
active-space integrals.
"""

from typing import Dict, Any, List, Optional
import copy

BASE_MODELS: Dict[str, Dict[str, Any]] = {
    "Pt": {
        "model_type": "metal active-site cluster",
        "structure": "Pt active-site surrogate",
        "active_site": "under-coordinated Pt site",
        "chi": 2.28,
        "d_level": 0.15,
        "coordination": 0.65,
        "coupling": 0.75,
        "affinity": 0.55,
        "site_factor": 1.00,
        "complete": True,
        "missing": [],
        "note": "Prototype Pt site is defined; a validated surface/cluster geometry is the next fidelity step.",
    },
    "Ru": {
        "model_type": "metal active-site cluster",
        "structure": "Ru active-site surrogate",
        "active_site": "under-coordinated Ru site",
        "chi": 2.20,
        "d_level": 0.05,
        "coordination": 0.60,
        "coupling": 0.70,
        "affinity": 0.65,
        "site_factor": 1.00,
        "complete": True,
        "missing": [],
        "note": "Prototype Ru site is defined; higher-fidelity geometry is required for chemistry claims.",
    },
    "Ir": {
        "model_type": "metal active-site cluster",
        "structure": "Ir active-site surrogate",
        "active_site": "under-coordinated Ir site",
        "chi": 2.20,
        "d_level": 0.10,
        "coordination": 0.68,
        "coupling": 0.72,
        "affinity": 0.58,
        "site_factor": 1.00,
        "complete": True,
        "missing": [],
        "note": "Prototype Ir site is defined; higher-fidelity geometry is required for chemistry claims.",
    },
    "Pd": {
        "model_type": "metal active-site cluster",
        "structure": "Pd active-site surrogate",
        "active_site": "under-coordinated Pd site",
        "chi": 2.20,
        "d_level": 0.18,
        "coordination": 0.62,
        "coupling": 0.68,
        "affinity": 0.48,
        "site_factor": 1.00,
        "complete": True,
        "missing": [],
        "note": "Prototype Pd site is defined; higher-fidelity geometry is required for chemistry claims.",
    },
    "Ni": {
        "model_type": "metal active-site cluster",
        "structure": "Ni active-site surrogate",
        "active_site": "under-coordinated Ni site",
        "chi": 1.91,
        "d_level": -0.10,
        "coordination": 0.50,
        "coupling": 0.60,
        "affinity": 0.75,
        "site_factor": 1.00,
        "complete": True,
        "missing": [],
        "note": "Prototype Ni site is defined; higher-fidelity geometry is required for chemistry claims.",
    },
    "Co": {
        "model_type": "metal active-site cluster",
        "structure": "Co active-site surrogate",
        "active_site": "under-coordinated Co site",
        "chi": 1.88,
        "d_level": -0.18,
        "coordination": 0.48,
        "coupling": 0.58,
        "affinity": 0.68,
        "site_factor": 1.00,
        "complete": True,
        "missing": [],
        "note": "Prototype Co site is defined; higher-fidelity geometry is required for chemistry claims.",
    },
    "Fe": {
        "model_type": "metal active-site cluster",
        "structure": "Fe active-site surrogate",
        "active_site": "under-coordinated Fe site",
        "chi": 1.83,
        "d_level": -0.25,
        "coordination": 0.45,
        "coupling": 0.55,
        "affinity": 0.62,
        "site_factor": 1.00,
        "complete": True,
        "missing": [],
        "note": "Prototype Fe site is defined; higher-fidelity geometry is required for chemistry claims.",
    },
    "Mo": {
        "model_type": "metal active-site cluster",
        "structure": "Mo active-site surrogate",
        "active_site": "under-coordinated Mo site",
        "chi": 2.16,
        "d_level": 0.00,
        "coordination": 0.42,
        "coupling": 0.64,
        "affinity": 0.72,
        "site_factor": 1.00,
        "complete": True,
        "missing": [],
        "note": "Prototype Mo site is defined; higher-fidelity geometry is required for chemistry claims.",
    },
    "W": {
        "model_type": "metal active-site cluster",
        "structure": "W active-site surrogate",
        "active_site": "under-coordinated W site",
        "chi": 2.36,
        "d_level": 0.12,
        "coordination": 0.44,
        "coupling": 0.66,
        "affinity": 0.60,
        "site_factor": 1.00,
        "complete": True,
        "missing": [],
        "note": "Prototype W site is defined; higher-fidelity geometry is required for chemistry claims.",
    },
    "MoS2": {
        "model_type": "edge-site cluster",
        "structure": "MoS₂ edge-site surrogate",
        "active_site": "Mo/S edge site",
        "chi": 2.16,
        "d_level": -0.02,
        "coordination": 0.35,
        "coupling": 0.70,
        "affinity": 0.72,
        "site_factor": 1.00,
        "complete": False,
        "missing": ["phase", "edge termination", "local adsorption geometry"],
        "note": "Define phase, edge termination and H* geometry before treating this as a reliable material-specific model.",
    },
    "WS2": {
        "model_type": "edge-site cluster",
        "structure": "WS₂ edge-site surrogate",
        "active_site": "W/S edge site",
        "chi": 2.36,
        "d_level": 0.08,
        "coordination": 0.35,
        "coupling": 0.72,
        "affinity": 0.62,
        "site_factor": 1.00,
        "complete": False,
        "missing": ["phase", "edge termination", "local adsorption geometry"],
        "note": "Define phase, edge termination and H* geometry before treating this as a reliable material-specific model.",
    },
    "NiMo": {
        "model_type": "alloy active-site cluster",
        "structure": "NiₓMoᵧ interface surrogate",
        "active_site": "Ni–Mo interfacial site",
        "chi": 2.03,
        "d_level": -0.05,
        "coordination": 0.46,
        "coupling": 0.63,
        "affinity": 0.78,
        "site_factor": 1.00,
        "complete": False,
        "missing": ["Ni:Mo composition", "local interface geometry", "H* adsorption site"],
        "note": "Define composition and local Ni–Mo interface geometry before making a material-specific decision.",
    },
}


def get_all_models() -> Dict[str, Dict[str, Any]]:
    """Return a deep copy of all base models."""
    return copy.deepcopy(BASE_MODELS)


def get_model(catalyst_id: str) -> Dict[str, Any]:
    """Retrieve base active-site model for catalyst_id."""
    if catalyst_id not in BASE_MODELS:
        raise KeyError(f"Catalyst ID '{catalyst_id}' not found in model registry.")
    return copy.deepcopy(BASE_MODELS[catalyst_id])


def configure_active_site_model(
    catalyst_id: str,
    user_inputs: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Constructs an updated active-site model based on researcher inputs.
    For MoS2, WS2, and NiMo, validates whether required structural parameters are defined.
    """
    model = get_model(catalyst_id)

    if catalyst_id in ("MoS2", "WS2"):
        phase = user_inputs.get("phase")
        edge = user_inputs.get("edge")
        geometry = user_inputs.get("geometry")

        missing: List[str] = []
        if not phase or phase == "Not defined":
            missing.append("phase")
        if not edge or edge == "Not defined":
            missing.append("edge termination")
        if not geometry or geometry == "Not defined (Incomplete)":
            missing.append("local adsorption geometry")

        if missing:
            model["complete"] = False
            model["missing"] = missing
            model["structure"] = f"{catalyst_id} edge-site surrogate (Incomplete)"
            model["active_site"] = f"Undefined {catalyst_id} site"
        else:
            model["complete"] = True
            model["missing"] = []
            metal_symbol = "Mo" if catalyst_id == "MoS2" else "W"
            model["structure"] = f"{catalyst_id} {phase} phase edge surrogate"
            model["active_site"] = f"{edge} ({geometry})"
            model["note"] = f"Researcher defined: {phase} phase, {edge}, {geometry}."

            # Physical shifts for active site parameters in reduced model
            if "1T" in str(phase):
                model["d_level"] += 0.06
                model["coordination"] += 0.05
                model["coupling"] += 0.04
            if "S-vacancy" in str(geometry):
                model["affinity"] += 0.06
                model["coupling"] += 0.03
            elif "Bridge" in str(geometry):
                model["affinity"] -= 0.04

    elif catalyst_id == "NiMo":
        ni_frac = float(user_inputs.get("ni_fraction", 0.50))
        geometry = user_inputs.get("geometry")
        site = user_inputs.get("adsorption_site")

        missing = []
        if geometry is None or geometry == "Not defined (Incomplete)":
            missing.append("local interface geometry")
        if site is None or site == "Not defined (Incomplete)":
            missing.append("H* adsorption site")

        if missing:
            model["complete"] = False
            model["missing"] = missing
            model["structure"] = "NiₓMoᵧ interface surrogate (Incomplete)"
            model["active_site"] = "Undefined interface site"
        else:
            model["complete"] = True
            model["missing"] = []
            mo_frac = 1.0 - ni_frac
            model["structure"] = f"Ni_{ni_frac*100:.0f}Mo_{mo_frac*100:.0f} interface surrogate"
            model["active_site"] = f"{geometry} • {site}"
            model["note"] = f"Researcher defined: {ni_frac*100:.0f}% Ni, {geometry}, {site}."

            # Interpolate effective alloy parameters
            model["chi"] = round(ni_frac * 1.91 + mo_frac * 2.16, 2)
            model["d_level"] = round(ni_frac * (-0.10) + mo_frac * 0.00, 2)
            if "bridge" in str(site).lower():
                model["affinity"] = 0.74
                model["coupling"] = 0.66
            elif "ni" in str(site).lower():
                model["affinity"] = 0.73
            else:
                model["affinity"] = 0.71

    else:
        # Metals are complete by default
        model["complete"] = True
        model["missing"] = []

    return model
