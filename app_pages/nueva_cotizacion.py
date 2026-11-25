"""
app_pages/nueva_cotizacion.py — Creación de nuevas cotizaciones con cálculo en tiempo real y generación de PDF.
"""

from pathlib import Path
import streamlit as st
import pandas as pd

from models.cliente import Cliente
from models.producto import Producto
from models.cotizacion import Cotizacion
import services.storage as db
from services.pdf_generator import generar_pdf, MAX_PRODUCTOS

st.title("Nueva cotización", icon=":material/post_add:")
st.caption("Crea y calcula cotizaciones comerciales para Colombia con IVA del 19% y exportación a PDF.")

# ── 1. GESTIÓN DEL CLIENTE ───────────────────────────────────────────────────
st.subheader("Información del cliente")

clientes_disponibles = db.listar_clientes()
opciones_cliente = ["Seleccionar cliente existente", "Registrar nuevo cliente"]
modo_cliente = st.radio(
    "Origen del cliente",
    opciones_cliente,
    horizontal=True,
    label_visibility="collapsed",
)

cliente_seleccionado: Cliente | None = None

if modo_cliente == "Seleccionar cliente existente":
    if not clientes_disponibles:
        st.info("No hay clientes registrados en la base de datos. Por favor registra uno nuevo.", icon=":material/info:")
    else:
        # Mapeo de clientes para el selector
        mapa_clientes = {
            f"{c.nombre} {'(' + c.empresa + ')' if c.empresa else ''} — NIT: {c.nit or 'Sin NIT'} [ID: {c.id_cliente}]": c
            for c in clientes_disponibles
        }
        
        # Pre-seleccionar si ya había uno activo
        indices = list(mapa_clientes.keys())
        indice_por_defecto = 0
        if st.session_state.cliente_activo_id:
            for idx, c in enumerate(mapa_clientes.values()):
                if c.id_cliente == st.session_state.cliente_activo_id:
                    indice_por_defecto = idx
                    break

        seleccion_str = st.selectbox(
            "Selecciona un cliente",
            options=indices,
            index=indice_por_defecto,
        )
        if seleccion_str:
            cliente_seleccionado = mapa_clientes[seleccion_str]
            st.session_state.cliente_activo_id = cliente_seleccionado.id_cliente

            with st.container(border=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**Nombre:** {cliente_seleccionado.nombre}")
                    st.markdown(f"**Empresa:** {cliente_seleccionado.empresa or '—'}")
                with col2:
                    st.markdown(f"**NIT / Cédula:** {cliente_seleccionado.nit or '—'}")
                    st.markdown(f"**Teléfono:** {cliente_seleccionado.telefono or '—'}")
                with col3:
                    st.markdown(f"**Correo:** {cliente_seleccionado.email or '—'}")
                    st.markdown(f"**Dirección:** {cliente_seleccionado.direccion or '—'}")

else:
    with st.container(border=True):
        st.markdown("**Registrar datos del cliente**")
        with st.form("form_nuevo_cliente", clear_on_submit=False):
            col_a, col_b = st.columns(2)
            with col_a:
                nuevo_nombre = st.text_input("Nombre completo *", placeholder="Ej: Juan Pérez")
                nueva_empresa = st.text_input("Empresa", placeholder="Ej: Soluciones SAS")
                nuevo_nit = st.text_input("NIT o Cédula", placeholder="Ej: 901.234.567-8")
            with col_b:
                nuevo_telefono = st.text_input("Teléfono", placeholder="Ej: +57 300 123 4567")
                nuevo_email = st.text_input("Correo electrónico", placeholder="Ej: contacto@ejemplo.com")
                nueva_direccion = st.text_input("Dirección", placeholder="Ej: Cra 15 # 85-20, Bogotá")

            btn_guardar_cliente = st.form_submit_button(
                "Guardar y usar cliente",
                icon=":material/person_add:",
                width="stretch",
            )

            if btn_guardar_cliente:
                if not nuevo_nombre.strip():
                    st.error("El nombre completo del cliente es obligatorio.", icon=":material/error:")
                else:
                    nuevo_cli = Cliente(
                        nombre=nuevo_nombre.strip(),
                        empresa=nueva_empresa.strip(),
                        nit=nuevo_nit.strip(),
                        direccion=nueva_direccion.strip(),
                        telefono=nuevo_telefono.strip(),
                        email=nuevo_email.strip(),
                    )
                    db.guardar_cliente(nuevo_cli)
                    st.session_state.cliente_activo_id = nuevo_cli.id_cliente
                    st.success(f"Cliente '{nuevo_cli.nombre}' registrado con éxito con ID: {nuevo_cli.id_cliente}.", icon=":material/check_circle:")
                    st.rerun()

    if st.session_state.cliente_activo_id:
        for c in db.listar_clientes():
            if c.id_cliente == st.session_state.cliente_activo_id:
                cliente_seleccionado = c
                break

st.write("")

# ── 2. PRODUCTOS Y SERVICIOS ─────────────────────────────────────────────────
st.subheader("Productos o servicios")

num_items_actual = len(st.session_state.items_cotizacion)

# Formulario para agregar un ítem
if num_items_actual < MAX_PRODUCTOS:
    with st.container(border=True):
        st.markdown(f"**Agregar ítem #{num_items_actual + 1}** (Máximo {MAX_PRODUCTOS} ítems)")
        with st.form("form_agregar_producto", clear_on_submit=True):
            f_desc = st.text_input("Descripción del producto o servicio *", placeholder="Ej: Consultoría técnica especializada")
            
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                f_cant = st.number_input("Cantidad", min_value=0.01, value=1.0, step=1.0)
            with c2:
                f_precio = st.number_input("Precio unitario (COP) *", min_value=0.0, value=100000.0, step=10000.0)
            with c3:
                f_desc_pct = st.number_input("Descuento %", min_value=0.0, max_value=100.0, value=0.0, step=1.0)
            with c4:
                f_iva_pct = st.number_input("IVA %", min_value=0.0, max_value=100.0, value=19.0, step=1.0)

            btn_agregar_item = st.form_submit_button("Agregar ítem a la lista", icon=":material/add:", width="stretch")

            if btn_agregar_item:
                if not f_desc.strip():
                    st.error("La descripción del producto/servicio es obligatoria.", icon=":material/error:")
                else:
                    nuevo_producto = Producto(
                        descripcion=f_desc.strip(),
                        cantidad=float(f_cant),
                        precio_unitario=float(f_precio),
                        descuento_pct=float(f_desc_pct),
                        iva_pct=float(f_iva_pct),
                    )
                    st.session_state.items_cotizacion.append(nuevo_producto)
                    st.success(f"Ítem '{f_desc.strip()}' agregado.", icon=":material/check:")
                    st.rerun()
else:
    st.warning(f"Has alcanzado el límite máximo permitido de {MAX_PRODUCTOS} ítems para la plantilla PDF.", icon=":material/warning:")

# Listado de productos agregados
if st.session_state.items_cotizacion:
    filas_tabla = []
    for idx, p in enumerate(st.session_state.items_cotizacion, 1):
        filas_tabla.append({
            "#": idx,
            "Descripción": p.descripcion,
            "Cantidad": f"{p.cantidad:g}",
            "Precio unitario": f"${p.precio_unitario:,.2f}",
            "Desc. %": f"{p.descuento_pct:.1f}%",
            "IVA %": f"{p.iva_pct:.1f}%",
            "Subtotal bruto": f"${p.subtotal_bruto:,.2f}",
            "Total ítem": f"${p.total:,.2f}",
        })
    
    df_items = pd.DataFrame(filas_tabla)
    st.dataframe(df_items, width="stretch", hide_index=True)

    col_del_1, col_del_2 = st.columns([3, 1], vertical_alignment="bottom")
    with col_del_1:
        item_a_eliminar = st.selectbox(
            "Seleccionar ítem a eliminar",
            options=range(1, len(st.session_state.items_cotizacion) + 1),
            format_func=lambda x: f"#{x} — {st.session_state.items_cotizacion[x - 1].descripcion}",
            label_visibility="collapsed",
        )
    with col_del_2:
        if st.button("Eliminar ítem", icon=":material/delete:", width="stretch"):
            del st.session_state.items_cotizacion[item_a_eliminar - 1]
            st.rerun()

    if st.button("Vaciar todos los ítems", icon=":material/clear_all:"):
        st.session_state.items_cotizacion = []
        st.rerun()
else:
    st.info("Aún no has agregado ningún producto o servicio a la cotización.", icon=":material/info:")

st.write("")

# ── 3. RESUMEN Y GENERACIÓN ──────────────────────────────────────────────────
st.subheader("Resumen y exportación")

if st.session_state.items_cotizacion:
    subtotal_bruto = sum(p.subtotal_bruto for p in st.session_state.items_cotizacion)
    total_descuentos = sum(p.valor_descuento for p in st.session_state.items_cotizacion)
    base_imponible = sum(p.base_imponible for p in st.session_state.items_cotizacion)
    total_iva = sum(p.valor_iva for p in st.session_state.items_cotizacion)
    total_general = sum(p.total for p in st.session_state.items_cotizacion)

    with st.container(border=True):
        col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
        col_m1.metric("Subtotal bruto", f"${subtotal_bruto:,.0f} COP")
        col_m2.metric("Descuentos (-)", f"${total_descuentos:,.0f} COP")
        col_m3.metric("Base imponible", f"${base_imponible:,.0f} COP")
        col_m4.metric("IVA 19% (+)", f"${total_iva:,.0f} COP")
        col_m5.metric("Total cotización", f"${total_general:,.0f} COP")

    notas_cotizacion = st.text_area(
        "Notas o términos y condiciones (opcional)",
        placeholder="Ej: Oferta válida por 30 días calendario. Forma de pago: 50% anticipo y 50% contra entrega.",
        height=90,
    )

    col_btn_guardar, col_btn_nuevo = st.columns([2, 1], vertical_alignment="bottom")

    with col_btn_guardar:
        btn_generar = st.button(
            "Guardar cotización y generar PDF",
            icon=":material/picture_as_pdf:",
            type="primary",
            width="stretch",
        )

    with col_btn_nuevo:
        if st.button("Reiniciar cotización", icon=":material/refresh:", width="stretch"):
            st.session_state.items_cotizacion = []
            st.session_state.ultima_cotizacion = None
            st.rerun()

    if btn_generar:
        if not cliente_seleccionado:
            st.error("Debes seleccionar o registrar un cliente antes de guardar.", icon=":material/error:")
        else:
            try:
                # Crear objeto cotización
                nueva_cot = Cotizacion(
                    cliente=cliente_seleccionado,
                    productos=list(st.session_state.items_cotizacion),
                    notas=notas_cotizacion.strip(),
                )
                
                # Guardar en base de datos SQLite
                db.guardar_cotizacion(nueva_cot)

                # Generar el PDF
                ruta_pdf = generar_pdf(nueva_cot)

                st.session_state.ultima_cotizacion = {
                    "cot": nueva_cot,
                    "pdf_path": str(ruta_pdf),
                    "numero": nueva_cot.numero,
                }

                st.success(
                    f"¡Cotización **{nueva_cot.numero}** guardada y generada exitosamente!",
                    icon=":material/check_circle:",
                )
            except Exception as e:
                st.error(f"Error al generar la cotización: {e}", icon=":material/error:")

# Descarga directa del PDF generado
if st.session_state.ultima_cotizacion:
    info_cot = st.session_state.ultima_cotizacion
    pdf_path = Path(info_cot["pdf_path"])

    if pdf_path.is_file():
        pdf_bytes = pdf_path.read_bytes()
        with st.container(border=True):
            st.markdown(f"**Descarga tu cotización {info_cot['numero']}**")
            st.download_button(
                label=f"Descargar archivo PDF ({info_cot['numero']}.pdf)",
                data=pdf_bytes,
                file_name=f"{info_cot['numero']}.pdf",
                mime="application/pdf",
                icon=":material/download:",
                width="stretch",
            )
