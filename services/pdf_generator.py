"""Genera cotizaciones usando la plantilla morada como base."""

from pathlib import Path

import pymupdf
from models.cotizacion import Cotizacion

PDF_DIR = Path(__file__).resolve().parent.parent / "pdfs"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TEMPLATE_PATH = PDF_DIR / "PLANTILLA_COTIZACION_MORADA.pdf"
MAX_PRODUCTOS = 10


def _insert_text(page, rect, text: str, *, size: float = 10, align: int = pymupdf.TEXT_ALIGN_LEFT):
    if text is None or text == "":
        return

    text = str(text)
    for font_size in (size, size - 0.5, size - 1, size - 1.5, size - 2):
        remaining = page.insert_textbox(
            rect,
            text,
            fontsize=font_size,
            fontname="helv",
            align=align,
        )
        if remaining >= 0:
            return
    raise ValueError(f"El texto no cabe en el espacio de la plantilla: {text}")


def generar_pdf(cot: Cotizacion) -> Path:
    """Genera un PDF con los datos de la cotización y devuelve su ruta."""
    if not TEMPLATE_PATH.is_file():
        raise FileNotFoundError(f"No se encontró la plantilla morada: {TEMPLATE_PATH}")
    if len(cot.productos) > MAX_PRODUCTOS:
        raise ValueError(
            f"La plantilla admite hasta {MAX_PRODUCTOS} productos por cotización."
        )

    PDF_DIR.mkdir(parents=True, exist_ok=True)
    ruta = PDF_DIR / f"{cot.numero}.pdf"

    with pymupdf.open(str(TEMPLATE_PATH)) as documento:
        pagina = documento[0]

        # Si la plantilla base no incluye el logo, estamparlo dinámicamente
        if len(pagina.get_images()) == 0:
            logo_candidatos = [
                DATA_DIR / "logo.png",
                DATA_DIR / "logo.png.jpg",
                DATA_DIR / "logo.jpg",
            ]
            logo_path = next((p for p in logo_candidatos if p.is_file()), None)
            if logo_path:
                pagina.insert_image(pymupdf.Rect(28, 10, 104, 84), filename=str(logo_path), keep_proportion=True)

        # Número y fechas: se escriben en los espacios que ya trae la plantilla.
        _insert_text(pagina, pymupdf.Rect(239, 102, 379, 118), cot.numero, size=9)
        _insert_text(pagina, pymupdf.Rect(220, 119, 296, 135), str(cot.fecha_emision), size=8)
        _insert_text(
            pagina,
            pymupdf.Rect(363, 119, 439, 135),
            str(cot.fecha_vencimiento),
            size=8,
        )

        # Los nombres de los campos ya están impresos en la plantilla morada.
        cliente = cot.cliente
        datos_cliente = (
            cliente.nombre,
            cliente.empresa,
            cliente.nit,
            cliente.direccion,
            cliente.telefono,
            cliente.email,
        )
        for index, valor in enumerate(datos_cliente):
            y = 172.5 + index * 19.84
            _insert_text(pagina, pymupdf.Rect(121, y, 560, y + 14), valor, size=9)

        columnas = (
            (31, 246, pymupdf.TEXT_ALIGN_LEFT),
            (251, 304, pymupdf.TEXT_ALIGN_CENTER),
            (309, 394, pymupdf.TEXT_ALIGN_RIGHT),
            (399, 451, pymupdf.TEXT_ALIGN_CENTER),
            (456, 503, pymupdf.TEXT_ALIGN_CENTER),
            (508, 564, pymupdf.TEXT_ALIGN_RIGHT),
        )
        for index, producto in enumerate(cot.productos):
            top = 323.2 + index * 19.84
            bottom = top + 19.84
            valores = (
                producto.descripcion,
                str(producto.cantidad),
                f"${producto.precio_unitario:,.0f}",
                f"{producto.descuento_pct:.0f}%",
                f"{producto.iva_pct:.0f}%",
                f"${producto.total:,.0f}",
            )
            for valor, (x0, x1, align) in zip(valores, columnas):
                _insert_text(
                    pagina,
                    pymupdf.Rect(x0, top + 1, x1, bottom - 1),
                    valor,
                    size=8,
                    align=align,
                )

        totales = (
            cot.subtotal_bruto,
            cot.total_descuentos,
            cot.base_imponible,
            cot.total_iva,
            cot.total,
        )
        for index, valor in enumerate(totales):
            top = (539.5, 559.4, 579.2, 599.1, 621.5)[index]
            _insert_text(
                pagina,
                pymupdf.Rect(440, top, 560, top + 14),
                f"$ {valor:,.0f} COP",
                size=9 if index < 4 else 10,
                align=pymupdf.TEXT_ALIGN_RIGHT,
            )

        if cot.notas:
            rect = pymupdf.Rect(30, 674, 561, 758)
            remaining = pagina.insert_textbox(
                rect,
                str(cot.notas),
                fontsize=9,
                fontname="helv",
            )
            if remaining < 0:
                raise ValueError("Las notas exceden el espacio disponible en la plantilla.")

        documento.save(str(ruta))

    return ruta
