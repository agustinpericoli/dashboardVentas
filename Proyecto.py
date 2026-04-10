import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# Configuración
st.set_page_config(page_title="Dashboard E-commerce", layout="wide")

st.title("📊 E-commerce Sales Dashboard")
st.caption("Interactive dashboard for analyzing e-commerce sales performance")

# =========================
# CARGA DE ARCHIVOS
# =========================

st.sidebar.header("📂 Cargar archivos")

ventas_file = st.sidebar.file_uploader("Ventas", type=["csv"])
productos_file = st.sidebar.file_uploader("Productos", type=["csv"])
clientes_file = st.sidebar.file_uploader("Clientes", type=["csv"])


def safe_read(file):
    try:
        df = pd.read_csv(file)
        if df.empty:
            return None
        return df
    except:
        return None


ventas = safe_read(ventas_file)
productos = safe_read(productos_file)
clientes = safe_read(clientes_file)

# =========================
# VALIDACIÓN
# =========================

if ventas is None or productos is None or clientes is None:
    st.warning("⚠️ Cargá los 3 archivos para ver el dashboard")
    st.stop()

# =========================
# PROCESAMIENTO
# =========================

# Merge
df = pd.merge(ventas, productos, on="producto")
df = pd.merge(df, clientes, on="cliente")

# Fechas
df["fecha"] = pd.to_datetime(df["fecha"])

# Métricas
df["ventas"] = df["unidades"] * df["precio"]
df["ganancia"] = (df["precio"] - df["costo"]) * df["unidades"]

# =========================
# FILTROS
# =========================

st.sidebar.header("🎛️ Filtros")

region = st.sidebar.selectbox(
    "Región", ["Todas"] + list(df["region"].unique())
)

if region != "Todas":
    df = df[df["region"] == region]

# =========================
# KPIs
# =========================

col1, col2, col3 = st.columns(3)

col1.metric("💰 Ventas Totales", f"${df['ventas'].sum():,.0f}")
col2.metric("📦 Unidades", df["unidades"].sum())
col3.metric("📈 Ganancia", f"${df['ganancia'].sum():,.0f}")

# =========================
# GRÁFICOS
# =========================

st.subheader("📅 Ventas en el tiempo")

ventas_fecha = df.groupby("fecha")["ventas"].sum()

fig, ax = plt.subplots()
fig, ax = plt.subplots(figsize=(10,4))
ventas_fecha.plot(ax=ax)
st.pyplot(fig)

# -------------------------

st.subheader("🏆 Top productos")

top_productos = df.groupby("producto")["ventas"].sum().sort_values(ascending=False)
st.bar_chart(top_productos)

# -------------------------

st.subheader("🌎 Ventas por región")

ventas_region = df.groupby("region")["ventas"].sum()
st.bar_chart(ventas_region)

# =========================
# TABLA
# =========================

st.subheader("📋 Datos")
st.dataframe(df)

# =========================
# EXPORTAR A EXCEL
# =========================

def generar_excel(dataframe):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        dataframe.to_excel(writer, index=False)
    return output.getvalue()


st.subheader("📥 Descargar reporte")

excel_data = generar_excel(df)

st.download_button(
    label="Descargar Excel",
    data=excel_data,
    file_name="reporte_ventas.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)