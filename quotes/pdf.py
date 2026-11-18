"""PDF de la cotización (ReportLab). Se genera al crear o editar y se guarda en Quote.pdf."""
from datetime import timedelta
from decimal import Decimal
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

LOGO = Path(__file__).resolve().parent / 'assets' / 'logo_siev.png'

INDIGO = colors.HexColor('#2d3484')
INDIGO_DARK = colors.HexColor('#1c2060')
ORANGE = colors.HexColor('#e4581d')
INK = colors.HexColor('#1f2230')
MUTED = colors.HexColor('#6c6f7e')
LINE = colors.HexColor('#e3e5ee')
SOFT = colors.HexColor('#f5f6fb')
ZEBRA = colors.HexColor('#fafbfe')

PAGE_W, PAGE_H = letter
MARGIN = 16 * mm
# El Frame de SimpleDocTemplate tiene 6 pt de padding por lado: las tablas usan el ancho útil real.
CONTENT_W = PAGE_W - 2 * MARGIN - 12

MONTHS = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']


def style(name, **kw):
    base = dict(fontName='Helvetica', fontSize=9, leading=12.5, textColor=INK)
    base.update(kw)
    return ParagraphStyle(name, **base)


S = {
    'eyebrow': style('eyebrow', fontName='Helvetica-Bold', fontSize=7, leading=9, textColor=ORANGE),
    'title': style('title', fontName='Helvetica-Bold', fontSize=24, leading=27, textColor=INDIGO, alignment=TA_RIGHT),
    'number': style('number', fontName='Helvetica-Bold', fontSize=11.5, leading=15, textColor=ORANGE, alignment=TA_RIGHT),
    'meta': style('meta', fontSize=8.5, leading=12, textColor=MUTED, alignment=TA_RIGHT),
    'card_title': style('card_title', fontName='Helvetica-Bold', fontSize=11, leading=14),
    'card': style('card', fontSize=8.5, leading=12.5, textColor=MUTED),
    'subject': style('subject', fontName='Helvetica-Bold', fontSize=12.5, leading=16),
    'th': style('th', fontName='Helvetica-Bold', fontSize=7.5, leading=9, textColor=colors.white),
    'th_r': style('th_r', fontName='Helvetica-Bold', fontSize=7.5, leading=9, textColor=colors.white, alignment=TA_RIGHT),
    'td': style('td', fontSize=8.5, leading=11.5),
    'td_r': style('td_r', fontSize=8.5, leading=11.5, alignment=TA_RIGHT),
    'td_muted': style('td_muted', fontSize=8, leading=11, textColor=MUTED),
    'item': style('item', fontName='Helvetica-Bold', fontSize=8.8, leading=11.5),
    'item_sub': style('item_sub', fontSize=7.5, leading=10, textColor=MUTED),
    'tot_label': style('tot_label', fontSize=9, leading=12, textColor=MUTED),
    'tot_value': style('tot_value', fontSize=9, leading=12, alignment=TA_RIGHT),
    'grand_label': style('grand_label', fontName='Helvetica-Bold', fontSize=10, leading=13, textColor=colors.white),
    'grand_value': style('grand_value', fontName='Helvetica-Bold', fontSize=14, leading=17, textColor=colors.white, alignment=TA_RIGHT),
    'cond_value': style('cond_value', fontName='Helvetica-Bold', fontSize=9.5, leading=12.5),
    'body': style('body', fontSize=8.5, leading=12.5, textColor=MUTED),
    'sign': style('sign', fontName='Helvetica-Bold', fontSize=9, leading=12),
}


def cop(value):
    """$ 1.234.567 (pesos sin centavos)."""
    amount = Decimal(value).quantize(Decimal('1'))
    return '$ ' + f'{amount:,.0f}'.replace(',', '.')


def long_date(value):
    return f'{value.day} de {MONTHS[value.month - 1]} de {value.year}'


def esc(text):
    return (str(text or '')).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


class NumberedCanvas(pdfcanvas.Canvas):
    """Dibuja encabezado/pie en cada página con «Página X de Y»."""

    def __init__(self, *args, quote=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved = []
        self._quote = quote

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved)
        for state in self._saved:
            self.__dict__.update(state)
            self._decorate(total)
            super().showPage()
        super().save()

    def _decorate(self, total):
        company = settings.SIEV_COMPANY
        # Franja superior de marca.
        self.setFillColor(INDIGO)
        self.rect(0, PAGE_H - 5, PAGE_W * 0.78, 5, stroke=0, fill=1)
        self.setFillColor(ORANGE)
        self.rect(PAGE_W * 0.78, PAGE_H - 5, PAGE_W * 0.22, 5, stroke=0, fill=1)
        # Pie.
        y = 12 * mm
        self.setStrokeColor(LINE)
        self.setLineWidth(0.6)
        self.line(MARGIN, y + 10, PAGE_W - MARGIN, y + 10)
        self.setFont('Helvetica-Bold', 7)
        self.setFillColor(INDIGO)
        self.drawString(MARGIN, y, company['name'])
        self.setFont('Helvetica', 7)
        self.setFillColor(MUTED)
        self.drawString(MARGIN, y - 9, f"NIT {company['nit']}  ·  {company['address']}  ·  {company['phone']}  ·  {company['email']}")
        page = self._pageNumber
        self.drawRightString(PAGE_W - MARGIN, y, f'{self._quote.number}')
        self.drawRightString(PAGE_W - MARGIN, y - 9, f'Página {page} de {total}')


def header(quote, issued):
    valid_until = issued + timedelta(days=quote.validity_days)
    logo = Image(str(LOGO), width=46 * mm, height=46 * mm * 404 / 700)
    right = [
        Paragraph('COTIZACIÓN', S['title']),
        Spacer(1, 2),
        Paragraph(quote.number, S['number']),
        Spacer(1, 4),
        Paragraph(f'Fecha de emisión: <b>{long_date(issued)}</b>', S['meta']),
        Paragraph(f'Válida hasta: <b>{long_date(valid_until)}</b>', S['meta']),
    ]
    table = Table([[logo, right]], colWidths=[CONTENT_W * 0.5, CONTENT_W * 0.5])
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    return table


def party_cards(quote):
    company = settings.SIEV_COMPANY
    issuer = [
        Paragraph('EMISOR', S['eyebrow']), Spacer(1, 5),
        Paragraph(esc(company['name']), S['card_title']), Spacer(1, 3),
        Paragraph(f"NIT {esc(company['nit'])}", S['card']),
        Paragraph(esc(company['address']), S['card']),
        Paragraph(f"{esc(company['phone'])}  ·  {esc(company['email'])}", S['card']),
    ]
    client_lines = [
        f'{quote.get_client_type_display()}  ·  {quote.document_label} {esc(quote.client_document)}',
        quote.client_contact and f'Contacto: {esc(quote.client_contact)}',
        ' · '.join(filter(None, [esc(quote.client_email), esc(quote.client_phone)])),
        esc(quote.client_address),
    ]
    client = [
        Paragraph('CLIENTE', S['eyebrow']), Spacer(1, 5),
        Paragraph(esc(quote.client_name), S['card_title']), Spacer(1, 3),
        *[Paragraph(line, S['card']) for line in client_lines if line],
    ]
    gap = 5 * mm
    card_w = (CONTENT_W - gap) / 2
    table = Table([[issuer, '', client]], colWidths=[card_w, gap, card_w])
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (0, 0), SOFT), ('BACKGROUND', (2, 0), (2, 0), SOFT),
        ('LINEBEFORE', (0, 0), (0, 0), 2.2, INDIGO), ('LINEBEFORE', (2, 0), (2, 0), 2.2, ORANGE),
        ('LEFTPADDING', (0, 0), (-1, -1), 11), ('RIGHTPADDING', (0, 0), (-1, -1), 11),
        ('TOPPADDING', (0, 0), (-1, -1), 10), ('BOTTOMPADDING', (0, 0), (-1, -1), 11),
        ('LEFTPADDING', (1, 0), (1, 0), 0), ('RIGHTPADDING', (1, 0), (1, 0), 0),
    ]))
    return table


def subject_block(quote):
    table = Table([[[Paragraph('ASUNTO', S['eyebrow']), Spacer(1, 4), Paragraph(esc(quote.subject), S['subject'])]]], colWidths=[CONTENT_W])
    table.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 0.6, LINE),
        ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    return table


def items_table(quote):
    widths = [9 * mm, None, 22 * mm, 14 * mm, 28 * mm, 30 * mm]
    widths[1] = CONTENT_W - sum(w for w in widths if w)
    rows = [[Paragraph('#', S['th']), Paragraph('DESCRIPCIÓN', S['th']), Paragraph('UNIDAD', S['th']),
             Paragraph('CANT.', S['th_r']), Paragraph('VR. UNITARIO', S['th_r']), Paragraph('VR. TOTAL', S['th_r'])]]
    items = list(quote.items.all())
    for index, item in enumerate(items, start=1):
        detail = ' · '.join(filter(None, [f'Cód. {esc(item.code)}', esc(item.brand)]))
        rows.append([
            Paragraph(f'{index:02d}', S['td_muted']),
            [Paragraph(esc(item.name), S['item']), Paragraph(detail, S['item_sub'])],
            Paragraph(esc(item.unit), S['td_muted']),
            Paragraph(str(item.quantity), S['td_r']),
            Paragraph(cop(item.unit_price), S['td_r']),
            Paragraph(f'<b>{cop(item.line_total)}</b>', S['td_r']),
        ])
    labor_row = None
    if quote.labor_cost and Decimal(quote.labor_cost) > 0:
        labor_row = len(rows)
        rows.append([
            Paragraph(f'{len(items) + 1:02d}', S['td_muted']),
            [Paragraph('Mano de obra', S['item']), Paragraph(esc(quote.labor_description or 'Servicio técnico especializado de SIEV'), S['item_sub'])],
            Paragraph('Servicio', S['td_muted']),
            Paragraph('1', S['td_r']),
            Paragraph(cop(quote.labor_cost), S['td_r']),
            Paragraph(f'<b>{cop(quote.labor_cost)}</b>', S['td_r']),
        ])
    table = Table(rows, colWidths=widths, repeatRows=1)
    commands = [
        ('BACKGROUND', (0, 0), (-1, 0), INDIGO),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, 0), 7), ('BOTTOMPADDING', (0, 0), (-1, 0), 7),
        ('TOPPADDING', (0, 1), (-1, -1), 5.5), ('BOTTOMPADDING', (0, 1), (-1, -1), 5.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6), ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 1), (-1, -1), 0.5, LINE),
    ]
    for row in range(2, len(rows), 2):
        commands.append(('BACKGROUND', (0, row), (-1, row), ZEBRA))
    if labor_row:
        commands += [('BACKGROUND', (0, labor_row), (-1, labor_row), colors.HexColor('#fff6f1')), ('LINEABOVE', (0, labor_row), (-1, labor_row), 0.8, ORANGE)]
    table.setStyle(TableStyle(commands))
    return table


def totals_table(quote):
    rate = (Decimal(quote.iva_rate) * 100).normalize()
    rows = [
        [Paragraph('Subtotal productos', S['tot_label']), Paragraph(cop(quote.products_subtotal), S['tot_value'])],
        [Paragraph('Mano de obra', S['tot_label']), Paragraph(cop(quote.labor_cost), S['tot_value'])],
        [Paragraph('<b>Subtotal</b>', S['tot_label']), Paragraph(f'<b>{cop(quote.subtotal)}</b>', S['tot_value'])],
        [Paragraph(f'IVA ({rate:f} %)', S['tot_label']), Paragraph(cop(quote.iva), S['tot_value'])],
        [Paragraph('TOTAL', S['grand_label']), Paragraph(cop(quote.total), S['grand_value'])],
    ]
    table = Table(rows, colWidths=[44 * mm, 40 * mm])
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 9), ('RIGHTPADDING', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 4.5), ('BOTTOMPADDING', (0, 0), (-1, -1), 4.5),
        ('LINEABOVE', (0, 2), (-1, 2), 0.6, LINE),
        ('BACKGROUND', (0, -1), (-1, -1), INDIGO_DARK),
        ('TOPPADDING', (0, -1), (-1, -1), 9), ('BOTTOMPADDING', (0, -1), (-1, -1), 9),
        ('LINEBEFORE', (0, -1), (0, -1), 3, ORANGE),
    ]))
    return table


def conditions(quote, width):
    """Condiciones comerciales apiladas (van a la izquierda de los totales)."""
    rows = []
    for label, value in [
        ('TIEMPO DE ENTREGA', quote.delivery_time),
        ('TIEMPO DE PAGO', quote.payment_terms),
        ('VALIDEZ', f'{quote.validity_days} días calendario'),
    ]:
        rows.append([Paragraph(label, S['eyebrow']), Paragraph(esc(value), S['cond_value'])])
    table = Table(rows, colWidths=[36 * mm, width - 36 * mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), SOFT),
        ('LINEBEFORE', (0, 0), (0, -1), 2.2, INDIGO),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEBELOW', (0, 0), (-1, -2), 0.8, colors.white),
        ('LEFTPADDING', (0, 0), (-1, -1), 10), ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 7.5), ('BOTTOMPADDING', (0, 0), (-1, -1), 7.5),
    ]))
    return table


def summary(quote):
    totals_w = 84 * mm
    gap = 8 * mm
    left_w = CONTENT_W - totals_w - gap
    table = Table([[conditions(quote, left_w), '', totals_table(quote)]], colWidths=[left_w, gap, totals_w])
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    return table


def closing(quote):
    company = settings.SIEV_COMPANY
    author = quote.created_by
    author_name = (author.get_full_name() or author.username) if author else company['name']
    parts = []
    if quote.notes:
        body = esc(quote.notes).replace('\n', '<br/>')
        notes = Table([[[Paragraph('OBSERVACIONES', S['eyebrow']), Spacer(1, 4), Paragraph(body, S['body'])]]], colWidths=[CONTENT_W])
        notes.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.6, LINE),
            ('LEFTPADDING', (0, 0), (-1, -1), 10), ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
        ]))
        parts += [notes, Spacer(1, 6)]
    parts += [
        Paragraph('Valores en pesos colombianos (COP); el total incluye el IVA indicado. '
                  'La disponibilidad de los materiales se confirma al momento de aceptar la cotización.', S['item_sub']),
        Spacer(1, 16),
        Paragraph('Atentamente,', S['body']),
        Spacer(1, 26),
    ]
    signature = Table([[[
        Paragraph(esc(author_name), S['sign']),
        Paragraph(esc(company['name']), S['card']),
        Paragraph(esc(author.email) if author and author.email else esc(company['email']), S['card']),
    ]]], colWidths=[100 * mm], hAlign='LEFT')
    signature.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 0.8, INK),
        ('LEFTPADDING', (0, 0), (-1, -1), 0), ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    parts.append(signature)
    return parts


def build_pdf(quote):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=14 * mm, bottomMargin=24 * mm,
        title=f'Cotización {quote.number}', author=settings.SIEV_COMPANY['name'], subject=quote.subject,
    )
    issued = timezone.localtime(quote.created_at).date() if quote.created_at else timezone.localdate()
    story = [
        header(quote, issued), Spacer(1, 7 * mm),
        party_cards(quote), Spacer(1, 6 * mm),
        subject_block(quote), Spacer(1, 5 * mm),
        items_table(quote), Spacer(1, 5 * mm),
        summary(quote),
        Spacer(1, 6 * mm),
        KeepTogether(closing(quote)),
    ]
    doc.build(story, canvasmaker=lambda *args, **kwargs: NumberedCanvas(*args, quote=quote, **kwargs))
    return buffer.getvalue()


def render_quote_pdf(quote):
    """Genera el PDF y lo guarda en quote.pdf (reemplaza el anterior)."""
    content = build_pdf(quote)
    if quote.pdf:
        quote.pdf.delete(save=False)
    quote.pdf.save(f'{quote.number}.pdf', ContentFile(content), save=False)
    quote.save(update_fields=['pdf', 'updated_at'])
