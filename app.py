import streamlit as st
import arabic_reshaper
from bidi.algorithm import get_display
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak
)
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import os

# =====================================================
# إعداد الصفحة - إضافة تبويبات متعددة
# =====================================================

st.set_page_config(
    page_title="نظام تحليل القوائم المالية",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS مخصص
st.markdown("""
<style>
    /* دعم RTL */
    body, .stApp, .main > div {
        direction: rtl !important;
    }

    /* إخفاء القائمة الجانبية في الطباعة */
    @media print {
        section[data-testid="stSidebar"] {
            display: none !important;
        }
        .main .block-container {
            padding-right: 2rem !important;
            padding-left: 2rem !important;
        }
        .stDownloadButton, .stFileUploader, .stTabs [role="tablist"] {
            display: none !important;
        }
    }

    /* بطاقات المؤشرات */
    .metric-card {
        background: linear-gradient(135deg, #1e3a5f, #2d6a9f);
        border-radius: 12px;
        padding: 18px;
        color: white;
        text-align: center;
        margin: 6px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        transition: transform 0.3s;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .metric-card .value { font-size: 2rem; font-weight: bold; }
    .metric-card .label { font-size: 0.85rem; opacity: 0.85; margin-top: 4px; }
    .status-good  { background: linear-gradient(135deg, #1a6b3c, #27ae60); }
    .status-warn  { background: linear-gradient(135deg, #7d5a00, #f39c12); }
    .status-bad   { background: linear-gradient(135deg, #7b1818, #c0392b); }

    /* الأقسام */
    .section-header {
        font-size: 1.3rem; font-weight: 700; color: #1e3a5f;
        border-right: 5px solid #2d6a9f; padding-right: 12px;
        margin: 18px 0 10px; direction: rtl;
    }

    /* صناديق التنبيه */
    .alert-box {
        border-radius: 8px; padding: 12px 16px; margin: 8px 0;
        border-right: 5px solid; direction: rtl;
    }
    .alert-success { background:#d4edda; border-color:#27ae60; color:#155724; }
    .alert-warning { background:#fff3cd; border-color:#f39c12; color:#856404; }
    .alert-danger  { background:#f8d7da; border-color:#c0392b; color:#721c24; }

    /* بطاقة شرح النسبة */
    .ratio-detail-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 12px;
        padding: 16px;
        margin: 10px 0;
        border-right: 4px solid #2d6a9f;
        direction: rtl;
        transition: all 0.3s;
    }
    .ratio-detail-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .ratio-name {
        font-size: 1rem;
        font-weight: bold;
        color: #1e3a5f;
        margin-bottom: 10px;
    }
    .ratio-calculation {
        font-family: monospace;
        background: #fff;
        padding: 8px 12px;
        border-radius: 8px;
        margin: 8px 0;
        font-size: 0.85rem;
        direction: ltr;
        text-align: right;
    }

    /* بطاقة المقارنة */
    .comparison-card {
        background: white;
        border-radius: 12px;
        padding: 16px;
        margin: 10px 0;
        border: 1px solid #dee2e6;
        direction: rtl;
    }
    .comparison-header {
        font-size: 1.1rem;
        font-weight: bold;
        color: #1e3a5f;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 2px solid #2d6a9f;
    }
    .trend-up { color: #27ae60; }
    .trend-down { color: #c0392b; }
    .trend-stable { color: #f39c12; }
</style>
""", unsafe_allow_html=True)


# =====================================================
# دوال مساعدة
# =====================================================

def get_arabic_fonts():
    """الحصول على خط عربي"""
    font_paths = [
        "C:/Windows/Fonts/Arial.ttf",
        "C:/Windows/Fonts/Tahoma.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in font_paths:
        if os.path.exists(path):
            return path, path
    return None, None


def ar(text):
    try:
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)
    except:
        return str(text)


def format_number(value, decimals=0):
    if pd.isna(value) or value == 0:
        return "0"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}م"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.2f}ألف"
    return f"{value:,.{decimals}f}"


def format_period_name(period_name):
    months_ar = {1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل', 5: 'مايو', 6: 'يونيو',
                 7: 'يوليو', 8: 'أغسطس', 9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'}
    try:
        date_obj = pd.to_datetime(period_name)
        return f"{months_ar[date_obj.month]} {date_obj.year}"
    except:
        return str(period_name)


# =====================================================
# البنود المطلوبة
# =====================================================

REQUIRED_ITEMS = {
    "الاصول الثابته بالصافي": "fixed_assets",
    "مجموع الأصول الغير متداوله": "non_current_assets",
    "العملاء و اوراق القبض": "receivables",
    "النقديه و ما في حكمها": "cash",
    "المخزون": "inventory",
    "مجموع الأصول متداوله": "current_assets",
    "إجمالي الاصول": "total_assets",
    "موردين و أوراق دفع": "payables",
    "مجموع الالتزامات المتداوله": "current_liabilities",
    "رأس المال": "capital",
    "أرباح مرحله": "retained_earnings",
    "صافي أرباح / خسائر الفتره": "net_profit",
    "مجموع حقوق اصحاب الحصص": "equity",
    "إجمالي حقوق اصحاب الحصص و الالتزامات": "total_equity_liabilities",
}


def safe_get(df, item, col):
    try:
        mask = df['البند'].str.strip() == item.strip()
        vals = df.loc[mask, col].values
        if len(vals) == 0:
            return 0.0
        v = vals[0]
        if pd.isna(v):
            return 0.0
        return float(v)
    except:
        return 0.0


# =====================================================
# حساب المؤشرات المالية المتقدمة
# =====================================================

def calculate_ratios(df, col):
    """حساب جميع المؤشرات المالية مع طريقة الحساب"""
    g = lambda item: safe_get(df, item, col)

    # القيم الأساسية
    current_assets = g('مجموع الأصول متداوله')
    current_liabilities = g('مجموع الالتزامات المتداوله')
    total_assets = g('إجمالي الاصول')
    inventory = g('المخزون')
    cash = g('النقديه و ما في حكمها')
    receivables = g('العملاء و اوراق القبض')
    equity = g('مجموع حقوق اصحاب الحصص')
    net_profit = g('صافي أرباح / خسائر الفتره')
    non_current_assets = g('مجموع الأصول الغير متداوله')
    fixed_assets = g('الاصول الثابته بالصافي')
    payables = g('موردين و أوراق دفع')
    capital = g('رأس المال')
    retained_earnings = g('أرباح مرحله')

    def safe_div(a, b):
        return round(a / b, 4) if b and b != 0 else 0

    # مؤشرات السيولة
    current_ratio = safe_div(current_assets, current_liabilities)
    quick_ratio = safe_div(current_assets - inventory, current_liabilities)
    cash_ratio = safe_div(cash, current_liabilities)
    operating_cash_flow_ratio = safe_div(cash, current_liabilities)  # مبسط

    # مؤشرات النشاط (الكفاءة التشغيلية)
    receivables_turnover = safe_div(total_assets, receivables) if receivables > 0 else 0
    inventory_turnover = safe_div(total_assets, inventory) if inventory > 0 else 0
    payables_turnover = safe_div(total_assets, payables) if payables > 0 else 0
    asset_turnover = safe_div(total_assets, total_assets)  # دوران الأصول الكلي

    # أيام التحصيل والمخزون
    days_receivables = safe_div(365, receivables_turnover) if receivables_turnover > 0 else 0
    days_inventory = safe_div(365, inventory_turnover) if inventory_turnover > 0 else 0
    days_payables = safe_div(365, payables_turnover) if payables_turnover > 0 else 0
    cash_conversion_cycle = days_receivables + days_inventory - days_payables

    # مؤشرات الهيكل المالي
    debt_ratio = safe_div(current_liabilities, total_assets)
    equity_ratio = safe_div(equity, total_assets)
    debt_to_equity = safe_div(current_liabilities, equity)
    fixed_assets_to_equity = safe_div(fixed_assets, equity)
    current_liabilities_to_equity = safe_div(current_liabilities, equity)

    # مؤشرات الربحية
    roe = safe_div(net_profit, equity)
    roa = safe_div(net_profit, total_assets)
    profit_margin = safe_div(net_profit, total_assets)  # هامش الربح الصافي
    operating_roa = safe_div(net_profit, total_assets)

    # مؤشرات النمو
    working_capital = current_assets - current_liabilities

    # مؤشرات إضافية
    equity_to_assets = equity_ratio
    current_assets_to_total = safe_div(current_assets, total_assets)
    fixed_assets_to_total = safe_div(fixed_assets, total_assets)

    ratios = {
        'القيم_الأصلية': {
            'الأصول_المتداولة': current_assets,
            'الالتزامات_المتداولة': current_liabilities,
            'المخزون': inventory,
            'النقدية': cash,
            'العملاء': receivables,
            'إجمالي_الأصول': total_assets,
            'حقوق_الملكية': equity,
            'صافي_الربح': net_profit,
            'الأصول_الغير_متداولة': non_current_assets,
            'الأصول_الثابتة': fixed_assets,
            'الموردين': payables,
            'رأس_المال': capital,
            'الأرباح_المرحلة': retained_earnings,
        },
        'السيولة': {
            'نسبة_التداول': {'القيمة': current_ratio, 'البسط': current_assets, 'المقام': current_liabilities},
            'النسبة_السريعة': {'القيمة': quick_ratio, 'البسط': current_assets - inventory,
                               'المقام': current_liabilities},
            'نسبة_النقدية': {'القيمة': cash_ratio, 'البسط': cash, 'المقام': current_liabilities},
            'رأس_المال_العامل': {'القيمة': working_capital, 'البسط': current_assets, 'المقام': current_liabilities},
        },
        'النشاط_والكفاءة': {
            'دوران_المستحقات': {'القيمة': receivables_turnover, 'البسط': total_assets, 'المقام': receivables},
            'دوران_المخزون': {'القيمة': inventory_turnover, 'البسط': total_assets, 'المقام': inventory},
            'دوران_الموردين': {'القيمة': payables_turnover, 'البسط': total_assets, 'المقام': payables},
            'أيام_التحصيل': {'القيمة': days_receivables, 'البسط': 365, 'المقام': receivables_turnover},
            'أيام_المخزون': {'القيمة': days_inventory, 'البسط': 365, 'المقام': inventory_turnover},
            'أيام_الموردين': {'القيمة': days_payables, 'البسط': 365, 'المقام': payables_turnover},
            'دورة_التحويل_النقدي': {'القيمة': cash_conversion_cycle,
                                    'البسط': days_receivables + days_inventory - days_payables, 'المقام': 1},
        },
        'الهيكل_المالي': {
            'نسبة_الديون': {'القيمة': debt_ratio, 'البسط': current_liabilities, 'المقام': total_assets},
            'نسبة_حقوق_الملكية': {'القيمة': equity_ratio, 'البسط': equity, 'المقام': total_assets},
            'الديون_لحقوق_الملكية': {'القيمة': debt_to_equity, 'البسط': current_liabilities, 'المقام': equity},
            'الأصول_الثابتة_للحقوق': {'القيمة': fixed_assets_to_equity, 'البسط': fixed_assets, 'المقام': equity},
        },
        'الربحية': {
            'العائد_على_حقوق_الملكية': {'القيمة': roe, 'البسط': net_profit, 'المقام': equity},
            'العائد_على_الأصول': {'القيمة': roa, 'البسط': net_profit, 'المقام': total_assets},
            'هامش_صافي_الربح': {'القيمة': profit_margin, 'البسط': net_profit, 'المقام': total_assets},
        },
        'الهيكل_الاستثماري': {
            'نسبة_الأصول_المتداولة': {'القيمة': current_assets_to_total, 'البسط': current_assets,
                                      'المقام': total_assets},
            'نسبة_الأصول_الثابتة': {'القيمة': fixed_assets_to_total, 'البسط': fixed_assets, 'المقام': total_assets},
        }
    }

    return ratios


# =====================================================
# الرسوم البيانية المتقدمة
# =====================================================

def create_advanced_charts(ratios_df, months, formatted_months):
    """إنشاء لوحة متكاملة من الرسوم البيانية"""
    
    fig = make_subplots(
        rows=4, cols=2,
        subplot_titles=(
            '📊 نسب السيولة', '💰 نسب الربحية',
            '🏗️ هيكل التمويل', '📈 نمو الأصول والربح',
            '🔄 مؤشرات النشاط', '⚖️ هيكل الأصول (نسبة)',
            '📉 تحليل رأس المال العامل', '🎯 العائد على حقوق الملكية'
        ),
        vertical_spacing=0.12,
        horizontal_spacing=0.15,
        specs=[
            [{"type": "xy"}, {"type": "xy"}],
            [{"type": "xy"}, {"type": "xy"}],
            [{"type": "xy"}, {"type": "xy"}],
            [{"type": "xy"}, {"type": "xy"}]
        ]
    )
    
    # 1. نسب السيولة
    fig.add_trace(
        go.Scatter(x=formatted_months, y=ratios_df['نسبة_التداول'],
                   name='نسبة التداول', mode='lines+markers',
                   line=dict(color='#2d6a9f', width=3), marker=dict(size=8)),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=formatted_months, y=ratios_df['النسبة_السريعة'],
                   name='النسبة السريعة', mode='lines+markers',
                   line=dict(color='#27ae60', width=3), marker=dict(size=8)),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=formatted_months, y=ratios_df['نسبة_النقدية'],
                   name='نسبة النقدية', mode='lines+markers',
                   line=dict(color='#f39c12', width=3), marker=dict(size=8)),
        row=1, col=1
    )
    fig.add_hline(y=2, line_dash="dash", line_color="green", row=1, col=1, annotation_text="مثالي 2")
    fig.add_hline(y=1, line_dash="dash", line_color="red", row=1, col=1, annotation_text="حد أدنى 1")
    
    # 2. نسب الربحية (أعمدة)
    fig.add_trace(
        go.Bar(x=formatted_months, y=ratios_df['العائد_على_حقوق_الملكية'] * 100,
               name='ROE %', marker_color='#2d6a9f'),
        row=1, col=2
    )
    fig.add_trace(
        go.Bar(x=formatted_months, y=ratios_df['العائد_على_الأصول'] * 100,
               name='ROA %', marker_color='#27ae60'),
        row=1, col=2
    )
    fig.add_trace(
        go.Scatter(x=formatted_months, y=ratios_df['هامش_صافي_الربح'] * 100,
                   name='هامش الربح %', mode='lines+markers',
                   line=dict(color='#e74c3c', width=2, dash='dot')),
        row=1, col=2
    )
    fig.add_hline(y=15, line_dash="dash", line_color="green", row=1, col=2, annotation_text="هدف ROE")
    
    # 3. هيكل التمويل (أعمدة مكدسة)
    for i, month in enumerate(formatted_months):
        fig.add_trace(
            go.Bar(x=[month], y=[ratios_df['نسبة_حقوق_الملكية'].iloc[i] * 100],
                   name='حقوق الملكية' if i == 0 else '', marker_color='#27ae60',
                   showlegend=(i == 0)),
            row=2, col=1
        )
        fig.add_trace(
            go.Bar(x=[month], y=[ratios_df['نسبة_الديون'].iloc[i] * 100],
                   name='ديون' if i == 0 else '', marker_color='#c0392b',
                   showlegend=(i == 0)),
            row=2, col=1
        )
    fig.update_yaxes(title_text="النسبة %", row=2, col=1)
    fig.add_hline(y=50, line_dash="dash", line_color="green", row=2, col=1, annotation_text="نقطة توازن")
    
    # 4. نمو الأصول والربح
    fig.add_trace(
        go.Scatter(x=formatted_months, y=ratios_df['إجمالي_الأصول'],
                   name='إجمالي الأصول', mode='lines+markers',
                   line=dict(color='#8e44ad', width=3), marker=dict(size=8)),
        row=2, col=2
    )
    fig.add_trace(
        go.Scatter(x=formatted_months, y=ratios_df['صافي_الربح'],
                   name='صافي الربح', mode='lines+markers',
                   line=dict(color='#f39c12', width=3), marker=dict(size=8)),
        row=2, col=2
    )
    
    # 5. مؤشرات النشاط
    fig.add_trace(
        go.Scatter(x=formatted_months, y=ratios_df['دوران_المستحقات'],
                   name='دوران المستحقات', mode='lines+markers',
                   line=dict(color='#2d6a9f', width=2)),
        row=3, col=1
    )
    fig.add_trace(
        go.Scatter(x=formatted_months, y=ratios_df['دوران_المخزون'],
                   name='دوران المخزون', mode='lines+markers',
                   line=dict(color='#27ae60', width=2)),
        row=3, col=1
    )
    fig.add_trace(
        go.Scatter(x=formatted_months, y=ratios_df['أيام_التحصيل'],
                   name='أيام التحصيل', mode='lines+markers',
                   line=dict(color='#e74c3c', width=2, dash='dot')),
        row=3, col=1
    )
    fig.update_yaxes(title_text="عدد المرات / الأيام", row=3, col=1)
    
    # 6. هيكل الأصول
    current_assets_ratio = (ratios_df['الأصول_المتداولة'] / ratios_df['إجمالي_الأصول']) * 100
    non_current_assets_ratio = (ratios_df['الأصول_الغير_متداولة'] / ratios_df['إجمالي_الأصول']) * 100
    
    fig.add_trace(
        go.Scatter(x=formatted_months, y=current_assets_ratio,
                   name='نسبة الأصول المتداولة', mode='lines+markers',
                   line=dict(color='#2d6a9f', width=3), fill='tozeroy',
                   fillcolor='rgba(45, 106, 159, 0.2)'),
        row=3, col=2
    )
    fig.add_trace(
        go.Scatter(x=formatted_months, y=non_current_assets_ratio,
                   name='نسبة الأصول غير المتداولة', mode='lines+markers',
                   line=dict(color='#27ae60', width=3), fill='tozeroy',
                   fillcolor='rgba(39, 174, 96, 0.2)'),
        row=3, col=2
    )
    fig.update_yaxes(title_text="نسبة من إجمالي الأصول %", row=3, col=2)
    fig.add_hline(y=50, line_dash="dash", line_color="gray", row=3, col=2, annotation_text="نصف الأصول")
    
    # 7. رأس المال العامل
    colors_wc = ['#27ae60' if v >= 0 else '#c0392b' for v in ratios_df['رأس_المال_العامل']]
    fig.add_trace(
        go.Bar(x=formatted_months, y=ratios_df['رأس_المال_العامل'],
               name='رأس المال العامل', marker_color=colors_wc,
               text=[format_number(v) for v in ratios_df['رأس_المال_العامل']],
               textposition='auto'),
        row=4, col=1
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=4, col=1, annotation_text="نقطة التعادل")
    fig.update_yaxes(title_text="القيمة", row=4, col=1)
    
    # 8. العائد على حقوق الملكية
    roe_values = ratios_df['العائد_على_حقوق_الملكية'] * 100
    colors_roe = ['#27ae60' if v >= 15 else '#f39c12' if v >= 10 else '#e74c3c' for v in roe_values]
    fig.add_trace(
        go.Bar(x=formatted_months, y=roe_values,
               name='ROE %', marker_color=colors_roe,
               text=[f"{v:.1f}%" for v in roe_values], textposition='auto'),
        row=4, col=2
    )
    fig.add_hline(y=15, line_dash="dash", line_color="green", row=4, col=2, annotation_text="هدف 15%")
    fig.add_hline(y=10, line_dash="dash", line_color="orange", row=4, col=2, annotation_text="حد مقبول 10%")
    fig.add_hline(y=5, line_dash="dash", line_color="red", row=4, col=2, annotation_text="حد أدنى 5%")
    fig.update_yaxes(title_text="النسبة %", row=4, col=2)
    
    fig.update_layout(
        height=1200,
        showlegend=True,
        template='plotly_white',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
            bgcolor='rgba(255,255,255,0.9)'
        ),
        hovermode='x unified'
    )
    
    for row in range(1, 5):
        for col in range(1, 3):
            fig.update_xaxes(title_text="الفترة", row=row, col=col, tickangle=45)
    
    return fig


def create_radar_chart(ratios_df, formatted_months):
    """إنشاء مخطط راداري للمقارنة بين أول وآخر فترة"""
    radar_categories = ['نسبة التداول', 'النسبة السريعة', 'العائد على حقوق الملكية',
                        'نسبة حقوق الملكية', 'دوران المخزون']

    first_values = [
        ratios_df['نسبة_التداول'].iloc[0],
        ratios_df['النسبة_السريعة'].iloc[0],
        ratios_df['العائد_على_حقوق_الملكية'].iloc[0] * 100,
        ratios_df['نسبة_حقوق_الملكية'].iloc[0] * 100,
        ratios_df['دوران_المخزون'].iloc[0]
    ]

    last_values = [
        ratios_df['نسبة_التداول'].iloc[-1],
        ratios_df['النسبة_السريعة'].iloc[-1],
        ratios_df['العائد_على_حقوق_الملكية'].iloc[-1] * 100,
        ratios_df['نسبة_حقوق_الملكية'].iloc[-1] * 100,
        ratios_df['دوران_المخزون'].iloc[-1]
    ]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=first_values,
        theta=radar_categories,
        fill='toself',
        name=f'{formatted_months[0]}',
        line=dict(color='#2d6a9f', width=2)
    ))
    fig_radar.add_trace(go.Scatterpolar(
        r=last_values,
        theta=radar_categories,
        fill='toself',
        name=f'{formatted_months[-1]}',
        line=dict(color='#27ae60', width=2)
    ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        showlegend=True,
        height=450,
        title="مقارنة الأداء بين أول وآخر فترة",
        template='plotly_white'
    )
    return fig_radar


def create_bar_changes_chart(ratios_df):
    """إنشاء مخطط شريطي يوضح التغيرات النسبية"""
    changes = {}
    for col in ['نسبة_التداول', 'نسبة_حقوق_الملكية', 'العائد_على_حقوق_الملكية',
                'إجمالي_الأصول', 'صافي_الربح']:
        if col in ratios_df.columns:
            first_val = ratios_df[col].iloc[0]
            last_val = ratios_df[col].iloc[-1]
            if first_val != 0:
                change = ((last_val - first_val) / abs(first_val)) * 100
                changes[col] = change

    colors_changes = ['#27ae60' if v >= 0 else '#c0392b' for v in changes.values()]
    fig_changes = go.Figure(go.Bar(
        x=list(changes.keys()),
        y=list(changes.values()),
        marker_color=colors_changes,
        text=[f"{v:+.1f}%" for v in changes.values()],
        textposition='auto'
    ))
    fig_changes.update_layout(
        height=450,
        title="نسبة التغير بين أول وآخر فترة (%)",
        yaxis_title="نسبة التغير %",
        xaxis_title="المؤشر",
        template='plotly_white'
    )
    return fig_changes


def create_kpi_timeline(ratios_df, formatted_months):
    """إنشاء مخطط تطور مؤشرات الأداء الرئيسية"""
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'نسب السيولة عبر الزمن',
            'مؤشرات الربحية',
            'كفاءة النشاط التشغيلي',
            'هيكل التمويل'
        ),
        vertical_spacing=0.15,
        horizontal_spacing=0.15
    )
    
    fig.add_trace(
        go.Scatter(x=formatted_months, y=ratios_df['نسبة_التداول'],
                   name='نسبة التداول', mode='lines+markers',
                   line=dict(color='#2d6a9f', width=3), marker=dict(size=10)),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=formatted_months, y=ratios_df['النسبة_السريعة'],
                   name='النسبة السريعة', mode='lines+markers',
                   line=dict(color='#27ae60', width=3), marker=dict(size=10, symbol='diamond')),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=formatted_months, y=ratios_df['العائد_على_حقوق_الملكية'] * 100,
                   name='ROE %', mode='lines+markers',
                   line=dict(color='#8e44ad', width=3), marker=dict(size=10)),
        row=1, col=2
    )
    fig.add_trace(
        go.Scatter(x=formatted_months, y=ratios_df['العائد_على_الأصول'] * 100,
                   name='ROA %', mode='lines+markers',
                   line=dict(color='#e67e22', width=3), marker=dict(size=10, symbol='square')),
        row=1, col=2
    )
    
    fig.add_trace(
        go.Scatter(x=formatted_months, y=ratios_df['دوران_المخزون'],
                   name='دوران المخزون', mode='lines+markers',
                   line=dict(color='#27ae60', width=3), marker=dict(size=10)),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(x=formatted_months, y=ratios_df['أيام_التحصيل'],
                   name='أيام التحصيل', mode='lines+markers',
                   line=dict(color='#e74c3c', width=3, dash='dot'), marker=dict(size=10, symbol='diamond')),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=formatted_months, y=ratios_df['نسبة_حقوق_الملكية'] * 100,
                   name='نسبة حقوق الملكية', mode='lines+markers',
                   line=dict(color='#27ae60', width=3), fill='tozeroy',
                   fillcolor='rgba(39, 174, 96, 0.2)'),
        row=2, col=2
    )
    fig.add_trace(
        go.Scatter(x=formatted_months, y=ratios_df['نسبة_الديون'] * 100,
                   name='نسبة الديون', mode='lines+markers',
                   line=dict(color='#c0392b', width=3), fill='tozeroy',
                   fillcolor='rgba(192, 57, 43, 0.2)'),
        row=2, col=2
    )
    
    fig.update_layout(
        height=700,
        showlegend=True,
        template='plotly_white',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    for row in range(1, 3):
        for col in range(1, 3):
            fig.update_xaxes(title_text="الفترة", row=row, col=col, tickangle=45)
    
    return fig


# =====================================================
# تحليل المقارنة بين الفترات
# =====================================================

def compare_periods(ratios_df, formatted_months):
    """مقارنة وتحليل الفترات"""

    comparison = []
    first_idx = 0
    last_idx = -1

    metrics_to_compare = [
        ('إجمالي_الأصول', 'إجمالي الأصول', 'currency'),
        ('صافي_الربح', 'صافي الربح', 'currency'),
        ('نسبة_التداول', 'نسبة التداول', 'ratio'),
        ('نسبة_حقوق_الملكية', 'نسبة حقوق الملكية', 'percent'),
        ('العائد_على_حقوق_الملكية', 'العائد على حقوق الملكية', 'percent'),
        ('العائد_على_الأصول', 'العائد على الأصول', 'percent'),
        ('رأس_المال_العامل', 'رأس المال العامل', 'currency'),
        ('دوران_المخزون', 'دوران المخزون', 'ratio'),
        ('أيام_التحصيل', 'أيام التحصيل', 'number'),
    ]

    for col, name, fmt in metrics_to_compare:
        if col in ratios_df.columns:
            first_val = ratios_df[col].iloc[first_idx]
            last_val = ratios_df[col].iloc[-1]

            if fmt == 'currency':
                first_disp = format_number(first_val)
                last_disp = format_number(last_val)
            elif fmt == 'percent':
                first_disp = f"{first_val * 100:.1f}%"
                last_disp = f"{last_val * 100:.1f}%"
            elif fmt == 'ratio':
                first_disp = f"{first_val:.2f}x"
                last_disp = f"{last_val:.2f}x"
            else:
                first_disp = f"{first_val:.0f} يوم"
                last_disp = f"{last_val:.0f} يوم"

            if first_val != 0:
                change_pct = ((last_val - first_val) / abs(first_val)) * 100
            else:
                change_pct = 0

            if change_pct > 10:
                trend = "up" if col not in ['أيام_التحصيل', 'نسبة_الديون'] else "down"
            elif change_pct < -10:
                trend = "down" if col not in ['أيام_التحصيل', 'نسبة_الديون'] else "up"
            else:
                trend = "stable"

            comparison.append({
                'المؤشر': name,
                f'{formatted_months[first_idx]}': first_disp,
                f'{formatted_months[last_idx]}': last_disp,
                'التغير': f"{change_pct:+.1f}%",
                'الاتجاه': trend
            })

    return pd.DataFrame(comparison)


def analyze_trends(ratios_df, formatted_months):
    """تحليل الاتجاهات والنمو"""

    trends = []

    # تحليل نمو الأصول
    assets_growth = []
    for i in range(1, len(ratios_df)):
        if ratios_df['إجمالي_الأصول'].iloc[i - 1] != 0:
            growth = ((ratios_df['إجمالي_الأصول'].iloc[i] - ratios_df['إجمالي_الأصول'].iloc[i - 1]) /
                      ratios_df['إجمالي_الأصول'].iloc[i - 1]) * 100
            assets_growth.append(growth)

    avg_assets_growth = np.mean(assets_growth) if assets_growth else 0

    # تحليل نمو الربح
    profit_growth = []
    for i in range(1, len(ratios_df)):
        if ratios_df['صافي_الربح'].iloc[i - 1] != 0:
            growth = ((ratios_df['صافي_الربح'].iloc[i] - ratios_df['صافي_الربح'].iloc[i - 1]) /
                      abs(ratios_df['صافي_الربح'].iloc[i - 1])) * 100
            profit_growth.append(growth)

    avg_profit_growth = np.mean(profit_growth) if profit_growth else 0

    trends.append({
        'المؤشر': 'متوسط نمو الأصول',
        'القيمة': f"{avg_assets_growth:+.1f}%",
        'التقييم': 'نمو جيد' if avg_assets_growth > 10 else ('نمو بطيء' if avg_assets_growth > 0 else 'انكماش'),
        'التوصية': 'استمرار التوسع' if avg_assets_growth > 10 else 'تحسين كفاءة الاستثمار'
    })

    trends.append({
        'المؤشر': 'متوسط نمو الأراحباح',
        'القيمة': f"{avg_profit_growth:+.1f}%",
        'التقييم': 'نمو ممتاز' if avg_profit_growth > 15 else ('نمو جيد' if avg_profit_growth > 5 else 'ضعيف'),
        'التوصية': 'تعزيز الربحية' if avg_profit_growth < 10 else 'الحفاظ على الأداء'
    })

    current_ratio_std = ratios_df['نسبة_التداول'].std()
    trends.append({
        'المؤشر': 'استقرار السيولة',
        'القيمة': f"{current_ratio_std:.3f}",
        'التقييم': 'مستقر' if current_ratio_std < 0.3 else 'متقلب',
        'التوصية': 'مراقبة مستمرة' if current_ratio_std > 0.3 else 'وضع مستقر'
    })

    days_rec_improvement = (ratios_df['أيام_التحصيل'].iloc[0] - ratios_df['أيام_التحصيل'].iloc[-1]) if len(
        ratios_df) > 1 else 0
    trends.append({
        'المؤشر': 'تحسين أيام التحصيل',
        'القيمة': f"{days_rec_improvement:.0f} يوم",
        'التقييم': 'تحسن' if days_rec_improvement > 0 else 'تدهور',
        'التوصية': 'سياسات تحصيل أفضل' if days_rec_improvement < 0 else 'استمرار السياسات'
    })

    return pd.DataFrame(trends)


# =====================================================
# عرض شرح النسبة
# =====================================================

def render_ratio_detail(ratio_name, value_data, period_name, category='عام'):
    """عرض بطاقة شرح مفصلة للنسبة"""

    value = value_data['القيمة']
    numerator = value_data['البسط']
    denominator = value_data['المقام']

    if 'نسبة' in ratio_name and ratio_name not in ['نسبة_التحصيل', 'دوران']:
        if 'رأس_المال' in ratio_name:
            display_value = format_number(value)
        else:
            display_value = f"{value:.2f}x" if value < 3 else f"{value:.1f}x"
    elif any(x in ratio_name for x in ['عائد', 'هامش']):
        display_value = f"{value * 100:.1f}%"
    elif 'يوم' in ratio_name:
        display_value = f"{value:.0f} يوم"
    else:
        display_value = f"{value:.2f}"

    eval_class = "good"
    evaluation = ""

    if 'تداول' in ratio_name:
        if value >= 2:
            evaluation, eval_class = "ممتازة - تغطي الالتزامات مرتين", "good"
        elif value >= 1.5:
            evaluation, eval_class = "جيدة - وضع سيولة مستقر", "good"
        elif value >= 1:
            evaluation, eval_class = "مقبولة - تحتاج تحسين", "warn"
        else:
            evaluation, eval_class = "ضعيفة - خطر مالي", "bad"
    elif 'سريعة' in ratio_name:
        if value >= 1:
            evaluation, eval_class = "ممتازة - سيولة فورية قوية", "good"
        elif value >= 0.7:
            evaluation, eval_class = "مقبولة", "warn"
        else:
            evaluation, eval_class = "ضعيفة - تعتمد على المخزون", "bad"
    elif 'ديون' in ratio_name:
        if value <= 0.4:
            evaluation, eval_class = "منخفضة - هيكل مالي آمن", "good"
        elif value <= 0.6:
            evaluation, eval_class = "معتدلة - ضمن الحدود", "warn"
        else:
            evaluation, eval_class = "مرتفعة - مخاطر مالية", "bad"
    elif 'حقوق_الملكية' in ratio_name:
        if value >= 0.5:
            evaluation, eval_class = "قوية - تمويل ذاتي ممتاز", "good"
        elif value >= 0.3:
            evaluation, eval_class = "مقبولة", "warn"
        else:
            evaluation, eval_class = "ضعيفة - اعتماد على الديون", "bad"
    elif 'ROE' in ratio_name or 'حقوق' in ratio_name and 'ملكية' in ratio_name:
        if value >= 0.15:
            evaluation, eval_class = "ممتاز - كفاءة عالية", "good"
        elif value >= 0.1:
            evaluation, eval_class = "جيد", "good"
        elif value >= 0.05:
            evaluation, eval_class = "مقبول - يحتاج تحسين", "warn"
        else:
            evaluation, eval_class = "ضعيف - عائد غير مرضٍ", "bad"
    elif 'عائد_على_الأصول' in ratio_name or 'ROA' in ratio_name:
        if value >= 0.1:
            evaluation, eval_class = "ممتاز - كفاءة تشغيلية", "good"
        elif value >= 0.05:
            evaluation, eval_class = "جيد", "good"
        else:
            evaluation, eval_class = "ضعيف - كفاءة منخفضة", "warn"
    else:
        evaluation = "تم حسابه بناءً على البيانات"

    icon = '✅' if eval_class == 'good' else ('⚠️' if eval_class == 'warn' else '🔴')

    st.markdown(f"""
    <div class="ratio-detail-card">
        <div class="ratio-name">{icon} {ratio_name} = {display_value}</div>
        <div class="ratio-calculation">
            📐 طريقة الحساب:<br>
            {format_number(numerator)} ÷ {format_number(denominator)} = {display_value}
        </div>
        <div class="ratio-meaning" style="color: {'#27ae60' if eval_class == 'good' else '#f39c12' if eval_class == 'warn' else '#c0392b'}">
            📊 التقييم: {evaluation}
        </div>
    </div>
    """, unsafe_allow_html=True)


# =====================================================
# الواجهة الرئيسية
# =====================================================

st.markdown("""
<div style="text-align:center; padding:20px 0 10px; direction:rtl">
    <h1 style="color:#1e3a5f; font-size:2rem;">📊 نظام التحليل المالي المتقدم</h1>
    <p style="color:#555; font-size:1rem;">تحليل احترافي للنسب المالية مع مقارنات ورسوم بيانية تفاعلية</p>
    <p style="color:#888; font-size:0.85rem;">ملاحظة: القائمة الجانبية لا تظهر عند الطباعة</p>
</div>
""", unsafe_allow_html=True)

st.divider()

uploaded_file = st.file_uploader(
    "📂 ارفع ملف Excel الخاص بالقوائم المالية",
    type=['xlsx', 'xls'],
    help="يجب أن يحتوي الملف على بنود القائمة المالية في العمود الأول، والفترات الزمنية في الأعمدة التالية"
)

if not uploaded_file:
    st.markdown("""
    <div style="background:#f0f4f8; border-radius:12px; padding:30px; text-align:center; direction:rtl; margin-top:20px">
        <h3 style="color:#1e3a5f">📋 كيفية إعداد ملف Excel</h3>
        <p style="margin:10px 0">العمود الأول: أسماء البنود المالية</p>
        <p style="margin:10px 0">الأعمدة التالية: الفترات الزمنية (شهر/ربع/سنة)</p>
        <p style="margin:10px 0">يتم حساب أكثر من 20 مؤشراً مالياً تلقائياً</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

try:
    raw_df = pd.read_excel(uploaded_file)
    raw_df.columns = raw_df.columns.astype(str)
    raw_df.rename(columns={raw_df.columns[0]: 'البند'}, inplace=True)
    raw_df['البند'] = raw_df['البند'].fillna('').astype(str).str.strip()
    raw_df = raw_df[raw_df['البند'] != '']

    months = list(raw_df.columns[1:])
    for col in months:
        raw_df[col] = pd.to_numeric(raw_df[col], errors='coerce').fillna(0)

    formatted_months = [format_period_name(m) for m in months]

    st.success(f"✅ تم تحميل الملف بنجاح | عدد الفترات: {len(months)}")

    all_ratios = []
    for month in months:
        ratios = calculate_ratios(raw_df, month)
        all_ratios.append(ratios)

    ratios_data = {}
    for key in all_ratios[0].keys():
        if key != 'القيم_الأصلية':
            for sub_key in all_ratios[0][key].keys():
                ratios_data[sub_key] = [r[key][sub_key]['القيمة'] for r in all_ratios]
        else:
            for sub_key in all_ratios[0][key].keys():
                ratios_data[sub_key] = [r[key][sub_key] for r in all_ratios]

    ratios_df = pd.DataFrame(ratios_data)
    ratios_df['الفترة'] = formatted_months

    with st.expander("📄 عرض البيانات الخام", expanded=False):
        st.dataframe(raw_df, use_container_width=True)

except Exception as e:
    st.error(f"❌ خطأ في قراءة الملف: {e}")
    st.stop()


# ══════════════════════════════════
# إنشاء التبويبات
# ══════════════════════════════════

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 ملخص المؤشرات",
    "📈 الرسوم البيانية",
    "📉 مقارنة الفترات",
    "🔍 تحليل تفصيلي",
    "📄 تقرير شامل"
])

# ==================== TAB 1: ملخص المؤشرات ====================
with tab1:
    st.markdown('<div class="section-header">🏆 أبرز المؤشرات (آخر فترة)</div>', unsafe_allow_html=True)

    last_ratios = all_ratios[-1]
    last_month = formatted_months[-1]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        cr_val = last_ratios['السيولة']['نسبة_التداول']['القيمة']
        cr_class = "good" if cr_val >= 1.5 else ("warn" if cr_val >= 1 else "bad")
        st.markdown(f"""
        <div class="metric-card status-{cr_class}">
            <div class="value">{cr_val:.2f}x</div>
            <div class="label">نسبة التداول</div>
            <div style="font-size:0.7rem; opacity:0.7">{last_month}</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        dr_val = last_ratios['الهيكل_المالي']['نسبة_الديون']['القيمة']
        dr_class = "good" if dr_val <= 0.4 else ("warn" if dr_val <= 0.6 else "bad")
        st.markdown(f"""
        <div class="metric-card status-{dr_class}">
            <div class="value">{dr_val * 100:.1f}%</div>
            <div class="label">نسبة الديون</div>
            <div style="font-size:0.7rem; opacity:0.7">{last_month}</div>
        </div>""", unsafe_allow_html=True)

    with col3:
        roe_val = last_ratios['الربحية']['العائد_على_حقوق_الملكية']['القيمة']
        roe_class = "good" if roe_val >= 0.15 else ("warn" if roe_val >= 0.05 else "bad")
        st.markdown(f"""
        <div class="metric-card status-{roe_class}">
            <div class="value">{roe_val * 100:.1f}%</div>
            <div class="label">العائد على حقوق الملكية</div>
            <div style="font-size:0.7rem; opacity:0.7">{last_month}</div>
        </div>""", unsafe_allow_html=True)

    with col4:
        wc_val = last_ratios['السيولة']['رأس_المال_العامل']['القيمة']
        wc_class = "good" if wc_val > 0 else "bad"
        st.markdown(f"""
        <div class="metric-card status-{wc_class}">
            <div class="value">{format_number(wc_val)}</div>
            <div class="label">رأس المال العامل</div>
            <div style="font-size:0.7rem; opacity:0.7">{last_month}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-header">📋 جدول المؤشرات المالية</div>', unsafe_allow_html=True)

    display_data = []
    for category in ['السيولة', 'النشاط_والكفاءة', 'الهيكل_المالي', 'الربحية']:
        for ratio_name, ratio_val in all_ratios[-1][category].items():
            value = ratio_val['القيمة']
            if 'نسبة' in ratio_name and 'رأس' not in ratio_name:
                formatted = f"{value:.2f}" if value < 10 else f"{value:.1f}"
                if 'تداول' in ratio_name or 'سريعة' in ratio_name or 'نقدية' in ratio_name:
                    formatted += "x"
                elif 'ديون' in ratio_name or 'حقوق' in ratio_name:
                    formatted = f"{value * 100:.1f}%"
            elif any(x in ratio_name for x in ['عائد', 'هامش']):
                formatted = f"{value * 100:.1f}%"
            elif 'يوم' in ratio_name:
                formatted = f"{value:.0f} يوم"
            else:
                formatted = format_number(value)

            display_data.append({
                'الفئة': category.replace('_', ' '),
                'المؤشر': ratio_name,
                'القيمة': formatted,
                'آخر فترة': last_month
            })

    st.dataframe(pd.DataFrame(display_data), use_container_width=True, hide_index=True)

# ==================== TAB 2: الرسوم البيانية ====================
with tab2:
    st.markdown('<div class="section-header">📈 لوحة الرسوم البيانية المتقدمة</div>', unsafe_allow_html=True)
    
    fig_advanced = create_advanced_charts(ratios_df, months, formatted_months)
    st.plotly_chart(fig_advanced, use_container_width=True)
    
    st.markdown('<div class="section-header">📊 تطور مؤشرات الأداء الرئيسية</div>', unsafe_allow_html=True)
    fig_kpi = create_kpi_timeline(ratios_df, formatted_months)
    st.plotly_chart(fig_kpi, use_container_width=True)
    
    st.markdown('<div class="section-header">🎯 تحليل الأداء والاتجاهات</div>', unsafe_allow_html=True)
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        fig_radar = create_radar_chart(ratios_df, formatted_months)
        st.plotly_chart(fig_radar, use_container_width=True)
    
    with col_chart2:
        fig_changes = create_bar_changes_chart(ratios_df)
        st.plotly_chart(fig_changes, use_container_width=True)

# ==================== TAB 3: مقارنة الفترات ====================
with tab3:
    st.markdown('<div class="section-header">📊 مقارنة الفترات المالية</div>', unsafe_allow_html=True)

    if len(months) >= 2:
        comparison_df = compare_periods(ratios_df, formatted_months)

        def color_trend(val):
            if 'up' in str(val):
                return 'color: #27ae60'
            elif 'down' in str(val):
                return 'color: #c0392b'
            return 'color: #f39c12'

        styled_df = comparison_df.style.applymap(color_trend, subset=['الاتجاه'])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

        st.markdown('<div class="section-header">📈 تحليل الاتجاهات والنمو</div>', unsafe_allow_html=True)

        trends_df = analyze_trends(ratios_df, formatted_months)

        for _, row in trends_df.iterrows():
            eval_class = "good" if 'ممتاز' in row['التقييم'] or 'جيد' in row['التقييم'] else (
                "warn" if 'بطيء' in row['التقييم'] or 'متقلب' in row['التقييم'] else "info")
            icon = '📈' if '+' in row['القيمة'] else ('📉' if '-' in row['القيمة'] else '➡️')
            st.markdown(f"""
            <div class="alert-box alert-{eval_class}">
                <strong>{icon} {row['المؤشر']}:</strong> {row['القيمة']}<br>
                📊 التقييم: {row['التقييم']}<br>
                💡 التوصية: {row['التوصية']}
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="section-header">⭐ أفضل وأسوأ الفترات</div>', unsafe_allow_html=True)

        col_best, col_worst = st.columns(2)

        with col_best:
            best_roe_idx = ratios_df['العائد_على_حقوق_الملكية'].idxmax()
            best_roe = ratios_df['العائد_على_حقوق_الملكية'].max()
            st.markdown(f"""
            <div class="metric-card status-good">
                <div class="value">{best_roe * 100:.1f}%</div>
                <div class="label">أفضل عائد على حقوق الملكية<br>{formatted_months[best_roe_idx]}</div>
            </div>
            """, unsafe_allow_html=True)

        with col_worst:
            worst_roe_idx = ratios_df['العائد_على_حقوق_الملكية'].idxmin()
            worst_roe = ratios_df['العائد_على_حقوق_الملكية'].min()
            st.markdown(f"""
            <div class="metric-card status-bad">
                <div class="value">{worst_roe * 100:.1f}%</div>
                <div class="label">أسوأ عائد على حقوق الملكية<br>{formatted_months[worst_roe_idx]}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ تحتاج إلى فترتين على الأقل لإجراء المقارنات")

# ==================== TAB 4: تحليل تفصيلي ====================
with tab4:
    st.markdown('<div class="section-header">🔍 التحليل التفصيلي لكل فترة</div>', unsafe_allow_html=True)

    period_selector = st.selectbox(
        "اختر الفترة للتحليل التفصيلي",
        options=range(len(formatted_months)),
        format_func=lambda x: formatted_months[x],
        index=len(formatted_months) - 1
    )

    selected_ratios = all_ratios[period_selector]
    selected_period = formatted_months[period_selector]

    for category, title in [('السيولة', '💧 مؤشرات السيولة'),
                            ('النشاط_والكفاءة', '🔄 مؤشرات النشاط والكفاءة'),
                            ('الهيكل_المالي', '🏗️ مؤشرات الهيكل المالي'),
                            ('الربحية', '💰 مؤشرات الربحية'),
                            ('الهيكل_الاستثماري', '📊 مؤشرات الهيكل الاستثماري')]:

        if category in selected_ratios:
            st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)

            items = list(selected_ratios[category].items())
            for i in range(0, len(items), 2):
                cols = st.columns(2)
                with cols[0]:
                    name, data = items[i]
                    render_ratio_detail(name, data, selected_period, category)
                if i + 1 < len(items):
                    with cols[1]:
                        name, data = items[i + 1]
                        render_ratio_detail(name, data, selected_period, category)

    st.markdown('<div class="section-header">📊 القيم المطلقة (آخر فترة)</div>', unsafe_allow_html=True)

    values = selected_ratios['القيم_الأصلية']
    value_data = []
    for key, val in values.items():
        value_data.append({'البند': key, 'القيمة': format_number(val)})

    st.dataframe(pd.DataFrame(value_data), use_container_width=True, hide_index=True)

# ==================== TAB 5: تقرير شامل ====================
with tab5:
    st.markdown('<div class="section-header">📄 التقرير الشامل</div>', unsafe_allow_html=True)

    st.info("""
    📋 هذا القسم يقدم تقريراً شاملاً يشمل:
    - ملخص تنفيذي لجميع الفترات
    - تحليل الاتجاهات والتغيرات
    - توصيات استراتيجية
    """)

    st.markdown('<div class="section-header">🎯 ملخص الأداء العام</div>', unsafe_allow_html=True)

    avg_roe = ratios_df['العائد_على_حقوق_الملكية'].mean()
    avg_roa = ratios_df['العائد_على_الأصول'].mean()
    avg_cr = ratios_df['نسبة_التداول'].mean()
    avg_dr = ratios_df['نسبة_الديون'].mean()

    col_avg1, col_avg2, col_avg3, col_avg4 = st.columns(4)

    with col_avg1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="value">{avg_roe * 100:.1f}%</div>
            <div class="label">متوسط ROE</div>
        </div>
        """, unsafe_allow_html=True)

    with col_avg2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="value">{avg_roa * 100:.1f}%</div>
            <div class="label">متوسط ROA</div>
        </div>
        """, unsafe_allow_html=True)

    with col_avg3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="value">{avg_cr:.2f}x</div>
            <div class="label">متوسط السيولة</div>
        </div>
        """, unsafe_allow_html=True)

    with col_avg4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="value">{avg_dr * 100:.1f}%</div>
            <div class="label">متوسط المديونية</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">💡 التوصيات الاستراتيجية</div>', unsafe_allow_html=True)

    recommendations = []

    if avg_cr < 1.5:
        recommendations.append(("تحسين السيولة", "تعزيز رأس المال العامل وتحصيل المستحقات", "warn"))
    if avg_dr > 0.5:
        recommendations.append(("خفض المديونية", "إعادة هيكلة الديون وزيادة رأس المال", "bad"))
    if avg_roe < 0.1:
        recommendations.append(("تحسين الربحية", "زيادة هامش الربح وخفض التكاليف", "warn"))
    if len(months) >= 2:
        growth = ((ratios_df['إجمالي_الأصول'].iloc[-1] - ratios_df['إجمالي_الأصول'].iloc[0]) /
                  ratios_df['إجمالي_الأصول'].iloc[0]) * 100 if ratios_df['إجمالي_الأصول'].iloc[0] != 0 else 0
        if growth < 5:
            recommendations.append(("تعزيز النمو", "التوسع في الاستثمارات المربحة", "warn"))

    if not recommendations:
        recommendations.append(("الوضع ممتاز", "الحفاظ على الأداء والمتابعة الدورية", "good"))

    for title, desc, level in recommendations:
        icon = '✅' if level == 'good' else ('⚠️' if level == 'warn' else '🔴')
        st.markdown(f"""
        <div class="alert-box alert-{level if level != 'good' else 'success'}">
            <strong>{icon} {title}:</strong><br>
            {desc}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    col_print1, col_print2, col_print3 = st.columns([1, 2, 1])
    with col_print2:
        st.markdown("""
        <div class="alert-box alert-success" style="text-align:center">
            🖨️ للطباعة: <strong>Ctrl+P</strong> (Windows) أو <strong>Cmd+P</strong> (Mac)<br>
            📄 لحفظ PDF: اختر "حفظ باسم PDF" من نافذة الطباعة<br>
            💡 القائمة الجانبية لا تظهر في النسخة المطبوعة
        </div>
        """, unsafe_allow_html=True)