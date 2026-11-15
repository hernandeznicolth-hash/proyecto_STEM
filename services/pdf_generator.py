"""Genera el PDF de una cotización a partir de la plantilla base."""

from pathlib import Path

import pymupdf
from models.cotizacion import Cotizacion

PDF_DIR = Path(__file__).resolve().parent.parent / "pdfs"
TEMPLATE_PATH = PDF_DIR / "PLANTILLA_COTIZACION.pdf"

EMPRESA = "Mi Empresa S.A.S"
NIT_EMPRESA = "900.123.456-7"
TEL_EMPRESA = "+57 (601) 123-4567"
EMAIL_EMPRESA = "ventas@miempresa.com"
COLOR_MORADO = (112, 48, 160)


def _normalize_color(color):
    if isinstance(color, (tuple, list)) and len(color) in (3, 4):
        if max(color) <= 1:
            return tuple(color)
        return tuple(c / 255 for c in color)
    return (0, 0, 0)


def _insert_text(page, x: float, y: float, text: str, *, size: int = 11, color=(0, 0, 0), font="helv"):
    if text is None:
        return
    page.insert_text((x, y), str(text), fontsize=size, fontname=font, color=_normalize_color(color))


def _insert_textbox(page, x: float, y: float, w: float, h: float, text: str, *, size: int = 10, color=(0, 0, 0)):
    if not text:
        return
    page.insert_textbox(pymupdf.Rect(x, y, x + w, y + h), str(text), fontsize=size, color=_normalize_color(color))


def generar_pdf(cot: Cotizacion) -> Path:
    """Genera una cotización nueva a partir del PDF de plantilla."""
    PDF_DIR.mkdir(exist_ok=True)
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"No se encontró la plantilla: {TEMPLATE_PATH}")

    ruta = PDF_DIR / f"{cot.numero}.pdf"
    documento = pymupdf.open(str(TEMPLATE_PATH))
    pagina = documento[0]

    # Encabezado de la empresa (blanco sobre morado)
    _insert_text(pagina, 190, 63, EMPRESA, size=17, color=(255, 255, 255), font="helv")
    _insert_text(pagina, 126, 82, f"NIT: {NIT_EMPRESA}", size=10, color=(255, 255, 255), font="helv")
    _insert_text(pagina, 250, 82, f"|  Tel: {TEL_EMPRESA}", size=10, color=(255, 255, 255), font="helv")
    _insert_text(pagina, 420, 82, f"|  {EMAIL_EMPRESA}", size=10, color=(255, 255, 255), font="helv")

    # Datos generales
    _insert_text(pagina, 235, 110, "COTIZACION", size=18, color=(44, 62, 80), font="helv")
    _insert_text(pagina, 178, 130, f"Nro.: {cot.numero}", size=11, color=(0, 0, 0), font="helv")
    _insert_text(
        pagina,
        120,
        150,
        f"Fecha emision: {cot.fecha_emision}      Valida hasta: {cot.fecha_vencimiento}",
        size=10,
        color=(0, 0, 0),
        font="helv",
    )

    # Datos del cliente
    _insert_text(pagina, 42, 195, "Nombre:", size=11, color=(0, 0, 0), font="helv")
    _insert_text(pagina, 125, 195, cot.cliente.nombre, size=11, color=(0, 0, 0), font="helv")
    _insert_text(pagina, 42, 220, "Empresa:", size=11, color=(0, 0, 0), font="helv")
    _insert_text(pagina, 125, 220, cot.cliente.empresa, size=11, color=(0, 0, 0), font="helv")
    _insert_text(pagina, 42, 245, "NIT / Cedula:", size=11, color=(0, 0, 0), font="helv")
    _insert_text(pagina, 125, 245, cot.cliente.nit, size=11, color=(0, 0, 0), font="helv")
    _insert_text(pagina, 42, 270, "Direccion:", size=11, color=(0, 0, 0), font="helv")
    _insert_text(pagina, 125, 270, cot.cliente.direccion, size=11, color=(0, 0, 0), font="helv")
    _insert_text(pagina, 42, 295, "Telefono:", size=11, color=(0, 0, 0), font="helv")
    _insert_text(pagina, 125, 295, cot.cliente.telefono, size=11, color=(0, 0, 0), font="helv")
    _insert_text(pagina, 42, 320, "Email:", size=11, color=(0, 0, 0), font="helv")
    _insert_text(pagina, 125, 320, cot.cliente.email, size=11, color=(0, 0, 0), font="helv")

    # Productos y tabla
    inicio_y = 370
    for index, producto in enumerate(cot.productos[:6]):
        y = inicio_y - (index * 26)
        _insert_text(pagina, 38, y, producto.descripcion[:38], size=9, color=(0, 0, 0), font="helv")
        _insert_text(pagina, 345, y, str(producto.cantidad), size=9, color=(0, 0, 0), font="helv")
        _insert_text(pagina, 392, y, f"${producto.precio_unitario:,.0f}", size=9, color=(0, 0, 0), font="helv")
        _insert_text(pagina, 462, y, f"{producto.descuento_pct:.0f}%", size=9, color=(0, 0, 0), font="helv")
        _insert_text(pagina, 510, y, f"{producto.iva_pct:.0f}%", size=9, color=(0, 0, 0), font="helv")
        _insert_text(pagina, 525, y, f"${producto.total:,.0f}", size=9, color=(0, 0, 0), font="helv")

    # Totales
    _insert_text(pagina, 420, 525, "Subtotal:", size=10, color=(0, 0, 0), font="helv")
    _insert_text(pagina, 500, 525, f"$ {cot.subtotal_bruto:,.0f} COP", size=10, color=(0, 0, 0), font="helv")
    _insert_text(pagina, 420, 545, "Descuentos (-):", size=10, color=(0, 0, 0), font="helv")
    _insert_text(pagina, 500, 545, f"$ {cot.total_descuentos:,.0f} COP", size=10, color=(0, 0, 0), font="helv")
    _insert_text(pagina, 420, 565, "Base imponible:", size=10, color=(0, 0, 0), font="helv")
    _insert_text(pagina, 500, 565, f"$ {cot.base_imponible:,.0f} COP", size=10, color=(0, 0, 0), font="helv")
    _insert_text(pagina, 420, 585, "IVA (%):", size=10, color=(0, 0, 0), font="helv")
    _insert_text(pagina, 500, 585, f"$ {cot.total_iva:,.0f} COP", size=10, color=(0, 0, 0), font="helv")
    _insert_text(pagina, 420, 610, "TOTAL:", size=12, color=COLOR_MORADO, font="helv")
    _insert_text(pagina, 500, 610, f"$ {cot.total:,.0f} COP", size=12, color=COLOR_MORADO, font="helv")

    # Notas
    if cot.notas:
        _insert_textbox(pagina, 44, 640, 500, 90, cot.notas, size=10)

    # Mantener segunda página de la plantilla para firma
    documento.save(str(ruta))
    return ruta
