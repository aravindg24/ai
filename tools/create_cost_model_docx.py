import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def set_cell_shading(cell, color_hex):
    """Apply background color to a cell."""
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set padding in dxa (1 pt = 20 dxa)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_table_borders(table, color="D1D5DB", sz="4"):
    """Set subtle gray borders for a table."""
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:left w:val="none"/>'
        f'  <w:bottom w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:right w:val="none"/>'
        f'  <w:insideH w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:insideV w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def add_callout(doc, text, bold_prefix="NOTE: ", border_color="2B6CB0", bg_color="F0F4F8"):
    """Add a shaded callout container box."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_shading(cell, bg_color)
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
    
    # Left border only
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'  <w:top w:val="none"/>'
        f'  <w:left w:val="single" w:sz="24" w:space="0" w:color="{border_color}"/>'
        f'  <w:bottom w:val="none"/>'
        f'  <w:right w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.bold = True
        r_pre.font.name = "Arial"
        r_pre.font.size = Pt(10)
        r_pre.font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)
    r_body = p.add_run(text)
    r_body.font.name = "Arial"
    r_body.font.size = Pt(10)
    r_body.font.color.rgb = RGBColor(0x2D, 0x37, 0x48)
    doc.add_paragraph().paragraph_format.space_after = Pt(6)

def build_document(output_path):
    doc = docx.Document()
    
    # Page Setup: Standard Letter, 1 inch margins
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        
        # Header / Footer (Clean public open-source footer)
        footer = section.footer
        f_p = footer.paragraphs[0]
        f_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        f_r = f_p.add_run("Saayam GenAI Microservices — Cost Model & Capacity Review")
        f_r.font.name = "Arial"
        f_r.font.size = Pt(8.5)
        f_r.font.color.rgb = RGBColor(0x71, 0x80, 0x96)

    # Styles & Colors
    NAVY = RGBColor(0x1A, 0x36, 0x5D)
    SLATE = RGBColor(0x2D, 0x37, 0x48)
    MUTED = RGBColor(0x71, 0x80, 0x96)
    BLUE_ACCENT = RGBColor(0x2B, 0x6C, 0xB0)
    
    # -------------------------------------------------------------------------
    # COVER / HEADER BLOCK
    # -------------------------------------------------------------------------
    p_pre = doc.add_paragraph()
    p_pre.paragraph_format.space_before = Pt(0)
    p_pre.paragraph_format.space_after = Pt(4)
    r_pre = p_pre.add_run("ENGINEERING & LEADERSHIP REVIEW")
    r_pre.font.name = "Arial"
    r_pre.font.size = Pt(9.5)
    r_pre.bold = True
    r_pre.font.color.rgb = BLUE_ACCENT
    
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(4)
    r_title = p_title.add_run("GenAI Cost Model & Capacity Review")
    r_title.font.name = "Arial"
    r_title.font.size = Pt(24)
    r_title.bold = True
    r_title.font.color.rgb = NAVY
    
    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(12)
    r_sub = p_sub.add_run("Empirical Baseline, Floor vs. Ceiling Range, Capacity Constraints, and Operational Governance")
    r_sub.font.name = "Arial"
    r_sub.font.size = Pt(13)
    r_sub.font.color.rgb = SLATE

    # Metadata Summary Table
    meta_table = doc.add_table(rows=2, cols=4)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(meta_table, color="E2E8F0")
    meta_headers = ["Issue / Project", "Rates Verified", "Model Currency Check", "Target Audience"]
    meta_values = ["[P1] Issue #194", "16 September 2026", "28 September 2026 (Live)", "Leadership & AI Team"]
    
    for i in range(4):
        c_h = meta_table.cell(0, i)
        set_cell_shading(c_h, "F7FAFC")
        set_cell_margins(c_h, top=80, bottom=80, left=100, right=100)
        p = c_h.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(meta_headers[i])
        r.font.name = "Arial"
        r.font.size = Pt(8.5)
        r.bold = True
        r.font.color.rgb = MUTED
        
        c_v = meta_table.cell(1, i)
        set_cell_margins(c_v, top=80, bottom=80, left=100, right=100)
        p = c_v.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(meta_values[i])
        r.font.name = "Arial"
        r.font.size = Pt(9.5)
        r.bold = True
        r.font.color.rgb = NAVY

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # -------------------------------------------------------------------------
    # 1. Executive Summary
    # -------------------------------------------------------------------------
    h1 = doc.add_heading("1. Executive Summary & Core Findings", level=1)
    h1.paragraph_format.space_before = Pt(16)
    h1.paragraph_format.space_after = Pt(6)
    for r in h1.runs:
        r.font.name = "Arial"
        r.font.color.rgb = NAVY
        
    p = doc.add_paragraph(
        "This cost model responds directly to leadership direction: 'We should be using the latest and "
        "the greatest LLM model services at the cheapest price... Please come up with our cost model — "
        "how much we are spending now, how much we may have to pay based on approximate end users, "
        "and monitor this expense regularly.' Across 2025–2026, research was requested four times but never "
        "crystallized into a durable, dated artifact. Following the token baseline audit (TOKEN_BASELINE.md, PR #189) "
        "and fixing LangChain reasoning double counting (commit 28688c2), costs are presented as an empirical range:"
    )
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(8)

    # Executive Range Table
    tbl_exec = doc.add_table(rows=1, cols=4)
    tbl_exec.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_exec)
    
    exec_headers = ["Metric", "Initial Estimate (16 Sep)", "Floor (Clean Baseline)", "Measured Mean (Ceiling)"]
    for i, h in enumerate(exec_headers):
        c = tbl_exec.cell(0, i)
        set_cell_shading(c, "1A365D")
        set_cell_margins(c, top=80, bottom=80, left=100, right=100)
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h)
        r.font.name = "Arial"
        r.font.size = Pt(9)
        r.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    exec_data = [
        ("Tokens per Help Request", "3,434", "~4,990", "8,116"),
        ("Cost per Help Request (Groq)", "$0.000433", "~$0.00072", "~$0.00163"),
        ("Cost per 1,000 Requests", "$0.43", "~$0.72", "~$1.63"),
        ("Free-Tier Daily Capacity", "58 / day", "~40 / day", "~24 / day"),
        ("Self-Hosting Breakeven", "~875,000 / mo", "~524,000 / mo", "~233,000 / mo")
    ]
    for row_idx, row in enumerate(exec_data):
        r_cells = tbl_exec.add_row().cells
        bg = "F7FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for i, val in enumerate(row):
            set_cell_shading(r_cells[i], bg)
            set_cell_margins(r_cells[i], top=70, bottom=70, left=100, right=100)
            p = r_cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            r.font.name = "Arial"
            r.font.size = Pt(9)
            if i == 0:
                r.bold = True
                r.font.color.rgb = NAVY
            else:
                r.font.color.rgb = SLATE

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    add_callout(
        doc,
        "1. Predictable, Low Unit Cost: Model inference costs ~$0.00072 to ~$0.00163 per request on Groq (<$2/1k requests).\n"
        "2. The Real Risk is Capacity, Not Cost: Groq's free tier (200k tokens/day) caps the platform at 24 to 40 requests/day. "
        "The capacity cliff arrives much sooner than the initial 58/day estimate. Moving to Pay-As-You-Go (<$10/mo near-term) is vital.\n"
        "3. Failover Multiplier: Sustained failover to Gemini 2.5 Flash is at least 6.8× and up to 15×+ when empty-result fallback "
        "and thinking tokens trigger large completions.\n"
        "4. Self-Hosting Disproven (#23): Dedicated EC2 GPU hosting ($378.72/mo) is economically unviable until volume exceeds "
        "~233,000 to ~524,000 requests/month.",
        bold_prefix="EXECUTIVE HIGHLIGHTS:\n"
    )

    # -------------------------------------------------------------------------
    # 2. Token Baseline per Service
    # -------------------------------------------------------------------------
    h2 = doc.add_heading("2. Measured Token Baseline per Microservice", level=1)
    h2.paragraph_format.space_before = Pt(14)
    h2.paragraph_format.space_after = Pt(6)
    for r in h2.runs:
        r.font.name = "Arial"
        r.font.color.rgb = NAVY

    doc.add_paragraph(
        "Token sizes were directly measured using tiktoken (o200k_base) against live prompt builders and "
        "benchmarked in docs/metrics/token_baseline.json across 8 diverse help request scenarios:"
    ).paragraph_format.space_after = Pt(6)

    # Table: Tokens
    tbl_tokens = doc.add_table(rows=1, cols=6)
    tbl_tokens.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_tokens)
    
    headers = ["Service", "Calls", "Prompt Tokens", "Completion Tokens", "Total Tokens", "Operational Notes"]
    for i, h in enumerate(headers):
        c = tbl_tokens.cell(0, i)
        set_cell_shading(c, "1A365D")
        set_cell_margins(c, top=100, bottom=100, left=100, right=100)
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h)
        r.font.name = "Arial"
        r.font.size = Pt(9)
        r.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    token_data = [
        ("predict_category", "2.25", "1,172", "258 (mean)", "1,430", "Hierarchical descent over 49 categories; raw Groq SDK."),
        ("search_orgs", "1.12", "1,188–1,292", "888–1,014 (970 mean)", "~2,210–3,710", "Structured 6 orgs × 13 fields; prompt is ~1,240 tokens."),
        ("generate_subject", "1.00", "523", "20 (clean) to 1,515 (mean)", "543–2,038", "70-char title. High reasoning caused ceiling hits."),
        ("generate_answer", "1.00", "528", "300 (clean) to 410 (meas)", "828–938", "Tailored guidance turn for beneficiary."),
        ("emergency_contacts", "0.00", "0", "0", "0", "Deterministic country database; zero model calls."),
        ("Total (Floor: Clean Baseline)", "~5.4", "3,442", "1,548", "~4,990", "Reasoning double-count removed; conservative completions."),
        ("Total (Ceiling: Measured Mean)", "~5.4", "3,586", "4,530", "8,116", "Empirical mean across benchmark runs with pre-fix counts.")
    ]

    for row_idx, row in enumerate(token_data):
        r_cells = tbl_tokens.add_row().cells
        is_highlight = "Total" in row[0]
        bg = "EDF2F7" if is_highlight else ("FAFAFA" if row_idx % 2 == 1 else "FFFFFF")
        for i, val in enumerate(row):
            set_cell_shading(r_cells[i], bg)
            set_cell_margins(r_cells[i], top=80, bottom=80, left=100, right=100)
            p = r_cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            r.font.name = "Arial"
            r.font.size = Pt(9)
            if is_highlight:
                r.bold = True
                r.font.color.rgb = NAVY
            else:
                r.font.color.rgb = SLATE

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # -------------------------------------------------------------------------
    # 3. Provider Rates & Arithmetic
    # -------------------------------------------------------------------------
    h3 = doc.add_heading("3. Provider Rates & Unit Cost Arithmetic", level=1)
    h3.paragraph_format.space_before = Pt(14)
    h3.paragraph_format.space_after = Pt(6)
    for r in h3.runs:
        r.font.name = "Arial"
        r.font.color.rgb = NAVY

    doc.add_paragraph(
        "Rates verified on 16 September 2026 and confirmed live on 28 September 2026. Classification uses the 4-tier chain "
        "(PR #199: 20b → 120b → safeguard-20b → Gemini), while other services use 20b → Gemini:"
    ).paragraph_format.space_after = Pt(6)

    tbl_rates = doc.add_table(rows=1, cols=5)
    tbl_rates.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_rates)
    
    rate_headers = ["Provider", "Model Role / Tier", "Input / 1M", "Output / 1M", "Free Tier Allowances"]
    for i, h in enumerate(rate_headers):
        c = tbl_rates.cell(0, i)
        set_cell_shading(c, "1A365D")
        set_cell_margins(c, top=100, bottom=100, left=100, right=100)
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h)
        r.font.name = "Arial"
        r.font.size = Pt(9)
        r.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    rate_rows = [
        ("Groq (Primary)", "openai/gpt-oss-20b", "$0.075", "$0.30", "30 RPM, 1,000 RPD, 8,000 TPM, 200,000 TPD"),
        ("Groq (Tier 2)", "openai/gpt-oss-120b", "$0.150", "$0.60", "30 RPM, 1,000 RPD, 8,000 TPM, 200,000 TPD"),
        ("Groq (Tier 3)", "openai/gpt-oss-safeguard-20b (Preview)", "$0.075", "$0.30", "Evaluation preview; subject to withdrawal"),
        ("Google (Fallback)", "gemini-2.5-flash", "$0.300", "$2.50", "15 RPM, 1,500 RPD, 1,000,000 TPM (to confirm in AI Studio)")
    ]
    for row_idx, row in enumerate(rate_rows):
        r_cells = tbl_rates.add_row().cells
        for i, val in enumerate(row):
            set_cell_shading(r_cells[i], "FFFFFF" if row_idx % 2 == 0 else "F7FAFC")
            set_cell_margins(r_cells[i], top=80, bottom=80, left=100, right=100)
            p = r_cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            r.font.name = "Arial"
            r.font.size = Pt(9)
            r.font.color.rgb = SLATE

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    add_callout(
        doc,
        "• Floor Cost (Groq): (3,442 prompt × $0.075/1M) + (1,548 completion × $0.30/1M) = $0.00025815 + $0.00046440 = $0.000723 (~$0.00072/req).\n"
        "• Ceiling Cost (Groq): (3,586 prompt × $0.075/1M) + (4,530 completion × $0.30/1M) = $0.00026895 + $0.00135900 = $0.001628 (~$0.00163/req).\n"
        "• Fallback Cost (Gemini Floor): (3,442 × $0.30/1M) + (1,548 × $2.50/1M) = $0.00103260 + $0.00387000 = $0.004903 (~$0.00490/req).\n"
        "• Failover Multiplier: Nominal rate ratio is 6.8×; in production, empty-result fallbacks and thinking tokens reach 15×+.",
        bold_prefix="REPRODUCIBLE ARITHMETIC:\n",
        border_color="2B6CB0",
        bg_color="EDF2F7"
    )

    # -------------------------------------------------------------------------
    # 4. Volume Projections
    # -------------------------------------------------------------------------
    h4 = doc.add_heading("4. Monthly Volume Projections", level=1)
    h4.paragraph_format.space_before = Pt(14)
    h4.paragraph_format.space_after = Pt(6)
    for r in h4.runs:
        r.font.name = "Arial"
        r.font.color.rgb = NAVY

    doc.add_paragraph(
        "Projected monthly expenditures across scaling volumes (using placeholder of 1.0 request/active user/month):"
    ).paragraph_format.space_after = Pt(6)

    tbl_proj = doc.add_table(rows=1, cols=4)
    tbl_proj.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_proj)
    
    proj_headers = ["Monthly Help Requests", "Spend on Groq (Floor: $0.00072)", "Spend on Groq (Ceiling: $0.00163)", "Sustained Gemini Fallback"]
    for i, h in enumerate(proj_headers):
        c = tbl_proj.cell(0, i)
        set_cell_shading(c, "1A365D")
        set_cell_margins(c, top=100, bottom=100, left=100, right=100)
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h)
        r.font.name = "Arial"
        r.font.size = Pt(9)
        r.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    proj_data = [
        ("1,000", "$0.72", "$1.63", "$4.90 – $16.30"),
        ("10,000", "$7.23", "$16.28", "$49.03 – $162.80"),
        ("50,000", "$36.13", "$81.40", "$245.13 – $814.00"),
        ("100,000", "$72.26", "$162.80", "$490.26 – $1,628.00"),
        ("500,000", "$361.28", "$813.98", "$2,451.30 – $8,139.75"),
        ("1,000,000", "$722.55", "$1,627.95", "$4,902.60 – $16,279.50")
    ]
    for row_idx, row in enumerate(proj_data):
        r_cells = tbl_proj.add_row().cells
        bg = "F7FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for i, val in enumerate(row):
            set_cell_shading(r_cells[i], bg)
            set_cell_margins(r_cells[i], top=80, bottom=80, left=100, right=100)
            p = r_cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            r.font.name = "Arial"
            r.font.size = Pt(9)
            r.font.color.rgb = SLATE

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # -------------------------------------------------------------------------
    # 5. Capacity Constraints & Operational Risks
    # -------------------------------------------------------------------------
    h5 = doc.add_heading("5. Operational Risks & Capacity Constraints", level=1)
    h5.paragraph_format.space_before = Pt(14)
    h5.paragraph_format.space_after = Pt(6)
    for r in h5.runs:
        r.font.name = "Arial"
        r.font.color.rgb = NAVY

    doc.add_paragraph(
        "• The Free-Tier Cliff (24–40 Requests/Day): Groq limits free tier organizations to 200,000 tokens/day. "
        "Dividing 200,000 by 4,990 tokens (Floor) gives ~40 requests/day, and by 8,116 tokens (Ceiling) gives ~24 requests/day. "
        "The platform is strictly token-bound, not request-bound. Moving to Groq's Pay-As-You-Go tier costs single-digit dollars (<$10/mo) "
        "and must be enabled before launch to eliminate HTTP 429 failures.\n\n"
        "• Caller-Controlled Transcript Ballooning: utils/__init__.py sets MAX_HISTORY_MESSAGES = 20 and "
        "MAX_MESSAGE_CHARS = 4000. A worst-case follow-up contains 16,781 tokens. Just 12 worst-case requests "
        "exhaust the entire daily quota. Furthermore, 16,781 tokens exceeds Groq's 8,000 TPM limit and fails immediately.\n\n"
        "• Silent Failover & Empty-Result Triggering: When Groq fails or when search_orgs returns zero organizations, "
        "the system silently invokes Gemini 2.5 Flash, incurring at least a 6.8× cost multiplier and risking 12k+ token completions."
    ).paragraph_format.line_spacing = 1.15

    # -------------------------------------------------------------------------
    # 6. Self-Hosting Feasibility (Issue #23)
    # -------------------------------------------------------------------------
    h6 = doc.add_heading("6. Self-Hosting Feasibility (Resolution of Issue #23)", level=1)
    h6.paragraph_format.space_before = Pt(14)
    h6.paragraph_format.space_after = Pt(6)
    for r in h6.runs:
        r.font.name = "Arial"
        r.font.color.rgb = NAVY

    add_callout(
        doc,
        "An on-demand AWS EC2 GPU instance (g4dn.xlarge, 1x NVIDIA T4) costs ~$0.526/hour in us-east-1, totaling "
        "~$378.72/month fixed cost even at zero requests.\n\n"
        "• At Floor ($0.000723/req): $378.72 ÷ $0.00072255 = ~524,000 requests/month (~17,500/day).\n"
        "• At Ceiling ($0.001628/req): $378.72 ÷ $0.00162795 = ~233,000 requests/month (~7,700/day).\n"
        "(Historical note: $378.72 ÷ $0.000433 = 874,541 requests/month).\n\n"
        "Verdict: Serverless API inference remains decisively cheaper than maintaining GPU instances until the platform "
        "surpasses a quarter-million to half-million requests per month, while completely avoiding operational maintenance.",
        bold_prefix="SELF-HOSTING ECONOMIC VERDICT:\n",
        border_color="C53030",
        bg_color="FFF5F5"
    )

    # -------------------------------------------------------------------------
    # 7. Model Strategy: Tiering vs Frontier
    # -------------------------------------------------------------------------
    h7 = doc.add_heading("7. Model Strategy: Tiering vs. Frontier Models", level=1)
    h7.paragraph_format.space_before = Pt(14)
    h7.paragraph_format.space_after = Pt(6)
    for r in h7.runs:
        r.font.name = "Arial"
        r.font.color.rgb = NAVY

    doc.add_paragraph(
        "Leadership's objective to use 'the latest and greatest at the cheapest price' requires microservice tiering, "
        "not a single frontier model. Frontier models cost 10× to 50× more and offer zero benefit for structured classification "
        "or string generation. Standing Policy: Route each microservice to the lowest-cost model satisfying its quality bar; "
        "reserve frontier models strictly for services where reasoning and empathy touch the person (generate_answer)."
    ).paragraph_format.line_spacing = 1.15

    # -------------------------------------------------------------------------
    # 8. Open Access Gaps & Stakeholder Action Items
    # -------------------------------------------------------------------------
    h8 = doc.add_heading("8. Open Gaps Requiring Stakeholder Confirmation", level=1)
    h8.paragraph_format.space_before = Pt(14)
    h8.paragraph_format.space_after = Pt(6)
    for r in h8.runs:
        r.font.name = "Arial"
        r.font.color.rgb = NAVY

    tbl_gaps = doc.add_table(rows=1, cols=4)
    tbl_gaps.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_gaps)
    
    gap_headers = ["Gap Area", "Responsible Owner / Inquired Leads", "Current Documented State", "Action Needed for Review"]
    for i, h in enumerate(gap_headers):
        c = tbl_gaps.cell(0, i)
        set_cell_shading(c, "1A365D")
        set_cell_margins(c, top=100, bottom=100, left=100, right=100)
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h)
        r.font.name = "Arial"
        r.font.size = Pt(9)
        r.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    gap_data = [
        ("Requests / User / Month", "Product & Request Teams (@srush-shah, @shivam131284, @MustakimFS)", "Modeled at 1.0 request/active user/mo (inquired 28 Sep 2026).", "Provide historical or forecasted monthly request frequency."),
        ("Lambda Memory & Timeout", "DevOps / AWS Cloud Admin", "Deploy workflow sets timeout for 1 function and memory for none (inquired 28 Sep 2026).", "Read current live memory (MB) and timeout (s) from AWS console."),
        ("Account Billing Tiers", "DevOps / Account Admin", "Checking Free vs Paid tier and Nov 2025 non-profit grant credits (inquired 28 Sep 2026).", "Confirm if Groq/Google accounts are on paid tier or have non-profit grant.")
    ]
    for row_idx, row in enumerate(gap_data):
        r_cells = tbl_gaps.add_row().cells
        bg = "F7FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for i, val in enumerate(row):
            set_cell_shading(r_cells[i], bg)
            set_cell_margins(r_cells[i], top=80, bottom=80, left=100, right=100)
            p = r_cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            r.font.name = "Arial"
            r.font.size = Pt(8.5)
            r.font.color.rgb = SLATE

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # -------------------------------------------------------------------------
    # 9. Model Currency & Deprecation Audit
    # -------------------------------------------------------------------------
    h9 = doc.add_heading("9. Model Currency & Deprecation Audit (28 September 2026)", level=1)
    h9.paragraph_format.space_before = Pt(14)
    h9.paragraph_format.space_after = Pt(6)
    for r in h9.runs:
        r.font.name = "Arial"
        r.font.color.rgb = NAVY

    doc.add_paragraph(
        "• gemini-2.0-flash: DECOMMISSIONED by Google on 1 June 2026. Successfully removed from codebase in PR #199.\n"
        "• gemini-2.5-flash: ACTIVE (GA) on Google Gemini with no shutdown date announced.\n"
        "• openai/gpt-oss-20b, 120b: ACTIVE (Production) on Groq.\n"
        "• openai/gpt-oss-safeguard-20b: ACTIVE (Preview) on Groq (flagged: preview models subject to short-notice change).\n"
        "• Deprecation Logs: Check quarterly against https://ai.google.dev/gemini-api/docs/deprecations, "
        "https://console.groq.com/docs/models, and https://console.groq.com/docs/deprecations."
    ).paragraph_format.line_spacing = 1.15

    # -------------------------------------------------------------------------
    # 10. Governance & Monthly Review
    # -------------------------------------------------------------------------
    h10 = doc.add_heading("10. Governance: Standing Monthly Review Agenda", level=1)
    h10.paragraph_format.space_before = Pt(14)
    h10.paragraph_format.space_after = Pt(6)
    for r in h10.runs:
        r.font.name = "Arial"
        r.font.color.rgb = NAVY

    doc.add_paragraph(
        "The following 4-point review must occur monthly (within 30 days) during the weekly AI meeting:\n"
        "1. Token Usage by Service: Extract CloudWatch Logs Insights TOKEN_USAGE metrics.\n"
        "2. Spend vs Projection: Actual monthly invoice compared against the $0.72–$1.63/1k projection.\n"
        "3. Provider Split: Primary vs Fallback invocation percentage (ensuring Groq uptime).\n"
        "4. Capacity Headroom: Tracking daily volume against tier quotas.\n"
        "Rule: The documentation's 'Last Reviewed' timestamp must remain under 30 days old."
    ).paragraph_format.line_spacing = 1.15

    # -------------------------------------------------------------------------
    # 11. Cost Reduction Shortlist
    # -------------------------------------------------------------------------
    h11 = doc.add_heading("11. Cost Reduction Shortlist (Prioritized Candidates)", level=1)
    h11.paragraph_format.space_before = Pt(14)
    h11.paragraph_format.space_after = Pt(6)
    for r in h11.runs:
        r.font.name = "Arial"
        r.font.color.rgb = NAVY

    tbl_opt = doc.add_table(rows=1, cols=4)
    tbl_opt.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_opt)
    
    opt_headers = ["Candidate Optimization", "Expected Impact", "Status", "Notes"]
    for i, h in enumerate(opt_headers):
        c = tbl_opt.cell(0, i)
        set_cell_shading(c, "1A365D")
        set_cell_margins(c, top=100, bottom=100, left=100, right=100)
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h)
        r.font.name = "Arial"
        r.font.size = Pt(9)
        r.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    opt_data = [
        ("Pin reasoning_effort='low'", "Eliminates reasoning runaway on LangChain models", "Proposed, PR pending", "Implemented in commit 28688c2; savings to be re-measured after merge."),
        ("Server-side MAX_MESSAGE_CHARS", "Eliminates 25× caller-controlled prompt risk", "Risk measured, change unmeasured", "Worst-case 16,781 tokens measured; code change in utils/__init__.py pending."),
        ("Trim Organization Fields", "Reduces 20–40% of search_orgs completion tokens", "Unmeasured", "Requires frontend cross-team JSON contract review (#170)."),
        ("Deterministic Pre-Routing", "Cuts 2–3 model calls down to 1 call", "Unmeasured", "Measured on elderly-medium (1 call, 527 tokens)."),
        ("Groq Prompt Caching", "Halves input cost on static prompts ($0.075 → $0.0375/M)", "Unmeasured", "Automatic on gpt-oss-20b; verify minimum cacheable prefix length."),
        ("Trained Local Classifier", "Eliminates 2–3 model calls per request entirely", "Unmeasured", "Evaluate XGBoost/LightGBM (April 2026 minutes).")
    ]
    for row_idx, row in enumerate(opt_data):
        r_cells = tbl_opt.add_row().cells
        bg = "F7FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for i, val in enumerate(row):
            set_cell_shading(r_cells[i], bg)
            set_cell_margins(r_cells[i], top=80, bottom=80, left=100, right=100)
            p = r_cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            r.font.name = "Arial"
            r.font.size = Pt(8.5)
            r.font.color.rgb = SLATE

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # -------------------------------------------------------------------------
    # 12. Recommendations & Future Roadmap
    # -------------------------------------------------------------------------
    h12 = doc.add_heading("12. Recommendations & Future Scope", level=1)
    h12.paragraph_format.space_before = Pt(14)
    h12.paragraph_format.space_after = Pt(6)
    for r in h12.runs:
        r.font.name = "Arial"
        r.font.color.rgb = NAVY

    doc.add_paragraph(
        "1. Fallback Alerting: Configure CloudWatch alarm if Gemini traffic exceeds >5% of total requests.\n"
        "2. EMF Custom Metrics: Migrate TOKEN_USAGE logging to native CloudWatch Custom Metrics via aws-lambda-powertools.\n"
        "3. Quality-Gated Model Routing: Create golden evaluation sets per microservice after 2 monthly reviews.\n"
        "4. Speech-to-Text Integration (#22): Evaluate natively multimodal models for voice input/output."
    ).paragraph_format.line_spacing = 1.15

    # -------------------------------------------------------------------------
    # 13. Stakeholder Review & Sign-Off Block
    # -------------------------------------------------------------------------
    h13 = doc.add_heading("13. Stakeholder Review & Sign-Off", level=1)
    h13.paragraph_format.space_before = Pt(14)
    h13.paragraph_format.space_after = Pt(6)
    for r in h13.runs:
        r.font.name = "Arial"
        r.font.color.rgb = NAVY

    doc.add_paragraph("Please record review sign-off or action items below:").paragraph_format.space_after = Pt(6)

    tbl_sign = doc.add_table(rows=1, cols=4)
    tbl_sign.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_sign)
    
    sign_headers = ["Role / Stakeholder", "Reviewer Name", "Status (Approved / Comments)", "Date"]
    for i, h in enumerate(sign_headers):
        c = tbl_sign.cell(0, i)
        set_cell_shading(c, "1A365D")
        set_cell_margins(c, top=100, bottom=100, left=100, right=100)
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h)
        r.font.name = "Arial"
        r.font.size = Pt(9)
        r.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    sign_data = [
        ("AI Microservice Lead", "Sameer Nagar", "Reviewed with feedback (Issue #194)", "28 Sep 2026"),
        ("DevOps / AWS Admin", "", "Open Access Gap (Lambda config & tiers)", ""),
        ("Product & Request Lead", "", "Open Access Gap (Requests/user/mo)", ""),
        ("Engineering Leadership", "", "", "")
    ]
    for row_idx, row in enumerate(sign_data):
        r_cells = tbl_sign.add_row().cells
        for i, val in enumerate(row):
            set_cell_margins(r_cells[i], top=120, bottom=120, left=100, right=100)
            p = r_cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            r.font.name = "Arial"
            r.font.size = Pt(9)
            r.font.color.rgb = SLATE

    # Save
    doc.save(output_path)
    print(f"Document successfully created at {output_path}")

if __name__ == "__main__":
    out_dir = r"d:\Saayam_ai\docs"
    out_file = os.path.join(out_dir, "gen_ai_cost_model_review.docx")
    build_document(out_file)
