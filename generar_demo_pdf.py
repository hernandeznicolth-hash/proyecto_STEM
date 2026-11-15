"""
generar_demo_pdf.py — Genera un PDF de cotización de demostración.
Ejecutar: python generar_demo_pdf.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from models.cliente    import Cliente
from models.producto   import Producto
from models.cotizacion import Cotizacion
from services.pdf_generator import generar_pdf

# ── Datos ficticios de ejemplo ──────────────────────────────────────────────

cliente = Cliente(
    id_cliente = 1,
    nombre     = "Carlos Andrés Ramírez",
    empresa    = "Distribuidora El Éxito Ltda.",
    nit        = "900.456.789-3",
    direccion  = "Cra. 7 # 32-15, Bogotá D.C.",
    telefono   = "+57 310 555 1234",
    email      = "carlos.ramirez@exito.com",
)

productos = [
    Producto("Servicio de diseño web corporativo",   1,   3_500_000, descuento_pct=0,  iva_pct=19),
    Producto("Hosting y dominio anual",              1,     480_000, descuento_pct=5,  iva_pct=0),
    Producto("Mantenimiento mensual (x3 meses)",     3,     250_000, descuento_pct=10, iva_pct=19),
    Producto("Capacitación de usuarios (horas)",     4,     120_000, descuento_pct=0,  iva_pct=19),
    Producto("Licencia software de gestión",         1,   1_200_000, descuento_pct=15, iva_pct=19),
]

notas = (
    "- Pago: 50% anticipo, 50% contra entrega.\n"
    "- Cotizacion valida por 30 dias a partir de la fecha de emision.\n"
    "- Incluye soporte tecnico por 90 dias post-implementacion.\n"
    "- Precios expresados en pesos colombianos (COP) + IVA segun aplique."
)

cotizacion = Cotizacion(cliente=cliente, productos=productos, notas=notas)

# ── Generar PDF ──────────────────────────────────────────────────────────────

ruta = generar_pdf(cotizacion)
print(f"\n  ✅ PDF generado exitosamente:")
print(f"     {ruta}\n")
print(f"  Resumen:")
print(cotizacion.resumen())
