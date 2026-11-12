"""
Clase Cotizacion — Agrupa cliente, productos y totales.
"""

import uuid
from datetime import date, timedelta
from models.cliente  import Cliente
from models.producto import Producto


class Cotizacion:
    VALIDEZ_DIAS = 30   # días de validez por defecto

    def __init__(self, cliente: Cliente, productos: list[Producto] = None,
                 notas: str = "", id_cotizacion=None, numero: str = None,
                 fecha_emision: date = None, fecha_vencimiento: date = None):
        self.id_cotizacion    = id_cotizacion
        self.numero           = numero or self._generar_numero()
        self.fecha_emision    = fecha_emision    or date.today()
        self.fecha_vencimiento= fecha_vencimiento or (date.today() + timedelta(days=self.VALIDEZ_DIAS))
        self.cliente          = cliente
        self.productos        = productos or []
        self.notas            = notas

    # ── Número único ──────────────────────────────────────────────────────────

    @staticmethod
    def _generar_numero() -> str:
        hoy = date.today()
        uid = str(uuid.uuid4())[:8].upper()
        return f"COT-{hoy.year}{hoy.month:02d}{hoy.day:02d}-{uid}"

    # ── Totales ───────────────────────────────────────────────────────────────

    @property
    def subtotal_bruto(self) -> float:
        return sum(p.subtotal_bruto for p in self.productos)

    @property
    def total_descuentos(self) -> float:
        return sum(p.valor_descuento for p in self.productos)

    @property
    def base_imponible(self) -> float:
        return sum(p.base_imponible for p in self.productos)

    @property
    def total_iva(self) -> float:
        return sum(p.valor_iva for p in self.productos)

    @property
    def total(self) -> float:
        return sum(p.total for p in self.productos)

    # ── Representación en consola ─────────────────────────────────────────────

    def resumen(self) -> str:
        lineas = [
            "=" * 60,
            f"  COTIZACIÓN  Nro.: {self.numero}",
            "=" * 60,
            f"  Fecha emisión   : {self.fecha_emision}",
            f"  Válida hasta    : {self.fecha_vencimiento}",
            "",
            "── CLIENTE ──────────────────────────────────────────────",
            f"  Nombre  : {self.cliente.nombre}",
            f"  Empresa : {self.cliente.empresa}",
            f"  NIT     : {self.cliente.nit}",
            "",
            "── ÍTEMS ────────────────────────────────────────────────",
        ]
        for i, p in enumerate(self.productos, 1):
            lineas.append(f"\n  [{i}] {p.descripcion}")
            lineas.append(
                f"      {p.cantidad} × ${p.precio_unitario:,.2f}"
                f"  Desc {p.descuento_pct:.0f}%  IVA {p.iva_pct:.0f}%"
                f"  → ${p.total:,.2f}"
            )
        lineas += [
            "",
            "── TOTALES ──────────────────────────────────────────────",
            f"  Subtotal        : $ {self.subtotal_bruto:>14,.2f} COP",
            f"  Descuentos (-)  : $ {self.total_descuentos:>14,.2f} COP",
            f"  Base imponible  : $ {self.base_imponible:>14,.2f} COP",
            f"  IVA 19 % (+)    : $ {self.total_iva:>14,.2f} COP",
            "  " + "─" * 42,
            f"  TOTAL           : $ {self.total:>14,.2f} COP",
            "=" * 60,
        ]
        if self.notas:
            lineas += [f"\n  Notas: {self.notas}", "=" * 60]
        return "\n".join(lineas)

    def to_dict(self):
        return {
            "id_cotizacion":    self.id_cotizacion,
            "numero":           self.numero,
            "fecha_emision":    str(self.fecha_emision),
            "fecha_vencimiento":str(self.fecha_vencimiento),
            "cliente":          self.cliente.to_dict(),
            "productos":        [p.to_dict() for p in self.productos],
            "notas":            self.notas,
            "subtotal_bruto":   self.subtotal_bruto,
            "total_descuentos": self.total_descuentos,
            "base_imponible":   self.base_imponible,
            "total_iva":        self.total_iva,
            "total":            self.total,
        }
