"""
Build policy brief PDF for the 2024 County-Level Partisan Swing Analysis.

Run from the repo root:
    python docs/build_policy_brief.py

Outputs: docs/policy_brief.pdf
"""

import os
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
    KeepTogether,
    PageBreak,
)
from reportlab.lib import colors

REPO = Path(__file__).resolve().parent.parent
OUT_PDF = REPO / "docs" / "policy_brief.pdf"

# --- Colors ---
NAVY = HexColor("#1B2A4A")
DARK_TEAL = HexColor("#1A6B5C")
LIGHT_TEAL_BG = HexColor("#E8F4F0")
TEAL_BORDER = HexColor("#2D8B73")
DARK_GRAY = HexColor("#333333")
MID_GRAY = HexColor("#666666")
LIGHT_GRAY = HexColor("#AAAAAA")

# --- Styles ---
style_title = ParagraphStyle(
    "Title",
    fontName="Helvetica-Bold",
    fontSize=18,
    leading=22,
    textColor=NAVY,
    spaceAfter=4,
)

style_subtitle = ParagraphStyle(
    "Subtitle",
    fontName="Helvetica",
    fontSize=10,
    leading=14,
    textColor=MID_GRAY,
    spaceAfter=14,
)

style_section = ParagraphStyle(
    "Section",
    fontName="Helvetica-Bold",
    fontSize=13,
    leading=16,
    textColor=NAVY,
    spaceBefore=16,
    spaceAfter=6,
)

style_subsection = ParagraphStyle(
    "Subsection",
    fontName="Helvetica-Bold",
    fontSize=10.5,
    leading=14,
    textColor=DARK_TEAL,
    spaceBefore=10,
    spaceAfter=4,
)

style_body = ParagraphStyle(
    "Body",
    fontName="Helvetica",
    fontSize=9.5,
    leading=13.5,
    textColor=DARK_GRAY,
    alignment=TA_JUSTIFY,
    spaceAfter=8,
)

style_bullet = ParagraphStyle(
    "Bullet",
    fontName="Helvetica",
    fontSize=9.5,
    leading=13.5,
    textColor=DARK_GRAY,
    leftIndent=18,
    bulletIndent=6,
    spaceAfter=6,
)

style_lede = ParagraphStyle(
    "Lede",
    fontName="Helvetica",
    fontSize=10.5,
    leading=15,
    textColor=DARK_GRAY,
    spaceAfter=12,
)

style_caption = ParagraphStyle(
    "Caption",
    fontName="Helvetica-Oblique",
    fontSize=8,
    leading=10,
    textColor=MID_GRAY,
    alignment=TA_CENTER,
    spaceAfter=10,
)

style_methods_label = ParagraphStyle(
    "MethodsLabel",
    fontName="Helvetica-Bold",
    fontSize=9,
    leading=12,
    textColor=NAVY,
    spaceAfter=3,
)

style_methods = ParagraphStyle(
    "Methods",
    fontName="Helvetica",
    fontSize=8.5,
    leading=12,
    textColor=MID_GRAY,
)

style_footer = ParagraphStyle(
    "Footer",
    fontName="Helvetica",
    fontSize=7.5,
    textColor=LIGHT_GRAY,
)


def footer_canvas(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(LIGHT_GRAY)
    canvas.drawString(
        inch, 0.5 * inch,
        f"County-Level Swing Analysis  |  Kaleb Mazurek  |  Page {doc.page}",
    )
    canvas.restoreState()


def key_findings_box(elements):
    """Build the shaded Key Findings box as a single-cell table."""
    box_title = Paragraph(
        "<b>KEY FINDINGS</b>",
        ParagraphStyle(
            "BoxTitle",
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=DARK_TEAL,
            spaceAfter=6,
        ),
    )

    bullets = [
        Paragraph(
            "<bullet>&bull;</bullet>"
            "<b>A third of the swing story is state-level, not county-level.</b> "
            "30.5% of the variation in how much counties swung toward Republicans "
            "is explained by which state they are in, suggesting that state-level forces "
            "like media markets, campaign spending, and political environment matter "
            "as much as local demographics.",
            style_bullet,
        ),
        Paragraph(
            "<bullet>&bull;</bullet>"
            "<b>Hispanic population share is the strongest predictor of rightward swing.</b> "
            "A 10-percentage-point higher Hispanic share predicts about 0.46 pp more "
            "Republican swing (p &lt; 10<super>-71</super>), consistent with the rightward shift among Latino voters "
            "documented in Pew and Catalist post-election studies.",
            style_bullet,
        ),
        Paragraph(
            "<bullet>&bull;</bullet>"
            "<b>Education polarization varies by state, but economic conditions don't explain why.</b> "
            "The education-swing gradient differs significantly across states "
            "(LR test p &lt; 10<super>-16</super>), but state-level unemployment change "
            "does not account for that variation (interaction p = 0.48). "
            "Other state-level factors, like media environment or campaign intensity, "
            "are likely drivers.",
            style_bullet,
        ),
    ]

    content = [box_title] + bullets
    t = Table([[content]], colWidths=[6.5 * inch])
    t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_TEAL_BG),
            ("BOX", (0, 0), (-1, -1), 1.5, TEAL_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ])
    )
    elements.append(t)
    elements.append(Spacer(1, 10))


def build_pdf():
    doc = SimpleDocTemplate(
        str(OUT_PDF),
        pagesize=letter,
        leftMargin=inch,
        rightMargin=inch,
        topMargin=inch,
        bottomMargin=0.85 * inch,
    )
    elements = []

    # ---- PAGE 1 ----

    # Title
    elements.append(Paragraph(
        "Where Did the 2024 Swing Come From?<br/>"
        "A County-Level Analysis of the Partisan Shift",
        style_title,
    ))
    elements.append(Paragraph(
        "Kaleb Mazurek  |  March 2026",
        style_subtitle,
    ))

    # Lede
    elements.append(Paragraph(
        "The average US county swung 1.7 percentage points toward Republicans between 2020 "
        "and 2024, but the variation was enormous: some counties shifted 13 points right while "
        "others moved 7 points left. Standard single-level models can't tell you how much of "
        "this story is state-level versus county-level. A multilevel analysis of 3,101 counties "
        "across 49 states and DC can, and the answer reshapes how we think about what drove "
        "the shift and where.",
        style_lede,
    ))

    # Key Findings box
    key_findings_box(elements)

    # Why This Matters
    elements.append(Paragraph("Why This Matters", style_section))
    elements.append(Paragraph(
        "For campaign strategists, these findings challenge the assumption that national "
        "demographic targeting models will perform equally well in every state. The same "
        "education-based targeting strategy that identifies persuadable voters in Pennsylvania "
        "may be less useful in Florida or Texas, where the education gradient was steeper or "
        "flatter than the national average. For advocacy organizations and political researchers, "
        "the large state-level component points toward structural forces, such as media "
        "environments, state party organizing capacity, and ballot initiative effects, that "
        "deserve as much attention as county-level demographic composition. The Hispanic "
        "population finding should prompt investment in better data on Latino political "
        "attitudes, rather than treating the rightward shift as a monolithic phenomenon.",
        style_body,
    ))

    # ---- PAGE 2 ----
    elements.append(PageBreak())

    elements.append(Paragraph("What We Found", style_section))

    # State vs county
    elements.append(Paragraph("The state vs. county story", style_subsection))
    elements.append(Paragraph(
        "Before adding any demographic predictors, a simple model that only accounts for "
        "state groupings shows that 30.5% of the total variation in county swing "
        "sits between states, not between counties within states. This intraclass correlation "
        "of 0.305 means that knowing which state a county is in already explains nearly a "
        "third of its swing. Standard single-level regression models that ignore this "
        "nesting structure would produce misleading standard errors and overstate the "
        "precision of their estimates. Whatever drove the 2024 swing operated partly at "
        "a level above county demographics.",
        style_body,
    ))

    # Hispanic puzzle
    elements.append(Paragraph("The Hispanic county puzzle", style_subsection))
    elements.append(Paragraph(
        "Hispanic population share is the single strongest predictor of rightward swing in "
        "the model. A 10-percentage-point increase in a county's Hispanic share is associated "
        "with a 0.46 pp larger Republican swing (p &lt; 10<super>-71</super>), after "
        "controlling for education, income, population density, prior partisanship, "
        "racial composition, and urban-rural classification. The pattern is driven heavily "
        "by South Texas, the Florida I-4 corridor, and Southern California, but it holds "
        "nationally. An important caution: this is a county-level finding, not an "
        "individual-level one. We cannot say that individual Hispanic voters shifted right; "
        "we can say that places with more Hispanic residents swung further right, which "
        "could reflect a combination of voter persuasion, differential turnout, and "
        "compositional shifts in who lives in these counties.",
        style_body,
    ))

    # Figure: Hispanic scatter
    fig_hispanic = REPO / "figures" / "hispanic_highlighted_states.png"
    if fig_hispanic.exists():
        elements.append(Spacer(1, 4))
        img = Image(str(fig_hispanic), width=4.2 * inch, height=2.8 * inch)
        elements.append(img)
        elements.append(Paragraph(
            "Figure 1. Counties with larger Hispanic populations swung further toward "
            "Republicans. Key states highlighted; bubble size reflects population.",
            style_caption,
        ))

    # Education effect
    elements.append(Paragraph(
        "Education polarization: real but uneven", style_subsection
    ))
    elements.append(Paragraph(
        "A 10-percentage-point higher college-educated share predicts a 0.60 pp smaller "
        "Republican swing (p &lt; 10<super>-23</super>). This confirms the now-familiar "
        "education polarization story: more-educated places resisted the rightward shift. "
        "But the size of this effect varies significantly across states. Adding a random slope "
        "for education improves the model substantially (likelihood ratio test: "
        "chi-squared = 72.4, p &lt; 10<super>-16</super>). In some states, the education "
        "gradient was steep; in others, it was nearly flat.",
        style_body,
    ))
    elements.append(Paragraph(
        "The natural follow-up question is why. We tested whether state-level economic "
        "conditions, measured as the change in state unemployment rate from 2020 to 2024, "
        "could explain the cross-state variation in the education effect. They could not. "
        "The cross-level interaction is not statistically significant (p = 0.48), and "
        "adding it to the model slightly worsens fit (AIC rises from -18,575 to -18,572). "
        "Education polarization operates differently across states, but the source of "
        "that variation remains an open question, one that likely involves media environment, "
        "campaign strategy, or state political culture rather than economic conditions.",
        style_body,
    ))

    # ---- PAGE 3 (continuation) ----

    # Limitations
    elements.append(Paragraph("What This Doesn't Tell Us", style_section))
    elements.append(Paragraph(
        "This analysis describes county-level patterns, not individual voter behavior. "
        "The ecological fallacy applies: a county's demographic profile predicts its swing, "
        "but that does not mean the individuals matching those demographics drove the change. "
        "The models also do not account for spatial dependencies between neighboring "
        "counties or for compositional changes in who turned out to vote in 2024 versus 2020. "
        "Survey data and voter-file analyses would complement these findings by connecting "
        "place-level patterns to individual-level decisions.",
        style_body,
    ))

    # Data & Methods box
    elements.append(Spacer(1, 6))
    methods_content = [
        Paragraph("DATA &amp; METHODS", style_methods_label),
        Paragraph(
            "Multilevel linear models (counties nested within states) fit with "
            "statsmodels MixedLM. Election returns from the MIT Election Data + Science Lab "
            "(MEDSL); demographics from the American Community Survey 5-year estimates "
            "(2019-2023); state unemployment from the Bureau of Labor Statistics; "
            "urban-rural classification from the NCHS 2013 scheme. "
            "N = 3,101 counties in 49 states + DC (Alaska excluded due to non-standard "
            "county-equivalents). Multilevel models account for the grouping of counties "
            "within states, producing correct standard errors and allowing effects to vary "
            "across states, which single-level regression cannot do.",
            style_methods,
        ),
    ]
    methods_table = Table([[methods_content]], colWidths=[6.5 * inch])
    methods_table.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.75, LIGHT_GRAY),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ])
    )
    elements.append(methods_table)
    elements.append(Spacer(1, 14))

    # Links and contact
    elements.append(Paragraph(
        "<b>Full analysis and code:</b> "
        '<a href="https://github.com/kmazurek95/us-election-county-swing" '
        'color="#1A6B5C">github.com/kmazurek95/us-election-county-swing</a>',
        ParagraphStyle(
            "Link", parent=style_body, fontSize=9, textColor=DARK_GRAY, spaceAfter=3,
        ),
    ))
    elements.append(Paragraph(
        "<b>Interactive dashboard:</b> "
        '<a href="https://us-election-county-swing-9ovbfe8vvncgikvc4ftgrz.streamlit.app/" '
        'color="#1A6B5C">us-election-county-swing-9ovbfe8vvncgikvc4ftgrz.streamlit.app</a>',
        ParagraphStyle(
            "Link", parent=style_body, fontSize=9, textColor=DARK_GRAY, spaceAfter=10,
        ),
    ))
    elements.append(Paragraph(
        "Kaleb Mazurek",
        ParagraphStyle(
            "Author", fontName="Helvetica-Bold", fontSize=9, textColor=NAVY,
            spaceAfter=0,
        ),
    ))

    # Build
    doc.build(elements, onFirstPage=footer_canvas, onLaterPages=footer_canvas)
    print(f"PDF saved to {OUT_PDF}")


if __name__ == "__main__":
    build_pdf()
