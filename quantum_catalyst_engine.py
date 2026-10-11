"""
Q-CATALYST: Quantum Catalyst Engine
===================================
Quantum-assisted computational engine using Qiskit for active-site electronic modeling.
Implements:
1. ElectronicStructureBackend interface (future-ready architecture)
2. ReducedModelBackend (Qiskit SparsePauliOp + RealAmplitudes VQE + Exact Solver)
3. FuturePsi4Backend (ab-initio extension interface)
4. Numerical validation between VQE ground state and exact diagonalization of the identical Hamiltonian.
5. Direct computation of H* adsorption interaction and screening proxy.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
from datetime import datetime
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

# Handle Windows Application Control (AppLocker) blocking rustworkx DLL
try:
    import rustworkx
except Exception:
    import sys, types
    rw = types.ModuleType('rustworkx')
    rwv = types.ModuleType('rustworkx.visualization')
    rwv.graphviz_draw = lambda *a, **k: None
    rw.PyDiGraph = object
    rw.PyGraph = object
    rw.PyDAG = object
    rw.ColoringStrategy = types.SimpleNamespace(Saturation=1)
    rw.visualization = rwv
    sys.modules['rustworkx'] = rw
    sys.modules['rustworkx.visualization'] = rwv

from qiskit.quantum_info import SparsePauliOp, Statevector
from qiskit.circuit.library import real_amplitudes

from screening_types import (
    SingleVqeResult,
    ScreeningPolicy,
    CalculatedResult,
    ValidationFailedResult,
    ModelIncompleteResult,
    AnyScreeningResult,
    result_from_dict,
)
from catalyst_database import get_catalyst


class ElectronicStructureBackend(ABC):
    """
    Abstract interface for quantum chemistry / active-site electronic structure backends.
    Allows substituting the reduced effective Hamiltonian with full ab-initio active-space
    Hamiltonians (e.g., Psi4 / Qiskit Nature) without rewriting screening or UI logic.
    """

    @abstractmethod
    def build_hamiltonian(
        self,
        model: Dict[str, Any],
        adsorbed: bool,
        inputs: Dict[str, Any],
    ) -> SparsePauliOp:
        """Construct the active-space Hamiltonian as a Qiskit Pauli operator."""
        pass

    @abstractmethod
    def run_vqe(
        self,
        hamiltonian: SparsePauliOp,
        max_iter: int = 400,
        gtol: float = 1e-8,
        seed: int = 42,
        force_fail: bool = False,
    ) -> SingleVqeResult:
        """Execute VQE and validate against exact matrix diagonalization of the identical operator."""
        pass


class ReducedModelBackend(ElectronicStructureBackend):
    """
    Transparent reduced effective active-site model.
    Constructs a 2-qubit effective Hamiltonian parameterizing the interaction between
    an under-coordinated metal d-state and an adsorbing H 1s orbital.
    Solves using Qiskit parameterized circuits (RealAmplitudes) and validates against
    exact matrix diagonalization.
    """

    def __init__(self, num_qubits: int = 2, reps: int = 2):
        self.num_qubits = num_qubits
        self.reps = reps
        self.ansatz = real_amplitudes(num_qubits=self.num_qubits, reps=self.reps)

    def build_hamiltonian(
        self,
        model: Dict[str, Any],
        adsorbed: bool,
        inputs: Dict[str, Any],
    ) -> SparsePauliOp:
        chi = float(model.get("chi", 2.0))
        d_level = float(model.get("d_level", 0.0))
        coord = float(model.get("coordination", 0.5))
        coup = float(model.get("coupling", 0.65))
        affinity = float(model.get("affinity", 0.65))

        distance = float(inputs.get("adsorption_distance", 1.55))
        charge = float(inputs.get("local_charge", 0.0))
        site_factor = float(inputs.get("site_factor", model.get("site_factor", 1.0)))

        # Effective active-site accessibility and distance attenuation
        effective_affinity = float(np.clip(
            affinity * site_factor + 0.15 * (1.0 - site_factor) + 0.10 * charge,
            0.05, 1.20
        ))
        distance_factor = float(np.exp(-0.9 * (distance - 1.55)))
        effective_coupling = coup * distance_factor

        # 2-qubit Pauli operator coefficients:
        # Qubit 0: Active metal site electronic proxy
        # Qubit 1: Local coordination / H-adsorbate interaction orbital
        c0 = -1.05 + 0.08 * (chi - 2.10) + 0.05 * (coord - 0.50)
        z1 = -0.18 + 0.14 * d_level + 0.04 * (coord - 0.50) + 0.03 * charge
        z2 = -0.34 + 0.08 * (chi - 2.00) - 0.02 * charge
        zz = 0.08 + 0.04 * (1.0 - coord)
        xx = 0.10 + 0.16 * effective_coupling
        yy = 0.06 + 0.10 * effective_coupling

        if adsorbed:
            # Electronic perturbation from adsorbed hydrogen:
            # Deepens site energy, polarizes local d-states, and increases inter-orbital exchange
            c0 += -0.24 * effective_affinity + 0.03 * (distance - 1.55)
            z1 += 0.05 * (1.0 - effective_affinity)
            z2 += 0.03 * (effective_affinity - 0.50)
            xx += 0.05 * effective_affinity
            yy += 0.03 * effective_affinity

        return SparsePauliOp.from_list([
            ("II", c0),
            ("ZI", z1),
            ("IZ", z2),
            ("ZZ", zz),
            ("XX", xx),
            ("YY", yy),
        ])

    def run_vqe(
        self,
        hamiltonian: SparsePauliOp,
        max_iter: int = 400,
        gtol: float = 1e-8,
        seed: int = 42,
        force_fail: bool = False,
    ) -> SingleVqeResult:
        # Exact ground state energy from exact diagonalization of the identical Hamiltonian
        H_matrix = hamiltonian.to_matrix()
        exact_energy = float(np.linalg.eigvalsh(H_matrix)[0].real)

        if force_fail:
            # Simulated failure mode: severely restrict optimizer to demonstrate validation failure
            max_iter = 1
            gtol = 1.0

        def objective(params):
            qc = self.ansatz.assign_parameters(params)
            sv = Statevector(qc)
            return float(sv.expectation_value(hamiltonian).real)

        rng = np.random.default_rng(seed)
        num_params = self.ansatz.num_parameters
        starts = [
            np.zeros(num_params),
            rng.uniform(-np.pi, np.pi, num_params),
        ]

        best_res = None
        for s in starts:
            res = minimize(
                objective,
                s,
                method="BFGS",
                options={"maxiter": max_iter, "gtol": gtol},
            )
            if best_res is None or res.fun < best_res.fun:
                best_res = res

        vqe_energy = float(best_res.fun)
        error = abs(vqe_energy - exact_energy)
        converged = bool(best_res.success) and (not force_fail)

        return SingleVqeResult(
            vqe_energy_ev=vqe_energy,
            exact_energy_ev=exact_energy,
            absolute_error_ev=error,
            iterations=int(getattr(best_res, "nit", 0)),
            evaluations=int(getattr(best_res, "nfev", 0)),
            converged=converged,
            backend_name="Qiskit Statevector VQE (RealAmplitudes)",
            num_qubits=self.num_qubits,
            ansatz=f"Qiskit RealAmplitudes ({self.num_qubits}-qubit, reps={self.reps})",
        )


class FuturePsi4Backend(ElectronicStructureBackend):
    """
    Architecture interface for future first-principles ab-initio quantum chemistry.
    When configured with Psi4 + Qiskit Nature on Windows:
    1. Reads explicit 3D atomic coordinates (XYZ) for clean active site and H-adsorbed site.
    2. Performs active space orbital selection (CASSCF).
    3. Transforms fermionic integrals to qubit Pauli operators (Jordan-Wigner / Bravyi-Kitaev).
    4. Evaluates ground state via VQE and validates against FCI reference.
    """

    def __init__(self):
        self.available = False

    def build_hamiltonian(
        self,
        model: Dict[str, Any],
        adsorbed: bool,
        inputs: Dict[str, Any],
    ) -> SparsePauliOp:
        raise NotImplementedError(
            "FuturePsi4Backend is an architectural interface designed for future ab-initio "
            "integration. It requires native Psi4 + Qiskit Nature. Use ReducedModelBackend for "
            "the current prototype."
        )

    def run_vqe(
        self,
        hamiltonian: SparsePauliOp,
        max_iter: int = 400,
        gtol: float = 1e-8,
        seed: int = 42,
        force_fail: bool = False,
    ) -> SingleVqeResult:
        raise NotImplementedError("Future ab-initio backend not active in current prototype.")


# Default engine backend instance
DEFAULT_BACKEND = ReducedModelBackend()


def calculate(
    catalyst_id: str,
    model: Dict[str, Any],
    catalyst_meta: Optional[Dict[str, Any]] = None,
    overrides: Optional[Dict[str, Any]] = None,
    policy: Optional[ScreeningPolicy] = None,
    backend: Optional[ElectronicStructureBackend] = None,
    force_validation_fail: bool = False,
) -> AnyScreeningResult:
    """
    Executes the complete quantum-assisted active-site screening pipeline:
    1. Validates model completeness.
    2. Constructs clean active-site Hamiltonian and adsorbed H* Hamiltonian.
    3. Runs VQE ground-state simulation and exact eigensolver validation.
    4. Computes H* interaction energy: E(cat + H*) - E(cat).
    5. Computes HER screening proxy: ΔE_H* + Δ_thermo.
    6. Returns an explicit typed result object (CalculatedResult, ValidationFailedResult, or ModelIncompleteResult).
    """
    if policy is None:
        policy = ScreeningPolicy()
    if backend is None:
        backend = DEFAULT_BACKEND

    overrides = overrides or {}
    distance = float(overrides.get("adsorption_distance", 1.55))
    charge = float(overrides.get("local_charge", 0.0))
    site_factor = float(overrides.get("site_factor", model.get("site_factor", 1.0)))

    inputs = {
        "adsorption_distance_A": distance,
        "local_charge": charge,
        "site_factor": site_factor,
    }
    for k in ("phase", "edge", "geometry", "ni_fraction", "adsorption_site"):
        if k in overrides:
            inputs[k] = overrides[k]

    if catalyst_meta is None:
        try:
            catalyst_meta = get_catalyst(catalyst_id)
        except KeyError:
            catalyst_meta = {
                "id": catalyst_id,
                "name": catalyst_id,
                "formula": catalyst_id,
                "category": "Unknown",
            }

    # 1. Model Completeness Check
    if not model.get("complete", False):
        missing = model.get("missing", [])
        return ModelIncompleteResult(
            catalyst_id=catalyst_id,
            formula=catalyst_meta.get("formula", catalyst_id),
            name=catalyst_meta.get("name", catalyst_id),
            category=catalyst_meta.get("category", "Unknown"),
            model_type=model.get("model_type", "reduced cluster"),
            structure=model.get("structure", "surrogate model"),
            active_site=model.get("active_site", "surrogate site"),
            missing_fields=list(missing),
            reason=f"Required model information is missing: {', '.join(missing)}." if missing else model.get("note", "Model incomplete."),
            next_action="Complete the missing material/site definition before running the quantum calculation.",
            timestamp=datetime.now().isoformat(),
            inputs=inputs,
            model_params={
                k: v for k, v in model.items()
                if k in ("chi", "d_level", "coordination", "coupling", "affinity", "site_factor")
            },
        )

    # 2. Build Hamiltonians
    clean_h = backend.build_hamiltonian(
        model,
        adsorbed=False,
        inputs={"adsorption_distance": distance, "local_charge": charge, "site_factor": site_factor},
    )
    ads_h = backend.build_hamiltonian(
        model,
        adsorbed=True,
        inputs={"adsorption_distance": distance, "local_charge": charge, "site_factor": site_factor},
    )

    # 3. Run VQE & Exact Validation
    clean_res = backend.run_vqe(clean_h, seed=11, force_fail=force_validation_fail)
    ads_res = backend.run_vqe(ads_h, seed=23, force_fail=force_validation_fail)

    max_vqe_error = max(clean_res.absolute_error_ev, ads_res.absolute_error_ev)

    # 4. Check Quantum Validation
    if max_vqe_error > policy.max_acceptable_vqe_error or force_validation_fail:
        return ValidationFailedResult(
            catalyst_id=catalyst_id,
            formula=catalyst_meta.get("formula", catalyst_id),
            name=catalyst_meta.get("name", catalyst_id),
            category=catalyst_meta.get("category", "Unknown"),
            model_type=model.get("model_type", "reduced cluster"),
            structure=model.get("structure", "surrogate model"),
            active_site=model.get("active_site", "surrogate site"),
            clean=clean_res,
            adsorbed=ads_res,
            max_vqe_error_ev=max_vqe_error,
            tolerance_ev=policy.max_acceptable_vqe_error,
            reason=(
                f"Quantum validation did not pass: VQE vs exact error is {max_vqe_error:.3e} eV, "
                f"above the {policy.max_acceptable_vqe_error:.0e} eV prototype tolerance. "
                "The calculation should not be treated as a validated screening result."
            ),
            next_action="Refine the quantum ansatz or increase optimization iterations. Do not use this unvalidated calculation for screening decisions.",
            timestamp=datetime.now().isoformat(),
            inputs=inputs,
            model_params={
                k: v for k, v in model.items()
                if k in ("chi", "d_level", "coordination", "coupling", "affinity", "site_factor")
            },
            backend="2-qubit Qiskit Statevector VQE",
        )

    # 5. Interaction Energy and HER Screening Proxy
    interaction = ads_res.vqe_energy_ev - clean_res.vqe_energy_ev
    thermo_corr = policy.thermo_correction_ev
    proxy = interaction + thermo_corr
    dist = abs(proxy - policy.target_ev)

    # 6. Evidence-Based Screening Decision
    if dist <= policy.shortlist_window_ev:
        decision = "SHORTLIST"
        reason = (
            f"The HER screening proxy is {proxy:+.4f} eV, which is {dist:.4f} eV from "
            f"the {policy.target_ev:.2f} eV target and lies inside the current prototype "
            f"screening region (±{policy.shortlist_window_ev:.2f} eV)."
        )
        next_action = (
            "Use this active-site model for higher-fidelity investigation. "
            "Define the actual surface/cluster geometry and validate the H* free-energy calculation."
        )
    elif dist <= policy.borderline_window_ev:
        decision = "BORDERLINE"
        reason = (
            f"The HER screening proxy is {proxy:+.4f} eV, which is {dist:.4f} eV from "
            f"the {policy.target_ev:.2f} eV target, lying in the borderline review region "
            f"(±{policy.borderline_window_ev:.2f} eV)."
        )
        next_action = "Refine the active-site geometry or electronic model and repeat the calculation."
    else:
        decision = "NOT SHORTLISTED"
        reason = (
            f"The HER screening proxy is {proxy:+.4f} eV, which is {dist:.4f} eV from "
            f"the {policy.target_ev:.2f} eV target, outside the ±{policy.shortlist_window_ev:.2f} eV shortlist region."
        )
        next_action = "Inspect the active-site assumptions and repeat using a higher-fidelity model before drawing conclusions."

    return CalculatedResult(
        catalyst_id=catalyst_id,
        formula=catalyst_meta.get("formula", catalyst_id),
        name=catalyst_meta.get("name", catalyst_id),
        category=catalyst_meta.get("category", "Unknown"),
        model_type=model.get("model_type", "reduced cluster"),
        structure=model.get("structure", "surrogate model"),
        active_site=model.get("active_site", "surrogate site"),
        clean=clean_res,
        adsorbed=ads_res,
        interaction_energy_ev=interaction,
        thermochemical_correction_ev=thermo_corr,
        her_screening_proxy_ev=proxy,
        distance_from_target_ev=dist,
        max_vqe_error_ev=max_vqe_error,
        decision=decision,
        decision_reason=reason,
        next_action=next_action,
        timestamp=datetime.now().isoformat(),
        inputs=inputs,
        model_params={
            k: v for k, v in model.items()
            if k in ("chi", "d_level", "coordination", "coupling", "affinity", "site_factor")
        },
        backend="2-qubit Qiskit Statevector VQE (RealAmplitudes)",
        model_scope="reduced effective active-site Hamiltonian",
    )


def save_results(path: Union[str, Path], results: Dict[str, AnyScreeningResult]) -> None:
    """Save dictionary of typed results to JSON."""
    raw = {}
    for cid, r in results.items():
        if hasattr(r, "to_dict"):
            raw[cid] = r.to_dict()
        elif isinstance(r, dict):
            raw[cid] = r
    with open(path, "w", encoding="utf-8") as f:
        json.dump(raw, f, indent=2, ensure_ascii=False)


def load_results(path: Union[str, Path]) -> Dict[str, AnyScreeningResult]:
    """Load JSON file and parse into typed result objects."""
    p = Path(path)
    if not p.exists():
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, dict):
            return {}
        return {cid: result_from_dict(d) for cid, d in raw.items()}
    except Exception:
        return {}
