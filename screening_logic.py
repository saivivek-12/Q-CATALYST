"""
Q-CATALYST: Screening Logic and Decision Engine
================================================
Implements the prototype screening policy for Hydrogen Evolution Reaction (HER) catalysts.
Classifies candidates into exactly four primary statuses:
1. SHORTLIST
2. BORDERLINE
3. NOT SHORTLISTED
4. MODEL INCOMPLETE

All evaluations are calculation-driven, transparent, and reproducible.
"""

from typing import Tuple, Dict, Any, Optional, Union
from screening_types import (
    ScreeningPolicy,
    CalculatedResult,
    ValidationFailedResult,
    ModelIncompleteResult,
    AnyScreeningResult,
)

TARGET_EV: float = 0.00
SHORTLIST_WINDOW_EV: float = 0.10
BORDERLINE_WINDOW_EV: float = 0.20
MAX_ACCEPTABLE_VQE_ERROR: float = 1e-5
THERMO_CORRECTION_EV: float = 0.24

DEFAULT_POLICY = ScreeningPolicy(
    target_ev=TARGET_EV,
    shortlist_window_ev=SHORTLIST_WINDOW_EV,
    borderline_window_ev=BORDERLINE_WINDOW_EV,
    max_acceptable_vqe_error=MAX_ACCEPTABLE_VQE_ERROR,
    thermo_correction_ev=THERMO_CORRECTION_EV,
)


def get_next_action(status: str) -> str:
    """Return the recommended next research action for a given decision status."""
    if status == "SHORTLIST":
        return (
            "Use this active-site model for higher-fidelity investigation: "
            "define the actual surface/cluster geometry and validate the "
            "H* free-energy calculation against a higher-level benchmark."
        )
    elif status == "BORDERLINE":
        return (
            "Refine the active-site geometry or electronic model and repeat the "
            "calculation. Check VQE convergence tolerance or explore local site sensitivity."
        )
    elif status == "NOT SHORTLISTED":
        return (
            "Do not discard the material experimentally from this reduced model alone. "
            "First inspect active-site coordination assumptions and repeat with a higher-fidelity model."
        )
    else:  # MODEL INCOMPLETE
        return (
            "Complete the missing material/site definition (phase, edge termination, "
            "or interface geometry) before running the quantum calculation."
        )


def evaluate(
    result: Union[AnyScreeningResult, Dict[str, Any]],
    model: Optional[Dict[str, Any]] = None,
    policy: Optional[ScreeningPolicy] = None,
) -> Tuple[str, str]:
    """
    Evaluates screening candidate and returns a 2-tuple (status, reason).
    Guaranteed never to raise KeyError.
    """
    if policy is None:
        policy = DEFAULT_POLICY
    model = model or {}

    # Handle typed ModelIncompleteResult
    if isinstance(result, ModelIncompleteResult):
        return ("MODEL INCOMPLETE", result.reason)

    # Handle typed ValidationFailedResult
    if isinstance(result, ValidationFailedResult):
        return ("BORDERLINE", result.reason)

    # Handle typed CalculatedResult
    if isinstance(result, CalculatedResult):
        return (result.decision, result.decision_reason)

    # Handle raw dictionary input
    if isinstance(result, dict):
        # 1. Model completeness check
        if not (model.get("complete", False) or result.get("model_complete") is True):
            missing = model.get("missing") or result.get("missing") or []
            if missing:
                return (
                    "MODEL INCOMPLETE",
                    f"Required model information is missing: {', '.join(missing)}.",
                )
            return (
                "MODEL INCOMPLETE",
                model.get("note") or result.get("model_note") or "Material-specific model is incomplete.",
            )

        # 2. Check presence of quantum results
        if not all(k in result for k in ("clean", "adsorbed")):
            missing_fields = [k for k in ("clean", "adsorbed") if k not in result]
            return (
                "MODEL INCOMPLETE",
                f"No quantum calculation available for this model yet (missing {', '.join(missing_fields)}).",
            )

        # 3. Check quantum validation error
        error = float(result.get("max_vqe_error_ev", 0.0))
        if error > policy.max_acceptable_vqe_error or result.get("status") == "validation_failed":
            return (
                "BORDERLINE",
                (
                    f"Quantum validation did not pass: VQE vs exact error is {error:.3e} eV, "
                    f"above the {policy.max_acceptable_vqe_error:.0e} eV prototype tolerance. "
                    "The HER proxy should not be treated as a validated screening result."
                ),
            )

        # 4. Evaluate screening proxy distance
        proxy = float(result.get("her_screening_proxy_ev", 0.0))
        distance = abs(proxy - policy.target_ev)

        if distance <= policy.shortlist_window_ev:
            return (
                "SHORTLIST",
                (
                    f"The HER screening proxy is {proxy:+.4f} eV, which is {distance:.4f} eV "
                    f"from the {policy.target_ev:.2f} eV target and lies inside the current prototype "
                    f"screening region (±{policy.shortlist_window_ev:.2f} eV)."
                ),
            )

        if distance <= policy.borderline_window_ev:
            return (
                "BORDERLINE",
                (
                    f"The HER screening proxy is {proxy:+.4f} eV, which is {distance:.4f} eV "
                    f"from the {policy.target_ev:.2f} eV target, lying in the borderline review region "
                    f"(±{policy.borderline_window_ev:.2f} eV)."
                ),
            )

        return (
            "NOT SHORTLISTED",
            (
                f"The HER screening proxy is {proxy:+.4f} eV, which is {distance:.4f} eV "
                f"from the {policy.target_ev:.2f} eV target, outside the ±{policy.shortlist_window_ev:.2f} eV shortlist region."
            ),
        )

    return ("MODEL INCOMPLETE", "Invalid result structure provided.")


def evaluate_full(
    result: Union[AnyScreeningResult, Dict[str, Any]],
    model: Optional[Dict[str, Any]] = None,
    policy: Optional[ScreeningPolicy] = None,
) -> Tuple[str, str, str]:
    """Evaluates screening candidate and returns 3-tuple (status, reason, next_action)."""
    status, reason = evaluate(result, model, policy)
    next_action = get_next_action(status)
    return status, reason, next_action
