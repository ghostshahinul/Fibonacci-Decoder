# Validation and limitations

## Run the checks

Install the project and notebook dependencies, then run the regression suite:

```bash
python -m pip install -e ".[notebook]"
python -m unittest discover -s tests -v
python demo.py
```

The [CI workflow](../.github/workflows/ci.yml) runs these checks on Python 3.10 and 3.12. It also validates the notebook schema with nbformat and executes every cell in a fresh Python kernel. Executed notebooks are uploaded as workflow artifacts.

## Test coverage

The 11 unittest methods cover:

* Periodic lattice geometry and single-bit syndrome extraction.
* Even defect parity for every single-bit error under all 32 symmetry translations at `L=8`.
* Exact recovery of all 32 single-bit errors and the fixed eight-bit example.
* Zero-round handling of an empty syndrome, including rejection of nonzero residual codewords as exact recoveries.
* Consistency between recorded residual syndromes and the error XOR prediction.
* Shortest-path multiplicities and minimum-weight matching with negative edge weights.
* Both weight models, explicit DP fallback coverage, input validation, and seeded sampling.
* Notebook structure, cleared saved outputs, and agreement between notebook and module definitions.

## Recorded results

[GitHub Actions run 39813604923](https://github.com/ghostshahinul/Fibonacci-Decoder/actions/runs/39813604923) passed on Python 3.10 and 3.12 for implementation commit `e43b48c04ca44d878f515624fc3a9411adcc0600`. Both jobs passed package installation, all 11 tests with NetworkX available, notebook schema validation, and execution of every notebook cell, including plotting and widget creation.

The following reference results use Python 3.12 and the exact DP matching backend:

| Experiment | Parameters | Result |
|---|---|---|
| Fixed error | `L=8`, `p=0.08`, distance weights; bits `[3,7,12,14,16,20,27,29]` | Exact recovery in four rounds; defect counts `20,14,10,4,0` |
| Fixed error | Same error and geometry, degeneracy weights | Exact recovery |
| Independent bit flips | `L=8`, `p=0.08`, distance weights, 100 samples, seed 0 | 92 exact recoveries, 1 incorrect cleared result, 7 give-ups |

These are small reproducibility examples, not threshold estimates. The command-line demo uses NetworkX when installed; its results can differ from the DP reference when equal-cost matchings are resolved differently. The [SVG generator](../tools/render_example.py) explicitly selects DP to reproduce the illustrated trajectory.

## Notebook portability

The committed notebook excludes saved widget state, output references, execution counts, and session-specific metadata. Widgets and plots are generated when the notebook runs. This keeps the file suitable for static GitHub rendering and avoids stale widget references. Use Jupyter for the interactive slider.

## Scientific and reproducibility limits

This implementation decodes a classical parity-check code. Published threshold reproduction and equivalence to the reference C++ lookup tables have not been established. In the experimental degeneracy model, `N` counts shortest graph paths; agreement with the reference tables remains to be checked.

Current experiments use independent bit flips rather than the paper's full correlated spanning-noise study. Matching ties can alter trajectories across backends and dependency versions. A cleared syndrome is counted as success only when the predicted error equals the injected error exactly.
