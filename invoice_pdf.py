from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os

# Currency symbol
CURRENCY = "GHC"

def generate_invoice_pdf(invoice_id, customer, items, total, payment, balance, date_str, company_info=None):
    """
    Generates a PDF invoice.
    
    Args:
        invoice_id: Invoice number (e.g., "00001")
        customer: Customer name
        items: List of dicts with 'name', 'quantity', 'unit_price', 'total'
        total: Total amount
        payment: Payment received
        balance: Balance remaining
        date_str: Date string
        company_info: Dict with 'name', 'address', 'phone', 'email'
    
    Returns:
        filename: Path to the generated PDF
    """
    # Create invoices directory if it doesn't exist
    invoices_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'invoices')
    if not os.path.exists(invoices_dir):
        os.makedirs(invoices_dir)
    
    # Generate safe filename - remove invalid characters
    safe_customer = "".join(c for c in customer if c.isalnum() or c in (' ', '_', '-')).strip()
    safe_customer = safe_customer.replace(' ', '_')
    filename = os.path.join(invoices_dir, f"{safe_customer}_{invoice_id}.pdf")
    
    # Create PDF
    doc = SimpleDocTemplate(filename, pagesize=letter, 
                           leftMargin=0.75*inch, rightMargin=0.75*inch,
                           topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Company Header Style
    company_style = ParagraphStyle(
        'CompanyName',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1a5276'),
        spaceAfter=5,
        alignment=TA_CENTER
    )
    
    company_address_style = ParagraphStyle(
        'CompanyAddress',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#566573'),
        alignment=TA_CENTER,
        spaceAfter=3
    )
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=20,
        spaceBefore=15,
        alignment=TA_CENTER
    )
    
    # Company Header
    if company_info and company_info.get('name'):
        company_name = Paragraph(company_info['name'], company_style)
        elements.append(company_name)
        
        if company_info.get('address'):
            address = Paragraph(company_info['address'], company_address_style)
            elements.append(address)
        
        contact_parts = []
        if company_info.get('phone'):
            contact_parts.append(f"Tel: {company_info['phone']}")
        if company_info.get('email'):
            contact_parts.append(f"Email: {company_info['email']}")
        
        if contact_parts:
            contact = Paragraph(" | ".join(contact_parts), company_address_style)
            elements.append(contact)
        
        elements.append(Spacer(1, 0.2*inch))
    
    # Title
    title = Paragraph("SALES INVOICE", title_style)
    elements.append(title)
    
    # Invoice Info Table
    info_data = [
        ['Invoice No:', invoice_id],
        ['Date:', date_str],
        ['Customer:', customer]
    ]
    
    info_table = Table(info_data, colWidths=[1.5*inch, 4.5*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Items Table
    items_data = [['Product ID', 'Item', 'Qty', f'Price ({CURRENCY})', f'Total ({CURRENCY})']]
    
    for item in items:
        items_data.append([
            item['product_id'],
            item['name'],
            str(item['quantity']),
            f"{item['unit_price']:.2f}",
            f"{item['total']:.2f}"
        ])
    
    items_table = Table(items_data, colWidths=[0.8*inch, 2.5*inch, 0.6*inch, 1.1*inch, 1.1*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Totals
    totals_data = [
        ['', 'Total Amount:', f'{CURRENCY} {total:.2f}'],
        ['', 'Payment Received:', f'{CURRENCY} {payment:.2f}'],
        ['', 'Balance Due:', f'{CURRENCY} {balance:.2f}']
    ]
    
    totals_table = Table(totals_data, colWidths=[3.5*inch, 1.5*inch, 1.5*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('FONTNAME', (1, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (1, 0), (-1, -1), 11),
        ('LINEABOVE', (1, 0), (-1, 0), 1, colors.black),
        ('LINEABOVE', (1, -1), (-1, -1), 2, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (1, -1), (-1, -1), colors.HexColor('#e8f6f3') if balance <= 0 else colors.HexColor('#fdedec')),
    ]))
    elements.append(totals_table)
    
    # Footer
    elements.append(Spacer(1, 0.5*inch))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, 
                                  textColor=colors.HexColor('#7f8c8d'), alignment=TA_CENTER)
    footer = Paragraph("Thank you for your business!", footer_style)
    elements.append(footer)
    
    # Build PDF
    doc.build(elements)
    
    return filename
