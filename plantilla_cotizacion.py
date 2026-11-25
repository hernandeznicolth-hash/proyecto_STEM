"""
plantilla_cotizacion.py — Genera una plantilla PDF en blanco de cotizacion.
Ejecutar: python plantilla_cotizacion.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path
from fpdf import FPDF

PDF_DIR = Path(__file__).parent / "pdfs"
DATA_DIR = Path(__file__).parent / "data"

_FONTS_WIN    = Path("C:/Windows/Fonts")
_FONT_REGULAR = str(_FONTS_WIN / "calibri.ttf")
_FONT_BOLD    = str(_FONTS_WIN / "calibrib.ttf")
_FONT_ITALIC  = str(_FONTS_WIN / "calibrii.ttf")

# Colores extraídos del logo Nicolttissue
FONDO_LOGO   = (253, 241, 243)  # Fondo rosa suave exacto del logo
ROSA_MARCA   = (214, 94, 131)   # Rosa elegante del logo (texto y crochet)
ROSA_OSCURO  = (160, 50, 85)    # Rosa oscuro para textos destacados
MORADO       = ROSA_MARCA       # Reemplazo de tono principal para mantener compatibilidad
AZUL         = ROSA_MARCA
GRIS         = FONDO_LOGO       # Filas alternas con el tono rosa suave del logo
OSCURO       = (55, 45, 50)     # Gris cálido legible para el cuerpo del texto
LINEA        = (238, 208, 218)  # Líneas sutiles a tono


class PlantillaPDF(FPDF):

    def setup_fonts(self):
        self.add_font("CAL", style="",  fname=_FONT_REGULAR)
        self.add_font("CAL", style="B", fname=_FONT_BOLD)
        self.add_font("CAL", style="I", fname=_FONT_ITALIC)

    def header(self):
        # Banda superior con el color exacto del fondo del logo
        self.set_fill_color(*FONDO_LOGO)
        self.rect(0, 0, 210, 30, "F")

        # Inserción del logo
        logo_candidatos = [
            DATA_DIR / "logo.png",
            DATA_DIR / "logo.png.jpg",
            DATA_DIR / "logo.jpg",
        ]
        logo_path = next((p for p in logo_candidatos if p.is_file()), None)
        if logo_path:
            self.image(str(logo_path), x=10, y=3.5, w=23, h=23)

        # Nombre empresa y eslogan
        self.set_text_color(*ROSA_OSCURO)
        self.set_font("CAL", "B", 16)
        self.set_xy(36, 4.5)
        self.cell(0, 7, "NICOLTTISSUE")

        self.set_font("CAL", "I", 9.5)
        self.set_text_color(*ROSA_MARCA)
        self.set_xy(36, 11.5)
        self.cell(0, 5, "Tejiendo fibras del alma")

        self.set_font("CAL", "B", 9)
        self.set_text_color(*OSCURO)
        self.set_xy(36, 17.5)
        self.cell(0, 5, "NIT: 1.043.753-8   |   CEL: (300) 284 2461")

        self.set_text_color(0, 0, 0)
        # Fijar y exactamente en 27 mm para que el cuerpo empiece exactamente igual al original
        self.set_y(27)

    def footer(self):
        self.set_y(-13)
        self.set_font("CAL", "I", 8)
        self.set_text_color(130, 130, 130)
        self.cell(0, 10, f"Pagina {self.page_no()} - Documento generado automaticamente", align="C")


def generar_plantilla() -> Path:
    PDF_DIR.mkdir(exist_ok=True)
    ruta = PDF_DIR / "PLANTILLA_COTIZACION.pdf"

    pdf = PlantillaPDF()
    pdf.setup_fonts()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ── Titulo COTIZACION ──────────────────────────────────────────────────────
    pdf.set_font("CAL", "B", 15)
    pdf.set_text_color(*MORADO)
    pdf.cell(0, 9, "COTIZACION", ln=True, align="C")

    pdf.set_font("CAL", "", 10)
    pdf.set_text_color(*OSCURO)
    pdf.cell(0, 6, "Nro.: ____________________________", ln=True, align="C")
    pdf.cell(0, 6, "Fecha emision: _______________      Valida hasta: _______________", ln=True, align="C")
    pdf.ln(5)

    # ── Datos del cliente ──────────────────────────────────────────────────────
    pdf.set_fill_color(*MORADO)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("CAL", "B", 10)
    pdf.cell(0, 7, "  DATOS DEL CLIENTE", ln=True, fill=True)

    campos_cliente = [
        "Nombre",
        "Empresa",
        "NIT / Cedula",
        "Direccion",
        "Telefono",
        "Email",
    ]
    pdf.set_text_color(*OSCURO)
    pdf.set_draw_color(*LINEA)
    pdf.set_line_width(0.2)
    for campo in campos_cliente:
        pdf.set_font("CAL", "B", 10)
        pdf.cell(32, 7, f"  {campo}:", border=0)
        pdf.set_font("CAL", "", 10)
        # Linea punteada para rellenar
        x1 = pdf.get_x()
        y1 = pdf.get_y() + 5.5
        pdf.line(x1, y1, 198, y1)
        pdf.cell(0, 7, "", ln=True, border=0)
    pdf.ln(5)

    # ── Tabla de items ─────────────────────────────────────────────────────────
    pdf.set_fill_color(*MORADO)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("CAL", "B", 9)
    anchos    = [78, 20, 32, 20, 18, 22]
    cabeceras = ["Descripcion del producto / servicio", "Cant.", "Precio Unit. (COP)", "Desc %", "IVA %", "Total"]
    for ancho, cab in zip(anchos, cabeceras):
        pdf.cell(ancho, 7, cab, border=0, fill=True, align="C")
    pdf.ln()

    # 10 filas en blanco
    pdf.set_text_color(*OSCURO)
    pdf.set_draw_color(*LINEA)
    pdf.set_line_width(0.1)
    for i in range(10):
        fill = i % 2 == 0
        if fill:
            pdf.set_fill_color(*GRIS)
        else:
            pdf.set_fill_color(255, 255, 255)
        for ancho in anchos:
            pdf.cell(ancho, 7, "", border="B", fill=True)
        pdf.ln()

    pdf.ln(5)

    # ── Totales ────────────────────────────────────────────────────────────────
    def fila_total(etiqueta, negrita=False):
        pdf.set_font("CAL", "B" if negrita else "", 10)
        pdf.cell(145, 7, etiqueta, align="R")
        pdf.set_draw_color(*LINEA)
        pdf.set_line_width(0.2)
        x1 = pdf.get_x()
        y1 = pdf.get_y() + 5.5
        pdf.line(x1, y1, 198, y1)
        pdf.cell(0, 7, "", align="R", ln=True)

    fila_total("Subtotal:")
    fila_total("Descuentos (-):")
    fila_total("Base imponible:")
    fila_total("IVA (%):")

    pdf.set_draw_color(*MORADO)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(1)
    fila_total("TOTAL:", negrita=True)

    pdf.ln(7)

    # ── Notas / Terminos ───────────────────────────────────────────────────────
    pdf.set_font("CAL", "B", 10)
    pdf.set_text_color(*OSCURO)
    pdf.cell(0, 6, "Notas / Terminos y condiciones:", ln=True)
    pdf.set_font("CAL", "", 9)
    pdf.set_draw_color(*LINEA)
    pdf.set_line_width(0.2)
    for _ in range(4):
        y1 = pdf.get_y() + 5.5
        pdf.line(10, y1, 198, y1)
        pdf.cell(0, 7, "", ln=True)

    pdf.ln(10)

    # ── Firmas ─────────────────────────────────────────────────────────────────
    pdf.set_draw_color(*MORADO)
    pdf.set_line_width(0.4)
    pdf.line(15, pdf.get_y(), 95, pdf.get_y())
    pdf.line(115, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("CAL", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(95, 5, "Firma del emisor", align="C")
    pdf.cell(5,  5, "")
    pdf.cell(90, 5, "Firma del cliente / Vo. Bo.", align="C")

    # Guardar tanto en PLANTILLA_COTIZACION_MORADA.pdf (usada por el generador) como en PLANTILLA_COTIZACION.pdf
    ruta_morada = PDF_DIR / "PLANTILLA_COTIZACION_MORADA.pdf"
    ruta_std = PDF_DIR / "PLANTILLA_COTIZACION.pdf"

    for r in (ruta_morada, ruta_std):
        try:
            pdf.output(str(r))
        except PermissionError:
            print(f"  [!] '{r.name}' está abierto en un visor de PDF. Ciérralo para sobrescribir.")

    return ruta_morada


if __name__ == "__main__":
    ruta = generar_plantilla()
    print(f"\n  Plantilla generada: {ruta}\n")
