# Validation and limitations

## Notebook repair

The original file is parseable JSON. Its saved `metadata.widgets` entry contains widget model IDs directly under `application/vnd.jupyter.widget-state+json`, rather than a widget-state document with `state`, `version_major`, and `version_minor`. This malformed saved widget state is the identified rendering defect. The repair removes saved widget metadata, widget output references, stale outputs, execution counts, and Colab session metadata while retaining code and explanatory content. Widgets are created afresh when executed.

## Decoder changes

* Return immediately for an initially empty syndrome: zero errors are recovered in zero rounds, while a nonzero zero-syndrome codeword is classified as incorrect recovery.
* Give a cleared syndrome priority in the stopping condition.
* Check geometry, all columns of periodic CA closure, binary seed rows, probability ranges, weight-mode spelling, error indices, and sampling counts.
* Raise an explicit error on odd matching input and bound the exponential DP fallback.
* Accept an isolated random-number generator for reproducible sampling.
* Use distance weights as the documented baseline; preserve degeneracy weighting as an experimental option.

## Checks performed locally

On Python 3.12 using the standard-library exact DP matching backend:

* 11 unittest methods pass, including all 32 single-bit errors at `L=8`, parity checks for every single error under all 32 symmetry translations, and residual-syndrome consistency for fixed and seeded errors.
* The fixed eight-bit example recovers exactly under both weight modes. With distance weighting its defect counts are `20, 14, 10, 4, 0`.
* `python demo.py --samples 100 --seed 0` at `L=8`, `p=0.08`, distance weights gives 92 exact recoveries, 1 incorrect cleared result, and 7 give-ups. This is a small reproducibility example, not a benchmark or threshold estimate.
* JSON structure, unique notebook cell IDs, cleared outputs, and agreement between notebook core definitions and the module are tested.

The local environment has no scientific Python/Jupyter packages, and network restrictions prevent dependency installation. Full dependency validation was completed remotely: [GitHub Actions run 39813604923](https://github.com/ghostshahinul/Fibonacci-Decoder/actions/runs/39813604923) passed on Python 3.10 and 3.12 for implementation commit `e43b48c04ca44d878f515624fc3a9411adcc0600`. Both jobs installed the package and notebook dependencies, passed all 11 tests using NetworkX (with explicit DP fallback coverage), validated the notebook with nbformat, and executed every cell in a fresh kernel, including plotting and widget creation. Executed notebooks are attached to that run as artifacts. The SVG example is generated without plotting dependencies from recorded DP-backend snapshots.

## Remaining scientific limits

The code is a classical parity-check decoder. Its connection to quantum error correction is conceptual and algorithmic; it does not implement a quantum stabilizer code. Neither published threshold reproduction nor equivalence to the original C++ tables is established. The notebook's original C++ origin remains to be verified, and no speculative upstream URL or license has been supplied. Matching ties can alter trajectories across backends. Experiments currently use independent bit flips, not the paper's full correlated-noise study.
