# Figure reproduction

The workflow and evaluation figures are native Python vectors. The build
uses Matplotlib without a TeX executable to draw the figures:

```sh
python -m pip install -r figures/requirements.txt
python -B figures/build_figures.py
python -B figures/publication_figures.py
```

Run the publication generator after the legacy entry point. Its evaluation
diagram distinguishes subject replay from relation selection on a held-out
carrier or mechanism. The paper build copies these PDFs into the manuscript.
The native admission and external-pair plots use the retained cohort summary
and case table.

## Sensitivity panels

The two PDF panels read the retained four-suite and twelve-class counts in
`results-overview.csv`. These are finite planned-unit sensitivities, not population
estimates. Labels, category order, the 72-unit fixed-suite denominator and the
five zero-sensitivity classes are retained.

From the artifact directory, optionally install the plotting dependency and run:

```sh
python -m pip install -r figures/requirements.txt
python -B figures/publication_figures.py
```

To rederive the plot CSV from already retained outputs without running experiments:

```sh
python -B figures/draw_results_overview.py --refresh-data results/admission-study/derived
```

In the manuscript-containing project, refresh and redraw both copies from the
artifact directory with the standalone figure producer:

```sh
python -B figures/draw_results_overview.py --refresh-data results/admission-study/derived
python -B figures/publication_figures.py
```

These commands read the retained summary and class-holdout counts without running experiments or changing current table inputs or frozen native records. The article includes the saved results-overview panels and a separate verdict-transition chart. The latter reads `results/current-native/derived/legacy_transitions.csv` and normalizes each bar within its earlier outcome. `paper/build.sh` copies both sets of regenerated PDFs into the paper.

The original `scripts/generate_admission_tables.py` is a historical producer:
it can write historical table inputs and a `paper/figures/results-overview.tex`
wrapper, which is not included in this delivery. It has no plotting flag and is
not the current figure or current-table refresh command. The active
`results-overview-data.tex` wrapper is outside its write paths.

Current publication figures use the manuscript's Linux Libertine O faces,
resolved through `kpsewhich` or `FIGURE_TEX_FONT_DIR`.
For the separate table-refresh tool, the unmodified Linux Libertine regular TrueType face is bundled under
`../fonts/OFL-1.1.txt`. The renderer also accepts `--font` or matching installed
TeX/Matplotlib fonts; it rejects substitutions and CFF/Type1 fonts. Matplotlib
is optional and is not required by the scientific execution core.
