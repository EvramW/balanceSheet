"""
نظام تحليل القوائم المالية
============================
الخط المستخدم في PDF:
  - Windows: Amiri (ضعه في نفس مجلد السكريبت)
  - Linux/Server: DejaVuSans (مدمج في النظام)
"""

import streamlit as st
import arabic_reshaper
from bidi.algorithm import get_display
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import os

# ══════════════════════════════════════════════════════
# إعداد الصفحة
# ══════════════════════════════════════════════════════

st.set_page_config(
    page_title="نظام تحليل القوائم المالية",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
/* إخفاء الشريط الجانبي */
[data-testid="collapsedControl"] { display: none !important; }
section[data-testid="stSidebar"]  { display: none !important; }

/* RTL العام للمستند */
html, body, .stApp, .block-container {
    direction: rtl !important;
    text-align: right;
}

/* ترويسة */
.app-header {
    background: linear-gradient(135deg, #0d2137 0%, #1a4a7a 60%, #2d7dd2 100%);
    border-radius: 16px;
    padding: 30px 40px;
    margin-bottom: 24px;
    text-align: center;
    color: white;
    direction: rtl;
}
.app-header h1 { font-size: 1.9rem; margin: 0 0 6px; }
.app-header p  { font-size: .95rem; opacity: .82; margin: 0; }

/* عناوين الأقسام */
.sec-hdr {
    font-size: 1.15rem;
    font-weight: 700;
    color: #0d2137;
    border-right: 5px solid #2d7dd2;
    border-left: none;
    padding-right: 12px;
    padding-left: 0;
    margin: 20px 0 10px;
    direction: rtl;
    text-align: right;
}

/* بطاقات KPI */
.kpi-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin: 8px 0;
    direction: rtl;
}
.kpi-card {
    flex: 1 1 160px;
    border-radius: 11px;
    padding: 16px 12px;
    color: white;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0,0,0,.18);
    direction: rtl;
}
.kpi-val   { font-size: 1.8rem; font-weight: 800; line-height: 1.1; direction: ltr; display: inline-block; }
.kpi-lbl   { font-size: .76rem; opacity: .88; margin-top: 4px; }
.kpi-calc  { font-size: .65rem; opacity: .72; margin-top: 3px; font-style: italic; }
.kpi-good  { background: linear-gradient(135deg,#145a32,#27ae60); }
.kpi-warn  { background: linear-gradient(135deg,#7d5a00,#f39c12); }
.kpi-bad   { background: linear-gradient(135deg,#6e1010,#c0392b); }
.kpi-blue  { background: linear-gradient(135deg,#0d2137,#2d7dd2); }

/* صناديق التحليل */
.abox {
    border-radius: 9px;
    padding: 12px 16px;
    margin: 5px 0;
    border-right: 6px solid;
    border-left: none;
    direction: rtl;
    text-align: right;
    line-height: 1.8;
    font-size: .93rem;
}
.ab-good { background: #eafaf1; border-color: #27ae60; color: #145a32; }
.ab-warn { background: #fef9e7; border-color: #f39c12; color: #7d5a00; }
.ab-bad  { background: #fdedec; border-color: #c0392b; color: #6e1010; }
.ab-def  { background: #f4f8fd; border-color: #2d7dd2; color: #1a2f45; }

/* صناديق شرح النسب (مدمجة مع التحليل) */
.def-box {
    background: #eaf0fb;
    border-radius: 9px;
    border-right: 5px solid #2d7dd2;
    border-left: none;
    padding: 11px 15px;
    margin: 0 0 4px 0;
    direction: rtl;
    text-align: right;
    font-size: .88rem;
    line-height: 1.8;
    color: #1a2f45;
}
.def-box strong { color: #0d2137; }

/* مجموعة النسبة (تعريف + تحليل معاً) */
.ratio-group {
    border: 1px solid #d0dff0;
    border-radius: 12px;
    padding: 0;
    margin: 10px 0;
    overflow: hidden;
    direction: rtl;
}
.ratio-group-header {
    background: linear-gradient(90deg, #0d2137, #1a4a7a);
    color: white;
    font-size: 1rem;
    font-weight: 700;
    padding: 10px 16px;
    direction: rtl;
    text-align: right;
}
.ratio-group-body {
    padding: 10px 12px;
}

/* ملاحظة لا تُطبع */
.no-print {
    background: #fffbe6;
    border: 1px solid #f39c12;
    border-radius: 7px;
    padding: 7px 13px;
    font-size: .8rem;
    color: #7d5a00;
    direction: rtl;
    text-align: right;
    margin-bottom: 6px;
}
@media print { .no-print { display: none !important; } }

/* جدول مقارنة */
.ctbl {
    width: 100%;
    border-collapse: collapse;
    direction: rtl;
}
.ctbl th {
    background: #0d2137;
    color: white;
    padding: 9px 11px;
    font-size: .86rem;
    text-align: right;
}
.ctbl td {
    padding: 8px 11px;
    font-size: .84rem;
    text-align: right;
    border-bottom: 1px solid #e0e7ef;
}
.ctbl tr:nth-child(even) td { background: #f4f8fd; }

/* فاصل قسم */
.section-divider {
    border: none;
    border-top: 2px solid #2d7dd2;
    margin: 28px 0 18px 0;
    opacity: 0.3;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# البنود المطلوبة
# ══════════════════════════════════════════════════════

REQUIRED_ITEMS = {
    "الاصول الثابته بالصافي :":            "fixed_assets",
    "اعمال تحت التنفيذ":                    "wip",
    "ودائع صيانه":                          "maintenance_deposits",
    "مجموع الأصول الغير متداوله":           "non_current_assets",
    "العملاء و اوراق القبض":                "receivables",
    "مدينون و ارصده مدينه اخرى":           "other_debtors",
    "النقديه و ما في حكمها":                "cash",
    "المخزون":                               "inventory",
    "مبالغ مستحقه لأطراف ذوي علاقه":      "related_party_receivable",
    "مجموع الأصول متداوله":                 "current_assets",
    "إجمالي الاصول":                        "total_assets",
    "موردين و أوراق دفع":                   "payables",
    "دائنون و ارصده دائنه اخرى":           "other_creditors",
    "بنوك تسهيلات":                         "bank_facilities",
    "التزامات ضريبية مؤجله":                "deferred_tax",
    "مجموع الالتزامات المتداوله":           "current_liabilities",
    "رأس المال":                            "capital",
    "احتياطي قانوني":                       "legal_reserve",
    "أرباح مرحله":                          "retained_earnings",
    "صافي أرباح / خسائر الفتره":           "net_profit",
    "مجموع حقوق اصحاب الحصص":              "equity",
    "إجمالي حقوق اصحاب الحصص و الالتزامات": "total_equity_liabilities",
}

# ══════════════════════════════════════════════════════
# تعريفات المؤشرات — تُستخدم في الواجهة والـ PDF معاً
# ══════════════════════════════════════════════════════

RATIO_DEFS = {
    "نسبة_التداول": {
        "name":    "نسبة التداول  (Current Ratio)",
        "formula": "الأصول المتداولة ÷ الالتزامات المتداولة",
        "meaning": "تقيس مدى قدرة الشركة على سداد التزاماتها قصيرة الأجل من أصولها المتداولة. كلما ارتفعت كان وضع السيولة أفضل.",
        "ideal":   "ممتاز ≥ 2x  |  جيد 1.5–2x  |  مقبول 1–1.5x  |  ضعيف < 1x",
        "section": "السيولة والملاءة المالية",
    },
    "النسبة_السريعة": {
        "name":    "النسبة السريعة  (Quick Ratio)",
        "formula": "(الأصول المتداولة − المخزون) ÷ الالتزامات المتداولة",
        "meaning": "تستبعد المخزون لأنه الأصل الأقل سيولة، وتقيس القدرة الفورية على السداد دون الحاجة لبيعه.",
        "ideal":   "ممتاز ≥ 1x  |  مقبول 0.7–1x  |  ضعيف < 0.7x",
        "section": "السيولة والملاءة المالية",
    },
    "نسبة_النقدية": {
        "name":    "نسبة النقدية  (Cash Ratio)",
        "formula": "النقدية وما في حكمها ÷ الالتزامات المتداولة",
        "meaning": "أشد مقاييس السيولة تحفظاً؛ تعكس النقد الجاهز للسداد الفوري دون تحويل أي أصل آخر.",
        "ideal":   "جيد ≥ 0.5x  |  مقبول 0.2–0.5x  |  ضعيف < 0.2x",
        "section": "السيولة والملاءة المالية",
    },
    "نسبة_الديون": {
        "name":    "نسبة الديون  (Debt Ratio)",
        "formula": "الالتزامات المتداولة ÷ إجمالي الأصول",
        "meaning": "تقيس نسبة الأصول الممولة بالديون. كلما انخفضت كان الهيكل المالي أكثر أماناً واستقلالية.",
        "ideal":   "آمن < 40%  |  مقبول 40–60%  |  مرتفع > 60%",
        "section": "الهيكل المالي والتمويل",
    },
    "نسبة_حقوق_الملكية": {
        "name":    "نسبة حقوق الملكية  (Equity Ratio)",
        "formula": "حقوق الملكية ÷ إجمالي الأصول",
        "meaning": "تعكس نسبة الأصول الممولة ذاتياً من أموال الملاك. ارتفاعها يشير إلى استقلالية مالية وملاءة قوية.",
        "ideal":   "ممتاز ≥ 60%  |  جيد 40–60%  |  منخفض < 40%",
        "section": "الهيكل المالي والتمويل",
    },
    "العائد_على_الملكية": {
        "name":    "العائد على حقوق الملكية  (ROE)",
        "formula": "صافي الربح ÷ حقوق الملكية",
        "meaning": "يقيس كفاءة الشركة في توليد الأرباح من أموال المساهمين. من أهم مؤشرات الكفاءة الإدارية.",
        "ideal":   "ممتاز ≥ 15%  |  جيد 8–15%  |  ضعيف < 8%",
        "section": "الربحية والكفاءة",
    },
    "هامش_الأصول": {
        "name":    "العائد على الأصول  (ROA)",
        "formula": "صافي الربح ÷ إجمالي الأصول",
        "meaning": "يقيس كفاءة توظيف الأصول في تحقيق الأرباح بمعزل عن مصدر التمويل (ذاتي أو خارجي).",
        "ideal":   "ممتاز ≥ 10%  |  جيد 5–10%  |  ضعيف < 5%",
        "section": "الربحية والكفاءة",
    },
    "نسبة_التمويل_البنكي": {
        "name":    "نسبة التمويل البنكي",
        "formula": "التسهيلات البنكية ÷ إجمالي الأصول",
        "meaning": "تكشف اعتماد الشركة على البنوك في تمويل أصولها وما يترتب على ذلك من أعباء فوائد.",
        "ideal":   "محدود < 15%  |  معتدل 15–30%  |  مرتفع > 30%",
        "section": "الهيكل المالي والتمويل",
    },
}

# ══════════════════════════════════════════════════════
# اكتشاف الخط العربي الصحيح
# ══════════════════════════════════════════════════════

_FONT_R  = "Arabic"
_FONT_B  = "ArabicBold"
_loaded  = False

def _find_font(bold=False):
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir = os.getcwd()

    if bold:
        candidates = [
            os.path.join(script_dir, "Amiri-Bold.ttf"),
            "D:/python/balanceSheet/Amiri-Bold.ttf",
            "C:/python/balanceSheet/Amiri-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            os.path.join(script_dir, "Amiri-Regular.ttf"),
            "D:/python/balanceSheet/Amiri-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    else:
        candidates = [
            os.path.join(script_dir, "Amiri-Regular.ttf"),
            "D:/python/balanceSheet/Amiri-Regular.ttf",
            "C:/python/balanceSheet/Amiri-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]

    for c in candidates:
        if os.path.exists(c) and os.path.getsize(c) > 1000:
            return c
    return None

def load_fonts():
    global _loaded
    if _loaded:
        return True
    r = _find_font(bold=False)
    b = _find_font(bold=True)
    if not r:
        return False
    try:
        pdfmetrics.registerFont(TTFont(_FONT_R, r))
        pdfmetrics.registerFont(TTFont(_FONT_B, b if b else r))
        _loaded = True
        return True
    except Exception as e:
        st.error(f"❌ خطأ في تحميل الخط: {e}")
        return False

# ══════════════════════════════════════════════════════
# دوال التنسيق
# ══════════════════════════════════════════════════════

def ar(text):
    return get_display(arabic_reshaper.reshape(str(text)))

def fmt_num(v):
    if v is None or (isinstance(v, float) and (pd.isna(v) or v != v)):
        return "—"
    v = float(v)
    if abs(v) >= 1_000_000_000: return f"{v/1_000_000_000:.2f} مليار"
    if abs(v) >= 1_000_000:     return f"{v/1_000_000:.2f} مليون"
    return f"{v:,.0f}"

def fmt_full(v):
    try: return f"{float(v):,.0f}"
    except: return "0"

def fmt_pct(v):
    try: return f"{float(v)*100:.1f}%"
    except: return "—"

def fmt_ratio(v):
    try: return f"{float(v):.2f}x"
    except: return "—"

def period_label(col):
    m = {1:'يناير',2:'فبراير',3:'مارس',4:'أبريل',5:'مايو',6:'يونيو',
         7:'يوليو',8:'أغسطس',9:'سبتمبر',10:'أكتوبر',11:'نوفمبر',12:'ديسمبر'}
    try:
        d = pd.to_datetime(col)
        return f"{m[d.month]} {d.year}"
    except:
        return str(col)

def safe_get(df, item, col):
    try:
        mask = df['البند'].str.strip() == item.strip()
        v = df.loc[mask, col].values
        return float(v[0]) if len(v) and not pd.isna(v[0]) else 0.0
    except:
        return 0.0

def safe_div(a, b, d=4):
    try:
        a, b = float(a), float(b)
        return round(a / b, d) if b != 0 else 0.0
    except:
        return 0.0

# ══════════════════════════════════════════════════════
# التحقق من البيانات
# ══════════════════════════════════════════════════════

def validate(df, months):
    missing, warns = [], []
    actual = df['البند'].str.strip().tolist()
    for req in REQUIRED_ITEMS:
        if not any(req.strip() in a or a in req.strip() for a in actual):
            missing.append(req)
    for col in months:
        nz = df[col].replace(0, np.nan).dropna()
        if len(nz) == 0:
            warns.append(f"العمود '{period_label(col)}' فارغ أو يحتوي أصفاراً فقط")
    for col in months:
        ta  = safe_get(df, 'إجمالي الاصول', col)
        tel = safe_get(df, 'إجمالي حقوق اصحاب الحصص و الالتزامات', col)
        if ta > 0 and tel > 0:
            diff = abs(ta - tel) / ta * 100
            if diff > 2:
                warns.append(
                    f"الميزانية غير متوازنة في {period_label(col)}: "
                    f"الأصول={fmt_num(ta)} | ح.ملكية+التزامات={fmt_num(tel)} (فرق {diff:.1f}%)"
                )
    return missing, warns

# ══════════════════════════════════════════════════════
# حساب المؤشرات
# ══════════════════════════════════════════════════════

def calc_ratios(df, col):
    g = lambda i: safe_get(df, i, col)
    ca  = g('مجموع الأصول متداوله')
    cl  = g('مجموع الالتزامات المتداوله')
    ta  = g('إجمالي الاصول')
    eq  = g('مجموع حقوق اصحاب الحصص')
    np_ = g('صافي أرباح / خسائر الفتره')
    inv = g('المخزون')
    csh = g('النقديه و ما في حكمها')
    rec = g('العملاء و اوراق القبض')
    bnk = g('بنوك تسهيلات')
    nca = g('مجموع الأصول الغير متداوله')
    return {
        'الأصول_المتداولة':     ca,
        'الالتزامات_المتداولة': cl,
        'إجمالي_الأصول':        ta,
        'حقوق_الملكية':         eq,
        'صافي_الربح':           np_,
        'المخزون':               inv,
        'النقدية':               csh,
        'العملاء':               rec,
        'التسهيلات_البنكية':    bnk,
        'الأصول_الغير_متداولة': nca,
        'رأس_المال_العامل':      ca - cl,
        'نسبة_التداول':         safe_div(ca, cl),
        'النسبة_السريعة':       safe_div(ca - inv, cl),
        'نسبة_النقدية':         safe_div(csh, cl),
        'نسبة_الديون':          safe_div(cl, ta),
        'نسبة_حقوق_الملكية':   safe_div(eq, ta),
        'العائد_على_الملكية':   safe_div(np_, eq),
        'هامش_الأصول':          safe_div(np_, ta),
        'نسبة_التمويل_البنكي': safe_div(bnk, ta),
    }

# ══════════════════════════════════════════════════════
# التحليل النصي الكامل
# ══════════════════════════════════════════════════════

def build_analysis(r):
    g   = lambda k: float(r.get(k, 0) or 0)
    ca  = g('الأصول_المتداولة');   cl  = g('الالتزامات_المتداولة')
    ta  = g('إجمالي_الأصول');      eq  = g('حقوق_الملكية')
    np_ = g('صافي_الربح');          inv = g('المخزون')
    csh = g('النقدية');              rec = g('العملاء')
    bnk = g('التسهيلات_البنكية')
    cr  = g('نسبة_التداول');        qr  = g('النسبة_السريعة')
    nr  = g('نسبة_النقدية');        dr  = g('نسبة_الديون')
    er  = g('نسبة_حقوق_الملكية'); roe = g('العائد_على_الملكية')
    roa = g('هامش_الأصول');         br  = g('نسبة_التمويل_البنكي')
    wc  = g('رأس_المال_العامل')
    out = {}

    # ── 1. السيولة ──
    liq = []

    calc = f"{fmt_full(ca)} ÷ {fmt_full(cl)} = {fmt_ratio(cr)}"
    meaning = "تقيس قدرة الشركة على سداد الالتزامات قصيرة الأجل"
    if cr >= 2:
        liq.append(("نسبة_التداول", f"نسبة التداول: {fmt_ratio(cr)}", calc, meaning,
            "✅ ممتاز — السيولة قوية جداً، الشركة قادرة بيسر على تغطية كل التزاماتها قصيرة الأجل.", "good"))
    elif cr >= 1.5:
        liq.append(("نسبة_التداول", f"نسبة التداول: {fmt_ratio(cr)}", calc, meaning,
            "✅ جيد — السيولة مستقرة ضمن الحدود المقبولة.", "good"))
    elif cr >= 1:
        liq.append(("نسبة_التداول", f"نسبة التداول: {fmt_ratio(cr)}", calc, meaning,
            "⚠️ مقبول — يُنصح بتعزيز السيولة تحسباً لأي التزامات طارئة.", "warn"))
    else:
        liq.append(("نسبة_التداول", f"نسبة التداول: {fmt_ratio(cr)}", calc, meaning,
            "🔴 ضعيف — خطر عدم القدرة على سداد الالتزامات قصيرة الأجل!", "bad"))

    calc = f"({fmt_full(ca)} − {fmt_full(inv)}) ÷ {fmt_full(cl)} = {fmt_ratio(qr)}"
    meaning = "تستبعد المخزون وتقيس السيولة الفورية"
    if qr >= 1:
        liq.append(("النسبة_السريعة", f"النسبة السريعة: {fmt_ratio(qr)}", calc, meaning,
            "✅ ممتاز — سيولة فورية قوية دون الحاجة لبيع المخزون.", "good"))
    elif qr >= 0.7:
        liq.append(("النسبة_السريعة", f"النسبة السريعة: {fmt_ratio(qr)}", calc, meaning,
            "⚠️ مقبول — قدر من الاعتماد على المخزون لتغطية الالتزامات.", "warn"))
    else:
        liq.append(("النسبة_السريعة", f"النسبة السريعة: {fmt_ratio(qr)}", calc, meaning,
            "🔴 ضعيف — اعتماد كبير على المخزون ينطوي على مخاطرة مرتفعة.", "bad"))

    calc = f"{fmt_full(csh)} ÷ {fmt_full(cl)} = {fmt_ratio(nr)}"
    meaning = "النقد الجاهز مقارنةً بالالتزامات المتداولة"
    if nr >= 0.5:
        liq.append(("نسبة_النقدية", f"نسبة النقدية: {fmt_ratio(nr)}", calc, meaning,
            "✅ مريح — نقد كافٍ للسداد الفوري دون بيع أي أصل.", "good"))
    elif nr >= 0.2:
        liq.append(("نسبة_النقدية", f"نسبة النقدية: {fmt_ratio(nr)}", calc, meaning,
            "⚠️ معتدل — النقد متاح بحد معقول.", "warn"))
    else:
        liq.append(("نسبة_النقدية", f"نسبة النقدية: {fmt_ratio(nr)}", calc, meaning,
            "🔴 منخفض — شُح النقد قد يُعيق السداد الفوري.", "bad"))

    calc = f"{fmt_full(ca)} − {fmt_full(cl)} = {fmt_num(wc)}"
    if wc > 0:
        liq.append((None, f"رأس المال العامل: {fmt_num(wc)}", calc,
            "هامش الأمان التشغيلي",
            "✅ إيجابي — الشركة لديها هامش أمان تشغيلي كافٍ.", "good"))
    else:
        liq.append((None, f"رأس المال العامل: {fmt_num(wc)}", calc,
            "هامش الأمان التشغيلي",
            "🔴 سلبي — ضغط تشغيلي يستوجب المعالجة.", "bad"))
    out["السيولة والملاءة المالية"] = liq

    # ── 2. الهيكل المالي ──
    fin = []

    calc = f"{fmt_full(cl)} ÷ {fmt_full(ta)} = {fmt_pct(dr)}"
    meaning = "نسبة الأصول الممولة بالديون — كلما انخفضت كان أفضل"
    if dr <= 0.4:
        fin.append(("نسبة_الديون", f"نسبة الديون: {fmt_pct(dr)}", calc, meaning,
            "✅ آمن — هيكل مالي محافظ يعتمد أساساً على التمويل الذاتي.", "good"))
    elif dr <= 0.6:
        fin.append(("نسبة_الديون", f"نسبة الديون: {fmt_pct(dr)}", calc, meaning,
            "⚠️ معتدل — ضمن الحدود المقبولة مع وجوب المتابعة.", "warn"))
    else:
        fin.append(("نسبة_الديون", f"نسبة الديون: {fmt_pct(dr)}", calc, meaning,
            "🔴 مرتفع — مخاطر مالية متصاعدة تستوجب إعادة الهيكلة.", "bad"))

    calc = f"{fmt_full(eq)} ÷ {fmt_full(ta)} = {fmt_pct(er)}"
    meaning = "نسبة الأصول الممولة ذاتياً من أموال الملاك"
    if er >= 0.6:
        fin.append(("نسبة_حقوق_الملكية", f"نسبة حقوق الملكية: {fmt_pct(er)}", calc, meaning,
            "✅ قوي — استقلالية مالية مرتفعة.", "good"))
    elif er >= 0.4:
        fin.append(("نسبة_حقوق_الملكية", f"نسبة حقوق الملكية: {fmt_pct(er)}", calc, meaning,
            "⚠️ معتدل — مزيج من التمويل الذاتي والخارجي.", "warn"))
    else:
        fin.append(("نسبة_حقوق_الملكية", f"نسبة حقوق الملكية: {fmt_pct(er)}", calc, meaning,
            "🔴 منخفض — اعتماد مفرط على تمويل الغير.", "bad"))

    calc = f"{fmt_full(bnk)} ÷ {fmt_full(ta)} = {fmt_pct(br)}"
    meaning = "اعتماد الشركة على البنوك في تمويل أصولها"
    if br <= 0.15:
        fin.append(("نسبة_التمويل_البنكي", f"نسبة التمويل البنكي: {fmt_pct(br)}", calc, meaning,
            "✅ محدود — أعباء الفائدة منخفضة ومؤشر إيجابي.", "good"))
    elif br <= 0.3:
        fin.append(("نسبة_التمويل_البنكي", f"نسبة التمويل البنكي: {fmt_pct(br)}", calc, meaning,
            "⚠️ معتدل — يُستحسن مراقبة أعباء الفائدة.", "warn"))
    else:
        fin.append(("نسبة_التمويل_البنكي", f"نسبة التمويل البنكي: {fmt_pct(br)}", calc, meaning,
            "🔴 مرتفع — أعباء الفائدة تُثقل الهيكل المالي.", "bad"))
    out["الهيكل المالي والتمويل"] = fin

    # ── 3. الربحية ──
    prof = []
    if np_ > 0:
        calc = f"{fmt_full(np_)} ÷ {fmt_full(eq)} = {fmt_pct(roe)}"
        meaning = "كفاءة توليد الأرباح من أموال المساهمين"
        if roe >= 0.15:
            prof.append(("العائد_على_الملكية", f"العائد على الملكية ROE: {fmt_pct(roe)}", calc, meaning,
                "✅ ممتاز — كفاءة إدارية عالية جداً في توليد الأرباح.", "good"))
        elif roe >= 0.08:
            prof.append(("العائد_على_الملكية", f"العائد على الملكية ROE: {fmt_pct(roe)}", calc, meaning,
                "✅ جيد — أداء ربحي مقبول.", "good"))
        else:
            prof.append(("العائد_على_الملكية", f"العائد على الملكية ROE: {fmt_pct(roe)}", calc, meaning,
                "⚠️ ضعيف — كفاءة استخدام حقوق الملكية تحتاج تحسيناً.", "warn"))

        calc = f"{fmt_full(np_)} ÷ {fmt_full(ta)} = {fmt_pct(roa)}"
        meaning = "كفاءة توظيف الأصول في تحقيق الأرباح"
        if roa >= 0.10:
            prof.append(("هامش_الأصول", f"العائد على الأصول ROA: {fmt_pct(roa)}", calc, meaning,
                "✅ ممتاز — الأصول تُولّد عائداً مرتفعاً.", "good"))
        elif roa >= 0.05:
            prof.append(("هامش_الأصول", f"العائد على الأصول ROA: {fmt_pct(roa)}", calc, meaning,
                "✅ جيد — الأصول تُستخدم بكفاءة معقولة.", "good"))
        else:
            prof.append(("هامش_الأصول", f"العائد على الأصول ROA: {fmt_pct(roa)}", calc, meaning,
                "⚠️ منخفض — كفاءة توظيف الأصول تحتاج مراجعة.", "warn"))
    else:
        prof.append((None,
            f"نتيجة الفترة: خسارة ({fmt_num(abs(np_))})", "—",
            "الشركة تحقق خسائر في هذه الفترة",
            "🔴 عاجل — يتطلب خطة تصحيحية فورية لوقف النزيف المالي.", "bad"))
        prof.append((None,
            f"ROE: {fmt_pct(roe)}  |  ROA: {fmt_pct(roa)}", "—",
            "كلا المؤشرين سلبيان بسبب الخسارة",
            "🔴 أولوية قصوى لاستعادة الربحية.", "bad"))
    out["الربحية والكفاءة"] = prof

    # ── 4. التشغيل ──
    ops = []
    if ta > 0:
        rp = rec / ta
        calc = f"{fmt_full(rec)} ÷ {fmt_full(ta)} = {fmt_pct(rp)}"
        meaning = "حجم ديون العملاء مقارنةً بإجمالي الأصول"
        if rp > 0.40:
            ops.append((None, f"أرصدة العملاء: {fmt_num(rec)} ({fmt_pct(rp)} من الأصول)", calc, meaning,
                "🔴 مرتفع جداً — ضرورة تسريع التحصيل وتقليل فترة الائتمان.", "bad"))
        elif rp > 0.25:
            ops.append((None, f"أرصدة العملاء: {fmt_num(rec)} ({fmt_pct(rp)} من الأصول)", calc, meaning,
                "⚠️ معتدل — متابعة دورية مستمرة للتحصيل.", "warn"))
        else:
            ops.append((None, f"أرصدة العملاء: {fmt_num(rec)} ({fmt_pct(rp)} من الأصول)", calc, meaning,
                "✅ جيد — ضمن الحدود المعقولة.", "good"))

        ip = inv / ta
        calc = f"{fmt_full(inv)} ÷ {fmt_full(ta)} = {fmt_pct(ip)}"
        meaning = "حجم المخزون مقارنةً بإجمالي الأصول"
        if ip > 0.30:
            ops.append((None, f"المخزون: {fmt_num(inv)} ({fmt_pct(ip)} من الأصول)", calc, meaning,
                "🔴 مرتفع — مراجعة سياسة الشراء وتحسين دوران المخزون.", "bad"))
        elif ip > 0.15:
            ops.append((None, f"المخزون: {fmt_num(inv)} ({fmt_pct(ip)} من الأصول)", calc, meaning,
                "⚠️ معتدل — متابعة معدل الدوران.", "warn"))
        else:
            ops.append((None, f"المخزون: {fmt_num(inv)} ({fmt_pct(ip)} من الأصول)", calc, meaning,
                "✅ ضمن المستوى الطبيعي.", "good"))
    out["المؤشرات التشغيلية"] = ops

    # ── 5. التوصيات ──
    rec_l = []
    if cr < 1.5:
        rec_l.append((None, "تعزيز السيولة", "—",
            "تسريع تحصيل الديون أو تحويل جزء من التمويل قصير الأجل إلى طويل الأجل.",
            "يُنصح بمراجعة سياسة الائتمان وتحسين دورة التحصيل.", "bad"))
    if dr > 0.6:
        rec_l.append((None, "إعادة هيكلة الديون", "—",
            "تحويل الالتزامات قصيرة الأجل إلى طويلة لتخفيف الضغط المالي.",
            "التفاوض مع الجهات التمويلية لإعادة جدولة القروض.", "bad"))
    if br > 0.3:
        rec_l.append((None, "تنويع مصادر التمويل", "—",
            "تقليل الاعتماد على التسهيلات البنكية لخفض أعباء الفائدة.",
            "دراسة البدائل كإصدار صكوك أو رفع رأس المال.", "bad"))
    if np_ < 0:
        rec_l.append((None, "خطة إنقاذ تشغيلية عاجلة", "—",
            "مراجعة هيكل التكاليف ورفع الإيرادات لتحقيق التعادل ثم الربح.",
            "🔴 أولوية قصوى لوقف النزيف المالي فوراً.", "bad"))
    elif roe < 0.08:
        rec_l.append((None, "تحسين كفاءة التشغيل", "—",
            "مراجعة هامش الربح للوصول إلى معدل ROE ≥ 8%.",
            "تفعيل برامج خفض التكاليف ورفع الإنتاجية.", "warn"))
    if ta > 0 and rec / ta > 0.35:
        rec_l.append((None, "تشديد سياسة الائتمان", "—",
            "تطبيق سياسة ائتمان أكثر صرامة وتقليل فترات السماح الممنوحة للعملاء.",
            "مراجعة عقود العملاء وتطبيق غرامات التأخير.", "warn"))
    if ta > 0 and inv / ta > 0.25:
        rec_l.append((None, "تحسين إدارة المخزون", "—",
            "تقليل رأس المال المحتجز في المخزون باستخدام تقنيات JIT.",
            "مراجعة دورية لمعدل دوران المخزون وتصفية الراكد.", "warn"))
    if not rec_l:
        rec_l.append((None, "الوضع المالي مستقر ومشجع", "—",
            "جميع المؤشرات ضمن النطاق المقبول أو أفضل منه.",
            "✅ يُنصح بالتوسع الحذر مع المحافظة على السياسات الحالية.", "good"))
    out["التوصيات"] = rec_l

    return out

# ══════════════════════════════════════════════════════
# الرسوم البيانية
# ══════════════════════════════════════════════════════

def draw_charts(rdf, lbls):
    BL,GR,RD,AM,PU = '#2d7dd2','#27ae60','#c0392b','#f39c12','#8e44ad'

    st.markdown('<div class="sec-hdr">📈 اتجاه نسب السيولة</div>', unsafe_allow_html=True)
    fig = go.Figure()
    for col, nm, clr in [('نسبة_التداول','نسبة التداول',BL),
                          ('النسبة_السريعة','النسبة السريعة',GR),
                          ('نسبة_النقدية','نسبة النقدية',AM)]:
        fig.add_trace(go.Scatter(x=lbls, y=rdf[col], name=nm,
            mode='lines+markers', line=dict(color=clr,width=3), marker=dict(size=9)))
    fig.add_hline(y=2,line_dash='dash',line_color='green',annotation_text='مثالي 2x',annotation_position='left')
    fig.add_hline(y=1,line_dash='dash',line_color='red',  annotation_text='حد أدنى 1x',annotation_position='left')
    fig.update_layout(template='plotly_white',height=360,
        legend=dict(orientation='h',y=-0.25),yaxis_title='النسبة',xaxis_title='الفترة')
    st.plotly_chart(fig, use_container_width=True)

    c1,c2 = st.columns(2)
    with c1:
        st.markdown('<div class="sec-hdr">💰 صافي الربح / الخسارة</div>', unsafe_allow_html=True)
        clrs = [GR if v>=0 else RD for v in rdf['صافي_الربح']]
        fig2 = go.Figure(go.Bar(x=lbls,y=rdf['صافي_الربح'],marker_color=clrs,
            text=[fmt_num(v) for v in rdf['صافي_الربح']],textposition='auto'))
        fig2.update_layout(template='plotly_white',height=310,yaxis_title='القيمة')
        st.plotly_chart(fig2,use_container_width=True)
    with c2:
        st.markdown('<div class="sec-hdr">🏛 هيكل التمويل (آخر فترة)</div>', unsafe_allow_html=True)
        last = rdf.iloc[-1]
        fig3 = go.Figure(go.Pie(
            labels=['الالتزامات','حقوق الملكية'],
            values=[max(float(last['الالتزامات_المتداولة']),0),max(float(last['حقوق_الملكية']),0)],
            marker=dict(colors=[RD,GR]),hole=0.42))
        fig3.update_layout(template='plotly_white',height=310,legend=dict(orientation='h',y=-0.2))
        st.plotly_chart(fig3,use_container_width=True)

    c3,c4 = st.columns(2)
    with c3:
        st.markdown('<div class="sec-hdr">📉 العائد على الملكية ROE</div>', unsafe_allow_html=True)
        roe_v = [float(v)*100 for v in rdf['العائد_على_الملكية']]
        clrs2 = [GR if v>=10 else AM if v>=5 else RD for v in roe_v]
        fig4 = go.Figure(go.Bar(x=lbls,y=roe_v,marker_color=clrs2,
            text=[f"{v:.1f}%" for v in roe_v],textposition='auto'))
        fig4.add_hline(y=10,line_dash='dash',line_color='green',annotation_text='هدف 10%')
        fig4.update_layout(template='plotly_white',height=300,yaxis_title='%')
        st.plotly_chart(fig4,use_container_width=True)
    with c4:
        st.markdown('<div class="sec-hdr">📦 العملاء والمخزون</div>', unsafe_allow_html=True)
        fig5 = go.Figure()
        fig5.add_trace(go.Bar(x=lbls,y=rdf['العملاء'], name='العملاء', marker_color=BL))
        fig5.add_trace(go.Bar(x=lbls,y=rdf['المخزون'],name='المخزون',marker_color=AM))
        fig5.update_layout(template='plotly_white',height=300,barmode='group',
            legend=dict(orientation='h',y=-0.3))
        st.plotly_chart(fig5,use_container_width=True)

    st.markdown('<div class="sec-hdr">📊 نمو إجمالي الأصول</div>', unsafe_allow_html=True)
    fig6 = go.Figure(go.Scatter(x=lbls,y=rdf['إجمالي_الأصول'],
        fill='tozeroy',mode='lines+markers',line=dict(color=PU,width=3),marker=dict(size=9),
        text=[fmt_num(v) for v in rdf['إجمالي_الأصول']],textposition='top center'))
    fig6.update_layout(template='plotly_white',height=290,yaxis_title='القيمة')
    st.plotly_chart(fig6,use_container_width=True)

# ══════════════════════════════════════════════════════
# عرض التحليل المدمج (شرح + تحليل معاً) في الواجهة
# ══════════════════════════════════════════════════════

def render_merged_analysis_item(ratio_key, title, calc, meaning, taqeem, level):
    """
    عرض بطاقة مدمجة: إذا كان ratio_key موجوداً يعرض التعريف + المعيار أولاً
    ثم طريقة الحساب + التقييم.
    """
    css = {"good": "ab-good", "warn": "ab-warn", "bad": "ab-bad"}.get(level, "ab-warn")
    d = RATIO_DEFS.get(ratio_key)

    if d:
        # بطاقة مدمجة: تعريف + شرح + حساب + تقييم
        st.markdown(f"""
        <div class="ratio-group">
            <div class="ratio-group-header">📊 {d['name']}</div>
            <div class="ratio-group-body">
                <div class="def-box">
                    🔢 <strong>طريقة الحساب النظرية:</strong> {d['formula']}<br>
                    📌 <strong>المعنى:</strong> {d['meaning']}<br>
                    🎯 <strong>المعيار المرجعي:</strong> {d['ideal']}
                </div>
                <div class="abox {css}" style="margin-top:6px">
                    <strong style="font-size:.97rem">{title}</strong>
                    <div style="margin-top:5px;font-size:.87rem">📐 <strong>الحساب الفعلي:</strong> {calc}</div>
                    <div style="margin-top:3px;font-size:.87rem">📌 {meaning}</div>
                    <div style="margin-top:3px;font-size:.87rem">🎯 {taqeem}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # بطاقة عادية بدون تعريف (رأس المال العامل، التوصيات، إلخ)
        st.markdown(f"""
        <div class="abox {css}">
            <strong style="font-size:.97rem">{title}</strong>
            <div style="margin-top:5px;font-size:.87rem">📐 <strong>الحساب:</strong> {calc}</div>
            <div style="margin-top:3px;font-size:.87rem">📌 {meaning}</div>
            <div style="margin-top:3px;font-size:.87rem">🎯 {taqeem}</div>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# PDF باللغة العربية — A4 مضبوط مع فواصل
# ══════════════════════════════════════════════════════

# عرض الصفحة A4 = 595pt ، هوامش 40+30 = 70pt => صافي العرض = 525pt
PAGE_W   = A4[0]          # 595.27 pt
L_MARGIN = 30
R_MARGIN = 40
CONTENT_W = PAGE_W - L_MARGIN - R_MARGIN   # ~525 pt

def _ps(nm,sz=10,bold=False,align=TA_RIGHT,clr=colors.black,lead=None,sb=4,sa=4):
    if lead is None:
        lead = sz * 1.6
    return ParagraphStyle(nm,
        fontName=_FONT_B if bold else _FONT_R,
        fontSize=sz, alignment=align, leading=lead,
        textColor=clr, spaceBefore=sb, spaceAfter=sa,
        wordWrap='RTL')

def _section_divider():
    """فاصل أنيق بين الأقسام"""
    return [
        Spacer(1, 8),
        HRFlowable(width=CONTENT_W, thickness=1.5,
                   color=colors.HexColor('#2d7dd2'),
                   spaceAfter=8, spaceBefore=4),
    ]

def _section_title(text, style):
    """عنوان قسم داخل مستطيل ملون"""
    p = Paragraph(ar(text), style)
    t = Table([[p]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,-1), colors.HexColor('#0d2137')),
        ('TOPPADDING', (0,0),(-1,-1), 7),
        ('BOTTOMPADDING', (0,0),(-1,-1), 7),
        ('LEFTPADDING', (0,0),(-1,-1), 12),
        ('RIGHTPADDING', (0,0),(-1,-1), 12),
    ]))
    return t

def _subsection_title(text, style):
    """عنوان قسم فرعي بخلفية فاتحة"""
    p = Paragraph(ar(text), style)
    t = Table([[p]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,-1), colors.HexColor('#1a4a7a')),
        ('TOPPADDING', (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING', (0,0),(-1,-1), 10),
        ('RIGHTPADDING', (0,0),(-1,-1), 10),
    ]))
    return t

def alert_block_pdf(lines, level, styles):
    """كتلة ملونة في PDF مع ضبط العرض لـ A4"""
    BG = {'good': colors.HexColor('#eafaf1'),
          'warn': colors.HexColor('#fef9e7'),
          'bad':  colors.HexColor('#fdedec')}
    BD = {'good': colors.HexColor('#27ae60'),
          'warn': colors.HexColor('#f39c12'),
          'bad':  colors.HexColor('#c0392b')}
    bg = BG.get(level, colors.HexColor('#f4f8fd'))
    bd = BD.get(level, colors.HexColor('#2d7dd2'))

    cell_els = []
    S_BODY, S_SM = styles
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        sty = _ps(f'al_{i}_{id(line)}', 10 if i==0 else 9,
                  bold=(i==0), align=TA_RIGHT,
                  clr=colors.HexColor('#1a2f45'),
                  lead=18 if i>0 else 20)
        cell_els.append(Paragraph(ar(line), sty))
        if i < len(lines)-1:
            cell_els.append(Spacer(1, 2))

    t = Table([cell_els], colWidths=[CONTENT_W - 20])
    t.setStyle(TableStyle([
        ('BACKGROUND',   (0,0),(-1,-1), bg),
        ('LINEAFTER',    (0,0),(-1,-1), 5, bd),
        ('TOPPADDING',   (0,0),(-1,-1), 7),
        ('BOTTOMPADDING',(0,0),(-1,-1), 7),
        ('LEFTPADDING',  (0,0),(-1,-1), 10),
        ('RIGHTPADDING', (0,0),(-1,-1), 10),
    ]))
    return t

def def_block_pdf(d, styles):
    """كتلة تعريف النسبة في PDF"""
    S_BODY, S_SM = styles
    p = Paragraph(ar(
        f"🔢 طريقة الحساب: {d['formula']}   |   "
        f"📌 المعنى: {d['meaning']}   |   "
        f"🎯 المعيار: {d['ideal']}"
    ), S_SM)
    t = Table([[p]], colWidths=[CONTENT_W - 20])
    t.setStyle(TableStyle([
        ('BACKGROUND',   (0,0),(-1,-1), colors.HexColor('#eaf0fb')),
        ('LINEAFTER',    (0,0),(-1,-1), 4, colors.HexColor('#2d7dd2')),
        ('TOPPADDING',   (0,0),(-1,-1), 6),
        ('BOTTOMPADDING',(0,0),(-1,-1), 6),
        ('LEFTPADDING',  (0,0),(-1,-1), 10),
        ('RIGHTPADDING', (0,0),(-1,-1), 10),
    ]))
    return t

def build_pdf(ratios_list, months, labels):
    if not load_fonts():
        return None

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        rightMargin=R_MARGIN, leftMargin=L_MARGIN,
        topMargin=35, bottomMargin=30)

    # ── أنماط النصوص ──
    S_TTL  = _ps('ttl', 20, True,  TA_CENTER, colors.HexColor('#0d2137'), 30,  0, 10)
    S_SUB  = _ps('sub', 10, False, TA_CENTER, colors.HexColor('#555555'), 17,  2,  8)
    S_H1   = _ps('h1',  13, True,  TA_RIGHT,  colors.white,               26, 12,  4)
    S_H2   = _ps('h2',  11, True,  TA_RIGHT,  colors.white,               20,  6,  3)
    S_H3   = _ps('h3',  11, True,  TA_RIGHT,  colors.HexColor('#0d2137'), 20,  8,  3)
    S_BODY = _ps('bd',  10, False, TA_RIGHT,  colors.HexColor('#222222'), 20)
    S_SM   = _ps('sm',   9, False, TA_RIGHT,  colors.HexColor('#333333'), 18)
    S_CTR  = _ps('ct',   9, False, TA_CENTER, colors.HexColor('#666666'), 16)
    STYLES = (S_BODY, S_SM)

    el = []

    # ══════════════════════════════════════════════
    # الغلاف
    # ══════════════════════════════════════════════
    el += [
        Spacer(1, 30),
        Paragraph(ar("التقرير المالي الشامل"), S_TTL),
        Spacer(1, 6),
        Paragraph(ar("تحليل القوائم المالية — نسب ومؤشرات وتوصيات"), S_SUB),
        Paragraph(ar(f"الفترة: {labels[0]} — {labels[-1]}" if len(labels)>1 else labels[0]), S_SUB),
    ]
    el += _section_divider()

    # ══════════════════════════════════════════════
    # القسم الأول: ملخص المؤشرات
    # ══════════════════════════════════════════════
    el.append(Spacer(1, 6))
    el.append(_section_title("أولاً: ملخص المؤشرات المالية", S_H1))
    el.append(Spacer(1, 8))

    hdr  = [ar("المؤشر")] + [ar(lb) for lb in labels]
    rows = [hdr]
    INDICS = [
        ("نسبة_التداول",        "نسبة التداول",        fmt_ratio),
        ("النسبة_السريعة",      "النسبة السريعة",       fmt_ratio),
        ("نسبة_النقدية",        "نسبة النقدية",         fmt_ratio),
        ("نسبة_الديون",         "نسبة الديون",          fmt_pct),
        ("نسبة_حقوق_الملكية",  "نسبة حقوق الملكية",    fmt_pct),
        ("العائد_على_الملكية",  "ROE",                  fmt_pct),
        ("هامش_الأصول",         "ROA",                  fmt_pct),
        ("نسبة_التمويل_البنكي", "التمويل البنكي",        fmt_pct),
        ("إجمالي_الأصول",       "إجمالي الأصول",        fmt_num),
        ("صافي_الربح",          "صافي الربح / الخسارة", fmt_num),
        ("النقدية",             "النقدية",               fmt_num),
        ("العملاء",             "أرصدة العملاء",         fmt_num),
        ("المخزون",             "المخزون",               fmt_num),
        ("التسهيلات_البنكية",   "التسهيلات البنكية",     fmt_num),
        ("رأس_المال_العامل",    "رأس المال العامل",      fmt_num),
    ]
    for key, lbl, fmtr in INDICS:
        rows.append([ar(lbl)] + [ar(fmtr(r.get(key, 0))) for r in ratios_list])

    n  = len(labels)
    cw = [int(CONTENT_W * 0.40)] + [int(CONTENT_W * 0.60 / n)] * n

    tbl = Table(rows, colWidths=cw, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND',     (0,0), (-1,0),  colors.HexColor('#0d2137')),
        ('TEXTCOLOR',      (0,0), (-1,0),  colors.white),
        ('FONTNAME',       (0,0), (-1,-1), _FONT_R),
        ('FONTSIZE',       (0,0), (-1,0),  10),
        ('FONTSIZE',       (0,1), (-1,-1), 9),
        ('ALIGN',          (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',         (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f4f8fd'), colors.white]),
        ('GRID',           (0,0), (-1,-1), 0.4, colors.HexColor('#c5d3e0')),
        ('ROWHEIGHT',      (0,0), (-1,-1), 22),
        ('TOPPADDING',     (0,0), (-1,-1), 4),
        ('BOTTOMPADDING',  (0,0), (-1,-1), 4),
    ]))
    el.append(tbl)
    el += _section_divider()

    # ══════════════════════════════════════════════
    # القسم الثاني: التحليل التفصيلي المدمج لكل فترة
    # (شرح النسبة + طريقة الحساب + التقييم معاً)
    # ══════════════════════════════════════════════
    el.append(PageBreak())
    el.append(_section_title("ثانياً: التحليل التفصيلي المدمج لكل فترة", S_H1))
    el.append(Spacer(1, 6))
    el.append(Paragraph(ar(
        "يعرض هذا القسم لكل نسبة: تعريفها ومعناها أولاً، ثم القيمة المحسوبة من بيانات الشركة مع التقييم المباشر."
    ), S_SM))
    el.append(Spacer(1, 10))

    for r_idx, (r, lb) in enumerate(zip(ratios_list, labels)):
        if r_idx > 0:
            el.append(PageBreak())

        # عنوان الفترة
        period_p = Paragraph(ar(f"◈ الفترة: {lb}"),
            _ps(f'ph_{r_idx}', 13, True, TA_RIGHT, colors.HexColor('#1a4a7a'), 24, 10, 4))
        period_t = Table([[period_p]], colWidths=[CONTENT_W])
        period_t.setStyle(TableStyle([
            ('BACKGROUND', (0,0),(-1,-1), colors.HexColor('#ddeeff')),
            ('TOPPADDING', (0,0),(-1,-1), 8),
            ('BOTTOMPADDING', (0,0),(-1,-1), 8),
            ('LEFTPADDING', (0,0),(-1,-1), 12),
            ('RIGHTPADDING', (0,0),(-1,-1), 12),
            ('LINEBELOW', (0,0),(-1,-1), 2, colors.HexColor('#2d7dd2')),
        ]))
        el.append(period_t)
        el.append(Spacer(1, 10))

        analysis = build_analysis(r)

        for sec_name, items in analysis.items():
            if not items:
                continue

            # عنوان القسم
            el.append(_subsection_title(f"■ {sec_name}", S_H2))
            el.append(Spacer(1, 5))

            for (ratio_key, title, calc, meaning, taqeem, level) in items:
                d = RATIO_DEFS.get(ratio_key) if ratio_key else None
                group_els = []

                # تعريف النسبة إذا وُجد
                if d:
                    group_els.append(def_block_pdf(d, STYLES))
                    group_els.append(Spacer(1, 3))

                # كتلة التحليل
                lines = [title, f"📐 الحساب: {calc}", f"📌 {meaning}", f"🎯 {taqeem}"]
                group_els.append(alert_block_pdf(lines, level, STYLES))
                group_els.append(Spacer(1, 5))

                el.append(KeepTogether(group_els))

            el += _section_divider()

    # ══════════════════════════════════════════════
    # القسم الثالث: دليل المؤشرات المرجعية
    # ══════════════════════════════════════════════
    el.append(PageBreak())
    el.append(_section_title("ثالثاً: دليل المؤشرات المرجعية", S_H1))
    el.append(Spacer(1, 8))

    prev_section = None
    for key, d in RATIO_DEFS.items():
        if d.get('section') != prev_section:
            prev_section = d.get('section')
            if prev_section:
                el.append(Spacer(1, 6))
                el.append(_subsection_title(f"● {prev_section}", S_H2))
                el.append(Spacer(1, 5))

        name_p = Paragraph(ar(f"◆ {d['name']}"),
            _ps(f'dn_{key}', 11, True, TA_RIGHT, colors.HexColor('#0d2137'), 20, 6, 2))

        rows_def = [
            [ar("طريقة الحساب"), ar(d['formula'])],
            [ar("المعنى"),        ar(d['meaning'])],
            [ar("المعيار"),       ar(d['ideal'])],
        ]
        def_tbl = Table(rows_def, colWidths=[int(CONTENT_W*0.22), int(CONTENT_W*0.78)])
        def_tbl.setStyle(TableStyle([
            ('FONTNAME',    (0,0),(-1,-1), _FONT_R),
            ('FONTSIZE',    (0,0),(-1,-1), 9),
            ('ALIGN',       (0,0),(-1,-1), 'RIGHT'),
            ('VALIGN',      (0,0),(-1,-1), 'TOP'),
            ('TEXTCOLOR',   (0,0),(0,-1),  colors.HexColor('#1a4a7a')),
            ('FONTNAME',    (0,0),(0,-1),  _FONT_B),
            ('BACKGROUND',  (0,0),(0,-1),  colors.HexColor('#eaf0fb')),
            ('BACKGROUND',  (1,0),(1,-1),  colors.HexColor('#f9fbfe')),
            ('GRID',        (0,0),(-1,-1), 0.3, colors.HexColor('#c5d3e0')),
            ('TOPPADDING',  (0,0),(-1,-1), 4),
            ('BOTTOMPADDING',(0,0),(-1,-1), 4),
            ('LEFTPADDING', (0,0),(-1,-1), 8),
            ('RIGHTPADDING',(0,0),(-1,-1), 8),
        ]))
        el.append(KeepTogether([name_p, def_tbl, Spacer(1, 8)]))

    el += _section_divider()

    # ══════════════════════════════════════════════
    # تذييل الصفحة
    # ══════════════════════════════════════════════
    el += [
        Spacer(1, 16),
        HRFlowable(width=CONTENT_W, thickness=1,
                   color=colors.HexColor('#c5d3e0'), spaceAfter=8),
        Paragraph(ar("أُعدّ هذا التقرير بواسطة نظام التحليل المالي الآلي"), S_CTR),
        Paragraph(ar("جميع النسب محسوبة من البيانات المدخلة — يُنصح بمراجعة محاسب قانوني قبل اتخاذ القرارات"), S_CTR),
    ]

    doc.build(el)
    buf.seek(0)
    return buf

# ══════════════════════════════════════════════════════
# مساعدات الواجهة
# ══════════════════════════════════════════════════════

def sts(key, val):
    if key == 'نسبة_الديون':
        return "kpi-good" if val<=0.4 else "kpi-warn" if val<=0.6 else "kpi-bad"
    rules = {
        'نسبة_التداول':       [(2,"kpi-good"),(1.5,"kpi-warn")],
        'النسبة_السريعة':     [(1,"kpi-good"),(0.7,"kpi-warn")],
        'نسبة_النقدية':       [(0.5,"kpi-good"),(0.2,"kpi-warn")],
        'العائد_على_الملكية': [(0.15,"kpi-good"),(0.08,"kpi-warn")],
        'هامش_الأصول':        [(0.10,"kpi-good"),(0.05,"kpi-warn")],
    }
    if key in ('صافي_الربح','رأس_المال_العامل'):
        return "kpi-good" if val>=0 else "kpi-bad"
    if key not in rules: return "kpi-blue"
    for thr,cls in rules[key]:
        if val>=thr: return cls
    return "kpi-bad"

def kpi_html(label, val, fmt, key="", calc=""):
    if fmt=="ratio": disp=fmt_ratio(val)
    elif fmt=="pct": disp=fmt_pct(val)
    elif fmt=="num": disp=fmt_num(val)
    else: disp=str(val)
    cls = sts(key, val)
    ch = f'<div class="kpi-calc">{calc}</div>' if calc else ""
    return (f'<div class="kpi-card {cls}">'
            f'<div class="kpi-val">{disp}</div>'
            f'<div class="kpi-lbl">{label}</div>{ch}</div>')

def kpi_row(r, items):
    html = '<div class="kpi-grid">'
    for key, lbl, fmt, cfn in items:
        calc = cfn(r) if cfn else ""
        html += kpi_html(lbl, float(r.get(key, 0)), fmt, key, calc)
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# الواجهة الرئيسية
# ══════════════════════════════════════════════════════

st.markdown("""
<div class="app-header">
    <h1>📊 نظام تحليل القوائم المالية</h1>
    <p>تحليل شامل · نسب مالية · رسوم بيانية · تقرير PDF بالعربية</p>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="sec-hdr">📂 تحميل البيانات</div>', unsafe_allow_html=True)

AUTO_FILE = "5-2026.xlsx"

try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
except:
    script_dir = os.getcwd()

auto_path = os.path.join(script_dir, AUTO_FILE)

if "force_upload" not in st.session_state:
    st.session_state.force_upload = False

uploaded = None

col1, col2, col3 = st.columns([1,2,1])
with col2:
    if st.button("⬆ رفع ملف جديد", use_container_width=True):
        st.session_state.force_upload = True
        st.rerun()

if os.path.exists(auto_path) and not st.session_state.force_upload:
    st.success(f"✅ تم تحميل الملف تلقائياً: {AUTO_FILE}")
    with open(auto_path, "rb") as f:
        uploaded = BytesIO(f.read())
else:
    st.info("يمكن رفع ملف جديد وسيتم استبداله تلقائياً")
    new_file = st.file_uploader("اختر ملف Excel", type=["xlsx", "xls"])
    if new_file:
        save_path = os.path.join(script_dir, AUTO_FILE)
        with open(save_path, "wb") as f:
            f.write(new_file.getbuffer())
        uploaded = BytesIO(new_file.getvalue())
        st.session_state.force_upload = False
        st.success("✅ تم حفظ الملف الجديد واستبداله تلقائياً")

if not uploaded:
    st.markdown("""
    <div style="background:#f4f8fd;border-radius:12px;padding:20px;text-align:center">
    <h3>إدارة الملفات</h3>
    <p>• يتم تحميل 4-2026.xlsx تلقائياً إذا كان موجوداً</p>
    <p>• يمكنك حذفه أو استبداله بملف جديد</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# قراءة الملف
try:
    df = pd.read_excel(uploaded)
    df.columns = df.columns.astype(str)
    df.rename(columns={df.columns[0]:'البند'}, inplace=True)
    df['البند'] = df['البند'].fillna('').astype(str).str.strip()
    df = df[df['البند'] != '']
    months = list(df.columns[1:])
    for col in months:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
except Exception as e:
    st.error(f"❌ خطأ في قراءة الملف: {e}")
    st.stop()

labels = [period_label(m) for m in months]

# التحقق من البيانات
st.markdown('<div class="sec-hdr">🔎 التحقق من اكتمال البيانات</div>', unsafe_allow_html=True)
missing, warns = validate(df, months)
for w in warns:
    st.markdown(f'<div class="abox ab-warn">⚠️ {w}</div>', unsafe_allow_html=True)
if missing:
    ih = "".join(f"<li>{m}</li>" for m in missing)
    st.markdown(
        f'<div class="abox ab-warn"><strong>⚠️ البنود التالية غير موجودة ({len(missing)}):</strong>'
        f'<ul style="margin:5px 0 0;padding-right:18px">{ih}</ul>'
        f'<em>تحقق من تطابق أسماء البنود في الملف</em></div>',
        unsafe_allow_html=True)
    if not st.checkbox("⚡ الاستمرار رغم البنود الناقصة"):
        st.stop()
else:
    st.markdown('<div class="abox ab-good">✅ جميع البنود المطلوبة موجودة — البيانات مكتملة</div>',
                unsafe_allow_html=True)
st.success(f"✅ تم تحميل الملف | عدد الفترات: {len(months)}")

# حساب المؤشرات
ratios_list = [calc_ratios(df, m) for m in months]
rdf = pd.DataFrame(ratios_list)
rdf['label'] = labels

# ── بطاقات KPI ──
st.markdown('<div class="sec-hdr">📐 المؤشرات المالية</div>', unsafe_allow_html=True)
for i, (lb, r) in enumerate(zip(labels, ratios_list)):
    with st.expander(f"📌 {lb}", expanded=(i == len(labels)-1)):
        st.markdown("**📊 نسب السيولة**")
        kpi_row(r, [
            ("نسبة_التداول",    "نسبة التداول",   "ratio",
             lambda r: f"{fmt_full(r['الأصول_المتداولة'])} ÷ {fmt_full(r['الالتزامات_المتداولة'])}"),
            ("النسبة_السريعة",  "النسبة السريعة", "ratio",
             lambda r: f"(أصول−مخزون) ÷ {fmt_full(r['الالتزامات_المتداولة'])}"),
            ("نسبة_النقدية",    "نسبة النقدية",   "ratio",
             lambda r: f"{fmt_full(r['النقدية'])} ÷ {fmt_full(r['الالتزامات_المتداولة'])}"),
            ("رأس_المال_العامل","رأس المال العامل","num", None),
        ])
        st.markdown("**📊 الهيكل المالي والربحية**")
        kpi_row(r, [
            ("نسبة_الديون",       "نسبة الديون",   "pct", None),
            ("نسبة_حقوق_الملكية","حقوق الملكية",  "pct", None),
            ("العائد_على_الملكية","ROE",           "pct",
             lambda r: f"{fmt_full(r['صافي_الربح'])} ÷ {fmt_full(r['حقوق_الملكية'])}"),
            ("هامش_الأصول",       "ROA",           "pct",
             lambda r: f"{fmt_full(r['صافي_الربح'])} ÷ {fmt_full(r['إجمالي_الأصول'])}"),
        ])
        st.markdown("**📊 أرقام رئيسية**")
        kpi_row(r, [
            ("إجمالي_الأصول",   "إجمالي الأصول","num", None),
            ("صافي_الربح",      "صافي الربح",   "num", None),
            ("النقدية",         "النقدية",       "num", None),
            ("التسهيلات_البنكية","تسهيلات بنكية","num", None),
        ])

# ── الرسوم البيانية ──
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown('<div class="sec-hdr">📈 الرسوم البيانية والاتجاهات</div>', unsafe_allow_html=True)
draw_charts(rdf, labels)

# ══════════════════════════════════════════════════════
# التحليل المالي المدمج (شرح + تحليل معاً)
# ══════════════════════════════════════════════════════
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown('<div class="sec-hdr">🧠 التحليل المالي التفصيلي (الشرح + طريقة التنفيذ مدمجان)</div>',
            unsafe_allow_html=True)
st.markdown(
    '<div class="no-print">💡 كل نسبة تعرض: تعريفها ومعناها أولاً، ثم القيمة الفعلية وطريقة حسابها والتقييم مباشرةً</div>',
    unsafe_allow_html=True)

tabs = st.tabs([f"📌 {lb}" for lb in labels])
for tab, lb, r in zip(tabs, labels, ratios_list):
    with tab:
        analysis = build_analysis(r)
        for sec, items in analysis.items():
            if not items:
                continue
            st.markdown(f'<div class="sec-hdr">{sec}</div>', unsafe_allow_html=True)
            for (ratio_key, title, calc, meaning, taqeem, level) in items:
                render_merged_analysis_item(ratio_key, title, calc, meaning, taqeem, level)
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# ── جدول المقارنة الشاملة ──
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown('<div class="sec-hdr">📊 جدول المقارنة الشاملة</div>', unsafe_allow_html=True)
hh = "".join(f"<th>{lb}</th>" for lb in labels)
rh = ""
CMP = [
    ("نسبة_التداول",        "نسبة التداول",         fmt_ratio),
    ("النسبة_السريعة",      "النسبة السريعة",        fmt_ratio),
    ("نسبة_النقدية",        "نسبة النقدية",          fmt_ratio),
    ("نسبة_الديون",         "نسبة الديون",           fmt_pct),
    ("نسبة_حقوق_الملكية",  "نسبة حقوق الملكية",     fmt_pct),
    ("العائد_على_الملكية",  "ROE",                   fmt_pct),
    ("هامش_الأصول",         "ROA",                   fmt_pct),
    ("نسبة_التمويل_البنكي", "التمويل البنكي",         fmt_pct),
    ("إجمالي_الأصول",       "إجمالي الأصول",         fmt_num),
    ("صافي_الربح",          "صافي الربح / الخسارة",  fmt_num),
    ("النقدية",             "النقدية",                fmt_num),
    ("العملاء",             "أرصدة العملاء",          fmt_num),
    ("المخزون",             "المخزون",                fmt_num),
    ("التسهيلات_البنكية",   "التسهيلات البنكية",      fmt_num),
    ("رأس_المال_العامل",    "رأس المال العامل",       fmt_num),
]
for key, lbl, fmtr in CMP:
    cells = "".join(f"<td>{fmtr(r.get(key, 0))}</td>" for r in ratios_list)
    rh += f"<tr><td><strong>{lbl}</strong></td>{cells}</tr>"
st.markdown(
    f'<div style="overflow-x:auto"><table class="ctbl">'
    f'<thead><tr><th>المؤشر</th>{hh}</tr></thead>'
    f'<tbody>{rh}</tbody></table></div>',
    unsafe_allow_html=True)

# ── تحميل PDF ──
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown('<div class="sec-hdr">📄 تحميل التقرير PDF</div>', unsafe_allow_html=True)

font_r    = _find_font(False)
font_name = "Amiri" if font_r and "Amiri" in font_r else "DejaVu Sans"

st.info(
    f"📋 التقرير يشمل:\n"
    f"• ملخص جدولي بجميع المؤشرات\n"
    f"• تحليل مدمج لكل فترة (تعريف النسبة + حسابها + تقييمها في مكان واحد)\n"
    f"• دليل مرجعي لجميع النسب\n"
    f"• كل محتوى داخل حدود A4 مع فواصل واضحة بين الأقسام\n"
    f"• الخط المستخدم: {font_name}"
)

if st.button("🔄 إنشاء التقرير PDF", type="primary"):
    with st.spinner("جارٍ إعداد التقرير..."):
        pdf_buf = build_pdf(ratios_list, months, labels)
    if pdf_buf:
        st.download_button(
            label="⬇️ تحميل التقرير PDF",
            data=pdf_buf,
            file_name="financial_report.pdf",
            mime="application/pdf",
        )
        st.success("✅ التقرير جاهز للتحميل!")
    else:
        st.error("❌ تعذّر إنشاء PDF — تأكد من وجود ملفات الخط في مجلد السكريبت")
