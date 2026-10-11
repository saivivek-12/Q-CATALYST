"""
Q-CATALYST: Data Types and Result Schemas
=========================================
Strict typed data architecture for quantum screening results.
Provides type safety, explicit state representations, and safe serialization.
Prevents KeyError: 'clean' and UI state crashes by design.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Union
from datetime import datetime


@dataclass
class SingleVqeResult:
    """Represents the output of a single VQE statevector simulation."""
    vqe_energy_ev: float
    exact_energy_ev: float
    absolute_error_ev: float
    iterations: int
    evaluations: int
    converged: bool
    backend_name: str = "Qiskit Statevector VQE"
    num_qubits: int = 2
    ansatz: str = "Hardware-efficient RealAmplitudes (2-qubit)"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SingleVqeResult:
        return cls(
            vqe_energy_ev=float(data["vqe_energy_ev"]),
            exact_energy_ev=float(data["exact_energy_ev"]),
            absolute_error_ev=float(data["absolute_error_ev"]),
            iterations=int(data.get("iterations", 0)),
            evaluations=int(data.get("evaluations", 0)),
            converged=bool(data.get("converged", True)),
            backend_name=str(data.get("backend_name", "Qiskit Statevector VQE")),
            num_qubits=int(data.get("num_qubits", 2)),
            ansatz=str(data.get("ansatz", "Hardware-efficient RealAmplitudes (2-qubit)")),
        )


@dataclass
class ScreeningPolicy:
    """Configurable prototype screening policy thresholds."""
    target_ev: float = 0.00
    shortlist_window_ev: float = 0.10
    borderline_window_ev: float = 0.20
    max_acceptable_vqe_error: float = 1e-5
    thermo_correction_ev: float = 0.24


@dataclass
class ModelIncompleteResult:
    """Result state when a material or active-site model lacks required definitions."""
    catalyst_id: str
    formula: str
    name: str
    category: str
    model_type: str
    structure: str
    active_site: str
    missing_fields: List[str]
    reason: str
    next_action: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    inputs: Dict[str, Any] = field(default_factory=dict)
    model_params: Dict[str, Any] = field(default_factory=dict)
    status: str = "model_incomplete"

    @property
    def is_calculated(self) -> bool:
        return False

    @property
    def is_incomplete(self) -> bool:
        return True

    @property
    def is_validation_failed(self) -> bool:
        return False

    @property
    def decision(self) -> str:
        return "MODEL INCOMPLETE"

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ModelIncompleteResult:
        missing = data.get("missing_fields") or data.get("missing") or []
        return cls(
            catalyst_id=data["catalyst_id"],
            formula=data.get("formula", data["catalyst_id"]),
            name=data.get("name", data["catalyst_id"]),
            category=data.get("category", "General"),
            model_type=data.get("model_type", "reduced cluster"),
            structure=data.get("structure", "surrogate model"),
            active_site=data.get("active_site", "surrogate site"),
            missing_fields=list(missing),
            reason=data.get("reason") or data.get("model_note") or "Active-site model is incomplete.",
            next_action=data.get("next_action", "Complete the missing material/site definition before running the quantum calculation."),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            inputs=data.get("inputs", {}),
            model_params=data.get("model_params", {}),
            status="model_incomplete",
        )


@dataclass
class ValidationFailedResult:
    """Result state when quantum VQE optimization does not meet exact numerical tolerance."""
    catalyst_id: str
    formula: str
    name: str
    category: str
    model_type: str
    structure: str
    active_site: str
    clean: SingleVqeResult
    adsorbed: SingleVqeResult
    max_vqe_error_ev: float
    tolerance_ev: float
    reason: str
    next_action: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    inputs: Dict[str, Any] = field(default_factory=dict)
    model_params: Dict[str, Any] = field(default_factory=dict)
    backend: str = "2-qubit Qiskit Statevector VQE"
    status: str = "validation_failed"

    @property
    def is_calculated(self) -> bool:
        return False

    @property
    def is_incomplete(self) -> bool:
        return False

    @property
    def is_validation_failed(self) -> bool:
        return True

    @property
    def decision(self) -> str:
        return "BORDERLINE"

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["clean"] = self.clean.to_dict()
        d["adsorbed"] = self.adsorbed.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ValidationFailedResult:
        clean = (
            data["clean"]
            if isinstance(data["clean"], SingleVqeResult)
            else SingleVqeResult.from_dict(data["clean"])
        )
        adsorbed = (
            data["adsorbed"]
            if isinstance(data["adsorbed"], SingleVqeResult)
            else SingleVqeResult.from_dict(data["adsorbed"])
        )
        return cls(
            catalyst_id=data["catalyst_id"],
            formula=data.get("formula", data["catalyst_id"]),
            name=data.get("name", data["catalyst_id"]),
            category=data.get("category", "General"),
            model_type=data.get("model_type", "reduced cluster"),
            structure=data.get("structure", "surrogate model"),
            active_site=data.get("active_site", "surrogate site"),
            clean=clean,
            adsorbed=adsorbed,
            max_vqe_error_ev=float(data["max_vqe_error_ev"]),
            tolerance_ev=float(data.get("tolerance_ev", 1e-5)),
            reason=data.get("reason", "VQE validation error exceeded tolerance."),
            next_action=data.get("next_action", "Refine the active-site geometry or electronic model and repeat the calculation."),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            inputs=data.get("inputs", {}),
            model_params=data.get("model_params", {}),
            backend=data.get("backend", "2-qubit Qiskit Statevector VQE"),
            status="validation_failed",
        )


@dataclass
class CalculatedResult:
    """Fully calculated and quantum-validated screening result."""
    catalyst_id: str
    formula: str
    name: str
    category: str
    model_type: str
    structure: str
    active_site: str
    clean: SingleVqeResult
    adsorbed: SingleVqeResult
    interaction_energy_ev: float
    thermochemical_correction_ev: float
    her_screening_proxy_ev: float
    distance_from_target_ev: float
    max_vqe_error_ev: float
    decision: str  # "SHORTLIST", "BORDERLINE", "NOT SHORTLISTED"
    decision_reason: str
    next_action: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    inputs: Dict[str, Any] = field(default_factory=dict)
    model_params: Dict[str, Any] = field(default_factory=dict)
    backend: str = "2-qubit Qiskit Statevector VQE"
    model_scope: str = "reduced effective active-site Hamiltonian"
    status: str = "calculated"

    @property
    def is_calculated(self) -> bool:
        return True

    @property
    def is_incomplete(self) -> bool:
        return False

    @property
    def is_validation_failed(self) -> bool:
        return False

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["clean"] = self.clean.to_dict()
        d["adsorbed"] = self.adsorbed.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CalculatedResult:
        clean = (
            data["clean"]
            if isinstance(data["clean"], SingleVqeResult)
            else SingleVqeResult.from_dict(data["clean"])
        )
        adsorbed = (
            data["adsorbed"]
            if isinstance(data["adsorbed"], SingleVqeResult)
            else SingleVqeResult.from_dict(data["adsorbed"])
        )
        return cls(
            catalyst_id=data["catalyst_id"],
            formula=data.get("formula", data["catalyst_id"]),
            name=data.get("name", data["catalyst_id"]),
            category=data.get("category", "General"),
            model_type=data.get("model_type", "reduced cluster"),
            structure=data.get("structure", "surrogate model"),
            active_site=data.get("active_site", "surrogate site"),
            clean=clean,
            adsorbed=adsorbed,
            interaction_energy_ev=float(data["interaction_energy_ev"]),
            thermochemical_correction_ev=float(data.get("thermochemical_correction_ev", 0.24)),
            her_screening_proxy_ev=float(data["her_screening_proxy_ev"]),
            distance_from_target_ev=float(data.get("distance_from_target_ev", abs(float(data["her_screening_proxy_ev"])))),
            max_vqe_error_ev=float(data.get("max_vqe_error_ev", max(clean.absolute_error_ev, adsorbed.absolute_error_ev))),
            decision=str(data.get("decision", "BORDERLINE")),
            decision_reason=str(data.get("decision_reason", "")),
            next_action=str(data.get("next_action", "")),
            timestamp=str(data.get("timestamp", datetime.now().isoformat())),
            inputs=data.get("inputs", {}),
            model_params=data.get("model_params", {}),
            backend=str(data.get("backend", "2-qubit Qiskit Statevector VQE")),
            model_scope=str(data.get("model_scope", "reduced effective active-site Hamiltonian")),
            status="calculated",
        )


AnyScreeningResult = Union[CalculatedResult, ValidationFailedResult, ModelIncompleteResult]


def result_from_dict(data: Dict[str, Any]) -> AnyScreeningResult:
    """
    Robust polymorphic deserializer. Safely parses saved JSON or session state dictionaries
    into the correct typed result class without ever raising KeyError.
    """
    if not isinstance(data, dict):
        raise TypeError(f"Expected dict, got {type(data)}")

    status = data.get("status")

    # Incomplete result patterns
    if status == "model_incomplete" or data.get("model_complete") is False or ("missing" in data and "clean" not in data):
        return ModelIncompleteResult.from_dict(data)

    # Validation failed patterns
    if status == "validation_failed":
        return ValidationFailedResult.from_dict(data)

    # If clean and adsorbed are present, treat as calculated (or check validation)
    if "clean" in data and "adsorbed" in data:
        max_err = float(data.get("max_vqe_error_ev", 0.0))
        tol = float(data.get("tolerance_ev", 1e-5))
        if max_err > tol and status != "calculated":
            return ValidationFailedResult.from_dict(data)
        return CalculatedResult.from_dict(data)

    # Fallback to model incomplete
    return ModelIncompleteResult.from_dict(data)
