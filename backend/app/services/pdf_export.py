"""
PDF Export Service

Generates clean, professional PDF reports using ReportLab.
Design inspired by Elicit - minimal, black/white, professional typography.
"""

from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY, TA_CENTER
from app.schemas.report import ResearchReport


def generate_report_pdf(report: ResearchReport) -> bytes:
    """Generate a clean, professional PDF from a ResearchReport."""
    
    buffer = BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Custom styles - clean, minimal, professional
    styles = getSampleStyleSheet()
    
    # Title style
    styles.add(ParagraphStyle(
        name='ReportTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=6,
        spaceBefore=0,
        textColor=colors.black,
        fontName='Helvetica-Bold'
    ))
    
    # Question style
    styles.add(ParagraphStyle(
        name='Question',
        parent=styles['Normal'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=6,
        textColor=colors.HexColor('#333333'),
        fontName='Helvetica-Bold',
        leading=18
    ))
    
    # Section header
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=8,
        spaceBefore=16,
        textColor=colors.black,
        fontName='Helvetica-Bold',
        borderPadding=0
    ))
    
    # Body text
    styles.add(ParagraphStyle(
        name='ReportBody',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=8,
        textColor=colors.HexColor('#333333'),
        fontName='Helvetica',
        leading=14,
        alignment=TA_JUSTIFY
    ))
    
    # Summary box text
    styles.add(ParagraphStyle(
        name='SummaryText',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=4,
        textColor=colors.HexColor('#333333'),
        fontName='Helvetica',
        leading=14,
        leftIndent=10,
        rightIndent=10
    ))
    
    # Citation text (smaller)
    styles.add(ParagraphStyle(
        name='Citation',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=4,
        textColor=colors.HexColor('#666666'),
        fontName='Helvetica',
        leading=12
    ))
    
    # Source title
    styles.add(ParagraphStyle(
        name='SourceTitle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=2,
        textColor=colors.black,
        fontName='Helvetica-Bold',
        leading=12
    ))
    
    # Source meta
    styles.add(ParagraphStyle(
        name='SourceMeta',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=4,
        textColor=colors.HexColor('#666666'),
        fontName='Helvetica-Oblique',
        leading=11
    ))
    
    # Build document content
    story = []
    
    # Header
    story.append(Paragraph("Research Report", styles['ReportTitle']))
    story.append(Spacer(1, 4))
    
    # Question
    safe_question = _safe_text(report.question)
    story.append(Paragraph(safe_question, styles['Question']))
    
    # Metadata line
    meta_text = f"{report.papers_used} papers analyzed"
    story.append(Paragraph(meta_text, styles['Citation']))
    story.append(Spacer(1, 12))
    
    # Divider line
    story.append(_create_divider())
    
    # Executive Summary
    story.append(Paragraph("Summary", styles['SectionHeader']))
    safe_summary = _safe_text(report.executive_summary)
    story.append(Paragraph(safe_summary, styles['SummaryText']))
    story.append(Spacer(1, 8))
    
    # Key Findings
    story.append(Paragraph("Key Findings", styles['SectionHeader']))
    
    for i, finding in enumerate(report.key_findings, 1):
        sources_str = ", ".join([str(idx) for idx in finding.source_indices])
        safe_statement = _safe_text(finding.statement)
        
        # Finding with bullet number
        finding_text = f"<b>{i}.</b> {safe_statement}"
        story.append(Paragraph(finding_text, styles['ReportBody']))
        
        # Confidence and sources on same line
        meta_line = f"<i>Confidence: {finding.confidence.capitalize()} | Sources: [{sources_str}]</i>"
        story.append(Paragraph(meta_line, styles['Citation']))
        story.append(Spacer(1, 6))
    
    story.append(Spacer(1, 8))
    
    # Detailed Analysis
    story.append(Paragraph("Detailed Analysis", styles['SectionHeader']))
    
    # Split analysis into paragraphs
    analysis_paragraphs = report.detailed_analysis.split('\n\n')
    for para in analysis_paragraphs:
        if para.strip():
            safe_para = _safe_text(para.strip())
            story.append(Paragraph(safe_para, styles['ReportBody']))
    
    story.append(Spacer(1, 8))
    
    # Protocols (if any)
    if report.protocols:
        story.append(Paragraph("Protocols", styles['SectionHeader']))
        
        # Create a style for table cells
        cell_style = ParagraphStyle(
            name='TableCell',
            parent=styles['Normal'],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#333333'),
            fontName='Helvetica'
        )
        
        # Table header
        header_row = [
            Paragraph('<b>Protocol</b>', cell_style),
            Paragraph('<b>Dosage</b>', cell_style),
            Paragraph('<b>Species</b>', cell_style),
            Paragraph('<b>Result</b>', cell_style),
            Paragraph('<b>Ref</b>', cell_style)
        ]
        table_data = [header_row]
        
        for protocol in report.protocols:
            row = [
                Paragraph(_safe_text(protocol.name), cell_style),
                Paragraph(_safe_text(protocol.dosage) if protocol.dosage else '-', cell_style),
                Paragraph(protocol.species if protocol.species else '-', cell_style),
                Paragraph(_safe_text(protocol.result) if protocol.result else '-', cell_style),
                Paragraph(f"[{protocol.source_index}]", cell_style)
            ]
            table_data.append(row)
        
        # Create table with proper widths for wrapping
        table = Table(table_data, colWidths=[1.6*inch, 1.0*inch, 0.6*inch, 2.4*inch, 0.4*inch])
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
            ('LINEBELOW', (0, 1), (-1, -1), 0.5, colors.HexColor('#DDDDDD')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(table)
        story.append(Spacer(1, 12))
    
    # Limitations
    story.append(Paragraph("Limitations", styles['SectionHeader']))
    safe_limitations = _safe_text(report.limitations)
    story.append(Paragraph(safe_limitations, styles['ReportBody']))
    
    # Page break before sources
    story.append(PageBreak())
    
    # Sources
    story.append(Paragraph("References", styles['SectionHeader']))
    story.append(Spacer(1, 4))
    
    for source in report.sources:
        # Reference number and title
        safe_title = _safe_text(source.title)
        ref_text = f"<b>[{source.index}]</b> {safe_title}"
        story.append(Paragraph(ref_text, styles['SourceTitle']))
        
        # Journal, year, PMID
        safe_journal = _safe_text(source.journal)
        meta_text = f"{safe_journal} ({source.year})"
        if source.pmid:
            meta_text += f" • PMID: {source.pmid}"
        story.append(Paragraph(meta_text, styles['SourceMeta']))
        
        # Abstract (truncated)
        if source.abstract:
            safe_abstract = _safe_text(source.abstract[:400])
            if len(source.abstract) > 400:
                safe_abstract += "..."
            story.append(Paragraph(safe_abstract, styles['Citation']))
        
        story.append(Spacer(1, 10))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    return buffer.getvalue()


def _safe_text(text: str) -> str:
    """Make text safe for ReportLab by escaping special characters."""
    if not text:
        return ""
    # Replace problematic characters
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    # Handle unicode quotes and dashes
    text = text.replace('\u2018', "'")
    text = text.replace('\u2019', "'")
    text = text.replace('\u201c', '"')
    text = text.replace('\u201d', '"')
    text = text.replace('\u2013', '-')
    text = text.replace('\u2014', '-')
    text = text.replace('\u2026', '...')
    text = text.replace('\u00a0', ' ')
    return text


def _create_divider():
    """Create a horizontal divider line."""
    table = Table([['']], colWidths=[6.5*inch])
    table.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#CCCCCC')),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    return table
