"""
Q-CATALYST: Batch Quantum Screening Precomputation Script
===========================================================
Precomputes quantum VQE and exact ground-state calculations across the 12 catalysts.
Saves structured JSON results with complete data contracts for UI loading.
"""

from pathlib import Path
from catalyst_database import get_all_catalysts
from catalyst_models import get_all_models
from quantum_catalyst_engine import calculate, save_results
from screening_types import ScreeningPolicy

OUT_FILE = Path("quantum_screening_results.json")


def main():
    models = get_all_models()
    catalysts = get_all_catalysts()
    results = {}
    policy = ScreeningPolicy()

    print("============================================================")
    print("Q-CATALYST: Running Batch Quantum-Assisted Screening")
    print("============================================================")

    for item in catalysts:
        cid = item["id"]
        model = models[cid]

        result = calculate(
            catalyst_id=cid,
            model=model,
            catalyst_meta=item,
            policy=policy,
        )
        results[cid] = result

        if result.is_incomplete:
            print(f"[{cid:5s}] MODEL INCOMPLETE: {', '.join(result.missing_fields)}")
        elif result.is_validation_failed:
            print(f"[{cid:5s}] VALIDATION FAILED: max error = {result.max_vqe_error_ev:.2e} eV")
        else:
            print(
                f"[{cid:5s}] {result.decision:15s} | "
                f"HER Proxy: {result.her_screening_proxy_ev:+.4f} eV | "
                f"VQE Error: {result.max_vqe_error_ev:.2e} eV"
            )

    save_results(OUT_FILE, results)
    print("============================================================")
    print(f"Successfully precomputed and saved results to {OUT_FILE.resolve()}")
    print("============================================================")


if __name__ == "__main__":
    main()
