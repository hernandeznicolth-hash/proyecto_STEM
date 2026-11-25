"""
main.py — Punto de entrada del Cotizador de Facturas (Colombia, COP, IVA 19%)
Ejecutar: python main.py
"""

import sys
from models.cliente    import Cliente
from models.producto   import Producto
from models.cotizacion import Cotizacion
import services.storage as db

# Utilidades de consola 

def limpiar():
    print("\n" * 2)

def titulo(texto: str):
    print(f"\n{'=' * 60}")
    print(f"  {texto}")
    print('=' * 60)

def pedir(prompt: str, obligatorio=True) -> str:
    while True:
        valor = input(f"  {prompt}: ").strip()
        if valor or not obligatorio:
            return valor
        print("  Este campo es obligatorio.")

def pedir_numero(prompt: str, tipo=float, minimo=None, opcional=False) -> float | None:
    while True:
        raw = input(f"  {prompt}: ").strip()
        if not raw and opcional:
            return None
        try:
            valor = tipo(raw)
            if minimo is not None and valor < minimo:
                print(f"  El valor mínimo es {minimo}.")
                continue
            return valor
        except ValueError:
            print("  Ingresa un número válido.")

def confirmar(pregunta: str) -> bool:
    r = input(f"  {pregunta} [s/n]: ").strip().lower()
    return r in ("s", "si", "sí", "y", "yes")

def pausar():
    input("\n  Presiona Enter para continuar...")


# Gestión de clientes    

def seleccionar_o_crear_cliente() -> Cliente:
    titulo("CLIENTE")
    termino = pedir("Buscar cliente (nombre / empresa / NIT) o presiona Enter para crear uno nuevo", obligatorio=False)

    if termino:
        resultados = db.buscar_clientes(termino)
        if resultados:
            print(f"\n  Se encontraron {len(resultados)} resultado(s):\n")
            for i, c in enumerate(resultados, 1):
                print(f"  [{i}] {c.nombre}  |  {c.empresa}  |  NIT: {c.nit}")
            opcion = pedir_numero(f"\n  Selecciona [1-{len(resultados)}] o 0 para crear nuevo", tipo=int, minimo=0)
            if 1 <= int(opcion) <= len(resultados):
                return resultados[int(opcion) - 1]
        else:
            print("  No se encontraron clientes. Registrando uno nuevo...")

    return _registrar_cliente()


def _registrar_cliente() -> Cliente:
    titulo("NUEVO CLIENTE")
    nombre  = pedir("Nombre completo")
    empresa = pedir("Empresa", obligatorio=False)

    while True:
        nit = pedir("NIT / Cédula", obligatorio=False)
        if nit:
            cliente_existente = db.obtener_cliente_por_nit(nit)
            if cliente_existente:
                print(f"\n  [!] Ya existe un cliente registrado con el NIT/Cédula '{nit}':")
                print(f"      Nombre : {cliente_existente.nombre}")
                print(f"      Empresa: {cliente_existente.empresa or 'N/A'}")
                if confirmar("  ¿Deseas usar este cliente existente?"):
                    return cliente_existente
                print("  Ingresa un NIT diferente o déjalo vacío para continuar.\n")
                continue
        break

    direccion = pedir("Dirección", obligatorio=False)
    telefono  = pedir("Teléfono", obligatorio=False)
    email     = pedir("Email", obligatorio=False)

    cliente = Cliente(
        nombre    = nombre,
        empresa   = empresa,
        nit       = nit,
        direccion = direccion,
        telefono  = telefono,
        email     = email,
    )

    try:
        db.guardar_cliente(cliente)
        print(f"\n  Cliente registrado con ID: {cliente.id_cliente}")
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            print(f"\n  [!] El NIT '{nit}' ya está registrado en la base de datos.")
            cliente_existente = db.obtener_cliente_por_nit(nit)
            if cliente_existente:
                return cliente_existente
        raise e

    return cliente


#  Gestión de productos     

def agregar_productos() -> list[Producto]:
    from services.catalogo import cargar_catalogo

    titulo("AGREGAR PRODUCTOS / SERVICIOS")
    catalogo = cargar_catalogo()
    productos = []

    while True:
        print(f"\n  ── Ítem #{len(productos) + 1} ──────────────────────────────────────")

        if catalogo:
            print("\n  Catálogo de Productos (Nicolttissue):")
            for idx, item in enumerate(catalogo, 1):
                print(f"    [{idx}] {item['nombre_completo']:<45} $ {item['precio']:>10,.0f} COP")
            print("    [0] Ingresar producto manualmente")

            seleccion = pedir_numero(
                f"\n  Selecciona un producto [1-{len(catalogo)}] o 0 para manual",
                tipo=int,
                minimo=0,
            )

            if seleccion and 1 <= seleccion <= len(catalogo):
                elegido = catalogo[seleccion - 1]
                descripcion = elegido["nombre_completo"]
                precio_base = elegido["precio"]
                print(f"  -> Elegido: {descripcion}")

                precio_in = pedir_numero(
                    f"  Precio unitario COP (Enter = ${precio_base:,.0f})",
                    tipo=float,
                    minimo=0,
                    opcional=True,
                )
                precio_unitario = precio_base if precio_in is None else precio_in
            else:
                descripcion = pedir("Descripción del producto/servicio")
                precio_unitario = pedir_numero("Precio unitario (COP)", tipo=float, minimo=0)
        else:
            descripcion = pedir("Descripción del producto/servicio")
            precio_unitario = pedir_numero("Precio unitario (COP)", tipo=float, minimo=0)

        cantidad      = pedir_numero("Cantidad", tipo=float, minimo=0.001)
        descuento_pct = pedir_numero("Descuento % (Enter = 0)", tipo=float, minimo=0, opcional=True) or 0.0
        iva_pct       = pedir_numero("IVA % (Enter = 19)", tipo=float, minimo=0, opcional=True)
        if iva_pct is None:
            iva_pct = 19.0

        p = Producto(descripcion, cantidad, precio_unitario, descuento_pct, iva_pct)
        productos.append(p)
        print(f"\n{p}")

        if not confirmar("\n  ¿Agregar otro producto/servicio?"):
            break

    return productos


#  Nueva cotización 

def nueva_cotizacion():
    cliente   = seleccionar_o_crear_cliente()
    productos = agregar_productos()
    notas     = pedir("\nNotas / Términos y condiciones (opcional)", obligatorio=False)

    cot = Cotizacion(cliente=cliente, productos=productos, notas=notas)

    limpiar()
    print(cot.resumen())

    if not confirmar("\n  ¿Guardar esta cotización?"):
        print("  Cotización cancelada.")
        return

    db.guardar_cotizacion(cot)
    print(f"\n  Cotización guardada: {cot.numero}")

    if confirmar("  ¿Exportar a PDF?"):
        _exportar_pdf(cot)


def _exportar_pdf(cot: Cotizacion):
    try:
        from services.pdf_generator import generar_pdf
        ruta = generar_pdf(cot)
        print(f"\n  PDF generado: {ruta}")
    except ImportError:
        print("\n  PyMuPDF no está instalado.")
        print("     Ejecuta: pip install -r requirements.txt")
    except (FileNotFoundError, ValueError) as error:
        print(f"\n  No se pudo generar el PDF: {error}")


#  Historial de cotizaciones 

def ver_historial():
    titulo("HISTORIAL DE COTIZACIONES")
    lista = db.listar_cotizaciones()
    if not lista:
        print("  No hay cotizaciones guardadas.")
        pausar()
        return

    print(f"\n  {'#':<4} {'Número':<30} {'Cliente':<25} {'Fecha':<12} {'Total COP':>16}")
    print("  " + "─" * 90)
    for i, c in enumerate(lista, 1):
        cliente_str = c["empresa"] or c["nombre"]
        print(f"  {i:<4} {c['numero']:<30} {cliente_str:<25} {c['fecha_emision']:<12} ${c['total']:>14,.2f}")

    print("\n  [0] Volver")
    opcion = pedir_numero(f"  Selecciona [1-{len(lista)}] para ver detalle, o 0 para volver", tipo=int, minimo=0)
    if opcion == 0:
        return

    idx = int(opcion) - 1
    if 0 <= idx < len(lista):
        _detalle_cotizacion(lista[idx]["id"])


def _detalle_cotizacion(id_cot: int):
    cot = db.cargar_cotizacion(id_cot)
    if not cot:
        print("  No se encontró la cotización.")
        return

    limpiar()
    print(cot.resumen())

    print("\n  Opciones:")
    print("  [1] Exportar PDF")
    print("  [2] Eliminar cotización")
    print("  [0] Volver")

    op = pedir_numero("  Opción", tipo=int, minimo=0)
    if op == 1:
        _exportar_pdf(cot)
    elif op == 2:
        if confirmar("  ¿Eliminar definitivamente esta cotización?"):
            db.eliminar_cotizacion(id_cot)
            print("  Cotización eliminada.")
    pausar()


# ── Menú principal

def menu_principal():
    db.inicializar_bd()
    while True:
        limpiar()
        titulo("COTIZADOR DE FACTURAS — Colombia (COP)")
        print("  [1] Nueva cotización")
        print("  [2] Ver historial")
        print("  [0] Salir")

        op = input("\n  Selecciona una opción: ").strip()

        if op == "1":
            nueva_cotizacion()
            pausar()
        elif op == "2":
            ver_historial()
        elif op == "0":
            print("\n  ¡Hasta luego!\n")
            sys.exit(0)
        else:
            print("  Opción no válida.")
            pausar()


if __name__ == "__main__":
    menu_principal()

