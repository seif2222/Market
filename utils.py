import qrcode
import os
from io import BytesIO
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import json

def generate_qr_code(product):
    """Generate QR code for a product"""
    # Create QR code data
    qr_data = json.dumps({
        'id': product.id,
        'product_id': getattr(product, 'product_id', str(product.id)),
        'name': product.name,
        'price': product.price
    })
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    # Create QR code image
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Save QR code
    qr_dir = "static/qr_codes"
    if not os.path.exists(qr_dir):
        os.makedirs(qr_dir)
    
    qr_path = os.path.join(qr_dir, f"product_{product.id}.png")
    qr_img.save(qr_path)
    
    return qr_path

def generate_invoice_pdf(sale):
    """Generate PDF invoice for a sale"""
    # Create invoices directory if it doesn't exist
    invoice_dir = "static/invoices"
    if not os.path.exists(invoice_dir):
        os.makedirs(invoice_dir)
    
    # Create filename
    filename = f"invoice_{sale.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(invoice_dir, filename)
    
    # Create PDF
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Custom styles for Arabic text (RTL)
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1,  # Center alignment
        fontName='Helvetica-Bold'
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=15,
        alignment=2,  # Right alignment for Arabic
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=10,
        alignment=2,  # Right alignment for Arabic
        fontName='Helvetica'
    )
    
    # Company header with logo area
    elements.append(Paragraph("سوق المصطفى التجاري", title_style))
    elements.append(Paragraph("Al-Mustafa Commercial Market", title_style))
    elements.append(Paragraph("العنوان: شارع الجامعة، القاهرة، مصر", normal_style))
    elements.append(Paragraph("هاتف: 01234567890 | إيميل: info@almustafa-market.com", normal_style))
    elements.append(Spacer(1, 30))
    
    # Invoice details
    elements.append(Paragraph(f"فاتورة رقم: {sale.id}", header_style))
    elements.append(Paragraph(f"Invoice Number: {sale.id}", normal_style))
    elements.append(Paragraph(f"التاريخ: {sale.sale_date.strftime('%Y-%m-%d %H:%M')}", normal_style))
    elements.append(Paragraph(f"Date: {sale.sale_date.strftime('%Y-%m-%d %H:%M')}", normal_style))
    elements.append(Spacer(1, 20))
    
    # Customer information
    if sale.customer_name:
        elements.append(Paragraph(f"اسم العميل: {sale.customer_name}", normal_style))
        elements.append(Paragraph(f"Customer Name: {sale.customer_name}", normal_style))
    
    if sale.customer_phone:
        elements.append(Paragraph(f"رقم الهاتف: {sale.customer_phone}", normal_style))
        elements.append(Paragraph(f"Phone: {sale.customer_phone}", normal_style))
    
    elements.append(Spacer(1, 20))
    
    # Items table
    table_data = [
        ['المجموع', 'السعر', 'الكمية', 'المنتج'],
        ['Total', 'Price', 'Qty', 'Product']
    ]
    
    for item in sale.items:
        table_data.append([
            f"{item.total_price:.2f} جنيه",
            f"{item.unit_price:.2f} جنيه",
            str(item.quantity),
            item.product.name
        ])
    
    # Add total row
    table_data.append(['', '', 'المجموع الكلي:', f"{sale.total_amount:.2f} جنيه"])
    table_data.append(['', '', 'Total Amount:', f"{sale.total_amount:.2f} EGP"])
    
    # Create table
    table = Table(table_data, colWidths=[1.5*inch, 1*inch, 1*inch, 3*inch])
    
    # Table style
    table.setStyle(TableStyle([
        # Header style
        ('BACKGROUND', (0, 0), (-1, 1), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 1), 12),
        
        # Data style
        ('BACKGROUND', (0, 2), (-1, -3), colors.beige),
        ('FONTNAME', (0, 2), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 2), (-1, -1), 10),
        
        # Total rows style
        ('BACKGROUND', (0, -2), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -2), (-1, -1), 12),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 30))
    
    # Footer
    elements.append(Paragraph("شكراً لتعاملكم معنا", header_style))
    elements.append(Paragraph("Thank you for your business", normal_style))
    
    # Build PDF
    doc.build(elements)
    
    return filepath
