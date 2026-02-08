"""
Unified single-window UI. Tab container: one figure, tab bar, content area.
Handles tab switching only. No business logic.
"""

import matplotlib.pyplot as plt
from matplotlib.widgets import Button

from . import tabs
from .tabs import mission_overview
from .tabs import payload_library
from .tabs import analysis


_TAB_BG = "#141814"
_TAB_TEXT = "#e0ece0"

def _make_tab_buttons(fig, n_tabs, on_tab_click):
    """Create a row of tab button axes; return list of Button widgets."""
    left, bottom, width, height = 0.04, 0.88, 0.14, 0.06
    gap = 0.02
    buttons = []
    for i in range(n_tabs):
        ax = fig.add_axes([left + i * (width + gap), bottom, width, height])
        ax.set_facecolor(_TAB_BG)
        ax.set_axis_off()
        btn = Button(ax, tabs.TABS[i][0], color=_TAB_BG, hovercolor="#1e221e")
        btn.label.set_color(_TAB_TEXT)
        btn.label.set_fontsize(9)
        btn.on_clicked(lambda event, idx=i: on_tab_click(idx))
        buttons.append(btn)
    return buttons


def launch_unified_ui(
    impact_points,
    P_hit,
    cep50,
    target_position,
    target_radius,
    mission_state,
    advisory_result,
    initial_threshold_percent,
    initial_mode,
    slider_min,
    slider_max,
    slider_step,
    mode_thresholds,
    on_threshold_change,
):
    """
    Create one figure with tab bar and content area. Only one tab's content
    is shown at a time. Same signature for app compatibility; no business
    logic in this module.
    """
    fig = plt.figure(figsize=(10, 6), facecolor="#0c0e0c")
    content_ax = fig.add_axes([0.06, 0.06, 0.88, 0.78])

    mission_data = {
        "decision": advisory_result.current_feasibility,
        "target_hit_percentage": P_hit * 100.0,
        "cep50": cep50,
        "threshold": initial_threshold_percent,
        "mode": initial_mode,
        "impact_points": impact_points,
        "target_position": target_position,
        "target_radius": target_radius,
    }

    def show_tab(index):
        # Remove axes from other tabs (e.g. Payload Library widgets)
        keep = {content_ax} | set(tab_button_axes)
        for ax in list(fig.axes):
            if ax not in keep:
                fig.delaxes(ax)
        content_ax.clear()
        content_ax.set_axis_off()
        if index == 0:
            mission_overview.render(content_ax, **mission_data)
        elif index == 1:
            payload_library.render(content_ax, fig)
        elif index == 2:
            analysis.render(
                content_ax,
                impact_points=mission_data["impact_points"],
                target_position=mission_data["target_position"],
                target_radius=mission_data["target_radius"],
                cep50=mission_data["cep50"],
                target_hit_percentage=mission_data["target_hit_percentage"],
            )
        else:
            tabs.TABS[index][1](content_ax)
        fig.canvas.draw_idle()

    buttons = _make_tab_buttons(fig, len(tabs.TABS), lambda idx: show_tab(idx))
    tab_button_axes = [b.ax for b in buttons]
    show_tab(0)

    plt.show()
