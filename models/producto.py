"""
Clase Producto — Representa un ítem (producto o servicio) en la cotización.
"""

class Producto:
    IVA_DEFAULT = 0.19  # IVA Colombia 19 %

    def __init__(self, descripcion="", cantidad=1,
                 precio_unitario=0.0, descuento_pct=0.0, iva_pct=None):
        self.descripcion     = descripcion
        self.cantidad        = cantidad
        self.precio_unitario = precio_unitario
        self.descuento_pct   = descuento_pct          # porcentaje  0-100
        self.iva_pct         = iva_pct if iva_pct is not None else self.IVA_DEFAULT * 100

    # ── Cálculos ──────────────────────────────────────────────────────────────

    @property
    def subtotal_bruto(self) -> float:
        """cantidad × precio unitario, antes de descuento e IVA."""
        return self.cantidad * self.precio_unitario

    @property
    def valor_descuento(self) -> float:
        return self.subtotal_bruto * (self.descuento_pct / 100)

    @property
    def base_imponible(self) -> float:
        """Subtotal bruto menos descuento."""
        return self.subtotal_bruto - self.valor_descuento

    @property
    def valor_iva(self) -> float:
        return self.base_imponible * (self.iva_pct / 100)

    @property
    def total(self) -> float:
        return self.base_imponible + self.valor_iva

    # ── Representación ────────────────────────────────────────────────────────

    def __str__(self):
        return (
            f"  Descripción  : {self.descripcion}\n"
            f"  Cantidad     : {self.cantidad}\n"
            f"  Precio unit. : ${self.precio_unitario:,.2f} COP\n"
            f"  Descuento    : {self.descuento_pct:.1f}%  (−${self.valor_descuento:,.2f})\n"
            f"  IVA          : {self.iva_pct:.1f}%  (+${self.valor_iva:,.2f})\n"
            f"  Total ítem   : ${self.total:,.2f} COP"
        )

    def to_dict(self):
        return {
            "descripcion":     self.descripcion,
            "cantidad":        self.cantidad,
            "precio_unitario": self.precio_unitario,
            "descuento_pct":   self.descuento_pct,
            "iva_pct":         self.iva_pct,
            "subtotal_bruto":  self.subtotal_bruto,
            "valor_descuento": self.valor_descuento,
            "base_imponible":  self.base_imponible,
            "valor_iva":       self.valor_iva,
            "total":           self.total,
        }
