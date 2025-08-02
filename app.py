"""Módulo principal de la app de gestión de inventario: Registro de Ventas."""

# Importaciones estándar y externas
import os
from datetime import date
import streamlit as st
import psycopg2
import pandas as pd

# Ruta al archivo .env
host=st.secrets["DB_HOST"]

# Conexión a la base de datos
def get_db_connection():
    """
    Establece y retorna una conexión a la base de datos PostgreSQL
    usando las variables de entorno configuradas en .env.
    """
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT")
    )

# Inicializar estado para controlar refresco
if 'venta_guardada' not in st.session_state:
    st.session_state.venta_guardada = False

# Título
st.title("🛒 Registro de Ventas")

col1, col2 = st.columns([1, 2])

# --- Columna 2: Visualización de la tabla ---
with col2:
    st.subheader("📋 Registro actual de ventas")
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT sucursal, almacen, producto, descripcion, cantidad, stock, usuario, fecha_vt
                FROM ventas
                ORDER BY fecha_vt DESC
            """)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            data = pd.DataFrame(rows, columns=columns)
            st.dataframe(data, use_container_width=True)
    except Exception as e:
        st.error(f"Error al cargar los datos: {str(e)}")
    finally:
        if conn:
            conn.close()

# --- Columna 1: Formulario ---
with col1:
    st.subheader("Nueva Venta")
    # Usar un form key único basado en el estado
    form_key = "venta_form" if not st.session_state.venta_guardada else "venta_form_refresh"  # pylint: disable=invalid-name
    with st.form(key=form_key):
        # Campos del formulario con valores iniciales
        sucursal = st.text_input("Sucursal*", value="")
        almacen = st.text_input("Almacén*", value="")
        producto = st.text_input("Producto*", value="")
        descripcion = st.text_input("Descripción*", value="")
        cantidad = st.number_input("Cantidad Vendida*", min_value=1, step=1, value=1)
        stock = st.number_input("Stock Actual*", min_value=0, step=1, value=0)
        usuario = st.text_input("Usuario que registra la venta*", value="")
        fecha_vt = st.date_input("Fecha de la venta*", value=date.today())

        submitted = st.form_submit_button("💾 Guardar Venta")

        if submitted:
            # Validación de campos
            campos_validar = {
                "Sucursal": sucursal,
                "Almacén": almacen,
                "Producto": producto,
                "Descripción": descripcion,
                "Cantidad": cantidad,
                "Stock": stock,
                "Usuario": usuario,
                "Fecha": fecha_vt
            }
            campos_faltantes = [campo for campo, valor in campos_validar.items()
                              if (valor == "" or valor is None) and str(valor) != "0"]
            if campos_faltantes:
                st.error(f"ERROR: Complete todos los campos obligatorios. "
                         f"Faltan: {', '.join(campos_faltantes)}")
            else:
                conn = None # pylint: disable=invalid-name
                try:
                    conn = get_db_connection()
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO ventas 
                            (sucursal, almacen, producto, descripcion, cantidad, stock, usuario, fecha_vt)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (sucursal, almacen, producto, descripcion,
                              cantidad, stock, usuario, fecha_vt))
                        conn.commit()
                    st.success("✅ Venta registrada correctamente.")
                    st.session_state.venta_guardada = True
                    st.rerun()  # Forzar recarga completa

                except Exception as e:
                    st.error(f"❌ Error al guardar: {str(e)}")
                    if conn:
                        conn.rollback()
                finally:
                    if conn:
                        conn.close()
        else:
            # Resetear el estado si no se ha enviado el formulario
            st.session_state.venta_guardada = False

# Nota sobre campos obligatorios
st.markdown("""
<style>
.obligatorio {
    font-size: 0.8rem;
    color: #ff4b4b;
    margin-top: -10px;
    margin-bottom: 10px;
    font-weight: bold;
}
</style>
<div class="obligatorio">* Todos los campos son obligatorios</div>
""", unsafe_allow_html=True)
