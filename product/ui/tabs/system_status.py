"""System Status tab. Placeholder only."""


def render(ax):
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.5, 0.5, "System Status Tab", transform=ax.transAxes,
            ha="center", va="center", fontsize=14)
