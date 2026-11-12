"""
storage.py — Capa de persistencia en SQLite.
Tablas: clientes, cotizaciones, items_cotizacion
"""

import sqlite3
import json
from pathlib import Path
from datetime import date
from models.cliente   import Cliente
from models.producto  import Producto
from models.cotizacion import Cotizacion

DB_PATH = Path(__file__).parent.parent / "data" / "cotizador.db"


def _conectar() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def inicializar_bd():
    """Crea las tablas si no existen."""
    with _conectar() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS clientes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre      TEXT NOT NULL,
                empresa     TEXT,
                nit         TEXT UNIQUE,
                direccion   TEXT,
                telefono    TEXT,
                email       TEXT
            );

            CREATE TABLE IF NOT EXISTS cotizaciones (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                numero           TEXT UNIQUE NOT NULL,
                fecha_emision    TEXT NOT NULL,
                fecha_vencimiento TEXT NOT NULL,
                id_cliente       INTEGER NOT NULL REFERENCES clientes(id),
                notas            TEXT,
                subtotal_bruto   REAL,
                total_descuentos REAL,
                base_imponible   REAL,
                total_iva        REAL,
                total            REAL
            );

            CREATE TABLE IF NOT EXISTS items_cotizacion (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cotizacion    INTEGER NOT NULL REFERENCES cotizaciones(id),
                descripcion      TEXT,
                cantidad         REAL,
                precio_unitario  REAL,
                descuento_pct    REAL,
                iva_pct          REAL,
                subtotal_bruto   REAL,
                valor_descuento  REAL,
                base_imponible   REAL,
                valor_iva        REAL,
                total            REAL
            );
        """)


# ── CLIENTES ──────────────────────────────────────────────────────────────────

def guardar_cliente(cliente: Cliente) -> Cliente:
    with _conectar() as conn:
        cur = conn.execute(
            """INSERT INTO clientes (nombre, empresa, nit, direccion, telefono, email)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (cliente.nombre, cliente.empresa, cliente.nit,
             cliente.direccion, cliente.telefono, cliente.email)
        )
        cliente.id_cliente = cur.lastrowid
    return cliente


def buscar_clientes(termino: str) -> list[Cliente]:
    patron = f"%{termino}%"
    with _conectar() as conn:
        filas = conn.execute(
            """SELECT * FROM clientes
               WHERE nombre LIKE ? OR empresa LIKE ? OR nit LIKE ?""",
            (patron, patron, patron)
        ).fetchall()
    return [_fila_a_cliente(f) for f in filas]


def listar_clientes() -> list[Cliente]:
    with _conectar() as conn:
        filas = conn.execute("SELECT * FROM clientes ORDER BY nombre").fetchall()
    return [_fila_a_cliente(f) for f in filas]


def _fila_a_cliente(fila) -> Cliente:
    return Cliente(
        id_cliente=fila["id"],
        nombre=fila["nombre"],
        empresa=fila["empresa"] or "",
        nit=fila["nit"] or "",
        direccion=fila["direccion"] or "",
        telefono=fila["telefono"] or "",
        email=fila["email"] or "",
    )


# ── COTIZACIONES ──────────────────────────────────────────────────────────────

def guardar_cotizacion(cot: Cotizacion) -> Cotizacion:
    with _conectar() as conn:
        cur = conn.execute(
            """INSERT INTO cotizaciones
               (numero, fecha_emision, fecha_vencimiento, id_cliente, notas,
                subtotal_bruto, total_descuentos, base_imponible, total_iva, total)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (cot.numero, str(cot.fecha_emision), str(cot.fecha_vencimiento),
             cot.cliente.id_cliente, cot.notas,
             cot.subtotal_bruto, cot.total_descuentos,
             cot.base_imponible, cot.total_iva, cot.total)
        )
        cot.id_cotizacion = cur.lastrowid
        for p in cot.productos:
            conn.execute(
                """INSERT INTO items_cotizacion
                   (id_cotizacion, descripcion, cantidad, precio_unitario,
                    descuento_pct, iva_pct, subtotal_bruto, valor_descuento,
                    base_imponible, valor_iva, total)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (cot.id_cotizacion, p.descripcion, p.cantidad, p.precio_unitario,
                 p.descuento_pct, p.iva_pct, p.subtotal_bruto, p.valor_descuento,
                 p.base_imponible, p.valor_iva, p.total)
            )
    return cot


def listar_cotizaciones() -> list[dict]:
    with _conectar() as conn:
        filas = conn.execute(
            """SELECT c.id, c.numero, c.fecha_emision, c.total, cl.nombre, cl.empresa
               FROM cotizaciones c JOIN clientes cl ON c.id_cliente = cl.id
               ORDER BY c.fecha_emision DESC"""
        ).fetchall()
    return [dict(f) for f in filas]


def cargar_cotizacion(id_cot: int) -> Cotizacion | None:
    with _conectar() as conn:
        fila_cot = conn.execute(
            "SELECT * FROM cotizaciones WHERE id = ?", (id_cot,)
        ).fetchone()
        if not fila_cot:
            return None
        fila_cli = conn.execute(
            "SELECT * FROM clientes WHERE id = ?", (fila_cot["id_cliente"],)
        ).fetchone()
        filas_items = conn.execute(
            "SELECT * FROM items_cotizacion WHERE id_cotizacion = ?", (id_cot,)
        ).fetchall()

    cliente = _fila_a_cliente(fila_cli)
    productos = [
        Producto(
            descripcion=f["descripcion"],
            cantidad=f["cantidad"],
            precio_unitario=f["precio_unitario"],
            descuento_pct=f["descuento_pct"],
            iva_pct=f["iva_pct"],
        )
        for f in filas_items
    ]
    return Cotizacion(
        cliente=cliente,
        productos=productos,
        notas=fila_cot["notas"] or "",
        id_cotizacion=fila_cot["id"],
        numero=fila_cot["numero"],
        fecha_emision=date.fromisoformat(fila_cot["fecha_emision"]),
        fecha_vencimiento=date.fromisoformat(fila_cot["fecha_vencimiento"]),
    )


def eliminar_cotizacion(id_cot: int):
    with _conectar() as conn:
        conn.execute("DELETE FROM items_cotizacion WHERE id_cotizacion = ?", (id_cot,))
        conn.execute("DELETE FROM cotizaciones WHERE id = ?", (id_cot,))
