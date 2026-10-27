"""Plot the Figure of Merit over time: project/reports/fom.csv -> project/reports/fom.png.

    python3 project/reports/plot_fom.py

Three panels on one x-axis (the FoM points), because the measures have different scales
and a chart never gets two y-axes: verifier alignment in %, open deviations, and unit-test
checks passed. Colours are the first three slots of the reference palette of the dataviz
method (blue, orange, aqua), in a fixed order.
"""
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent

SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#e6e5e1"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"

# Short names for the x-axis, one per point (the full labels are in fom.csv).
SHORT = {
    "1": "baseline",
    "2": "+sequence",
    "3": "weak_ptr",
    "4": "+tests",
    "5": "+System Op.",
    "6": "Cabin→Sys",
    "7": "History owns",
    "8": "severity, limit",
    "9": "getters, resolve",
}


def number(text):
    return float(text) if text not in ("", None) else None


def read_points():
    with open(HERE / "fom.csv", newline="") as f:
        return list(csv.DictReader(f))


def style(axis, title):
    axis.set_facecolor(SURFACE)
    axis.set_title(title, loc="left", fontsize=11, color=TEXT, pad=8)
    axis.grid(axis="y", color=GRID, linewidth=1)
    axis.set_axisbelow(True)
    for side in ("top", "right", "left"):
        axis.spines[side].set_visible(False)
    axis.spines["bottom"].set_color(GRID)
    axis.tick_params(colors=TEXT_SECONDARY, length=0)


def line(axis, xs, ys, color, label, markersize=7):
    shown = [(x, y) for x, y in zip(xs, ys) if y is not None]
    px, py = zip(*shown)
    axis.plot(px, py, color=color, linewidth=2, solid_capstyle="round", solid_joinstyle="round",
              marker="o", markersize=markersize, markeredgecolor=SURFACE, markeredgewidth=2, label=label)
    return px[-1], py[-1]


def main():
    points = read_points()
    xs = [int(p["point"]) for p in points]
    class_pct = [number(p["class_pct"]) for p in points]
    sequence_pct = [number(p["sequence_smoke_escalation_pct"]) for p in points]
    # The state machines: the lowest alignment among those that exist at that point.
    state_pct = [min(v for v in (number(p["state_incident_pct"]), number(p["state_cabin_pct"]),
                                 number(p["state_monitoring_system_pct"])) if v is not None)
                 for p in points]
    deviations = [number(p["deviations"]) for p in points]
    tests = [number(p["tests_passed"].split("/")[0]) if p["tests_passed"] else None for p in points]

    figure, (top, middle, bottom) = plt.subplots(
        3, 1, figsize=(10, 8.2), sharex=True, gridspec_kw={"height_ratios": [2.2, 1, 1]})
    figure.patch.set_facecolor(SURFACE)

    style(top, "Verifier alignment between design and implementation (%)")
    # Sequence and state machines are both at 100 % for points 2-7: the sequence is drawn
    # first with bigger dots, so its orange ring stays visible around the smaller aqua dots.
    for ys, color, name, size in ((sequence_pct, ORANGE, "Sequence smoke_escalation", 11),
                                  (state_pct, AQUA, "State machines (lowest)", 6),
                                  (class_pct, BLUE, "Class diagram", 7)):
        last_x, last_y = line(top, xs, ys, color, name, size)
        top.annotate(f"{last_y:.1f} %", (last_x, last_y), xytext=(10, -4 if color != AQUA else 4),
                     textcoords="offset points", color=TEXT, fontsize=9)
    top.set_ylim(60, 104)
    top.legend(loc="lower left", frameon=False, fontsize=9, labelcolor=TEXT, ncol=3, handlelength=3.2)
    top.annotate("points 2–7: sequence and state machines both at 100 %", (4.5, 100),
                 xytext=(0, 9), textcoords="offset points", ha="center", color=TEXT_SECONDARY, fontsize=8)
    for x, y in ((1, class_pct[0]), (3, class_pct[2])):
        top.annotate(f"{y:.1f} %", (x, y), xytext=(0, -16), textcoords="offset points",
                     ha="center", color=TEXT_SECONDARY, fontsize=8)

    style(middle, "Open deviations (unclear UML resolved by Team Guide or AI assumption)")
    last_x, last_y = line(middle, xs, deviations, TEXT_SECONDARY, "Deviations")
    middle.annotate(f"{last_y:.0f}", (last_x, last_y), xytext=(10, -4), textcoords="offset points",
                    color=TEXT, fontsize=9)
    middle.set_ylim(0, 30)

    style(bottom, "Unit-test checks passed (all passing)")
    last_x, last_y = line(bottom, xs, tests, TEXT_SECONDARY, "Checks")
    bottom.annotate(f"{last_y:.0f}", (last_x, last_y), xytext=(10, -4), textcoords="offset points",
                    color=TEXT, fontsize=9)
    bottom.set_ylim(0, 80)
    bottom.set_xticks(xs)
    bottom.set_xticklabels([f"{x}\n{SHORT[str(x)]}" for x in xs], fontsize=8, color=TEXT_SECONDARY)
    bottom.set_xlim(0.6, 9.9)
    bottom.set_xlabel("Figure of Merit point (one per iteration, 2026-10-27)", color=TEXT_SECONDARY, fontsize=9)

    figure.suptitle("Hytte Monitoring – Figure of Merit over 9 iterations", x=0.01, ha="left",
                    fontsize=14, color=TEXT, fontweight="bold")
    figure.tight_layout(rect=(0, 0, 1, 0.96))
    figure.savefig(HERE / "fom.png", dpi=160, facecolor=SURFACE)
    print("wrote", HERE / "fom.png")


if __name__ == "__main__":
    main()
