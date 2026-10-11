"""Small presentation layer: themes, accessible motion and escaped shift cards."""
from html import escape
from collections import Counter
import streamlit as st

PALETTES = {
    'Midnight': dict(bg='#0b1020', panel='#141d32', field='#1b2740', text='#f1f5ff', muted='#b0bfd9', line='#344463', accent='#9d94ff', soft='#282248'),
    'Daylight': dict(bg='#f5f6fc', panel='#ffffff', field='#edf0f8', text='#17213b', muted='#53627d', line='#d4daea', accent='#5741c7', soft='#ede9ff'),
}

def apply_theme(theme, motion):
    p = PALETTES[theme]
    css = '''
    html {scroll-behavior:smooth;}
    .stApp {background:BG;color:TEXT;}
    [data-testid="stHeader"] {background:BG;}
    [data-testid="stSidebar"] {background:PANEL;border-right:1px solid LINE;}
    [data-testid="stSidebar"] *, [data-testid="stWidgetLabel"] *, [data-testid="stCaptionContainer"] {color:TEXT;}
    .stApp h1,.stApp h2,.stApp h3,.stApp p,.stApp label {color:TEXT;}
    [data-testid="stText"], [data-testid="stText"] pre {color:TEXT!important;line-height:1.65;}
    [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] li, [data-testid="stMarkdownContainer"] strong {color:TEXT;}
    [data-testid="stVerticalBlockBorderWrapper"] > div {border-color:LINE;}
    .block-container {max-width:1240px;padding-top:2.5rem;padding-bottom:3rem;}
    [data-testid="stForm"] {background:PANEL;border:1px solid LINE;border-radius:22px;padding:24px;}
    [data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,[data-testid="stDateInput"] input {
      background:FIELD;color:TEXT;caret-color:TEXT;border-radius:10px;}
    [data-testid="stTextInput"] [data-baseweb="input"], [data-testid="stDateInput"] [data-baseweb="input"] {background:FIELD;border-color:LINE;}
    [data-baseweb="select"] > div {background:FIELD;color:TEXT;}
    [data-testid="stMetric"] {background:PANEL;border:1px solid LINE;border-radius:16px;padding:18px;}
    [data-testid="stMetricValue"] {color:TEXT;}
    [data-testid="stExpander"] {background:PANEL;border:1px solid LINE;border-radius:16px;}
    [data-testid="stExpander"] summary {color:TEXT;background:FIELD!important;}
    [data-testid="stExpander"] details summary:hover {background:SOFT!important;}
    .stApp input:not([type="radio"]):not([type="checkbox"]) {background:FIELD!important;color:TEXT!important;}
    [data-baseweb="input"] {background:FIELD!important;border-color:LINE!important;}
    [data-baseweb="input"] button {background:FIELD!important;color:TEXT!important;}
    [data-testid="stSelectbox"] [data-baseweb="select"] > div {background:FIELD!important;color:TEXT!important;}
    .stApp a.jump {color:ACCENT!important;}
    .stButton button,.stDownloadButton button,[data-testid="stFormSubmitButton"] button {
      background:PANEL;color:TEXT;border:1px solid LINE;border-radius:12px;min-height:44px;transition:transform .18s,border-color .18s;}
    .stButton button:hover,.stDownloadButton button:hover {border-color:ACCENT;transform:translateY(-2px);}
    button[kind="primary"], [data-testid="stFormSubmitButton"] button {background:ACCENT;color:BG;border:none;font-weight:700;}
    button[kind="primary"] p,[data-testid="stFormSubmitButton"] button p {color:BG;}
    .hero {position:relative;overflow:hidden;background:linear-gradient(120deg,PANEL 20%,SOFT);border:1px solid LINE;border-radius:26px;padding:38px;margin:0 0 22px;}
    .hero::after {content:'';position:absolute;width:250px;height:250px;border:1px solid ACCENT;border-radius:50%;right:-65px;top:-55px;opacity:.2;box-shadow:0 0 0 38px SOFT,0 0 0 39px LINE;pointer-events:none;}
    .eyebrow {font-size:12px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:ACCENT;margin-bottom:16px;}
    .hero h1 {font-size:clamp(34px,5vw,58px);line-height:1.05;letter-spacing:-.045em;margin:0 0 14px;position:relative;z-index:1;}
    .hero p {max-width:650px;color:MUTED;font-size:17px;line-height:1.6;position:relative;z-index:1;}
    .badge {display:inline-block;background:SOFT;color:ACCENT;padding:6px 11px;border-radius:30px;font-size:12px;font-weight:650;margin:10px 6px 0 0;}
    .steps {display:flex;gap:12px;margin:18px 0 28px;flex-wrap:wrap;}
    .step {flex:1;min-width:170px;border:1px solid LINE;background:PANEL;border-radius:14px;padding:15px;color:MUTED;font-size:14px;}
    .step b {display:block;color:TEXT;margin-bottom:5px;}
    [data-testid="stForm"] {animation:enter .45s ease-out both;}
    [data-testid="stForm"] h4 {color:ACCENT;margin-top:18px;}
    .stApp input:focus-visible,.stApp button:focus-visible {outline:2px solid ACCENT;outline-offset:3px;}
    .shift-card {background:PANEL;border:1px solid LINE;border-radius:18px;padding:20px;margin:10px 0;min-height:180px;}
    .shift-card .time {color:ACCENT;font-size:13px;font-weight:700;}
    .shift-card h3 {font-size:20px;margin:10px 0;}
    .shift-card .crew {color:MUTED;font-size:14px;line-height:1.6;}
    .coverage {height:5px;background:LINE;border-radius:8px;margin:16px 0 8px;overflow:hidden;}
    .coverage span {display:block;height:100%;background:ACCENT;border-radius:8px;}
    .small {color:MUTED;font-size:12px;}
    .jump {color:ACCENT;text-decoration:none;font-weight:600;display:inline-block;margin-top:15px;}
    @keyframes enter {from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
    @keyframes breathe {50%{transform:translateY(8px)}}
    .hero,.step,.shift-card {animation:enter .45s ease-out both;}
    .hero::after {animation:breathe 7s ease-in-out infinite;}
    .step:nth-child(2) {animation-delay:.08s;} .step:nth-child(3) {animation-delay:.16s;}
    @media(max-width:640px) {.hero{padding:24px}.block-container{padding:1.5rem 1rem}.hero::after{opacity:.1}}
    @media(prefers-reduced-motion:reduce) {html{scroll-behavior:auto}*,*::after{animation:none!important;transition:none!important}}
    '''
    for token, key in [('ACCENT','accent'),('MUTED','muted'),('PANEL','panel'),('FIELD','field'),('TEXT','text'),('LINE','line'),('SOFT','soft'),('BG','bg')]:
        css = css.replace(token, p[key])
    if not motion:
        css += 'html{scroll-behavior:auto}.hero,.step,.shift-card,.hero::after,[data-testid="stForm"]{animation:none!important}.stButton button,.stDownloadButton button{transition:none!important;transform:none!important}'
    st.markdown('<style>' + css + '</style>', unsafe_allow_html=True)

def hero():
    st.markdown('''<section class="hero"><div class="eyebrow">CREWSYNC / YOUR COORDINATION COPILOT</div>
    <h1>You lead.<br>We coordinate.</h1><p>A calmer way to bring people together. Build a shift plan, spot the gaps, and turn logistics into thoughtful communication.</p>
    <span class="badge">Availability-aware scheduling</span><span class="badge">Conflict checks</span><span class="badge">AI-assisted communication</span><br>
    <a class="jump" href="#workspace">Start coordinating ↓</a></section>
    <div class="steps"><div class="step"><b>01 · Set the scene</b>Your event, your people, your shifts.</div><div class="step"><b>02 · Align the crew</b>Check coverage and resolve conflicts.</div><div class="step"><b>03 · Keep everyone in sync</b>Review and share tailored reminders.</div></div>
    <div id="workspace"></div>''', unsafe_allow_html=True)

def shift_cards(plan):
    counts = Counter(a['shift_id'] for a in plan['assignments'])
    names = {v['id']:v['name'] for v in plan['volunteers']}
    cols = st.columns(min(3, len(plan['shifts'])))
    for i, s in enumerate(sorted(plan['shifts'],key=lambda s:s['start'])):
        crew = [names[a['volunteer_id']] for a in plan['assignments'] if a['shift_id']==s['id']]
        n = counts[s['id']]
        with cols[i % len(cols)]:
            st.markdown(f'''<article class="shift-card"><div class="time">{escape(s['start'])} — {escape(s['end'])}</div><h3>{escape(s['label'])}</h3><div class="crew">{escape(' · '.join(crew) or 'No volunteers assigned')}</div><div class="coverage"><span style="width:{min(100,100*n/s['required']):.0f}%"></span></div><div class="small">{n} / {s['required']} volunteers · {'Covered' if n>=s['required'] else 'Needs attention'}</div></article>''', unsafe_allow_html=True)
