"""
app.py — Punto de entrada de la aplicación Streamlit para el Cotizador de Facturas.
Ejecutar: streamlit run app.py
"""

import streamlit as st
import services.storage as db

# Configuración inicial de la página
st.set_page_config(
    page_title="Cotizador de Facturas",
    page_icon=":material/receipt_long:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inicializar base de datos SQLite si no existe
db.inicializar_bd()

# Inicializar estados de sesión compartidos
if "items_cotizacion" not in st.session_state:
    st.session_state.items_cotizacion = []

if "cliente_activo_id" not in st.session_state:
    st.session_state.cliente_activo_id = None

if "ultima_cotizacion" not in st.session_state:
    st.session_state.ultima_cotizacion = None

# Definición de páginas con st.navigation
paginas = [
    st.Page(
        "app_pages/nueva_cotizacion.py",
        title="Nueva cotización",
        icon=":material/post_add:",
        default=True,
    ),
    st.Page(
        "app_pages/historial.py",
        title="Historial de cotizaciones",
        icon=":material/history:",
    ),
    st.Page(
        "app_pages/clientes.py",
        title="Directorio de clientes",
        icon=":material/groups:",
    ),
]

navegacion = st.navigation(paginas, position="sidebar")
navegacion.run()
