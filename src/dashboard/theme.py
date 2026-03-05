COLORS = {
    # Backgrounds
    "bg_base":      "#0a0c10",   # near-black base
    "bg_surface":   "#111318",   # card/panel surface
    "bg_elevated":  "#181c24",   # elevated elements, modals
    "bg_border":    "#252b38",   # subtle borders

    # Accents
    "primary":      "#c8972a",   # Dota gold
    "primary_dim":  "#8a6420",   # muted gold for hover states
    "radiant":      "#4caf7d",   # Radiant green
    "dire":         "#c94f4f",   # Dire red
    "neutral":      "#7b8fa6",   # neutral stats

    # Text
    "text_bright":  "#e8eaf0",   # headings
    "text_body":    "#9aa5b8",   # body text
    "text_muted":   "#4f5a6e",   # labels, hints
}

PLOTLY_COLORSCALES = {
    # Gold → Green (winrate, positive metrics)
    "winrate": [
        [0.0, COLORS["dire"]],
        [0.5, COLORS["neutral"]],
        [1.0, COLORS["radiant"]],
    ],
    # Dark → Gold (pick rate, general intensity)
    "intensity": [
        [0.0, "#1a1f2e"],
        [0.5, COLORS["primary_dim"]],
        [1.0, COLORS["primary"]],
    ],
    # Radiant vs Dire diverging
    "diverging": [
        [0.0,  COLORS["dire"]],
        [0.5,  "#2a2f3d"],
        [1.0,  COLORS["radiant"]],
    ],
}

# Reusable Plotly layout base — apply to every figure
PLOTLY_LAYOUT = dict(
    paper_bgcolor=COLORS["bg_surface"],
    plot_bgcolor=COLORS["bg_surface"],
    font=dict(
        family="'Rajdhani', 'Barlow Condensed', sans-serif",
        color=COLORS["text_body"],
        size=13,
    ),
    title_font=dict(
        color=COLORS["text_bright"],
        size=15,
    ),
    xaxis=dict(
        gridcolor=COLORS["bg_border"],
        linecolor=COLORS["bg_border"],
        tickcolor=COLORS["text_muted"],
        tickfont=dict(color=COLORS["text_muted"]),
        zerolinecolor=COLORS["bg_border"],
    ),
    yaxis=dict(
        gridcolor=COLORS["bg_border"],
        linecolor=COLORS["bg_border"],
        tickcolor=COLORS["text_muted"],
        tickfont=dict(color=COLORS["text_muted"]),
        zerolinecolor=COLORS["bg_border"],
    ),
    legend=dict(
        bgcolor=COLORS["bg_elevated"],
        bordercolor=COLORS["bg_border"],
        borderwidth=1,
        font=dict(color=COLORS["text_body"]),
    ),
    hoverlabel=dict(
        bgcolor=COLORS["bg_elevated"],
        bordercolor=COLORS["primary"],
        font=dict(color=COLORS["text_bright"], size=13),
    ),
    margin=dict(l=16, r=16, t=40, b=16),
)