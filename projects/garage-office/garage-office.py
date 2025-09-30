
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

# ----------------------------------------------------------
# Drawing helpers (matplotlib)
import matplotlib.pyplot as plt

# ---------- TOP-DOWN PLAN ----------
fig, ax = plt.subplots(figsize=(ROOM_W /12, ROOM_D /12))

# Room boundary
ax.plot([0, ROOM_W, ROOM_W, 0, 0], [0, 0, ROOM_D, ROOM_D, 0], 'k-', lw=2)

# Pocket door opening on the new wall (right side)
pd_x0 = ROOM_W - POCKET_DOOR_CLEAR_W - POCKET_DOOR_OFFSET_FROM_RIGHT
pd_x1 = ROOM_W - POCKET_DOOR_OFFSET_FROM_RIGHT
pd_x2 = pd_x0 - POCKET_DOOR_CLEAR_W - POCKET_DOOR_OFFSET_FROM_RIGHT
pd_y = WALL_THK / 2
ax.plot([pd_x0, pd_x1], [pd_y, pd_y], 'c-', lw=6)
ax.plot([pd_x2, pd_x0], [pd_y, pd_y], 'c:', lw=6) # hidden pocket door kit
ax.text((pd_x0+pd_x1)/2, WALL_THK, f"Pocket Door {POCKET_DOOR_CLEAR_W}\"", ha='center', va='bottom', fontsize=8)

# Window centered on opposite wall (top)
win_x = (ROOM_W - WINDOW_W)/2
ax.plot([win_x, win_x + WINDOW_W], [ROOM_D, ROOM_D], 'c-', lw=6)
ax.text(win_x + WINDOW_W/2, ROOM_D-3, f"Window {WINDOW_W}\"", ha='center', va='top', fontsize=8)

# Desk against interior face of new wall
desk_x = 0
desk_y = WALL_THK
ax.add_patch(plt.Rectangle((desk_x, desk_y), DESK_W, DESK_D, fill=False, ec='y'))
ax.text(desk_x + DESK_W/2, desk_y + DESK_D/2, f"Desk {DESK_W}\"×{DESK_D}\"", ha='center', va='center', fontsize=8)

# Bookshelf (top right area)
bs_x = ROOM_W - BOOKSHELF_W
bs_y = ROOM_D - BOOKSHELF_D
ax.add_patch(plt.Rectangle((bs_x, bs_y), BOOKSHELF_W, BOOKSHELF_D, fill=False, ec='y'))
ax.text(bs_x + BOOKSHELF_W/2, bs_y + BOOKSHELF_D/2, f"Bookshelf {BOOKSHELF_W}\"×{BOOKSHELF_D}\"", ha='center', va='center', fontsize=7)

# Overhead platform above desk
plat_x = 0
plat_stud_x = plat_x + (PLATFORM_W - STUD_D*2)
ax.add_patch(plt.Rectangle((plat_stud_x, 0), STUD_D, PLATFORM_D, fill=False, ec='k'))
ax.text(plat_stud_x/2, ROOM_D*2/3, f"Overhead Platform \n {PLATFORM_W}\"×{PLATFORM_D}\"", ha='center', va='center', fontsize=8)

# HVAC rectangle (office projection only) — centered under desk
hvac_x = pd_x2 - HVAC_W - STUD_D
hvac_y = 0
ax.add_patch(plt.Rectangle((hvac_x, hvac_y), HVAC_W, HVAC_PROJ_OFFICE, fill=False, ec='m', ls=':'))
ax.text(hvac_x + HVAC_W/2, hvac_y + HVAC_PROJ_OFFICE/2, "HVAC (outlet)", ha='center', va='center', fontsize=7)

# Indicate through-wall & garage projection with dashed box
# ax.add_patch(plt.Rectangle((hvac_x, 0), HVAC_W, WALL_THK, fill=False, ec='m', ls='--'))
ax.add_patch(plt.Rectangle((hvac_x, -HVAC_PROJ_GARAGE), HVAC_W, HVAC_PROJ_GARAGE, fill=False, ec='m', ls='-'))
ax.text(hvac_x + HVAC_W/2, -HVAC_PROJ_GARAGE/2, "HVAC (condenser)", ha='center', va='center', fontsize=7)

# New wall strip along bottom
ax.add_patch(plt.Rectangle((0, 0), ROOM_W, WALL_THK, fill=False, ec='k'))
ax.text(PLATFORM_W/2, WALL_THK/2, f"New Wall {WALL_THK}\"", ha='center', va='center', fontsize=7)

# Dimensions
ax.annotate('', xy=(0, -8), xytext=(ROOM_W, -8), arrowprops=dict(arrowstyle='<->'))
ax.text(ROOM_W/2, -10, f"{ROOM_W}\" width", ha='center', va='top', fontsize=8)
ax.annotate('', xy=(-8, 0), xytext=(-8, ROOM_D), arrowprops=dict(arrowstyle='<->'))
ax.text(-10, (ROOM_D)/2, f"{ROOM_D}\" depth", ha='right', va='center', fontsize=8, rotation=90)

ax.set_xlim(-20, ROOM_W + 20)
ax.set_ylim(-20, ROOM_D + 20)
ax.set_aspect('equal')
ax.axis('off')
ax.set_title('Top-Down Plan')
plt.show()

# ---------- FRONT ELEVATION (desk wall) ----------
fig2, ax2 = plt.subplots(figsize=(ROOM_W/12, ROOM_H/12))

# Wall frame
ax2.plot([0, ROOM_W, ROOM_W, 0, 0], [0, 0, ROOM_H, ROOM_H, 0], 'k-', lw=2)

# Pocket door jamb (right) — show opening width & height
ax2.add_patch(plt.Rectangle((pd_x0, 0), POCKET_DOOR_CLEAR_W, POCKET_DOOR_CLEAR_H, fill=False, ec='c'))
ax2.add_patch(plt.Rectangle((pd_x2, 0), POCKET_DOOR_CLEAR_W, POCKET_DOOR_CLEAR_H, fill=False, ec='c', ls=':')) # hidden pocket door kit
ax2.text(pd_x0 + POCKET_DOOR_CLEAR_W/2, POCKET_DOOR_CLEAR_H + 2, f"Pocket Door {POCKET_DOOR_CLEAR_W}\"×{POCKET_DOOR_CLEAR_H}\"", ha='center', va='bottom', fontsize=8)

# Desk surface
ax2.add_patch(plt.Rectangle((desk_x, DESK_H), DESK_W, 1.2, fill=True, ec='y'))
ax2.text(desk_x + DESK_W/2, DESK_H + 3, f"Desk height {DESK_H}\"", ha='center', va='bottom', fontsize=8)

# HVAC grille area under desk (schematic)
hvac_face_h = HVAC_H
hvac_face_w = HVAC_W
hvac_face_x = hvac_x
hvac_face_z = DESK_H - hvac_face_h - HVAC_H/2
ax2.add_patch(plt.Rectangle((hvac_face_x, hvac_face_z), hvac_face_w, hvac_face_h, fill=False, ec='m'))
ax2.text(hvac_face_x + hvac_face_w/2, hvac_face_z + hvac_face_h/2, 'HVAC grille', ha='center', va='center', fontsize=8)

# Overhead platform above desk
plat_z = PLATFORM_H + STUD_W
ax2.add_patch(plt.Rectangle((plat_x, plat_z), PLATFORM_W, STUD_W, fill=True, ec='k'))
ax2.text(plat_x + PLATFORM_W/2, plat_z + STUD_W * 1.5, f"Overhead platform \n {PLATFORM_W}\"×{PLATFORM_D}\" @ >{PLATFORM_H}\" AFF", ha='center', va='bottom', fontsize=8)

# Eye line reference
ax2.hlines(EYE_H, 0, ROOM_W, colors='k', linestyles='dashed')
ax2.text(ROOM_W - 5, EYE_H, f"{EYE_H}\" eye line", ha='right', va='bottom', fontsize=8)

# Faux Window position
ax2.add_patch(plt.Rectangle((win_x, WINDOW_AFF), WINDOW_W, WINDOW_H, fill=False, ec='c'))
ax2.text(win_x + WINDOW_W/2, WINDOW_AFF + WINDOW_H + 2, f"Faux Window {WINDOW_W}\"×{WINDOW_H}\"", ha='center', va='bottom', fontsize=8)

# Bookshelf (top right area)
ax2.add_patch(plt.Rectangle((bs_x, 0), BOOKSHELF_W, BOOKSHELF_H, fill=False, ec='y'))
ax2.text(bs_x + BOOKSHELF_W/2, bs_y + BOOKSHELF_H/2, f"Bookshelf {BOOKSHELF_W}\"×{BOOKSHELF_H}\"", ha='center', va='center', fontsize=7)

# Axes styling
ax2.set_xlim(-10, ROOM_W + 10)
ax2.set_ylim(0, ROOM_H + 10)
ax2.axis('off')
ax2.set_title('Front Elevation (Desk Wall)')
plt.show()
