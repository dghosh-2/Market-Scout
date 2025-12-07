import os
from datetime import datetime
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY


# Get the absolute path to the reports directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPORTS_DIR = os.path.join(BASE_DIR, "output", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# Colors
PRIMARY = HexColor("#1a1a2e")
SECONDARY = HexColor("#16213e")
ACCENT = HexColor("#0f3460")
TEXT_DARK = HexColor("#1a1a1a")
TEXT_LIGHT = HexColor("#666666")
BUY_COLOR = HexColor("#16a34a")
SELL_COLOR = HexColor("#dc2626")
HOLD_COLOR = HexColor("#ca8a04")
BORDER = HexColor("#e5e5e5")


def get_styles():
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        'Title_Custom',
        parent=styles['Title'],
        fontSize=28,
        textColor=PRIMARY,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=TEXT_LIGHT,
        spaceAfter=24,
        alignment=TA_CENTER,
        fontName='Helvetica'
    ))
    
    styles.add(ParagraphStyle(
        'Section_Header',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=PRIMARY,
        spaceBefore=20,
        spaceAfter=12,
        fontName='Helvetica-Bold',
        borderColor=ACCENT,
        borderWidth=0,
        borderPadding=0
    ))
    
    styles.add(ParagraphStyle(
        'Body_Text',
        parent=styles['Normal'],
        fontSize=10,
        textColor=TEXT_DARK,
        spaceAfter=8,
        alignment=TA_JUSTIFY,
        leading=14,
        fontName='Helvetica'
    ))
    
    styles.add(ParagraphStyle(
        'Recommendation_Buy',
        parent=styles['Normal'],
        fontSize=14,
        textColor=BUY_COLOR,
        spaceAfter=12,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER
    ))
    
    styles.add(ParagraphStyle(
        'Recommendation_Sell',
        parent=styles['Normal'],
        fontSize=14,
        textColor=SELL_COLOR,
        spaceAfter=12,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER
    ))
    
    styles.add(ParagraphStyle(
        'Recommendation_Hold',
        parent=styles['Normal'],
        fontSize=14,
        textColor=HOLD_COLOR,
        spaceAfter=12,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER
    ))
    
    styles.add(ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=TEXT_LIGHT,
        spaceBefore=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique'
    ))
    
    return styles


def format_number(value, prefix="", suffix="", decimals=2):
    """Format numbers with appropriate suffixes"""
    if value is None or value == "N/A":
        return "N/A"
    try:
        num = float(value)
        if abs(num) >= 1e12:
            return f"{prefix}{num/1e12:.{decimals}f}T{suffix}"
        elif abs(num) >= 1e9:
            return f"{prefix}{num/1e9:.{decimals}f}B{suffix}"
        elif abs(num) >= 1e6:
            return f"{prefix}{num/1e6:.{decimals}f}M{suffix}"
        elif abs(num) >= 1e3:
            return f"{prefix}{num/1e3:.{decimals}f}K{suffix}"
        else:
            return f"{prefix}{num:.{decimals}f}{suffix}"
    except:
        return str(value)


def format_percent(value):
    """Format as percentage"""
    if value is None or value == "N/A":
        return "N/A"
    try:
        return f"{float(value) * 100:.2f}%"
    except:
        return str(value)


def generate_report(data: Dict[str, Any], report_id: str) -> str:
    """Generate PDF report from research data"""
    
    ticker = data.get("ticker", "UNKNOWN")
    company_name = data.get("company_name", "Unknown Company")
    analysis = data.get("analysis", {})
    raw_data = data.get("raw_data", {})
    price_data = data.get("price_data", {})
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{ticker}_{timestamp}_{report_id}.pdf"
    filepath = os.path.join(REPORTS_DIR, filename)
    
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    styles = get_styles()
    story = []
    
    # Title
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("Stock Research Report", styles['Title_Custom']))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(f"{company_name} ({ticker})", styles['Section_Header']))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        styles['Subtitle']
    ))
    
    # Key metrics table
    financials = raw_data.get("financials", {})
    if financials and not financials.get("error"):
        metrics_data = [
            ["Current Price", "Market Cap", "P/E Ratio", "52W High", "52W Low"],
            [
                format_number(financials.get("current_price"), prefix="$"),
                format_number(financials.get("market_cap"), prefix="$"),
                str(round(financials.get("pe_ratio", 0), 2)) if financials.get("pe_ratio") not in [None, "N/A"] else "N/A",
                format_number(financials.get("fifty_two_week_high"), prefix="$"),
                format_number(financials.get("fifty_two_week_low"), prefix="$"),
            ]
        ]
        
        metrics_table = Table(metrics_data, colWidths=[1.4*inch]*5)
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), ACCENT),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#ffffff")),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), HexColor("#f8f9fa")),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ]))
        story.append(metrics_table)
    
    story.append(Spacer(1, 0.3*inch))
    
    # Executive Summary / Recommendation
    recommendation_text = analysis.get("recommendation", "")
    if recommendation_text:
        story.append(Paragraph("Executive Summary", styles['Section_Header']))
        
        rec_upper = recommendation_text.upper()
        if "BUY" in rec_upper[:50]:
            story.append(Paragraph("RECOMMENDATION: BUY", styles['Recommendation_Buy']))
        elif "SELL" in rec_upper[:50]:
            story.append(Paragraph("RECOMMENDATION: SELL", styles['Recommendation_Sell']))
        elif "HOLD" in rec_upper[:50]:
            story.append(Paragraph("RECOMMENDATION: HOLD", styles['Recommendation_Hold']))
        
        story.append(Paragraph(recommendation_text, styles['Body_Text']))
    
    # Company Overview
    company_overview = analysis.get("company_overview", "")
    if company_overview:
        story.append(Paragraph("Company Overview", styles['Section_Header']))
        story.append(Paragraph(company_overview, styles['Body_Text']))
    
    # Financial Analysis
    financial_analysis = analysis.get("financial_analysis", "")
    if financial_analysis:
        story.append(Paragraph("Financial Analysis", styles['Section_Header']))
        story.append(Paragraph(financial_analysis, styles['Body_Text']))
        
        # Financial metrics table
        if financials and not financials.get("error"):
            fin_data = [
                ["Metric", "Value", "Metric", "Value"],
                ["Revenue", format_number(financials.get("revenue"), prefix="$"), 
                 "Profit Margin", format_percent(financials.get("profit_margins"))],
                ["Revenue Growth", format_percent(financials.get("revenue_growth")),
                 "Operating Margin", format_percent(financials.get("operating_margins"))],
                ["EPS", f"${financials.get('earnings_per_share', 'N/A')}",
                 "ROE", format_percent(financials.get("return_on_equity"))],
                ["Total Cash", format_number(financials.get("total_cash"), prefix="$"),
                 "Total Debt", format_number(financials.get("total_debt"), prefix="$")],
                ["Debt/Equity", str(financials.get("debt_to_equity", "N/A")),
                 "Current Ratio", str(financials.get("current_ratio", "N/A"))],
            ]
            
            fin_table = Table(fin_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            fin_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), SECONDARY),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#ffffff")),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor("#ffffff")),
                ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
            ]))
            story.append(Spacer(1, 0.1*inch))
            story.append(fin_table)
    
    # Risk Assessment
    risk_analysis = analysis.get("risk_assessment", "")
    if risk_analysis:
        story.append(Paragraph("Risk Assessment", styles['Section_Header']))
        story.append(Paragraph(risk_analysis, styles['Body_Text']))
        
        risks = raw_data.get("risks", {})
        if risks and not risks.get("error"):
            risk_data = [
                ["Risk Factor", "Value"],
                ["Beta (Volatility)", str(risks.get("beta", "N/A"))],
                ["Annualized Volatility", f"{risks.get('volatility_percent', 'N/A')}%"],
                ["Short % of Float", format_percent(risks.get("short_percent_of_float"))],
                ["Debt to Equity", str(risks.get("debt_to_equity", "N/A"))],
                ["Current Ratio", str(risks.get("current_ratio", "N/A"))],
            ]
            
            risk_table = Table(risk_data, colWidths=[3*inch, 2*inch])
            risk_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), SECONDARY),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#ffffff")),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
            ]))
            story.append(Spacer(1, 0.1*inch))
            story.append(risk_table)
    
    # News Analysis
    news_analysis = analysis.get("news_analysis", "")
    if news_analysis:
        story.append(Paragraph("News and Market Sentiment", styles['Section_Header']))
        story.append(Paragraph(news_analysis, styles['Body_Text']))
        
        news = raw_data.get("news", {})
        if news and news.get("articles"):
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph("Recent Headlines:", styles['Body_Text']))
            for article in news["articles"][:5]:
                title = article.get("title", "")
                publisher = article.get("publisher", "")
                story.append(Paragraph(f"- {title} ({publisher})", styles['Body_Text']))
    
    # Price Performance
    if price_data and not price_data.get("error"):
        story.append(Paragraph("Price Performance", styles['Section_Header']))
        change = price_data.get("change_percent", 0)
        change_color = "green" if change >= 0 else "red"
        story.append(Paragraph(
            f"1-Year Change: <font color='{change_color}'>{change:+.2f}%</font> "
            f"(${price_data.get('start_price', 0):.2f} to ${price_data.get('end_price', 0):.2f})",
            styles['Body_Text']
        ))
    
    # Disclaimer
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(
        "DISCLAIMER: This report is for informational purposes only and should not be considered investment advice. "
        "Past performance does not guarantee future results. Always conduct your own due diligence before making investment decisions.",
        styles['Disclaimer']
    ))
    
    doc.build(story)
    
    return f"/reports/{filename}"
