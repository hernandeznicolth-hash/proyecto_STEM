"""
app_pages/historial.py — Historial y consulta de cotizaciones registradas.
"""

from pathlib import Path
import streamlit as st
import pandas as pd

import services.storage as db
from services.pdf_generator import generar_pdf

st.title("Historial de cotizaciones", icon=":material/history:")
st.caption("Consulta, descarga en PDF y administra todas las cotizaciones guardadas en el sistema.")

lista_cotizaciones = db.listar_cotizaciones()

if not lista_cotizaciones:
    st.info("Aún no tienes cotizaciones registradas en la base de datos.", icon=":material/info:")
    st.page_link("app_pages/nueva_cotizacion.py", label="Crear una cotización ahora", icon=":material/add_circle:")
else:
    # ── MÉTRICAS GENERALES ───────────────────────────────────────────────────
    total_cotizaciones = len(lista_cotizaciones)
    suma_total = sum(c["total"] for c in lista_cotizaciones)
    promedio = suma_total / total_cotizaciones if total_cotizaciones else 0

    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    col_kpi1.metric("Total cotizaciones", f"{total_cotizaciones}")
    col_kpi2.metric("Monto total cotizado", f"${suma_total:,.0f} COP")
    col_kpi3.metric("Promedio por cotización", f"${promedio:,.0f} COP")

    st.write("")

    # ── BUSCADOR Y TABLA ─────────────────────────────────────────────────────
    filtro = st.text_input(
        "Buscar cotizaciones",
        placeholder="Filtra por número de cotización, nombre del cliente o empresa...",
        label_visibility="collapsed",
    ).strip().lower()

    if filtro:
        cotizaciones_filtradas = [
            c for c in lista_cotizaciones
            if filtro in c["numero"].lower()
            or filtro in (c["nombre"] or "").lower()
            or filtro in (c["empresa"] or "").lower()
        ]
    else:
        cotizaciones_filtradas = lista_cotizaciones

    if not cotizaciones_filtradas:
        st.warning("No se encontraron cotizaciones con ese criterio de búsqueda.", icon=":material/search_off:")
    else:
        # Preparar datos para visualización tabular
        filas = []
        for c in cotizaciones_filtradas:
            filas.append({
                "ID": c["id"],
                "Número": c["numero"],
                "Cliente": c["nombre"],
                "Empresa": c["empresa"] or "—",
                "Fecha emisión": c["fecha_emision"],
                "Total (COP)": f"${c['total']:,.2f}",
            })

        df_cots = pd.DataFrame(filas)
        st.dataframe(df_cots, width="stretch", hide_index=True)

        st.subheader("Detalle de la cotización")

        mapa_opciones = {
            f"{c['numero']} — {c['empresa'] or c['nombre']} (${c['total']:,.0f} COP)": c["id"]
            for c in cotizaciones_filtradas
        }

        seleccion_cot_str = st.selectbox(
            "Selecciona una cotización para ver el detalle y opciones",
            options=list(mapa_opciones.keys()),
        )

        id_seleccionado = mapa_opciones[seleccion_cot_str]
        cot = db.cargar_cotizacion(id_seleccionado)

        if cot:
            with st.container(border=True):
                # Cabecera de la cotización
                col_d1, col_d2, col_d3 = st.columns(3)
                with col_d1:
                    st.markdown(f"### {cot.numero}")
                    st.caption(f"Emisión: {cot.fecha_emision} | Vencimiento: {cot.fecha_vencimiento}")
                with col_d2:
                    st.markdown(f"**Cliente:** {cot.cliente.nombre}")
                    st.markdown(f"**Empresa:** {cot.cliente.empresa or '—'}")
                    st.markdown(f"**NIT / Cédula:** {cot.cliente.nit or '—'}")
                with col_d3:
                    st.markdown(f"**Teléfono:** {cot.cliente.telefono or '—'}")
                    st.markdown(f"**Correo:** {cot.cliente.email or '—'}")
                    st.markdown(f"**Dirección:** {cot.cliente.direccion or '—'}")

                st.divider()

                # Tabla de productos de la cotización
                st.markdown("**Ítems cotizados:**")
                filas_items = []
                for idx, p in enumerate(cot.productos, 1):
                    filas_items.append({
                        "#": idx,
                        "Descripción": p.descripcion,
                        "Cantidad": f"{p.cantidad:g}",
                        "Precio unitario": f"${p.precio_unitario:,.2f}",
                        "Descuento": f"{p.descuento_pct:.1f}%",
                        "IVA": f"{p.iva_pct:.1f}%",
                        "Total ítem": f"${p.total:,.2f}",
                    })
                st.dataframe(pd.DataFrame(filas_items), width="stretch", hide_index=True)

                # Resumen de totales
                col_t1, col_t2, col_t3, col_t4, col_t5 = st.columns(5)
                col_t1.metric("Subtotal bruto", f"${cot.subtotal_bruto:,.0f}")
                col_t2.metric("Descuentos (-)", f"${cot.total_descuentos:,.0f}")
                col_t3.metric("Base imponible", f"${cot.base_imponible:,.0f}")
                col_t4.metric("IVA 19% (+)", f"${cot.total_iva:,.0f}")
                col_t5.metric("Total COP", f"${cot.total:,.0f}")

                if cot.notas:
                    st.info(f"**Notas:** {cot.notas}", icon=":material/notes:")

                st.write("")

                # Acciones: Exportar / Descargar PDF y Eliminar
                col_act1, col_act2 = st.columns([2, 1], vertical_alignment="bottom")

                with col_act1:
                    # Comprobar o generar PDF
                    ruta_pdf = Path(__file__).resolve().parent.parent / "pdfs" / f"{cot.numero}.pdf"
                    if not ruta_pdf.is_file():
                        try:
                            ruta_pdf = generar_pdf(cot)
                        except Exception as e:
                            st.error(f"No se pudo generar el PDF: {e}")
                            ruta_pdf = None

                    if ruta_pdf and ruta_pdf.is_file():
                        st.download_button(
                            label=f"Descargar PDF ({cot.numero}.pdf)",
                            data=ruta_pdf.read_bytes(),
                            file_name=f"{cot.numero}.pdf",
                            mime="application/pdf",
                            icon=":material/download:",
                            width="stretch",
                        )

                with col_act2:
                    confirmar_eliminar = st.checkbox(
                        "Confirmar eliminación",
                        key=f"check_del_{cot.id_cotizacion}",
                    )
                    if st.button(
                        "Eliminar cotización",
                        icon=":material/delete_forever:",
                        type="secondary",
                        disabled=not confirmar_eliminar,
                        width="stretch",
                    ):
                        db.eliminar_cotizacion(cot.id_cotizacion)
                        st.success(f"Cotización {cot.numero} eliminada correctamente.")
                        st.rerun()
