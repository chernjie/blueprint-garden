"""
Generate plan and elevation drawings for the garage office using layout metadata.

Examples:
    python3 projects/garage-office/garage-office.py
    python3 projects/garage-office/garage-office.py --config projects/garage-office/layout.yaml --no-show --output-dir projects/garage-office/renders
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict

import matplotlib

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None

plt = None  # populated in configure_matplotlib

STUD_D = 0.0
STUD_W = 0.0
EYE_H = 0.0
ROOM_W = ROOM_D = ROOM_H = 0.0
WALL_THK = 0.0
POCKET_DOOR_CLEAR_W = POCKET_DOOR_CLEAR_H = POCKET_DOOR_OFFSET_FROM_RIGHT = 0.0
WINDOW_W = WINDOW_H = WINDOW_AFF = 0.0
DESK_W = DESK_D = DESK_H = 0.0
HVAC_W = HVAC_H = HVAC_PROJ_OFFICE = HVAC_PROJ_GARAGE = 0.0
BOOKSHELF_W = BOOKSHELF_D = BOOKSHELF_H = 0.0
PLATFORM_W = PLATFORM_D = PLATFORM_H = 0.0


def load_config(path: Path) -> Dict:
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        data = yaml.safe_load(text) or {}
    else:
        data = json.loads(text)
    if not data:
        raise SystemExit(f"Configuration file {path} is empty.")
    return data


def apply_config(cfg: Dict) -> None:
    global STUD_D, STUD_W, EYE_H, ROOM_W, ROOM_D, ROOM_H, WALL_THK
    global POCKET_DOOR_CLEAR_W, POCKET_DOOR_CLEAR_H, POCKET_DOOR_OFFSET_FROM_RIGHT
    global WINDOW_W, WINDOW_H, WINDOW_AFF
    global DESK_W, DESK_D, DESK_H
    global HVAC_W, HVAC_H, HVAC_PROJ_OFFICE, HVAC_PROJ_GARAGE
    global BOOKSHELF_W, BOOKSHELF_D, BOOKSHELF_H
    global PLATFORM_W, PLATFORM_D, PLATFORM_H

    STUD_D = cfg["stud"]["depth"]
    STUD_W = cfg["stud"]["width"]
    EYE_H = cfg["eye_height"]

    ROOM_W = cfg["room"]["width"]
    ROOM_D = cfg["room"]["depth"]
    ROOM_H = cfg["room"]["height"]

    WALL_THK = cfg["wall"]["thickness"]

    POCKET_DOOR_CLEAR_W = cfg["pocket_door"]["clear_width"]
    POCKET_DOOR_CLEAR_H = cfg["pocket_door"]["clear_height"]
    POCKET_DOOR_OFFSET_FROM_RIGHT = cfg["pocket_door"]["offset_from_right"]

    WINDOW_W = cfg["window"]["width"]
    WINDOW_H = cfg["window"]["height"]
    WINDOW_AFF = cfg["window"].get("sill_aff", ROOM_H - WINDOW_H - 24)

    DESK_W = cfg["desk"]["width"]
    DESK_D = cfg["desk"]["depth"]
    DESK_H = cfg["desk"]["height"]

    HVAC_W = cfg["hvac"]["width"]
    HVAC_H = cfg["hvac"]["height"]
    HVAC_PROJ_OFFICE = cfg["hvac"]["proj_office"]
    HVAC_PROJ_GARAGE = cfg["hvac"]["proj_garage"]

    BOOKSHELF_W = cfg["bookshelf"]["width"]
    BOOKSHELF_D = cfg["bookshelf"]["depth"]
    BOOKSHELF_H = cfg["bookshelf"]["height"]

    PLATFORM_W = cfg["platform"]["width"]
    PLATFORM_D = cfg["platform"]["depth"]
    PLATFORM_H = cfg["platform"]["height_aff"]


def layout_context() -> Dict:
    """Derived coordinates shared by both drawings."""
    pd_x0 = ROOM_W - POCKET_DOOR_CLEAR_W - POCKET_DOOR_OFFSET_FROM_RIGHT
    pd_x1 = ROOM_W - POCKET_DOOR_OFFSET_FROM_RIGHT
    pd_x2 = pd_x0 - POCKET_DOOR_CLEAR_W - POCKET_DOOR_OFFSET_FROM_RIGHT
    win_x = (ROOM_W - WINDOW_W) / 2
    plat_x = 0
    ctx = {
        "pd_x0": pd_x0,
        "pd_x1": pd_x1,
        "pd_x2": pd_x2,
        "pd_y": WALL_THK / 2,
        "win_x": win_x,
        "desk_x": 0,
        "desk_y": WALL_THK,
        "bs_x": ROOM_W - BOOKSHELF_W,
        "bs_y": ROOM_D - BOOKSHELF_D,
        "plat_x": plat_x,
        "plat_stud_x": plat_x + (PLATFORM_W - STUD_D * 2),
        "hvac_x": pd_x2 - HVAC_W - STUD_D,
        "hvac_y": 0,
        "plat_z": PLATFORM_H + STUD_W,
    }
    ctx["hvac_face_z"] = DESK_H - HVAC_H - HVAC_H / 2
    return ctx


def build_top_down(ctx: Dict):
    global plt
    assert plt is not None
    fig, ax = plt.subplots(figsize=(ROOM_W / 12, ROOM_D / 12))

    ax.plot([0, ROOM_W, ROOM_W, 0, 0], [0, 0, ROOM_D, ROOM_D, 0], 'k-', lw=2)

    ax.plot([ctx["pd_x0"], ctx["pd_x1"]], [ctx["pd_y"], ctx["pd_y"]], 'c-', lw=6)
    ax.plot([ctx["pd_x2"], ctx["pd_x0"]], [ctx["pd_y"], ctx["pd_y"]], 'c:', lw=6)
    ax.text((ctx["pd_x0"] + ctx["pd_x1"]) / 2, WALL_THK,
            f"Pocket Door {POCKET_DOOR_CLEAR_W}\"",
            ha='center', va='bottom', fontsize=8)

    ax.plot([ctx["win_x"], ctx["win_x"] + WINDOW_W], [ROOM_D, ROOM_D], 'c-', lw=6)
    ax.text(ctx["win_x"] + WINDOW_W / 2, ROOM_D - 3,
            f"Window {WINDOW_W}\"", ha='center', va='top', fontsize=8)

    ax.add_patch(plt.Rectangle((ctx["desk_x"], ctx["desk_y"]), DESK_W, DESK_D, fill=False, ec='y'))
    ax.text(ctx["desk_x"] + DESK_W / 2, ctx["desk_y"] + DESK_D / 2,
            f"Desk {DESK_W}\"×{DESK_D}\"", ha='center', va='center', fontsize=8)

    ax.add_patch(plt.Rectangle((ctx["bs_x"], ctx["bs_y"]), BOOKSHELF_W, BOOKSHELF_D, fill=False, ec='y'))
    ax.text(ctx["bs_x"] + BOOKSHELF_W / 2, ctx["bs_y"] + BOOKSHELF_D / 2,
            f"Bookshelf {BOOKSHELF_W}\"×{BOOKSHELF_D}\"", ha='center', va='center', fontsize=7)

    ax.add_patch(plt.Rectangle((ctx["plat_stud_x"], 0), STUD_D, PLATFORM_D, fill=False, ec='k'))
    ax.text(ctx["plat_stud_x"] / 2, ROOM_D * 2 / 3,
            f"Overhead Platform \n {PLATFORM_W}\"×{PLATFORM_D}\"",
            ha='center', va='center', fontsize=8)

    ax.add_patch(plt.Rectangle((ctx["hvac_x"], ctx["hvac_y"]), HVAC_W, HVAC_PROJ_OFFICE, fill=False, ec='m', ls=':'))
    ax.text(ctx["hvac_x"] + HVAC_W / 2, ctx["hvac_y"] + HVAC_PROJ_OFFICE / 2,
            "HVAC (outlet)", ha='center', va='center', fontsize=7)

    ax.add_patch(plt.Rectangle((ctx["hvac_x"], -HVAC_PROJ_GARAGE), HVAC_W, HVAC_PROJ_GARAGE, fill=False, ec='m', ls='-'))
    ax.text(ctx["hvac_x"] + HVAC_W / 2, -HVAC_PROJ_GARAGE / 2,
            "HVAC (condenser)", ha='center', va='center', fontsize=7)

    ax.add_patch(plt.Rectangle((0, 0), ROOM_W, WALL_THK, fill=False, ec='k'))
    ax.text(PLATFORM_W / 2, WALL_THK / 2, f"New Wall {WALL_THK}\"", ha='center', va='center', fontsize=7)

    ax.annotate('', xy=(0, -8), xytext=(ROOM_W, -8), arrowprops=dict(arrowstyle='<->'))
    ax.text(ROOM_W / 2, -10, f"{ROOM_W}\" width", ha='center', va='top', fontsize=8)
    ax.annotate('', xy=(-8, 0), xytext=(-8, ROOM_D), arrowprops=dict(arrowstyle='<->'))
    ax.text(-10, ROOM_D / 2, f"{ROOM_D}\" depth", ha='right', va='center', fontsize=8, rotation=90)

    ax.set_xlim(-20, ROOM_W + 20)
    ax.set_ylim(-20, ROOM_D + 20)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('Top-Down Plan')
    return fig


def build_front_elevation(ctx: Dict):
    global plt
    assert plt is not None
    fig, ax2 = plt.subplots(figsize=(ROOM_W / 12, ROOM_H / 12))
    ax2.plot([0, ROOM_W, ROOM_W, 0, 0], [0, 0, ROOM_H, ROOM_H, 0], 'k-', lw=2)

    ax2.add_patch(plt.Rectangle((ctx["pd_x0"], 0), POCKET_DOOR_CLEAR_W, POCKET_DOOR_CLEAR_H, fill=False, ec='c'))
    ax2.add_patch(plt.Rectangle((ctx["pd_x2"], 0), POCKET_DOOR_CLEAR_W, POCKET_DOOR_CLEAR_H, fill=False, ec='c', ls=':'))
    ax2.text(ctx["pd_x0"] + POCKET_DOOR_CLEAR_W / 2, POCKET_DOOR_CLEAR_H + 2,
             f"Pocket Door {POCKET_DOOR_CLEAR_W}\"×{POCKET_DOOR_CLEAR_H}\"",
             ha='center', va='bottom', fontsize=8)

    ax2.add_patch(plt.Rectangle((ctx["desk_x"], DESK_H), DESK_W, 1.2, fill=True, ec='y'))
    ax2.text(ctx["desk_x"] + DESK_W / 2, DESK_H + 3,
             f"Desk height {DESK_H}\"", ha='center', va='bottom', fontsize=8)

    hvac_face_h = HVAC_H
    hvac_face_w = HVAC_W
    hvac_face_x = ctx["hvac_x"]
    hvac_face_z = ctx["hvac_face_z"]
    ax2.add_patch(plt.Rectangle((hvac_face_x, hvac_face_z), hvac_face_w, hvac_face_h, fill=False, ec='m'))
    ax2.text(hvac_face_x + hvac_face_w / 2, hvac_face_z + hvac_face_h / 2,
             'HVAC grille', ha='center', va='center', fontsize=8)

    ax2.add_patch(plt.Rectangle((ctx["plat_x"], ctx["plat_z"]), PLATFORM_W, STUD_W, fill=True, ec='k'))
    ax2.text(ctx["plat_x"] + PLATFORM_W / 2, ctx["plat_z"] + STUD_W * 1.5,
             f"Overhead platform \n {PLATFORM_W}\"×{PLATFORM_D}\" @ >{PLATFORM_H}\" AFF",
             ha='center', va='bottom', fontsize=8)

    ax2.hlines(EYE_H, 0, ROOM_W, colors='k', linestyles='dashed')
    ax2.text(ROOM_W - 5, EYE_H, f"{EYE_H}\" eye line", ha='right', va='bottom', fontsize=8)

    ax2.add_patch(plt.Rectangle((ctx["win_x"], WINDOW_AFF), WINDOW_W, WINDOW_H, fill=False, ec='c'))
    ax2.text(ctx["win_x"] + WINDOW_W / 2, WINDOW_AFF + WINDOW_H + 2,
             f"Faux Window {WINDOW_W}\"×{WINDOW_H}\"", ha='center', va='bottom', fontsize=8)

    ax2.add_patch(plt.Rectangle((ctx["bs_x"], 0), BOOKSHELF_W, BOOKSHELF_H, fill=False, ec='y'))
    ax2.text(ctx["bs_x"] + BOOKSHELF_W / 2, ctx["bs_y"] + BOOKSHELF_H / 2,
             f"Bookshelf {BOOKSHELF_W}\"×{BOOKSHELF_H}\"", ha='center', va='center', fontsize=7)

    ax2.set_xlim(-10, ROOM_W + 10)
    ax2.set_ylim(0, ROOM_H + 10)
    ax2.axis('off')
    ax2.set_title('Front Elevation (Desk Wall)')
    return fig


def configure_matplotlib(backend: str | None, headless: bool) -> None:
    desired = backend or ("Agg" if headless else None)
    if desired:
        matplotlib.use(desired, force=True)
    global plt
    import matplotlib.pyplot as _plt

    plt = _plt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).with_name("layout.yaml"),
        help="YAML/JSON file containing the layout metadata (default: layout.yaml).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent,
        help="Directory to write rendered PNGs (default: script directory).",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Skip displaying the windows (useful for batch exports).",
    )
    parser.add_argument(
        "--backend",
        help="Matplotlib backend to force (defaults to Agg when --no-show).",
    )
    return parser.parse_args()


def save_figures(figs: Dict[str, 'plt.Figure'], output_dir: Path, show: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, fig in figs.items():
        output_path = output_dir / f"{name}.png"
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        if not show:
            plt.close(fig)
        print(f"Saved {output_path}")
    if show:
        plt.show()


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    apply_config(cfg)
    configure_matplotlib(args.backend, args.no_show)
    ctx = layout_context()
    top_fig = build_top_down(ctx)
    elevation_fig = build_front_elevation(ctx)
    save_figures(
        {
            "garage_office_top_down": top_fig,
            "garage_office_front_elevation": elevation_fig,
        },
        args.output_dir,
        show=not args.no_show,
    )


if __name__ == "__main__":
    main()
