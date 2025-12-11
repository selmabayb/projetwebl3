# garage/utils/pdf.py

from django.template.loader import render_to_string
from django.conf import settings
import io

# Import xhtml2pdf (compatible Windows)
try:
    from xhtml2pdf import pisa
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("ERREUR: xhtml2pdf n'est pas installé. Installez-le avec: pip install xhtml2pdf")


def generate_pdf_from_html(html_string, css_string=None):
    """
    Génère un PDF depuis une chaîne HTML en utilisant xhtml2pdf

    Args:
        html_string: Le contenu HTML à convertir
        css_string: CSS optionnel pour le style (intégré dans le HTML)

    Returns:
        BytesIO contenant le PDF généré

    Raises:
        RuntimeError: Si xhtml2pdf n'est pas disponible
    """
    if not PDF_AVAILABLE:
        raise RuntimeError(
            "xhtml2pdf n'est pas disponible. "
            "Installez-le avec: pip install xhtml2pdf"
        )

    pdf_file = io.BytesIO()

    # Combiner HTML et CSS si fourni
    if css_string:
        html_with_css = f"<style>{css_string}</style>{html_string}"
    else:
        html_with_css = html_string

    # Générer le PDF avec xhtml2pdf
    pisa_status = pisa.CreatePDF(html_with_css, dest=pdf_file)

    if pisa_status.err:
        raise RuntimeError(f"Erreur lors de la génération du PDF: {pisa_status.err}")

    pdf_file.seek(0)
    return pdf_file


def generate_quote_pdf(quote):
    """
    Génère un PDF pour un devis

    Args:
        quote: Instance du modèle Quote

    Returns:
        BytesIO contenant le PDF du devis
    """
    from garage.catalog.models import SystemSettings

    # Récupérer les informations du garage
    settings_obj = SystemSettings.get_settings()

    # Récupérer les lignes du devis
    lines = quote.lines.all()

    # Préparer le contexte pour le template
    context = {
        'quote': quote,
        'lines': lines,
        'garage_name': settings_obj.garage_name,
        'garage_address': settings_obj.garage_address,
        'garage_phone': settings_obj.garage_phone,
        'garage_email': settings_obj.garage_email,
    }

    # Rendre le template HTML
    html_string = render_to_string('pdf/quote_pdf.html', context)

    # CSS pour le style du PDF
    css_string = """
        @page {
            size: A4;
            margin: 2cm;
        }
        body {
            font-family: Arial, Helvetica, sans-serif;
            font-size: 10pt;
            line-height: 1.5;
        }
        h1 {
            color: #0066cc;
            font-size: 20pt;
            margin-bottom: 10px;
        }
        h2 {
            color: #333;
            font-size: 14pt;
            margin-top: 20px;
            margin-bottom: 10px;
            border-bottom: 2px solid #0066cc;
            padding-bottom: 5px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            margin-bottom: 20px;
        }
        table thead {
            background-color: #0066cc;
            color: white;
        }
        table th, table td {
            padding: 8px;
            text-align: left;
            border: 1px solid #ddd;
        }
        table th {
            font-weight: bold;
        }
        table tfoot {
            background-color: #f5f5f5;
            font-weight: bold;
        }
        .text-right {
            text-align: right;
        }
        .header {
            margin-bottom: 30px;
        }
        .garage-info {
            float: left;
            width: 50%;
        }
        .quote-info {
            float: right;
            width: 45%;
            text-align: right;
        }
        .client-info {
            clear: both;
            margin-top: 20px;
            padding: 10px;
            background-color: #f9f9f9;
            border-left: 4px solid #0066cc;
        }
        .footer {
            margin-top: 30px;
            padding-top: 10px;
            border-top: 1px solid #ddd;
            font-size: 9pt;
            text-align: center;
            color: #666;
        }
        .total-row {
            font-size: 12pt;
            background-color: #e6f2ff !important;
        }
    """

    return generate_pdf_from_html(html_string, css_string)


def generate_invoice_pdf(invoice):
    """
    Génère un PDF pour une facture

    Args:
        invoice: Instance du modèle Invoice

    Returns:
        BytesIO contenant le PDF de la facture
    """
    from garage.catalog.models import SystemSettings

    # Récupérer les informations du garage
    settings_obj = SystemSettings.get_settings()

    # Récupérer les lignes de la facture
    lines = invoice.lines.all()

    # Préparer le contexte pour le template
    context = {
        'invoice': invoice,
        'lines': lines,
        'garage_name': settings_obj.garage_name,
        'garage_address': settings_obj.garage_address,
        'garage_phone': settings_obj.garage_phone,
        'garage_email': settings_obj.garage_email,
    }

    # Rendre le template HTML
    html_string = render_to_string('pdf/invoice_pdf.html', context)

    # CSS pour le style du PDF (couleurs rouges pour facture)
    css_string = """
        @page {
            size: A4;
            margin: 2cm;
        }
        body {
            font-family: Arial, Helvetica, sans-serif;
            font-size: 10pt;
            line-height: 1.5;
        }
        h1 {
            color: #d9534f;
            font-size: 20pt;
            margin-bottom: 10px;
        }
        h2 {
            color: #333;
            font-size: 14pt;
            margin-top: 20px;
            margin-bottom: 10px;
            border-bottom: 2px solid #d9534f;
            padding-bottom: 5px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            margin-bottom: 20px;
        }
        table thead {
            background-color: #d9534f;
            color: white;
        }
        table th, table td {
            padding: 8px;
            text-align: left;
            border: 1px solid #ddd;
        }
        table th {
            font-weight: bold;
        }
        table tfoot {
            background-color: #f5f5f5;
            font-weight: bold;
        }
        .text-right {
            text-align: right;
        }
        .header {
            margin-bottom: 30px;
        }
        .garage-info {
            float: left;
            width: 50%;
        }
        .invoice-info {
            float: right;
            width: 45%;
            text-align: right;
        }
        .client-info {
            clear: both;
            margin-top: 20px;
            padding: 10px;
            background-color: #f9f9f9;
            border-left: 4px solid #d9534f;
        }
        .footer {
            margin-top: 30px;
            padding-top: 10px;
            border-top: 1px solid #ddd;
            font-size: 9pt;
            text-align: center;
            color: #666;
        }
        .total-row {
            font-size: 12pt;
            background-color: #ffe6e6 !important;
        }
        .paid-stamp {
            color: #5cb85c;
            font-weight: bold;
            font-size: 16pt;
            text-align: center;
            margin-top: 20px;
            padding: 10px;
            border: 3px solid #5cb85c;
            border-radius: 10px;
        }
    """

    return generate_pdf_from_html(html_string, css_string)
