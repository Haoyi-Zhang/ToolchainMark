# Figure reproduction

The five reference schematics are direct Python vector drawings of the
relationships in the manuscript. They use Matplotlib without a TeX executable:

```sh
python -m pip install -r figures/requirements.txt
python -B figures/build_figures.py
```

The article reads fixed artwork from `../paper/figures/illustrations/`, which
this command does not overwrite. These illustrations do not add experimental
observations; the carrier-plane grids are schematic views of the declared
evaluation design.

## Sensitivity panels

The two PDF panels read the retained four-suite and twelve-class counts in
`results-overview.csv`. These are finite planned-unit sensitivities, not population
estimates. Labels, category order, the 72-unit fixed-suite denominator and the
five zero-sensitivity classes are retained.

From the artifact directory, optionally install the plotting dependency and run:

```sh
python -m pip install -r figures/requirements.txt
python -B figures/draw_results_overview.py
```

To rederive the plot CSV from already retained outputs without running experiments:

```sh
python -B figures/draw_results_overview.py --refresh-data results/admission-study/derived
```

In the manuscript-containing project, refresh and redraw both copies from the
artifact directory with the standalone figure producer:

```sh
python -B figures/draw_results_overview.py --refresh-data results/admission-study/derived
python -B figures/draw_results_overview.py --refresh-data results/admission-study/derived --data ../paper/figures/results-overview.csv --out-dir ../paper/figures
```

These commands read the retained summary and class-holdout counts without rerunning experiments. The paper wrapper includes the two saved vector panels without redrawing them in TeX. Python draws the axes, titles, and exact counts.

The original `scripts/generate_admission_tables.py` is a historical producer:
it can write historical table inputs and a `paper/figures/results-overview.tex`
wrapper, which is not included in this delivery. It has no plotting flag and is
not the current figure or current-table refresh command. The active
`results-overview-data.tex` wrapper is outside its write paths.

The figure PDFs embed Linux Libertine, the manuscript's body family. The
unchanged TrueType faces and their SIL Open Font License are in `../fonts/`.
The ACM manuscript template uses the corresponding Type 1 faces.
Matplotlib is not required by the scientific execution core.
