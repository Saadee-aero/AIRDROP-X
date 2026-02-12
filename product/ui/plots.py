"""
Reusable plotting functions. Military HUD style. No engine or advisory calls.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

_PANEL = "#0f120f"
_ACCENT = "#00ff41"
_ACCENT_DIM = "#1a4d1a"
_TARGET_RING = "#00ff41"
_CEP_RING = "#4a7c4a"
_SCATTER = "#00ff41"
_LABEL = "#6b8e6b"
_GRID = "#1a3a1a"
_BORDER = "#2a3a2a"


def plot_impact_dispersion(
    ax,
    impact_points,
    target_position,
    target_radius,
    cep50=None,
    release_point=None,
    wind_vector=None,
):
    impact_points = np.asarray(impact_points, dtype=float)
    target_position = np.asarray(target_position, dtype=float).reshape(2)
    r_target = float(target_radius) if target_radius is not None else 0.0
    r_cep = float(cep50) if (cep50 is not None and cep50 > 0) else 0.0

    # Auto-center axis: mean of impacts (or target if no impacts)
    if impact_points.size > 0:
        impact_x = impact_points[:, 0]
        impact_y = impact_points[:, 1]
        mean_x = float(np.mean(impact_x))
        mean_y = float(np.mean(impact_y))
        r = np.sqrt((impact_x - mean_x) ** 2 + (impact_y - mean_y) ** 2)
        max_dispersion = float(np.max(r))
    else:
        mean_x, mean_y = float(target_position[0]), float(target_position[1])
        max_dispersion = 0.0

    plot_radius = max(1.5 * max_dispersion, 1.5 * r_target)
    plot_radius = max(plot_radius, 1.0)  # avoid collapse when both are 0
    plot_radius *= 1.1  # 10% adaptive margin

    xmin, xmax = mean_x - plot_radius, mean_x + plot_radius
    ymin, ymax = mean_y - plot_radius, mean_y + plot_radius

    ax.set_facecolor(_PANEL)
    ax.tick_params(colors=_LABEL)
    ax.xaxis.label.set_color(_LABEL)
    ax.yaxis.label.set_color(_LABEL)
    for spine in ax.spines.values():
        spine.set_color(_BORDER)

    # Impact scatter
    ax.scatter(impact_points[:, 0], impact_points[:, 1], color=_SCATTER, alpha=0.35, s=10, edgecolors="none", clip_on=True)
    mean_impact = np.mean(impact_points, axis=0) if impact_points.size > 0 else target_position
    ax.scatter(mean_impact[0], mean_impact[1], color="#ffffff", s=60, marker="x", linewidths=2, clip_on=True)

    # Release point: triangle, yellow, size 120
    if release_point is not None:
        rp = np.asarray(release_point, dtype=float).reshape(2)
        ax.scatter(rp[0], rp[1], color="yellow", s=120, marker="^", clip_on=True)

    # Target circle: subtle fill, solid lime edge
    ax.add_patch(
        plt.Circle(
            target_position,
            r_target,
            facecolor=(0, 1, 0, 0.05),
            edgecolor="lime",
            linewidth=1.5,
            clip_on=True,
        )
    )
    ax.scatter(target_position[0], target_position[1], color=_TARGET_RING, s=40, zorder=5, edgecolors=_PANEL, linewidths=0.5, clip_on=True)

    # CEP circle: centered at mean impact, dashed light green
    if r_cep > 0:
        ax.add_patch(
            plt.Circle(
                mean_impact,
                r_cep,
                color=_CEP_RING,
                fill=False,
                linestyle="--",
                linewidth=1.2,
                alpha=0.9,
                clip_on=True,
            )
        )

    # Wind vector: length = 0.4 * plot_radius, direction normalized
    if wind_vector is not None:
        wind = np.asarray(wind_vector, dtype=float).reshape(2)
        wind_mag = float(np.linalg.norm(wind))
        if wind_mag > 0:
            arrow_length = 0.4 * plot_radius
            direction = wind / wind_mag
            vec = direction * arrow_length
            start = np.asarray(target_position, dtype=float).reshape(2)
            ax.arrow(
                start[0],
                start[1],
                vec[0],
                vec[1],
                width=0.18 * (arrow_length / 10.0),
                head_width=0.9 * (arrow_length / 10.0),
                head_length=1.3 * (arrow_length / 10.0),
                color="#e6b800",
                length_includes_head=True,
                clip_on=True,
            )

    # Covariance-based 2σ confidence ellipse, principal axes, and KDE-based density
    if impact_points.shape[0] >= 2:
        try:
            # Statistically correct covariance and eigen decomposition
            cov = np.cov(impact_points.T)
            eigvals, eigvecs = np.linalg.eigh(cov)
            order = eigvals.argsort()[::-1]
            eigvals = eigvals[order]
            eigvecs = eigvecs[:, order]

            # 2σ ellipse: semi-axis = 2*sqrt(eigenvalue), diameter = 2*semi_axis
            semi_major_2sigma = 2.0 * np.sqrt(max(eigvals[0], 0.0))
            semi_minor_2sigma = 2.0 * np.sqrt(max(eigvals[1], 0.0))
            ellipse_width = 2.0 * semi_major_2sigma
            ellipse_height = 2.0 * semi_minor_2sigma
            angle = np.degrees(np.arctan2(eigvecs[1, 0], eigvecs[0, 0]))

            from matplotlib.patches import Ellipse

            ellipse_patch = Ellipse(
                xy=(mean_x, mean_y),
                width=ellipse_width,
                height=ellipse_height,
                angle=angle,
                edgecolor="orange",
                facecolor="none",
                linewidth=1.0,
                linestyle="--",
                alpha=0.8,
            )
            ax.add_patch(ellipse_patch)

            # Principal axes (1σ direction indicators from mean)
            axis_length_major = np.sqrt(max(eigvals[0], 0.0))
            axis_length_minor = np.sqrt(max(eigvals[1], 0.0))
            major_vec = eigvecs[:, 0]
            minor_vec = eigvecs[:, 1]
            ax.plot(
                [mean_x - axis_length_major * major_vec[0], mean_x + axis_length_major * major_vec[0]],
                [mean_y - axis_length_major * major_vec[1], mean_y + axis_length_major * major_vec[1]],
                color="white",
                linewidth=1,
            )
            ax.plot(
                [mean_x - axis_length_minor * minor_vec[0], mean_x + axis_length_minor * minor_vec[0]],
                [mean_y - axis_length_minor * minor_vec[1], mean_y + axis_length_minor * minor_vec[1]],
                color="white",
                linewidth=1,
            )
        except Exception:
            pass

        # STEP 3–5 — KDE, heatmap, and density contours (performance safeguard)
        kde_drawn = False
        if impact_points.shape[0] >= 30:
            try:
                from scipy.stats import gaussian_kde  # local import

                xi, yi = np.mgrid[xmin:xmax:200j, ymin:ymax:200j]
                coords = np.vstack([impact_x, impact_y])
                kde = gaussian_kde(coords)
                zi = kde(np.vstack([xi.flatten(), yi.flatten()]))
                zi = zi.reshape(xi.shape)

                # Heatmap: analytical tone, reduced dominance
                ax.imshow(
                    np.rot90(zi),
                    extent=[xmin, xmax, ymin, ymax],
                    cmap="viridis",
                    alpha=0.20,
                    aspect="auto",
                    origin="lower",
                )

                # Density contours: HUD green, same statistical levels
                ax.contour(
                    xi,
                    yi,
                    zi,
                    levels=6,
                    colors=_CEP_RING,
                    linewidths=1.2,
                )
                kde_drawn = True
            except Exception:
                kde_drawn = False
        else:
            # Not enough samples for KDE
            ax.text(
                0.02,
                0.02,
                "Density map requires \u2265 30 samples.",
                transform=ax.transAxes,
                ha="left",
                va="bottom",
                fontsize=6,
                color=_LABEL,
                family="monospace",
            )

    # Dynamic axis limits: 20% margin around impact spread (or fallback)
    if impact_points.shape[0] > 0:
        all_x = impact_points[:, 0]
        all_y = impact_points[:, 1]
        x_range = all_x.max() - all_x.min()
        y_range = all_y.max() - all_y.min()
        margin_x = 0.2 * x_range if x_range > 0 else 0.2 * plot_radius
        margin_y = 0.2 * y_range if y_range > 0 else 0.2 * plot_radius
        ax.set_xlim(all_x.min() - margin_x, all_x.max() + margin_x)
        ax.set_ylim(all_y.min() - margin_y, all_y.max() + margin_y)
    else:
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
    ax.set_aspect("equal", adjustable="box")

    ax.set_xlabel("X (m)", labelpad=0)
    ax.set_ylabel("Y (m)", labelpad=0)
    ax.tick_params(axis="both", pad=2)
    ax.grid(True, color=_GRID, alpha=0.6, linestyle="-")
    ax.text(
        0.98,
        0.02,
        "Model: Low-subsonic, drag-dominated free fall",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=6,
        color=_LABEL,
        family="monospace",
    )

    # Legend: logical order per spec
    handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=_SCATTER, markeredgecolor="none", markersize=6, label="Impacts"),
        Line2D([0], [0], marker="x", color="#ffffff", markersize=8, label="Mean"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="lime", markeredgecolor="lime", markersize=6, label="Target"),
        Line2D([0], [0], linestyle="--", color=_CEP_RING, linewidth=1.2, label="CEP50"),
        Line2D([0], [0], linestyle="--", color="orange", linewidth=1.0, label="2\u03c3 Confidence Ellipse"),
        Line2D([0], [0], color="#e6b800", linewidth=2, label="Wind"),
    ]
    if release_point is not None:
        handles.append(
            Line2D([0], [0], marker="^", color="none", markerfacecolor="yellow", markeredgecolor="yellow", markersize=8, label="Release Point"),
        )
    # Probability density (only if KDE was drawn)
    if impact_points.shape[0] >= 30:
        handles.append(
            Line2D([0], [0], linestyle="-", color=_CEP_RING, linewidth=1.2, label="Probability Density"),
        )
    ax.legend(
        handles=handles,
        loc="upper left",
        frameon=True,
        fontsize=7,
        facecolor=_PANEL,
        edgecolor=_BORDER,
        labelcolor=_LABEL,
    )


def plot_sensitivity(ax, x_values, y_values, x_label, y_label, title=None):
    x_values = np.asarray(x_values, dtype=float)
    y_values = np.asarray(y_values, dtype=float)
    ax.set_facecolor(_PANEL)
    ax.tick_params(colors=_LABEL)
    ax.plot(x_values, y_values, color=_ACCENT, clip_on=True)
    ax.margins(x=0.04, y=0.04)
    ax.set_xlabel(x_label, color=_LABEL)
    ax.set_ylabel(y_label, color=_LABEL)
    ax.grid(True, color=_GRID, alpha=0.6)
    if title is not None:
        ax.set_title(title, color=_LABEL)
    for spine in ax.spines.values():
        spine.set_color(_BORDER)


def create_figure_axes(nrows=1, ncols=1, figsize=(6, 6)):
    fig, ax = plt.subplots(nrows, ncols, figsize=figsize)
    if nrows == 1 and ncols == 1:
        return fig, ax
    return fig, ax
