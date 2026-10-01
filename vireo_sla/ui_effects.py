"""
ui_effects.py — Vireo "dusk glass" theme, scroll effects and pipeline.

In app.py:
    from ui_effects import apply_theme, render_topbar, render_pipeline
    apply_theme()        # right after st.set_page_config (replaces the old <style> block)
    render_topbar()      # first element on the page
    render_pipeline()    # after the "Client ask" bar
Also copy .streamlit/config.toml next to app.py (dark base theme for tables/widgets).
"""
from __future__ import annotations

import json

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
import streamlit.components.v1 as components

# ------------------------------------------------------------------
# Plotly: one dark, transparent template for every chart
# ------------------------------------------------------------------
_GRID = "rgba(255,255,255,0.07)"
pio.templates["vireo"] = go.layout.Template(
    layout=dict(
        font=dict(family="Manrope, sans-serif", color="#cfc9e6", size=12),
        title=dict(font=dict(size=16, color="#f4f1ff")),
        colorway=["#a78bfa", "#f5b971", "#5eead4", "#fb7185", "#7dd3fc", "#f0abfc"],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor=_GRID, linecolor=_GRID, zerolinecolor=_GRID),
        yaxis=dict(gridcolor=_GRID, linecolor=_GRID, zerolinecolor=_GRID),
        legend=dict(font=dict(color="#cfc9e6")),
        hoverlabel=dict(bgcolor="#1b1730", font=dict(color="#ffffff")),
        colorscale=dict(
            sequential=[[0, "#1a1530"], [0.5, "#7c5ce0"], [1, "#f5b971"]]
        ),
        coloraxis=dict(
            colorbar=dict(outlinewidth=0, tickfont=dict(color="#cfc9e6"))
        ),
        annotationdefaults=dict(font=dict(color="#cfc9e6")),
    )
)
pio.templates.default = "vireo"

# ------------------------------------------------------------------
# CSS
# ------------------------------------------------------------------
THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #0a0912;
    --tx: #f4f1ff;
    --mut: #a59fc0;
    --glass: rgba(255,255,255,0.055);
    --glass-2: rgba(255,255,255,0.09);
    --line: rgba(255,255,255,0.11);
    --violet: #a78bfa;
    --violet-d: #7c5ce0;
    --amber: #f5b971;
    --teal: #5eead4;
    --rose: #fb7185;
    --ink: #0b0a14;
}

html, body, [class*="css"], .stApp { font-family: 'Manrope', sans-serif !important; }
html { scroll-behavior: smooth; }

/* ---------- dusk backdrop ---------- */
.stApp {
    background:
        radial-gradient(900px 600px at 8% -5%, rgba(124,92,224,.45), transparent 60%),
        radial-gradient(800px 600px at 100% 10%, rgba(236,110,173,.22), transparent 60%),
        radial-gradient(900px 700px at 70% 105%, rgba(245,185,113,.18), transparent 60%),
        var(--bg) !important;
    background-attachment: fixed !important;
    color: var(--tx);
}
[data-testid="stHeader"] { background: transparent !important; }

/* ---------- the glass frame ---------- */
.block-container {
    max-width: 1400px !important;
    margin: 1rem auto 2rem auto;
    padding: 1.6rem 2.4rem 3rem 2.4rem !important;
    background: rgba(16,13,30,.58);
    backdrop-filter: blur(26px) saturate(140%);
    -webkit-backdrop-filter: blur(26px) saturate(140%);
    border: 1px solid var(--line);
    border-radius: 30px;
    box-shadow: 0 30px 80px rgba(0,0,0,.45);
}

[data-testid="stSidebar"] {
    background: rgba(12,10,24,.82) !important;
    backdrop-filter: blur(20px);
    border-right: 1px solid var(--line) !important;
}
[data-testid="stSidebar"] * { color: #e8e4fa; }

h1,h2,h3,h4,h5, p, li, label, .stMarkdown { color: var(--tx); }
hr { border-color: var(--line) !important; }

/* ---------- top bar ---------- */
.topbar {
    display: flex; align-items: center; justify-content: space-between;
    gap: 1rem; flex-wrap: wrap;
    padding: .6rem .7rem .6rem 1rem; margin-bottom: 1.6rem;
    background: var(--glass); border: 1px solid var(--line); border-radius: 999px;
}
.tb-brand { display: flex; align-items: center; gap: .75rem; }
.tb-mark {
    width: 38px; height: 38px; border-radius: 50%; display: grid; place-items: center;
    background: linear-gradient(135deg, var(--violet), #ec6ead); color: #fff; font-size: 1.05rem;
}
.tb-brand b { display: block; font-size: .98rem; line-height: 1.1; color: var(--tx); }
.tb-brand small { color: var(--mut); font-size: .75rem; }
.tb-chips { display: flex; gap: .5rem; flex-wrap: wrap; }
.tb-chips span {
    padding: .42rem .85rem; border-radius: 999px; font-size: .78rem; font-weight: 600;
    color: #d9d3f2; background: var(--glass-2); border: 1px solid var(--line);
}

/* ---------- hero ---------- */
.hero { padding: .4rem 0 1.2rem 0; color: var(--tx); }
.hero-kicker {
    display: inline-block; padding: .35rem .8rem; border-radius: 999px;
    background: rgba(167,139,250,.16); border: 1px solid rgba(167,139,250,.35);
    color: #d6caff; font-size: .8rem; font-weight: 700; letter-spacing: 0; text-transform: none;
}
.hero-title {
    font-family: 'Manrope', sans-serif !important; font-weight: 800;
    font-size: 3.4rem; line-height: 1.04; letter-spacing: -.02em;
    margin: .8rem 0 .6rem 0; color: #fff;
}
.hero-sub { color: var(--mut); font-size: 1.02rem; line-height: 1.6; max-width: 760px; }

.question-bar {
    background: var(--glass); border: 1px solid var(--line);
    border-left: 4px solid var(--amber); border-radius: 16px;
    padding: 1rem 1.2rem; margin: .2rem 0 1.4rem 0; color: #d9d3f2; line-height: 1.55;
}
.question-bar strong { color: #fff; }

/* ---------- cards ---------- */
.card, .card-dark, .insight, .evidence-step {
    background: var(--glass); border: 1px solid var(--line);
    border-radius: 20px; padding: 1.15rem 1.25rem;
    box-shadow: 0 10px 30px rgba(0,0,0,.18);
    backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
    color: var(--tx);
}
.card-dark {
    background: linear-gradient(150deg, rgba(167,139,250,.26), rgba(236,110,173,.10));
    border-color: rgba(167,139,250,.38);
}
.card-label { color: var(--mut); font-size: .8rem; font-weight: 600; letter-spacing: 0; text-transform: none; }
.card-dark .card-label { color: #d6caff; }
.card-number { color: #fff !important; font-size: 2.15rem; font-weight: 800; letter-spacing: -.02em; margin-top: .25rem; }
.card-detail { color: var(--mut); font-size: .86rem; line-height: 1.55; margin-top: .3rem; }
.card-dark .card-detail { color: #d9d3f2; }
.card h4, .card-dark h4, [style*="#071426"] { color: #fff !important; }

.section-title {
    font-family: 'Manrope', sans-serif !important; font-weight: 800;
    font-size: 1.7rem; letter-spacing: -.015em; color: #fff; margin: 1.8rem 0 .25rem 0;
}
.section-subtitle { color: var(--mut); font-size: .92rem; margin-bottom: 1rem; max-width: 780px; line-height: 1.55; }

.insight { height: 100%; line-height: 1.6; color: #d9d3f2; }
.insight strong { color: #fff; }
.insight .number {
    display: inline-grid; place-items: center; width: 2.3rem; height: 2.3rem; border-radius: 50%;
    background: rgba(167,139,250,.2); color: #d6caff; font-size: .85rem; font-weight: 800; margin-bottom: .6rem;
}

.callout {
    background: var(--glass); border: 1px solid var(--line); border-left: 4px solid var(--violet);
    border-radius: 14px; padding: .95rem 1.1rem; color: #d9d3f2; line-height: 1.6; margin-top: .6rem;
}
.callout strong { color: #fff; }
.callout-red  { border-left-color: var(--rose); background: rgba(251,113,133,.08); }
.callout-blue { border-left-color: var(--teal); background: rgba(94,234,212,.07); }

.evidence-step { min-height: 160px; }
.step-no {
    display: inline-grid; place-items: center; width: 1.9rem; height: 1.9rem; border-radius: 50%;
    background: rgba(245,185,113,.16); color: var(--amber); font-weight: 800; font-size: .75rem;
}
.step-title { color: var(--mut); font-weight: 600; font-size: .86rem; margin-top: .55rem; }
.step-value { color: #fff; font-size: 1.55rem; font-weight: 800; margin: .25rem 0; letter-spacing: -.01em; }
.step-text { color: var(--mut); font-size: .8rem; line-height: 1.5; }
.small-note { color: var(--mut); font-size: .78rem; }

/* ---------- streamlit widgets ---------- */
.stTabs [data-baseweb="tab-list"] {
    gap: .3rem; padding: .35rem; border-radius: 999px;
    background: rgba(16,13,30,.8); border: 1px solid var(--line);
    backdrop-filter: blur(12px);
    position: sticky; top: 3.8rem; z-index: 50; width: fit-content; max-width: 100%;
}
.stTabs [data-baseweb="tab"] { padding: .5rem 1rem; border-radius: 999px; height: auto; color: var(--mut); font-weight: 600; }
.stTabs [aria-selected="true"] { background: linear-gradient(135deg, var(--violet-d), #b25fd6); color: #fff !important; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none !important; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.2rem; }

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--violet-d), #c05fd0); border: 0; color: #fff;
    border-radius: 999px; padding: .6rem 1.4rem; font-weight: 700;
}
[data-baseweb="select"] > div { background: var(--glass) !important; border: 1px solid var(--line) !important; border-radius: 12px !important; }
[data-testid="stExpander"] { background: var(--glass); border: 1px solid var(--line) !important; border-radius: 14px; }
[data-testid="stAlert"] { background: rgba(167,139,250,.1); border: 1px solid rgba(167,139,250,.3); border-radius: 14px; }
div[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 14px; overflow: hidden; }
[data-testid="stCodeBlock"] pre { background: rgba(0,0,0,.35) !important; border-radius: 12px; }

/* ---------- scroll progress + reveal ---------- */
#vireo-progress {
    position: fixed; top: 0; left: 0; height: 3px; width: 100%;
    transform-origin: 0 50%; transform: scaleX(0);
    background: linear-gradient(90deg, var(--violet), var(--amber));
    z-index: 999999; pointer-events: none;
}
.reveal {
    opacity: 0; transform: translateY(20px);
    transition: opacity .6s ease var(--d,0ms), transform .6s cubic-bezier(.2,.7,.2,1) var(--d,0ms);
}
.reveal.in-view { opacity: 1; transform: none; }

/* ---------- pipeline ---------- */
.pl-panel {
    margin: 1.6rem 0 1rem 0; padding: 2rem;
    background: rgba(255,255,255,.035); border: 1px solid var(--line); border-radius: 26px;
}
.pl-head { margin-bottom: 1.6rem; max-width: 640px; }
.pl-head h2 { margin: 0 0 .4rem 0; font-size: 1.9rem; font-weight: 800; letter-spacing: -.02em; color: #fff; }
.pl-head p { margin: 0; color: var(--mut); font-size: .95rem; line-height: 1.55; }

.pl-wrap { --cur: #a78bfa; --pl-pct: 12.5; }
.pl-grid { display: grid; grid-template-columns: minmax(250px, .8fr) minmax(0, 1.5fr); gap: 1.6rem; align-items: start; }

.pl-side {
    position: sticky; top: 7.5rem; padding: 1.6rem; border-radius: 24px;
    background: linear-gradient(160deg, rgba(167,139,250,.24), rgba(255,255,255,.04));
    border: 1px solid rgba(167,139,250,.35);
}
.pl-ring {
    width: 150px; height: 150px; border-radius: 50%; margin: 0 auto 1.1rem auto; position: relative;
    background: conic-gradient(var(--cur) calc(var(--pl-pct) * 1%), rgba(255,255,255,.1) 0);
    transition: background .3s;
}
.pl-ring::before { content: ""; position: absolute; inset: 11px; border-radius: 50%; background: #17122b; }
.pl-ring b {
    position: absolute; inset: 0; display: grid; place-items: center;
    font-size: 1.7rem; font-weight: 800; color: #fff; letter-spacing: -.02em;
}
.pl-side small { display: block; text-align: center; color: var(--mut); font-size: .8rem; margin-bottom: .3rem; }
.pl-cur-title { text-align: center; font-size: 1.2rem; font-weight: 800; color: #fff; }
.pl-cur-text { text-align: center; color: #cfc9e6; font-size: .88rem; line-height: 1.55; margin-top: .4rem; }

.pl-list { display: flex; flex-direction: column; gap: .8rem; }
.pl-row {
    display: grid; grid-template-columns: 60px minmax(0,1fr) 30px; gap: 1.1rem; align-items: center;
    padding: .95rem 1.2rem; border-radius: 18px;
    background: var(--glass); border: 1px solid var(--line);
}
.pl-lens {
    width: 60px; height: 60px; border-radius: 50%; display: grid; place-items: center;
    background: var(--c); color: var(--ink);
    filter: grayscale(1) brightness(.55); transition: filter .5s ease, box-shadow .5s ease;
}
.pl-lens svg { width: 27px; height: 27px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.pl-copy { min-width: 0; transition: opacity .4s; opacity: .55; }
.pl-copy small { color: var(--mut); font-size: .74rem; font-weight: 600; }
.pl-copy h4 { margin: .1rem 0 .2rem 0; font-size: 1.05rem; font-weight: 700; color: #fff !important; }
.pl-copy p { margin: 0; color: var(--mut); font-size: .88rem; line-height: 1.5; }
.pl-dot {
    width: 28px; height: 28px; border-radius: 50%; border: 1.5px solid var(--line);
    display: grid; place-items: center; color: transparent; font-size: .8rem; font-weight: 800; transition: all .4s;
}
.pl-row.lit { border-color: color-mix(in srgb, var(--c) 45%, transparent); }
.pl-row.lit .pl-lens { filter: none; box-shadow: 0 0 26px 2px color-mix(in srgb, var(--c) 55%, transparent); }
.pl-row.lit .pl-copy { opacity: 1; }
.pl-row.lit .pl-dot { background: var(--c); border-color: var(--c); color: var(--ink); }
.pl-dot::after { content: "✓"; }

@media (max-width: 900px) {
    .block-container { padding: 1.2rem 1rem 2rem 1rem !important; border-radius: 20px; }
    .hero-title { font-size: 2.3rem; }
    .pl-grid { grid-template-columns: 1fr; }
    .pl-side { position: static; }
    .pl-panel { padding: 1.1rem; }
}
@media (prefers-reduced-motion: reduce) {
    html { scroll-behavior: auto; }
    .reveal { opacity: 1; transform: none; transition: none; }
    .pl-lens, .pl-copy, .pl-dot { transition: none; }
    #vireo-progress { display: none; }
}
</style>
"""

# ------------------------------------------------------------------
# JS (runs in the parent document so it survives Streamlit reruns)
# ------------------------------------------------------------------
FX_JS = r"""
(function () {
  if (window.__vireoFx2) return;
  window.__vireoFx2 = true;
  var doc = document;

  var bar = doc.createElement('div');
  bar.id = 'vireo-progress';
  doc.body.appendChild(bar);

  var SEL = ['.topbar','.hero','.question-bar','.card','.card-dark','.insight','.evidence-step',
    '.callout','.section-title','.section-subtitle','.pl-head','.pl-row',
    '[data-testid="stPlotlyChart"]','[data-testid="stDataFrame"]'].join(',');

  var io = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.add('in-view'); io.unobserve(e.target); }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -5% 0px' });

  function scan() {
    doc.querySelectorAll(SEL).forEach(function (el) {
      if (el.dataset.fx) return;
      el.dataset.fx = '1';
      el.classList.add('reveal');
      var col = el.closest('[data-testid="stColumn"], [data-testid="column"]');
      var idx = col ? Array.prototype.indexOf.call(col.parentElement.children, col) : 0;
      el.style.setProperty('--d', Math.max(0, idx) * 90 + 'ms');
      io.observe(el);
    });
  }

  var last = {};
  function onScroll() {
    var s = doc.querySelector('[data-testid="stMain"]') || doc.querySelector('section.main');
    if (s) {
      var max = s.scrollHeight - s.clientHeight;
      bar.style.transform = 'scaleX(' + (max > 0 ? s.scrollTop / max : 0) + ')';
    }
    var vh = window.innerHeight;
    doc.querySelectorAll('.pl-wrap').forEach(function (w) {
      var rows = w.querySelectorAll('.pl-row'), lit = 0;
      rows.forEach(function (r) {
        var b = r.getBoundingClientRect();
        var on = b.top + b.height / 2 < vh * 0.7;
        r.classList.toggle('lit', on);
        if (on) lit++;
      });
      var idx = Math.max(1, lit), cur = rows[idx - 1];
      if (!cur || last.idx === idx) return;
      last.idx = idx;
      w.style.setProperty('--cur', cur.dataset.c);
      w.style.setProperty('--pl-pct', (lit / rows.length) * 100);
      w.querySelector('.pl-cur-no').textContent = String(idx).padStart(2, '0') + ' / ' + String(rows.length).padStart(2, '0');
      w.querySelector('.pl-cur-title').textContent = cur.dataset.title;
      w.querySelector('.pl-cur-text').textContent = cur.dataset.text;
    });
  }
  window.addEventListener('scroll', onScroll, true);
  window.addEventListener('resize', onScroll);
  new MutationObserver(function () { scan(); onScroll(); }).observe(doc.body, { childList: true, subtree: true });
  scan(); onScroll();
})();
"""


def apply_theme() -> None:
    """Inject theme CSS and the scroll-effect script (idempotent)."""
    st.markdown(THEME_CSS, unsafe_allow_html=True)
    loader = f"""
    <script>
    try {{
        var p = window.parent.document;
        if (!p.getElementById('vireo-fx2')) {{
            var s = p.createElement('script');
            s.id = 'vireo-fx2';
            s.textContent = {json.dumps(FX_JS)};
            p.head.appendChild(s);
        }}
    }} catch (e) {{ console.warn('Vireo FX unavailable', e); }}
    </script>
    """
    components.html(loader, height=0)


def render_topbar(chips: tuple[str, ...] = (
    "11,200 canonical tickets",
    "Data through 30 Jun 2026",
    "Times in IST",
)) -> None:
    chip_html = "".join(f"<span>{c}</span>" for c in chips)
    st.markdown(
        '<div class="topbar"><div class="tb-brand"><div class="tb-mark">◈</div>'
        "<div><b>Vireo Audio</b><small>SLA command center</small></div></div>"
        f'<div class="tb-chips">{chip_html}</div></div>',
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------
# Pipeline
# ------------------------------------------------------------------
_ICONS = {
    "data": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
    "quality": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/><path d="m8 11 2 2 4-4"/>',
    "sla": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "team": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c0-3.6 3-6 6.5-6s6.5 2.4 6.5 6"/><circle cx="17.5" cy="9" r="2.5"/><path d="M17 14c2.8.2 4.5 2.2 4.5 5"/>',
    "chart": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    "signal": '<path d="M12 3 2.5 20h19L12 3z"/><path d="M12 10v4M12 17.5v.01"/>',
    "shield": '<path d="M12 3 4 6v6c0 4.5 3.3 7.7 8 9 4.7-1.3 8-4.5 8-9V6l-8-3z"/><path d="m8.5 12 2.5 2.5 4.5-5"/>',
    "dash": '<rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4M7 13l3-3 3 2 4-5"/>',
}

PIPELINE_STAGES = [
    ("data", "#b5e22e", "Raw support data", "Collects tickets, agents, customers, orders, products"),
    ("quality", "#e3ef3a", "Data quality", "Removes duplicates, resolves migration artifacts"),
    ("sla", "#ffb35c", "SLA measurement", "Normalizes time, calculates first response, evaluates SLA"),
    ("team", "#f55f96", "Workforce context", "Maps roster, attributes shifts, enriches teams"),
    ("chart", "#dc66f0", "Comparative analytics", "Analyzes channels, shifts, teams, agents, trends"),
    ("signal", "#b08cfb", "Operational signals", "Detects breach concentration, night risk, morning dependency"),
    ("shield", "#6fb5f7", "Independent validation", "Recomputes SLA, verifies audit, tests boundaries"),
    ("dash", "#4df0c4", "Vireo SLA Command Center", "Displays KPIs, hotspots, insights, context, trends"),
]


def render_pipeline() -> None:
    first = PIPELINE_STAGES[0]
    rows = "".join(
        f'<div class="pl-row" style="--c:{c}" data-c="{c}" data-title="{t}" data-text="{d}">'
        f'<div class="pl-lens"><svg viewBox="0 0 24 24">{_ICONS[ic]}</svg></div>'
        f'<div class="pl-copy"><small>Stage {i:02d}</small><h4>{t}</h4><p>{d}</p></div>'
        f'<div class="pl-dot"></div></div>'
        for i, (ic, c, t, d) in enumerate(PIPELINE_STAGES, 1)
    )
    side = (
        '<div class="pl-side"><div class="pl-ring"><b class="pl-cur-no">01 / 08</b></div>'
        "<small>Current stage</small>"
        f'<div class="pl-cur-title">{first[2]}</div>'
        f'<div class="pl-cur-text">{first[3]}</div></div>'
    )
    st.markdown(
        '<div class="pl-panel"><div class="pl-head"><h2>From raw data to actionable insight</h2>'
        "<p>Scroll to follow the work. Each stage lights up as the analysis moves from raw "
        "tickets to this command center.</p></div>"
        f'<div class="pl-wrap"><div class="pl-grid">{side}<div class="pl-list">{rows}</div></div></div></div>',
        unsafe_allow_html=True,
    )