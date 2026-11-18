import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Load data
bat_rank = pd.read_parquet('bat_rankings_final.parquet')
# Take strictly top 10 + Shubman Gill (#11) for the quadrant comparison - NO Phil Salt
bat = bat_rank[bat_rank['rank_bat'] <= 11].copy().reset_index(drop=True)

# Colors
BG_DARK = '#070a13'
CARD_BG = '#0f172a'
BORDER = '#1e293b'
RR_PINK = '#ea008a'
RR_GOLD = '#f5c518'
RED = '#f43f5e'
LIGHT_BLUE = '#38bdf8'
WHITE = '#ffffff'
SUBTEXT = '#94a3b8'

plt.figure(figsize=(10, 6.2), facecolor=BG_DARK)
ax = plt.gca()
ax.set_facecolor(CARD_BG)

# Plot zero reference lines
ax.axvline(0, color=RED, linestyle='--', linewidth=1.5, alpha=0.7)
ax.axhline(0, color='white', linestyle=':', linewidth=0.8, alpha=0.3)

# Data points
for _, r in bat.iterrows():
    name = r['striker_name']
    x = float(r['rescue_wpa'])
    y = float(r['hp_ml_runs_added'])
    ca = float(r['ca_wpa'])
    size = max(180, abs(ca) * 16)
    
    if r['rank_bat'] <= 3:
        color = RR_GOLD
        edgecolor = WHITE
    elif name == 'Shubman Gill':
        color = RED
        edgecolor = WHITE
    else:
        color = RR_PINK
        edgecolor = WHITE
        
    ax.scatter(x, y, s=size, color=color, edgecolor=edgecolor, linewidth=1.5, alpha=0.9, zorder=5)

# Label offsets designed to avoid all overlaps
label_positions = {
    'David Miller': (14.28, -75, 'bottom center'),
    'Suryakumar Yadav': (20.12, 234.4, 'top center'),
    'Namboori Tilak Varma': (21.46, 75, 'top right'),
    'Heinrich Klaasen': (24.84, 110, 'top right'),
    'Glenn Phillips': (18.48, 24, 'bottom right'),
    'Shimron Hetmyer': (16.96, -12, 'top left'),
    'Hardik Pandya': (6.47, -68, 'bottom center'),
    'Virat Kohli': (1.27, -25, 'bottom left'),
    'Nicholas Pooran': (6.29, 96, 'top right'),
    'Venkatesh Iyer': (3.71, 35, 'bottom right'),
    'Shubman Gill': (-2.03, 93, 'top center'),
}

for name, (x, y, pos) in label_positions.items():
    va = 'bottom' if 'top' in pos else ('top' if 'bottom' in pos else 'center')
    ha = 'left' if 'right' in pos else ('right' if 'left' in pos else 'center')
    
    offset_y = 12 if 'top' in pos else (-14 if 'bottom' in pos else 0)
    offset_x = 0.5 if 'right' in pos else (-0.5 if 'left' in pos else 0)
    
    color = WHITE
    fontweight = 'bold' if name in ['David Miller', 'Suryakumar Yadav', 'Namboori Tilak Varma', 'Shubman Gill'] else 'normal'
    
    ax.annotate(
        name,
        xy=(x, y),
        xytext=(x + offset_x, y + offset_y),
        color=color,
        fontsize=9,
        fontweight=fontweight,
        ha=ha,
        va=va,
        zorder=6
    )

# Quadrant Annotation Boxes
# Quadrant I: Elite All-Phase
ax.text(
    19, 215,
    "QUADRANT I: ELITE ALL-PHASE MATCH WINNERS\n(Surya, Klaasen, Tilak)",
    color=RR_GOLD,
    fontsize=8.5,
    fontweight='bold',
    bbox=dict(boxstyle='round,pad=0.5', facecolor='#0b1120', edgecolor=RR_GOLD, alpha=0.9),
    zorder=4
)

# Quadrant II: Front-Running Vulnerable
ax.text(
    -4.2, 180,
    "QUADRANT II: FRONT-RUNNING VULNERABLE\n(Gill: Fails in Early Collapse)",
    color=RED,
    fontsize=8.5,
    fontweight='bold',
    bbox=dict(boxstyle='round,pad=0.5', facecolor='#0b1120', edgecolor=RED, alpha=0.9),
    zorder=4
)

# Quadrant IV: Pure Chase Closers
ax.text(
    15, -45,
    "QUADRANT IV: PURE CHASE CLOSERS\n(Miller: World #1 Chase Finisher)",
    color=LIGHT_BLUE,
    fontsize=8.5,
    fontweight='bold',
    bbox=dict(boxstyle='round,pad=0.5', facecolor='#0b1120', edgecolor=LIGHT_BLUE, alpha=0.9),
    zorder=4
)

# Collapse Failure Line label
ax.text(-0.2, -90, "Collapse Failure Threshold", color=RED, fontsize=8, rotation=90, va='bottom', ha='right', alpha=0.8)

# Styling axes
ax.set_xlim(-5, 29)
ax.set_ylim(-95, 265)
ax.set_xlabel('Crisis Rescue WPA (Innings Resurrection from Early Collapse)', color=WHITE, fontsize=10.5, labelpad=8, fontweight='bold')
ax.set_ylabel('High-Pressure ML Runs Added Above Expected', color=WHITE, fontsize=10.5, labelpad=8, fontweight='bold')
ax.set_title('Visual Proof 1: Batting Pressure Archetypes (Crisis Rescue WPA vs High-Pressure ML Runs Added)', color=WHITE, fontsize=12, pad=12, fontweight='bold')

ax.tick_params(colors=SUBTEXT, labelsize=9)
ax.grid(color=WHITE, alpha=0.06, linestyle='-')
for spine in ax.spines.values():
    spine.set_color(BORDER)
    spine.set_linewidth(1)

# Custom Legend
import matplotlib.lines as mlines
gold_dot = mlines.Line2D([], [], color=RR_GOLD, marker='o', linestyle='None', markersize=9, label='Gold: Top 3')
pink_dot = mlines.Line2D([], [], color=RR_PINK, marker='o', linestyle='None', markersize=9, label='Pink: Top 4–10')
red_dot = mlines.Line2D([], [], color=RED, marker='o', linestyle='None', markersize=9, label='Red: Shubman Gill (#11 Flaw Demotion)')

leg = ax.legend(handles=[gold_dot, pink_dot, red_dot], loc='upper left', facecolor='#0b1120', edgecolor=BORDER, fontsize=8.5)
for text in leg.get_texts():
    text.set_color(WHITE)

plt.tight_layout()
plt.savefig('assets/visual_proofs_scatter.png', dpi=200, facecolor=BG_DARK, edgecolor='none')
print("Successfully generated assets/visual_proofs_scatter.png with NO Phil Salt!")
