# Q-CATALYST

**Full Title:** Quantum-Assisted Active-Site Screening and Analysis for Hydrogen Evolution Reaction (HER) Catalyst Models

---

## 1. Project Purpose
**Q-CATALYST** is a university research prototype designed as a specialized computational workbench for computational materials scientists and electrochemists. It provides quantum-assisted active-site pre-screening for 12 Hydrogen Evolution Reaction (HER) catalyst candidates across noble metals, transition metals, 2D dichalcogenides, and alloys.

Rather than treating catalysts as abstract labels or running unverified black-box calculations, Q-CATALYST exposes the complete physical and algorithmic chain:
$$\text{Material} \rightarrow \text{Active Site Surrogate} \rightarrow \text{Electronic Hamiltonian} \rightarrow \text{Qiskit VQE} \rightarrow \text{Exact Validation} \rightarrow \Delta E_{H^*} \rightarrow \text{HER Descriptor Proxy} \rightarrow \text{Decision} \rightarrow \text{Next Action}$$

Every calculation is fully traceable, reproducible, and tied directly to concrete next steps for computational chemistry workflows.

---

## 2. Scientific Scope & Guardrails

### Scientific Honesty Principles
- **Computational Pre-Screening:** Q-CATALYST evaluates transparent reduced effective active-site Hamiltonians. It is intended for early-stage screening and parameter sensitivity analysis.
- **NEVER Claim "Best Catalyst" or "Experimentally Proven":** The meaningful thermodynamic descriptor for HER is the hydrogen adsorption free energy ($\Delta G_{H^*}$), with a standard Sabatier target near $0.00\text{ eV}$. However, $\Delta G_{H^*}$ alone is a necessary but **not sufficient** predictor of real-world electrocatalysis.
- **Transparent Reduced Model:** Model parameters (electronegativity $\chi$, effective $d$-level, coordination factor, electronic coupling, site accessibility) are exploratory surrogate model parameters. They are **not** experimental constants or DFT-fitted parameters.
- **Transparent Thermochemical Correction:** The $+0.24\text{ eV}$ term represents a standard prototype thermochemical approximation for hydrogen adsorption on transition metals ($\Delta \text{ZPE} - T\Delta S \approx +0.24\text{ eV}$). It is explicitly labeled and is not a catalyst-specific vibrational frequency calculation.

### Real-World Factors Not Addressed by Reduced Models
1. Full chemical kinetics (Volmer-Heyrovsky vs. Volmer-Tafel reaction barriers)
2. Solvent dielectric screening and water double-layer polarization
3. Electrolyte composition, ionic strength, and pH effects
4. Applied electrode bias and potential-dependent coverage
5. Dynamic surface restructuring and facet reconstruction under reaction conditions
6. Catalyst dissolution resistance, Pourbaix stability, and electrochemical corrosion

---

## 3. Installation & Windows Setup

The project is developed natively for Windows using Python 3.12+.

### Prerequisites
- Windows 10 or 11 (PowerShell or Command Prompt)
- Python 3.12+ (64-bit)

### Installation
From the project root (`C:\Users\palem\OneDrive\Documents\3rd Year\Q-CATALYST-FINAL-RESEARCH`):

```powershell
# Install required dependencies
python -m pip install -r requirements.txt
```

### Dependencies
- `qiskit>=2.5,<3.0` (Quantum circuit simulation, Pauli operators, Statevector)
- `streamlit>=1.40` (Interactive scientific research workbench)
- `numpy>=2.0` (Matrix operations and exact eigensolvers)
- `scipy>=1.14` (BFGS optimization for VQE)
- `pandas>=2.2` (Evidence table formatting and dataset export)
- `altair>=5.0` (Interactive screening distribution visualization)

---

## 4. How to Run

### Interactive Streamlit Workbench (Primary)
Launch the local web application:
```powershell
python -m streamlit run app.py
```
Streamlit will automatically open the application at `http://localhost:8501`.

### Batch Screening Precomputation (Optional)
To recalculate and update the precomputed JSON dataset (`quantum_screening_results.json`) for all 12 catalysts in batch mode:
```powershell
python run_quantum_screening.py
```

### Running Test Suite
Execute the full unit and end-to-end integration test suite:
```powershell
python -m unittest discover -s tests -v
```

---

## 5. System Architecture & Codebase Design

The codebase enforces clean modular separation and strict typed data structures:

```
Q-CATALYST-FINAL-RESEARCH/
├── app.py                      # Main Streamlit workbench (Analyze, Compare, How it works, Export)
├── catalyst_database.py        # 12 curated catalysts (Pt, Ru, Ir, Pd, Ni, Co, Fe, Mo, W, MoS2, WS2, NiMo)
├── catalyst_models.py          # Active-site surrogate models & dynamic site configuration
├── quantum_catalyst_engine.py  # Qiskit 2.x VQE engine, exact diagonalization, backend interfaces
├── screening_logic.py          # Evidence-based decision engine & research next actions
├── screening_types.py          # Strict dataclass schemas preventing KeyError: 'clean'
├── run_quantum_screening.py    # Batch screening precomputation script
├── requirements.txt            # Python dependencies
├── README.md                   # Complete scientific and technical documentation
├── tests/                      # Automated test suite (22 unit & integration tests)
│   ├── test_catalysts.py
│   ├── test_quantum_engine.py
│   ├── test_screening_logic.py
│   ├── test_result_handling.py
│   └── test_end_to_end.py
└── quantum_screening_results.json # Precomputed typed results
```

### Architectural Solution to `KeyError: 'clean'`
Previous prototypes crashed because incomplete models (such as $\text{MoS}_2$ or $\text{Ni–Mo}$) lacked `"clean"` or `"adsorbed"` keys.
Q-CATALYST solves this architecturally in `screening_types.py` via explicit result dataclasses:
- `CalculatedResult`: Fully validated quantum result containing VQE energies, exact reference, error, interaction energy, and screening proxy.
- `ValidationFailedResult`: Executed quantum calculation where VQE error exceeded numerical tolerance ($> 10^{-5}\text{ eV}$). Status set to `BORDERLINE` with explanation.
- `ModelIncompleteResult`: Candidate with missing structural definitions. Safely exports as `"MODEL INCOMPLETE"` with `N/A` for energies, preventing any dictionary lookup errors.

---

## 6. Calculation Workflow

1. **Active-Site Modeling:**
   Extracts active coordination sites rather than bulk approximations:
   - Monometallic: Under-coordinated step/edge site surrogate.
   - $\text{MoS}_2$ & $\text{WS}_2$: Requires phase (2H semiconducting / 1T metallic), edge orientation (metal/S edge), and local adsorption geometry (atop metal, bridge S-S, S-vacancy).
   - $\text{Ni–Mo}$: Requires alloy ratio ($\text{Ni}_x\text{Mo}_{1-x}$), interface boundary, and $\text{H}^*$ adsorption site.
   - If required structural choices are missing, status is set to `MODEL INCOMPLETE` and no fake calculation is performed.

2. **Electronic Hamiltonian Construction:**
   Constructs a 2-qubit operator via `qiskit.quantum_info.SparsePauliOp`:
   $$\hat{H} = c_0 \hat{I} + z_1 \hat{Z}_1 + z_2 \hat{Z}_2 + z_{12} \hat{Z}_1\hat{Z}_2 + x_{12} \hat{X}_1\hat{X}_2 + y_{12} \hat{Y}_1\hat{Y}_2$$
   Parameters scale dynamically with Pauling electronegativity $\chi$, effective $d$-band center, coordination number, accessibility factor, and $\text{H}^*$ distance.

3. **VQE & Exact Numerical Validation:**
   - **Ansatz:** Hardware-efficient parameterized circuit (`qiskit.circuit.library.real_amplitudes`, 2 qubits, $R_y$ rotations and CNOT entanglement).
   - **Optimization:** Scipy BFGS optimizer with analytical statevector expectation value.
   - **Exact Reference:** Direct matrix diagonalization ($\min \text{eig}(\hat{H})$) of the **identical** operator.
   - **Validation:** Absolute VQE error $|E_{\text{VQE}} - E_{\text{exact}}|$ must be below $10^{-5}\text{ eV}$.

4. **Interaction Energy & Screening Proxy:**
   $$\Delta E_{H^*}^{model} = E(cat + H^*) - E(cat)$$
   $$\Delta G_{H^*}^{proxy} = \Delta E_{H^*}^{model} + \Delta_{thermo} \quad (\Delta_{thermo} = +0.24\text{ eV})$$

5. **Screening Decision & Action Recommendation:**
   The proxy distance from the $0.00\text{ eV}$ target determines the classification and immediate research next step.

---

## 7. How Screening Decisions Work

Q-CATALYST uses a transparent prototype screening policy:
- **Target Value:** $0.00\text{ eV}$ (Ideal thermodynamic Sabatier reversibility)
- **Shortlist Region:** $\pm 0.10\text{ eV}$
- **Borderline Review Region:** $\pm 0.20\text{ eV}$
- **Quantum Validation Tolerance:** $10^{-5}\text{ eV}$

| Decision State | Criteria | Meaning | Next Research Action |
|---|---|---|---|
| **SHORTLIST** | VQE validated, $|\Delta G_{H^*}^{proxy}| \le 0.10\text{ eV}$ | Candidate falls within the thermodynamic target window. | Use this active-site model for higher-fidelity investigation: define the actual surface/cluster geometry and validate the $\text{H}^*$ free-energy calculation against a higher-level reference. |
| **BORDERLINE** | VQE failed validation, or $0.10 < |\Delta G_{H^*}^{proxy}| \le 0.20\text{ eV}$ | Candidate requires additional scrutiny or solver refinement. | Refine the active-site geometry or electronic model and repeat the calculation. Check VQE convergence tolerance or explore local site sensitivity. |
| **NOT SHORTLISTED** | VQE validated, $|\Delta G_{H^*}^{proxy}| > 0.20\text{ eV}$ | Adsorption is either too weak or too strong in the current model. | Do not discard the material experimentally from this reduced model alone. First inspect active-site coordination assumptions and repeat with a higher-fidelity model. |
| **MODEL INCOMPLETE** | Structural parameters undefined | Insufficient data to build Hamiltonian. | Complete the missing material/site definition before running the quantum calculation. |

---

## 8. Stale-Result Detection

To maintain scientific integrity during interactive parameter exploration:
- When a user adjusts any slider ($\text{H}^*$ distance, site accessibility, local charge) or alters edge/interface options, the software compares current UI controls against the input snapshot stored in the active result.
- If parameters differ, an on-screen alert notifies the researcher:
  > ⚠️ **Inputs changed.** The displayed result was computed with previous parameters. Click **Run Quantum-Assisted Analysis** to update.
- The software never silently presents an outdated calculation as if it reflects new inputs.

---

## 9. Future-Ready Architecture

The quantum engine defines an abstract base interface:
```python
class ElectronicStructureBackend(ABC):
    @abstractmethod
    def build_hamiltonian(self, model, adsorbed, inputs) -> SparsePauliOp: ...
    @abstractmethod
    def run_vqe(self, hamiltonian, max_iter, gtol, seed, force_fail) -> SingleVqeResult: ...
```
- Current implementation: `ReducedModelBackend` (Qiskit 2.x Statevector VQE + Exact matrix diagonalization).
- Future integration point: `FuturePsi4Backend` (prepares for native Windows Psi4 + Qiskit Nature integration, active space CASSCF selection, and Jordan-Wigner fermion-to-qubit mapping without UI alterations).
