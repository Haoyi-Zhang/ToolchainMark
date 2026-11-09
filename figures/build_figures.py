"""Render the trace, factorial design, and endpoint-check figures."""
import argparse
from pathlib import Path

def motivating(out):
    from toolchain_panels import motivating as panel
    return panel(out / "motivating-counterexample.pdf")


def trace(out):
    from toolchain_panels import trace as panel
    return panel(out / "trace-model.pdf")


def architecture(out):
    from toolchain_panels import architecture as panel
    return panel(out / "architecture.pdf")


def evaluation(out):
    from toolchain_panels import evaluation as panel
    return panel(out / "evaluation-design.pdf")


def coherence(out):
    from toolchain_panels import coherence as panel
    return panel(out / "snapshot-coherence.pdf")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--outdir', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    for draw in (motivating, trace, architecture, evaluation, coherence):
        draw(args.outdir)


if __name__ == '__main__':
    main()
