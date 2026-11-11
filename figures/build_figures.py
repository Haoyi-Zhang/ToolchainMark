"""Regenerate the principal paper diagrams using the shared figure sources."""
import argparse
from pathlib import Path

from figure_style import paper_style
from publication_figures import architecture, coherence, evaluation, motivation, trace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--outdir', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    paper_style('tosem')
    for draw in (motivation, trace, architecture, evaluation, coherence):
        draw(args.outdir, None)


if __name__ == '__main__':
    main()
