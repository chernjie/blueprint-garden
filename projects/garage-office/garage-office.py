
"""
Generate plan and elevation drawings for the garage office and optionally export them.

Examples:
    python3 projects/garage-office/garage-office.py
    python3 projects/garage-office/garage-office.py --no-show --output-dir projects/garage-office/renders
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

plt = None  # populated in configure_matplotlib

# Stud
STUD_D = 1.5
STUD_W = 3.5

# Eye level
EYE_H = 60

# Editable parameters (in inches)
ROOM_W = 108   # interior width
ROOM_D = 72    # interior depth
ROOM_H = 108   # wall height

# New wall on the desk side (pocket-door wall)
WALL_THK = 4.25
POCKET_DOOR_CLEAR_W = 30
POCKET_DOOR_CLEAR_H = 80
POCKET_DOOR_OFFSET_FROM_RIGHT = STUD_D   # set >0 if you want reveal/trim at the right corner

# Window on opposite wall
WINDOW_W = 60
WINDOW_H = 48
WINDOW_AFF = ROOM_H - 24 - WINDOW_H

# Desk on interior face of new wall
DESK_W = 78
DESK_D = 30
DESK_H = 30

# Window HVAC (under desk)
HVAC_W = 20
HVAC_H = 14
HVAC_PROJ_OFFICE = 8     # how far HVAC projects into the office beyond desk front
HVAC_PROJ_GARAGE = 14    # how far HVAC projects into garage beyond the outer face of the wall

# Bookshelf opposite the pocket door (first impression)
BOOKSHELF_W = 36
BOOKSHELF_D = 12
BOOKSHELF_H = 108  # full-height look; change to 96 if desired

# Overhead platform above desk
PLATFORM_W = 24
PLATFORM_D = 72
PLATFORM_H = 76  # height above finished floor (AFF)


def layout_context() -> dict:
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


def build_top_down(ctx: dict):
    global plt
    assert plt is not None
    fig, ax = plt.subplots(figsize=(ROOM_W / 12, ROOM_D / 12))

    ax.plot([0, ROOM_W, ROOM_W, 0, 0], [0, 0, ROOM_D, ROOM_D, 0], 'k-', lw=2)

    ax.plot([ctx["pd_x0"], ctx["pd_x1"]], [ctx["pd_y"], ctx["pd_y"]], 'c-', lw=6)
    ax.plot([ctx["pd_x2"], ctx["pd_x0"]], [ctx["pd_y"], ctx["pd_y"]], 'c:', lw=6)
    ax.text((ctx["pd_x0"] + ctx["pd_x1"]) / 2, WALL_THK, f"Pocket Door {POCKET_DOOR_CLEAR_W}\"",
            ha='center', va='bottom', fontsize=8)

    ax.plot([ctx["win_x"], ctx["win_x"] + WINDOW_W], [ROOM_D, ROOM_D], 'c-', lw=6)
    ax.text(ctx["win_x"] + WINDOW_W / 2, ROOM_D - 3, f"Window {WINDOW_W}\"", ha='center', va='top', fontsize=8)

    ax.add_patch(plt.Rectangle((ctx["desk_x"], ctx["desk_y"]), DESK_W, DESK_D, fill=False, ec='y'))
    ax.text(ctx["desk_x"] + DESK_W / 2, ctx["desk_y"] + DESK_D / 2, f"Desk {DESK_W}\"×{DESK_D}\"",
            ha='center', va='center', fontsize=8)

    ax.add_patch(plt.Rectangle((ctx["bs_x"], ctx["bs_y"]), BOOKSHELF_W, BOOKSHELF_D, fill=False, ec='y'))
    ax.text(ctx["bs_x"] + BOOKSHELF_W / 2, ctx["bs_y"] + BOOKSHELF_D / 2,
            f"Bookshelf {BOOKSHELF_W}\"×{BOOKSHELF_D}\"", ha='center', va='center', fontsize=7)

    ax.add_patch(plt.Rectangle((ctx["plat_stud_x"], 0), STUD_D, PLATFORM_D, fill=False, ec='k'))
    ax.text(ctx["plat_stud_x"] / 2, ROOM_D * 2 / 3, f"Overhead Platform \n {PLATFORM_W}\"×{PLATFORM_D}\"",
            ha='center', va='center', fontsize=8)

    ax.add_patch(plt.Rectangle((ctx["hvac_x"], ctx["hvac_y"]), HVAC_W, HVAC_PROJ_OFFICE, fill=False, ec='m', ls=':'))
    ax.text(ctx["hvac_x"] + HVAC_W / 2, ctx["hvac_y"] + HVAC_PROJ_OFFICE / 2, "HVAC (outlet)",
            ha='center', va='center', fontsize=7)

    ax.add_patch(plt.Rectangle((ctx["hvac_x"], -HVAC_PROJ_GARAGE), HVAC_W, HVAC_PROJ_GARAGE, fill=False, ec='m', ls='-'))
    ax.text(ctx["hvac_x"] + HVAC_W / 2, -HVAC_PROJ_GARAGE / 2, "HVAC (condenser)", ha='center', va='center', fontsize=7)

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


def build_front_elevation(ctx: dict):
    global plt
    assert plt is not None
    fig, ax2 = plt.subplots(figsize=(ROOM_W / 12, ROOM_H / 12))
    ax2.plot([0, ROOM_W, ROOM_W, 0, 0], [0, 0, ROOM_H, ROOM_H, 0], 'k-', lw=2)

    ax2.add_patch(plt.Rectangle((ctx["pd_x0"], 0), POCKET_DOOR_CLEAR_W, POCKET_DOOR_CLEAR_H, fill=False, ec='c'))
    ax2.add_patch(plt.Rectangle((ctx["pd_x2"], 0), POCKET_DOOR_CLEAR_W, POCKET_DOOR_CLEAR_H, fill=False, ec='c', ls=':'))
    ax2.text(ctx["pd_x0"] + POCKET_DOOR_CLEAR_W / 2, POCKET_DOOR_CLEAR_H + 2,
             f"Pocket Door {POCKET_DOOR_CLEAR_W}\"×{POCKET_DOOR_CLEAR_H}\"", ha='center', va='bottom', fontsize=8)

    ax2.add_patch(plt.Rectangle((ctx["desk_x"], DESK_H), DESK_W, 1.2, fill=True, ec='y'))
    ax2.text(ctx["desk_x"] + DESK_W / 2, DESK_H + 3, f"Desk height {DESK_H}\"", ha='center', va='bottom', fontsize=8)

    hvac_face_h = HVAC_H
    hvac_face_w = HVAC_W
    hvac_face_x = ctx["hvac_x"]
    hvac_face_z = ctx["hvac_face_z"]
    ax2.add_patch(plt.Rectangle((hvac_face_x, hvac_face_z), hvac_face_w, hvac_face_h, fill=False, ec='m'))
    ax2.text(hvac_face_x + hvac_face_w / 2, hvac_face_z + hvac_face_h / 2,
             'HVAC grille', ha='center', va='center', fontsize=8)

    ax2.add_patch(plt.Rectangle((ctx["plat_x"], ctx["plat_z"]), PLATFORM_W, STUD_W, fill=True, ec='k'))
    ax2.text(ctx["plat_x"] + PLATFORM_W / 2, ctx["plat_z"] + STUD_W * 1.5,
             f"Overhead platform \n {PLATFORM_W}\"×{PLATFORM_D}\" @ >{PLATFORM_H}\" AFF", ha='center', va='bottom', fontsize=8)

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


def save_figures(figs: dict[str, 'plt.Figure'], output_dir: Path, show: bool) -> None:
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
