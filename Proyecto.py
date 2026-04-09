import pandas as pd
import streamlit as st
import numpy as np
from io import BytesIO

st.title("📊 Dashboard de Ventas E-commerce")
st.markdown("Análisis interactivo con insights, alertas y predicción")

# ==============================
# CARGA DE ARCHIVOS
# ==============================

st.sidebar.header("📂 Cargar archivos")

ventas_file = st.sidebar.file_uploader("ventas.csv", type=["csv"])
productos_file = st.sidebar.file_uploader("productos.csv", type=["csv"])
clientes_file = st.sidebar.file_uploader("clientes.csv", type=["csv"])

if ventas_file and productos_file and clientes_file:

    ventas = pd.read_csv(ventas_file)
    productos = pd.read_csv(productos_file)
    clientes = pd.read_csv(clientes_file)

    # ==============================
    # MERGE
    # ==============================

    df = pd.merge(ventas, productos, on="producto")
    df = pd.merge(df, clientes, on="cliente_id")

    # ==============================
    # LIMPIEZA + MÉTRICAS
    # ==============================

    df["fecha"] = pd.to_datetime(df["fecha"])
    df["ventas"] = df["unidades"] * df["precio"]
    df["ganancia"] = (df["precio"] - df["costo"]) * df["unidades"]

    # ==============================
    # FILTROS
    # ==============================

    st.sidebar.header("Filtros")

    fecha_min = df["fecha"].min()
    fecha_max = df["fecha"].max()

    rango_fechas = st.sidebar.date_input(
        "Rango de fechas",
        [fecha_min, fecha_max]
    )

    region = st.sidebar.selectbox(
        "Región",
        ["Todas"] + list(df["region"].unique())
    )

    producto = st.sidebar.selectbox(
        "Producto",
        ["Todos"] + list(df["producto"].unique())
    )

    df_filtrado = df.copy()

    if len(rango_fechas) == 2:
        inicio, fin = rango_fechas
        df_filtrado = df_filtrado[
            (df_filtrado["fecha"] >= pd.to_datetime(inicio)) &
            (df_filtrado["fecha"] <= pd.to_datetime(fin))
        ]

    if region != "Todas":
        df_filtrado = df_filtrado[df_filtrado["region"] == region]

    if producto != "Todos":
        df_filtrado = df_filtrado[df_filtrado["producto"] == producto]

    # ==============================
    # KPIs
    # ==============================

    ventas_totales = df_filtrado["ventas"].sum()
    ganancia_total = df_filtrado["ganancia"].sum()

    col1, col2, col3 = st.columns(3)

    col1.metric("💰 Ventas", f"${ventas_totales:,.0f}")
    col2.metric("💵 Ganancia", f"${ganancia_total:,.0f}")
    col3.metric("📦 Registros", len(df_filtrado))

    # ==============================
    # TOP PRODUCTOS
    # ==============================

    ventas_producto = df_filtrado.groupby("producto")["ventas"].sum().sort_values(ascending=False)

    st.subheader("🏆 Top 3 productos")
    st.write(ventas_producto.head(3))

    st.subheader("📦 Ventas por producto")
    st.bar_chart(ventas_producto)

    # ==============================
    # COMPARACIÓN DE PERÍODOS
    # ==============================

    if len(rango_fechas) == 2:
        inicio, fin = rango_fechas
        dias = (pd.to_datetime(fin) - pd.to_datetime(inicio)).days

        df_actual = df[
            (df["fecha"] >= pd.to_datetime(inicio)) &
            (df["fecha"] <= pd.to_datetime(fin))
        ]

        df_anterior = df[
            (df["fecha"] >= pd.to_datetime(inicio) - pd.Timedelta(days=dias)) &
            (df["fecha"] < pd.to_datetime(inicio))
        ]

        ventas_actual = df_actual["ventas"].sum()
        ventas_anterior = df_anterior["ventas"].sum()

        st.subheader("📊 Comparación de períodos")
        st.write("Ventas actuales:", ventas_actual)
        st.write("Ventas anteriores:", ventas_anterior)

        if ventas_anterior != 0:
            cambio = (ventas_actual - ventas_anterior) / ventas_anterior
            st.write(f"Cambio: {cambio:.2%}")

            if ventas_actual < ventas_anterior:
                st.error("⚠️ Las ventas están bajando")
            else:
                st.success("✅ Ventas estables o creciendo")

    # ==============================
    # ALERTAS
    # ==============================

    st.subheader("🚨 Alertas")

    ganancia_producto = df_filtrado.groupby("producto")["ganancia"].sum()

    if ventas_producto.idxmax() != ganancia_producto.idxmax():
        st.warning("El producto más vendido no es el más rentable")

    margen = ganancia_total / ventas_totales if ventas_totales > 0 else 0

    if margen < 0.3:
        st.error("Margen bajo")

    # ==============================
    # PREDICCIÓN SIMPLE
    # ==============================

    ventas_dia = df_filtrado.groupby("fecha")["ventas"].sum().reset_index()

    if len(ventas_dia) > 1:
        ventas_dia["fecha_num"] = range(len(ventas_dia))

        coef = np.polyfit(ventas_dia["fecha_num"], ventas_dia["ventas"], 1)
        ventas_dia["prediccion"] = np.polyval(coef, ventas_dia["fecha_num"])

        st.subheader("📈 Predicción de ventas")
        st.line_chart(ventas_dia.set_index("fecha")[["ventas", "prediccion"]])

    # ==============================
    # EXPORTAR A EXCEL
    # ==============================

    def generar_excel(df_filtrado):
        output = BytesIO()

        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_filtrado.to_excel(writer, sheet_name="datos")
            ventas_producto.to_excel(writer, sheet_name="ventas_producto")

        return output.getvalue()

    st.subheader("📥 Descargar reporte")

    excel_data = generar_excel(df_filtrado)

    st.download_button(
        label="Descargar Excel",
        data=excel_data,
        file_name="reporte_ventas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )