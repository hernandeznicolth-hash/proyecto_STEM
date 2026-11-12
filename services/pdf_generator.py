"""
pdf_generator.py — Exporta una cotización a PDF usando fpdf2.
Instalar: pip install fpdf2
"""

from pathlib import Path
from fpdf import FPDF
from models.cotizacion import Cotizacion

PDF_DIR = Path(__file__).parent.parent / "pdfs"


class _PDF(FPDF):
    """PDF con encabezado y pie de página personalizados."""

    EMPRESA  = "Mi Empresa S.A.S"
    NIT_EMP  = "900.123.456-7"
    TEL_EMP  = "+57 (601) 123-4567"
    EMAIL_EMP = "ventas@miempresa.com"
    COLOR_PRINCIPAL = (41, 128, 185)   # azul

    def header(self):
        self.set_fill_color(*self.COLOR_PRINCIPAL)
        self.rect(0, 0, 210, 28, "F")
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 16)
        self.set_xy(10, 6)
        self.cell(0, 8, self.EMPRESA, ln=True)
        self.set_font("Helvetica", "", 9)
        self.set_x(10)
        self.cell(0, 5, f"NIT: {self.NIT_EMP}  |  Tel: {self.TEL_EMP}  |  {self.EMAIL_EMP}", ln=True)
        self.set_text_color(0, 0, 0)
        self.ln(6)

    def footer(self):
        self.set_y(-13)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Página {self.page_no()} — Documento generado automáticamente", align="C")


def generar_pdf(cot: Cotizacion) -> Path:
    """Genera el PDF y devuelve la ruta del archivo creado."""
    PDF_DIR.mkdir(exist_ok=True)
    ruta = PDF_DIR / f"{cot.numero}.pdf"

    pdf = _PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    AZUL   = (41, 128, 185)
    GRIS   = (230, 230, 230)
    OSCURO = (44, 62, 80)

    # ── Encabezado cotización ─────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*AZUL)
    pdf.cell(0, 8, "COTIZACIÓN", ln=True, align="C")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*OSCURO)
    pdf.cell(0, 6, f"Nro.: {cot.numero}", ln=True, align="C")
    pdf.cell(0, 6,
             f"Fecha emisión: {cot.fecha_emision}    Válida hasta: {cot.fecha_vencimiento}",
             ln=True, align="C")
    pdf.ln(4)

    # ── Datos del cliente ─────────────────────────────────────────────────────
    pdf.set_fill_color(*AZUL)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "  DATOS DEL CLIENTE", ln=True, fill=True)

    pdf.set_text_color(*OSCURO)
    pdf.set_font("Helvetica", "", 10)
    datos_cli = [
        ("Nombre",  cot.cliente.nombre),
        ("Empresa", cot.cliente.empresa),
        ("NIT",     cot.cliente.nit),
        ("Dirección", cot.cliente.direccion),
        ("Teléfono", cot.cliente.telefono),
        ("Email",    cot.cliente.email),
    ]
    for etiqueta, valor in datos_cli:
        if valor:
            pdf.cell(35, 6, f"  {etiqueta}:", border=0)
            pdf.cell(0, 6, valor, ln=True, border=0)
    pdf.ln(4)

    # ── Tabla de ítems ────────────────────────────────────────────────────────
    pdf.set_fill_color(*AZUL)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    anchos = [75, 20, 30, 20, 20, 25]
    cabeceras = ["Descripción", "Cant.", "Precio Unit.", "Desc %", "IVA %", "Total"]
    for ancho, cab in zip(anchos, cabeceras):
        pdf.cell(ancho, 7, cab, border=0, fill=True, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*OSCURO)
    for i, p in enumerate(cot.productos):
        fill = i % 2 == 0
        pdf.set_fill_color(*GRIS) if fill else pdf.set_fill_color(255, 255, 255)
        valores = [
            p.descripcion,
            str(p.cantidad),
            f"${p.precio_unitario:,.2f}",
            f"{p.descuento_pct:.0f}%",
            f"{p.iva_pct:.0f}%",
            f"${p.total:,.2f}",
        ]
        alineaciones = ["L", "C", "R", "C", "C", "R"]
        for ancho, val, aln in zip(anchos, valores, alineaciones):
            pdf.cell(ancho, 6, val, border=0, fill=True, align=aln)
        pdf.ln()

    pdf.ln(4)

    # ── Totales ───────────────────────────────────────────────────────────────
    def fila_total(etiqueta, valor, negrita=False):
        pdf.set_font("Helvetica", "B" if negrita else "", 10)
        pdf.cell(145, 7, etiqueta, align="R")
        pdf.cell(0,  7, f"$ {valor:>14,.2f} COP", align="R", ln=True)

    fila_total("Subtotal:", cot.subtotal_bruto)
    fila_total("Descuentos (−):", cot.total_descuentos)
    fila_total("Base imponible:", cot.base_imponible)
    fila_total("IVA 19 % (+):", cot.total_iva)
    pdf.set_draw_color(*AZUL)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(1)
    fila_total("TOTAL:", cot.total, negrita=True)

    # ── Notas ─────────────────────────────────────────────────────────────────
    if cot.notas:
        pdf.ln(6)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, "Notas / Términos y condiciones:", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5, cot.notas)

    pdf.output(str(ruta))
    return ruta
