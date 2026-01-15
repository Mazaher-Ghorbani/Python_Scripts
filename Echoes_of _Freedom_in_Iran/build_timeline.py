
import base64
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

# =========================
# (A) BASIC CONFIG
# =========================
CSV_PATH = Path("Events.csv")          # CSV file (Year, Event, Text, Description)
OUTPUT_HTML = Path("index.html")       # Output single-file HTML (shareable)
BG_COLOR = "#D6413D"                   # Full-screen background color

# =========================
# (B) ICON CONFIG
# =========================
# Prefer SVG for crisp scaling. If you use PNG:
#   ICON_PATH = Path("icon.png")
#   ICON_MIME = "image/png"
ICON_PATH = Path("icon.svg")
ICON_MIME = "image/svg+xml"

# =========================
# (C) TIMELINE STYLE CONFIG
# =========================
ACTIVE_COLOR = "#111111"                    # Active/past line + past nodes + selected node (black)
INACTIVE_COLOR = "rgba(150,150,150,0.90)"   # Future/unselected line + future nodes (gray)
TICK_COLOR = "rgba(245,245,245,0.72)"       # Year labels + tick marks (light)
LINE_WIDTH = 8                               # Line thickness
SELECTED_SIZE = 22                           # Selected node size
UNSELECTED_SIZE = 15                         # Unselected node size


# =========================
# (D) HELPERS
# =========================
def file_to_data_uri(path: Path, mime: str) -> str:
    """
    Convert a local file into a base64 data URI so the final HTML is fully portable
    (no external image dependencies).
    """
    if not path.exists():
        return ""
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:{mime};base64,{b64}"


# =========================
# (E) BUILD PLOTLY FIGURE (TIMELINE)
# =========================
def build_figure(df: pd.DataFrame):
    """
    Create a Plotly timeline:
      - Two line traces: past (active) + future (inactive)
      - One marker trace: all nodes (years)
      - Custom year labels + vertical tick marks (to avoid overlap)
      - Tooltip is DISABLED but clicking nodes still works
    """
    df = df.sort_values(["Year", "Event"]).reset_index(drop=True)

    years = df["Year"].tolist()
    y0 = 0

    customdata = list(zip(df["Year"], df["Text"], df["Description"]))

    selected_idx = 0
    past_x = years[: selected_idx + 1]
    future_x = years[selected_idx:]

    colors = [ACTIVE_COLOR] + [INACTIVE_COLOR] * (len(years) - 1)
    sizes = [SELECTED_SIZE] + [UNSELECTED_SIZE] * (len(years) - 1)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=past_x,
            y=[y0] * len(past_x),
            mode="lines",
            line=dict(width=LINE_WIDTH, color=ACTIVE_COLOR),
            hoverinfo="skip",
            showlegend=False,
            name="past_line",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=future_x,
            y=[y0] * len(future_x),
            mode="lines",
            line=dict(width=LINE_WIDTH, color=INACTIVE_COLOR),
            hoverinfo="skip",
            showlegend=False,
            name="future_line",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=years,
            y=[y0] * len(years),
            mode="markers",
            marker=dict(
                size=sizes,
                color=colors,
                opacity=1.0,
                line=dict(width=0)
            ),
            customdata=customdata,

            # =========================
            # TOOLTIP (DISABLED) ✅
            # =========================
            hoverinfo="none",          # ✅ no tooltip, but points remain clickable
            # hovertemplate="<b>%{customdata[1]}</b><br>Year: %{customdata[0]}<extra></extra>",

            showlegend=False,
            name="points",
        )
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=0, b=85),
        height=360,
        title=None,

        # =========================
        # TOOLTIP STYLE (DISABLED) ✅
        # =========================
        # hoverlabel=dict(
        #     bgcolor="rgba(255,255,255,0.28)",
        #     font_color="#111",
        #     bordercolor="rgba(255,255,255,0.45)",
        #     font_size=20,
        #     align="left",
        #     namelength=-1,
        # ),

        autosize=True,
    )

    fig.update_xaxes(showgrid=False, showticklabels=False, zeroline=False)
    fig.update_yaxes(visible=False, range=[-0.42, 0.30], fixedrange=True)

    shapes = []
    annotations = []
    for i, year in enumerate(years):
        shapes.append(
            dict(
                type="line",
                xref="x",
                yref="y",
                x0=year,
                x1=year,
                y0=-0.03,
                y1=-0.16,
                line=dict(color=TICK_COLOR, width=2),
            )
        )

        y_label = -0.24 if i % 2 == 0 else -0.34
        annotations.append(
            dict(
                x=year,
                y=y_label,
                xref="x",
                yref="y",
                text=str(year),
                showarrow=False,
                font=dict(size=18, color=TICK_COLOR),
                align="center",
            )
        )

    fig.update_layout(shapes=shapes, annotations=annotations)
    return fig, df


# =========================
# (F) BUILD FULL RESPONSIVE HTML (LAYOUT + JS INTERACTION)
# =========================
def build_html(fig: go.Figure, df: pd.DataFrame, icon_uri: str) -> str:
    plot_div = pio.to_html(
        fig,
        include_plotlyjs="cdn",
        full_html=False,
        config={"responsive": True, "displayModeBar": False},
        div_id="timeline",
    )

    first = df.iloc[0]
    first_year = str(first["Year"])
    first_title = str(first["Text"])
    first_desc = str(first["Description"])

    icon_html = ""
    if icon_uri:
        icon_html = f'<img class="title-icon" src="{icon_uri}" alt="icon" />'

    return f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Echoes of Freedom in Iran</title>

<style>
  :root {{
    --bg: {BG_COLOR};
    --black: {ACTIVE_COLOR};
    --inactive: {INACTIVE_COLOR};
    --tick: {TICK_COLOR};

    --glass-bg: rgba(255,255,255,0.30);
    --glass-border: rgba(255,255,255,0.40);
    --glass-blur: 6px;
  }}

  body {{
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
    background: var(--bg);
  }}

  .stage {{ width: 100vw; height: 100vh; position: relative; }}

  .content {{
    position: absolute;
    inset: 0;
    display: grid;
    grid-template-rows: auto auto 1fr;
    justify-items: center;
    align-content: start;
    padding: clamp(18px, 3vw, 44px);
    gap: clamp(34px, 4vh, 56px);
  }}

  .title-row {{
    display: inline-flex;
    align-items: center;
    gap: 18px;
    margin-top: 18px;
  }}

  h1 {{
    margin: 0;
    font-size: clamp(62px, 6.5vw, 104px);
    font-weight: 900;
    color: var(--black);
    line-height: 1.05;
    text-align: center;
  }}

  .title-icon {{
    width: clamp(140px, 12vw, 220px);
    height: auto;
    display: inline-block;
  }}

  .timeline-wrap {{
    width: min(1500px, 96vw);
    position: relative;
    margin-top: 26px;
  }}

  #timeline {{
    width: 100%;
    height: clamp(360px, 40vh, 520px);
  }}

  .navbtn {{
    position: absolute;
    top: 32%;
    transform: translateY(-50%);
    width: 66px;
    height: 50px;
    border-radius: 999px;
    border: 1px solid rgba(0,0,0,0.22);
    background: rgba(255,255,255,0.22);
    color: var(--black);
    cursor: pointer;
    font-size: 24px;
    font-weight: 900;
  }}
  .navbtn:hover {{ background: rgba(255,255,255,0.30); }}
  .navbtn:active {{ transform: translateY(-50%) translateY(1px); }}
  #prevBtn {{ left: -34px; }}
  #nextBtn {{ right: -34px; }}

  .details {{
    width: min(1300px, 96vw);
    padding: clamp(18px, 2vw, 26px);

    /* Tooltip-related "glass" was not requested here; keeping your panel as-is */
    /*
    border-radius: 16px;
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    backdrop-filter: blur(var(--glass-blur));
    */

    height: fit-content;
    max-height: 38vh;
    overflow: auto;
    align-self: start;

    margin-top: -100px;
  }}

  .meta {{
    font-size: 18px;
    color: rgba(0,0,0,0.70);
    margin-bottom: 8px;
  }}

  .detail-title {{
    margin: 0 0 12px;
    font-size: clamp(30px, 2.7vw, 44px);
    font-weight: 900;
    color: var(--black);
  }}

  .desc {{
    font-size: clamp(18px, 1.8vw, 24px);
    line-height: 1.65;
    color: var(--black);
    white-space: pre-wrap;
  }}

  /* =========================
     TOOLTIP CSS (DISABLED) ✅
     ========================= */
  /*
  .js-plotly-plot .plotly .hoverlayer .hovertext {{
    filter: drop-shadow(0 8px 18px rgba(0,0,0,0.18));
  }}
  .js-plotly-plot .plotly .hoverlayer .hovertext path {{
    fill: var(--glass-bg) !important;
    stroke: var(--glass-border) !important;
    stroke-width: 1px !important;
  }}
  .js-plotly-plot .plotly .hoverlayer .hovertext text {{
    font-size: 20px !important;
  }}
  .js-plotly-plot .plotly .hoverlayer .hovertext tspan {{
    font-size: 20px !important;
    line-height: 1.35 !important;
  }}
  .js-plotly-plot .plotly .hoverlayer .hovertext .name {{
    font-weight: 900 !important;
  }}
  */

  @media (max-width: 640px) {{
    #prevBtn {{ left: 0; }}
    #nextBtn {{ right: 0; }}
    .timeline-wrap, .details {{ width: 96vw; }}
    .navbtn {{ width: 58px; height: 44px; }}
    .title-row {{ gap: 12px; }}
    .title-icon {{ width: clamp(90px, 18vw, 140px); }}
  }}
</style>
</head>

<body>
  <div class="stage">
    <div class="content">

      <div class="title-row">
        <h1>Echoes of Freedom in Iran</h1>
        {icon_html}
      </div>

      <div class="timeline-wrap">
        <button class="navbtn" id="prevBtn">‹</button>
        {plot_div}
        <button class="navbtn" id="nextBtn">›</button>
      </div>

      <div class="details">
        <div class="meta" id="metaYear">Year: {first_year}</div>
        <div class="detail-title" id="detailTitle">{first_title}</div>
        <div class="desc" id="detailDesc">{first_desc}</div>
      </div>

    </div>
  </div>

<script>
(function() {{
  const gd = document.getElementById("timeline");
  const PAST = 0, FUTURE = 1, POINTS = 2;

  let selectedIndex = 0;

  function clamp(i) {{
    const n = gd.data[POINTS].x.length;
    return Math.max(0, Math.min(n - 1, i));
  }}

  function updateDetails(i) {{
    const cd = gd.data[POINTS].customdata[i];
    document.getElementById("metaYear").textContent = "Year: " + cd[0];
    document.getElementById("detailTitle").textContent = cd[1];
    document.getElementById("detailDesc").textContent = cd[2];
  }}

  function updateLines(i) {{
    const xs = gd.data[POINTS].x;
    const pastX = xs.slice(0, i + 1);
    const futX  = xs.slice(i);

    Plotly.restyle(gd, {{
      x: [pastX],
      y: [Array(pastX.length).fill(0)]
    }}, [PAST]);

    Plotly.restyle(gd, {{
      x: [futX],
      y: [Array(futX.length).fill(0)]
    }}, [FUTURE]);
  }}

  function highlight(i) {{
    const n = gd.data[POINTS].x.length;
    const colors = Array(n).fill("{INACTIVE_COLOR}");
    const sizes  = Array(n).fill({UNSELECTED_SIZE});
    const opacities = Array(n).fill(1.0);

    for (let k = 0; k <= i; k++) {{
      colors[k] = "{ACTIVE_COLOR}";
      sizes[k] = {UNSELECTED_SIZE};
      opacities[k] = 1.0;
    }}

    colors[i] = "{ACTIVE_COLOR}";
    sizes[i]  = {SELECTED_SIZE};
    opacities[i] = 1.0;

    Plotly.restyle(gd, {{
      "marker.color": [colors],
      "marker.size":  [sizes],
      "marker.opacity": [opacities]
    }}, [POINTS]);

    updateLines(i);
    updateDetails(i);
    selectedIndex = i;
  }}

  gd.on("plotly_click", (e) => {{
    if (!e || !e.points || !e.points.length) return;
    const pt = e.points[0];
    if (pt.curveNumber !== POINTS) return;
    highlight(pt.pointIndex);
  }});

  document.getElementById("prevBtn").addEventListener("click", () => {{
    highlight(clamp(selectedIndex - 1));
  }});
  document.getElementById("nextBtn").addEventListener("click", () => {{
    highlight(clamp(selectedIndex + 1));
  }});

  setTimeout(() => highlight(0), 80);
}})();
</script>

</body>
</html>
"""


# =========================
# (G) MAIN ENTRY
# =========================
def main():
    df = pd.read_csv(CSV_PATH)

    required = {"Year", "Event", "Text", "Description"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {missing}. Found: {list(df.columns)}")

    fig, df_sorted = build_figure(df)
    icon_uri = file_to_data_uri(ICON_PATH, ICON_MIME)

    html = build_html(fig, df_sorted, icon_uri)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print("✅ index.html generated")


if __name__ == "__main__":
    main()