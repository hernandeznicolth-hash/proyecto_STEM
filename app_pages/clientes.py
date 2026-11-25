"""
app_pages/clientes.py — Directorio y gestión de clientes.
"""

import streamlit as st
import pandas as pd

from models.cliente import Cliente
import services.storage as db

st.title("Directorio de clientes", icon=":material/groups:")
st.caption("Administra tu base de datos de clientes y consulta el historial de cotizaciones asociadas.")

# ── 1. REGISTRAR NUEVO CLIENTE ───────────────────────────────────────────────
with st.expander("Registrar un nuevo cliente", icon=":material/person_add:"):
    with st.form("form_directorio_nuevo_cliente", clear_on_submit=True):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            nombre = st.text_input("Nombre completo *", placeholder="Ej: Diana Morales")
            empresa = st.text_input("Empresa", placeholder="Ej: Inversiones del Norte SAS")
            nit = st.text_input("NIT o Cédula", placeholder="Ej: 900.876.543-2")
        with col_c2:
            telefono = st.text_input("Teléfono", placeholder="Ej: +57 312 987 6543")
            email = st.text_input("Correo electrónico", placeholder="Ej: diana.morales@empresa.com")
            direccion = st.text_input("Dirección", placeholder="Ej: Calle 72 # 10-34, Medellín")

        btn_guardar = st.form_submit_button(
            "Guardar cliente en el sistema",
            icon=":material/save:",
            width="stretch",
        )

        if btn_guardar:
            if not nombre.strip():
                st.error("El nombre completo es obligatorio.", icon=":material/error:")
            else:
                cli = Cliente(
                    nombre=nombre.strip(),
                    empresa=empresa.strip(),
                    nit=nit.strip(),
                    direccion=direccion.strip(),
                    telefono=telefono.strip(),
                    email=email.strip(),
                )
                db.guardar_cliente(cli)
                st.success(f"Cliente '{cli.nombre}' registrado con éxito con ID: {cli.id_cliente}.", icon=":material/check_circle:")
                st.rerun()

st.write("")

# ── 2. LISTADO Y BÚSQUEDA DE CLIENTES ─────────────────────────────────────────
clientes = db.listar_clientes()

if not clientes:
    st.info("No hay clientes registrados en el sistema.", icon=":material/info:")
else:
    # Métricas de clientes
    total_clientes = len(clientes)
    con_empresa = sum(1 for c in clientes if c.empresa)
    con_nit = sum(1 for c in clientes if c.nit)

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Total clientes registrados", f"{total_clientes}")
    col_m2.metric("Clientes empresariales", f"{con_empresa}")
    col_m3.metric("Clientes con NIT/Cédula", f"{con_nit}")

    st.write("")

    filtro_cli = st.text_input(
        "Buscar cliente",
        placeholder="Filtra por nombre, empresa, NIT o correo...",
        label_visibility="collapsed",
    ).strip().lower()

    if filtro_cli:
        clientes_filtrados = [
            c for c in clientes
            if filtro_cli in c.nombre.lower()
            or filtro_cli in (c.empresa or "").lower()
            or filtro_cli in (c.nit or "").lower()
            or filtro_cli in (c.email or "").lower()
        ]
    else:
        clientes_filtrados = clientes

    if not clientes_filtrados:
        st.warning("No se encontraron clientes que coincidan con la búsqueda.", icon=":material/search_off:")
    else:
        filas_cli = []
        for c in clientes_filtrados:
            filas_cli.append({
                "ID": c.id_cliente,
                "Nombre": c.nombre,
                "Empresa": c.empresa or "—",
                "NIT / Cédula": c.nit or "—",
                "Teléfono": c.telefono or "—",
                "Correo electrónico": c.email or "—",
                "Dirección": c.direccion or "—",
            })

        st.dataframe(pd.DataFrame(filas_cli), width="stretch", hide_index=True)

        st.subheader("Cotizaciones por cliente")

        mapa_c = {
            f"{c.nombre} {'(' + c.empresa + ')' if c.empresa else ''} [ID: {c.id_cliente}]": c
            for c in clientes_filtrados
        }

        cli_seleccionado_str = st.selectbox(
            "Selecciona un cliente para ver su historial comercial",
            options=list(mapa_c.keys()),
        )

        cli_actual = mapa_c[cli_seleccionado_str]

        # Buscar cotizaciones de este cliente
        todas_cot = db.listar_cotizaciones()
        cotizaciones_del_cliente = [
            c for c in todas_cot
            if c["nombre"] == cli_actual.nombre
        ]

        if not cotizaciones_del_cliente:
            st.info(f"El cliente '{cli_actual.nombre}' aún no tiene cotizaciones generadas.", icon=":material/info:")
        else:
            filas_historial = []
            for item in cotizaciones_del_cliente:
                filas_historial.append({
                    "ID": item["id"],
                    "Número": item["numero"],
                    "Fecha emisión": item["fecha_emision"],
                    "Total COP": f"${item['total']:,.2f}",
                })
            st.dataframe(pd.DataFrame(filas_historial), width="stretch", hide_index=True)
