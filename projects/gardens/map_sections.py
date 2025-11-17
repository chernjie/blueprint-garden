"""
Plot a plan-view map of garden sections described in projects/gardens/README.md.

Run:
    python3 projects/gardens/map_sections.py

The script saves garden_map.png next to itself and displays the plot unless
--no-show is passed.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

import matplotlib


# Coordinates are in feet using the README coordinate system
SECTION_DATA: List[dict] = [
    {
        "name": "Driveway Trench",
        "kind": "rect",
        "coords": (0, 0, 1, 20),
        "color": "#f4d35e",
        "note": "Kurrajong → Mallow run",
        "label_offset": (-1.5, 0),
    },
    {
        "name": "Drybed12",
        "kind": "rect",
        "coords": (-10, 70, -7, 58),
        "color": "#ee964b",
        "note": "Wicking retention bed",
    },
    {
        "name": "Sunny Front Left",
        "kind": "rect",
        "coords": (0, 25, -10, 28),
        "color": "#9ad1d4",
        "note": "Front entry showcase",
    },
    {
        "name": "North8",
        "kind": "rect",
        "coords": (0, 25, 35, 50),
        "color": "#c5e1a5",
        "note": "Long edible strip",
    },
    {
        "name": "Herbal Strip + Compost",
        "kind": "rect",
        "coords": (-7, 70, 0, 60),
        "color": "#c3aed6",
        "note": "Culinary/medicinals",
    },
    {
        "name": "Orchard Section",
        "kind": "poly",
        # Approximate diagonal to show banana→pomegranate run
        "points": [(0, 60), (3, 58), (5, 54), (7, 50), (7, 55), (2, 60)],
        "color": "#80cbc4",
        "note": "Heat-wall fruits",
    },
    {
        "name": "Patio Planters",
        "kind": "rect",
        "coords": (10, 40, 12, 44),
        "color": "#ffccbc",
        "note": "Stacked towers",
    },
]

plt = None  # populated in configure_matplotlib
Polygon = None
Rectangle = None


def _rect_points(coords: Sequence[float]) -> List[Tuple[float, float]]:
    x1, y1, x2, y2 = coords
    x_low, x_high = sorted((x1, x2))
    y_low, y_high = sorted((y1, y2))
    return [
        (x_low, y_low),
        (x_high, y_low),
        (x_high, y_high),
        (x_low, y_high),
    ]


def _section_points(section: dict) -> List[Tuple[float, float]]:
    if section["kind"] == "rect":
        return _rect_points(section["coords"])
    return list(section["points"])


def _section_center(points: Iterable[Tuple[float, float]]) -> Tuple[float, float]:
    pts = list(points)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def _draw_section(ax, section: dict) -> None:
    global Polygon, Rectangle
    assert Rectangle is not None and Polygon is not None
    if section["kind"] == "rect":
        x1, y1, x2, y2 = section["coords"]
        rect = Rectangle(
            (min(x1, x2), min(y1, y2)),
            abs(x2 - x1),
            abs(y2 - y1),
            facecolor=section["color"],
            edgecolor="black",
            linewidth=1.2,
            alpha=0.7,
        )
        ax.add_patch(rect)
        points = _rect_points(section["coords"])
    else:
        poly = Polygon(
            section["points"],
            closed=True,
            facecolor=section["color"],
            edgecolor="black",
            linewidth=1.2,
            alpha=0.7,
        )
        ax.add_patch(poly)
        points = list(section["points"])

    cx, cy = _section_center(points)
    dx, dy = section.get("label_offset", (0.0, 0.0))
    label = section["name"]
    if section.get("note"):
        label += f"\n{section['note']}"
    ax.text(
        cx + dx,
        cy + dy,
        label,
        ha="center",
        va="center",
        fontsize=8,
        weight="bold",
    )


def _compute_bounds(sections: Sequence[dict]) -> Tuple[float, float, float, float]:
    xs: List[float] = []
    ys: List[float] = []
    for section in sections:
        pts = _section_points(section)
        xs.extend(p[0] for p in pts)
        ys.extend(p[1] for p in pts)
    margin = 5
    return (
        min(xs) - margin,
        max(xs) + margin,
        min(ys) - margin,
        max(ys) + margin,
    )


def build_map(output: Path, show_plot: bool) -> None:
    global plt
    assert plt is not None
    fig, ax = plt.subplots(figsize=(9, 10))
    for section in SECTION_DATA:
        _draw_section(ax, section)

    xmin, xmax, ymin, ymax = _compute_bounds(SECTION_DATA)
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_xlabel("x (ft east)")
    ax.set_ylabel("y (ft north)")
    ax.set_title("Blueprint Garden — Section Map")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, which="both", linewidth=0.3, color="#cccccc")

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=300, bbox_inches="tight")
    if show_plot:
        plt.show()
    else:
        plt.close(fig)
    print(f"Saved map to {output}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("garden_map.png"),
        help="Path to save the rendered map (default: %(default)s)",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Skip displaying the interactive window (handy for CI/export).",
    )
    parser.add_argument(
        "--backend",
        help="Matplotlib backend to use (defaults to Agg when --no-show is supplied).",
    )
    return parser.parse_args()


def configure_matplotlib(backend: str | None, headless: bool) -> None:
    desired = backend or ("Agg" if headless else None)
    if desired:
        matplotlib.use(desired, force=True)
    global plt, Polygon, Rectangle
    import matplotlib.pyplot as _plt
    from matplotlib.patches import Polygon as _Polygon, Rectangle as _Rectangle

    plt = _plt
    Polygon = _Polygon
    Rectangle = _Rectangle


def main() -> None:
    args = parse_args()
    configure_matplotlib(args.backend, args.no_show)
    build_map(args.output, show_plot=not args.no_show)


if __name__ == "__main__":
    main()
