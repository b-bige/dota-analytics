COLORS = {
    "bg_base":      "#f4f6f9",   # off-white page background
    "bg_surface":   "#ffffff",   # pure white cards
    "bg_elevated":  "#eef1f6",   # subtle hover / elevated
    "bg_border":    "#dde3ec",   # soft borders

    "primary":      "#3498db",   # confident blue — accent
    "primary_dim":  "#5eade2",   # light blue for secondary elements
    "radiant":      "#16a34a",   # win / positive
    "dire":         "#dc2626",   # loss / negative
    "neutral":      "#6b7280",   # neutral stats

    "text_bright":  "#0f172a",   # near-black headings
    "text_body":    "#374151",   # dark gray body
    "text_muted":   "#9ca3af",   # light gray labels

    "colorscale_low": '#1abc9c'
}

PLOTLY_COLORSCALES = {
    "colorscale": [
        [0.0, '#5eade2'],
        [1.0, '#2574a9']
    ],
    "winrate": [
        [0.0, COLORS["dire"]],
        [0.5, COLORS["neutral"]],
        [1.0, COLORS["radiant"]],
    ],
    "intensity": [
        [0.0, COLORS["bg_elevated"]],
        [0.5, COLORS["primary_dim"]],
        [1.0, COLORS["primary"]],
    ],
    "diverging": [
        [0.0,  COLORS["dire"]],
        [0.5,  COLORS["bg_border"]],
        [1.0,  COLORS["radiant"]],
    ],
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor=COLORS["bg_surface"],
    plot_bgcolor=COLORS["bg_surface"],
    font=dict(
        family="'DM Sans', 'Inter', sans-serif",
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

MANTINE_THEME = {
    "primaryColor": "brand", #HERE
    "fontFamily": "'DM Sans', sans-serif",
    "colors": {
        "brand": [
            "#ebf5fb",  # 0 lightest
            "#d6eaf8",  # 1
            "#aed6f1",  # 2
            "#86c1e9",  # 3
            "#5eade2",  # 4
            "#3a9fd9",  # 5
            "#3498db",  # 6 ← your main color
            "#2e86c1",  # 7
            "#2574a9",  # 8
            "#1a5276",  # 9 darkest
        ],
        "gray": [
            COLORS["bg_surface"],   # 0
            COLORS["bg_base"],      # 1
            COLORS["bg_elevated"],  # 2
            COLORS["bg_border"],    # 3
            "#c8d0db",              # 4
            COLORS["text_muted"],   # 5
            COLORS["neutral"],      # 6
            COLORS["text_body"],    # 7
            COLORS["text_bright"],  # 8
            "#060a10",              # 9
        ]
    },
}