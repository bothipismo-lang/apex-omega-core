import streamlit as st
import pdfplumber
import pandas as pd
import sqlite3

st.set_page_config(page_title="OMEGA-CORE", page_icon="🏇", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    </style>
""", unsafe_allow_html=True)

st.title("🏇 APEX-OMEGA ×50")
st.subheader("Terminal de Análisis Hípico · OMEGA-CORE")

def init_db():
    conn = sqlite3.connect('omega_core.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS historial 
                 (hipodromo TEXT, carrera TEXT, caballo TEXT, cuota REAL, prob REAL, edge REAL, resultado TEXT)''')
    conn.commit()
    return conn

conn = init_db()

tab1, tab2, tab3 = st.tabs(["📊 Calculadora", "📄 Leer PDF", "🧠 Memoria"])

with tab1:
    with st.form("datos_carrera"):
        col1, col2 = st.columns(2)
        with col1:
            hipodromo = st.text_input("Hipódromo:", value="Gulfstream Park")
            caballo = st.text_input("Nombre del Caballo:")
        with col2:
            carrera = st.number_input("Carrera (R#):", min_value=1, value=1)
            cuota = st.number_input("Cuota (ej. 4.50):", min_value=1.01, value=4.00)

        pp = st.slider("Prime Power (0.0 a 1.0):", 0.0, 1.0, 0.75)
        jockey_pct = st.slider("Win % Jockey:", 0.0, 0.40, 0.15)
        forma = st.slider("Forma reciente:", 0.0, 1.0, 0.50)
        
        boton = st.form_submit_button("🚀 CALCULAR")

    if boton:
        p_fund = (pp * 0.6) + (jockey_pct * 0.3) + (forma * 0.1)
        p_mercado = (1 / cuota) / 0.30 
        p_final = (0.50 * p_mercado) + (0.50 * p_fund)
        edge = (p_final * cuota) - 1

        st.metric(label="Probabilidad de Victoria", value=f"{p_final*100:.1f}%")
        
        if edge >= 0.05:
            st.success(f"✅ **VALOR DETECTADO (Edge: {edge:+.2f})**")
            st.info(f"💰 **ACCIÓN:** Apostar a WIN por **{caballo}**")
            c = conn.cursor()
            c.execute("INSERT INTO historial VALUES (?, ?, ?, ?, ?, ?, ?)", (hipodromo, f"R{carrera}", caballo, cuota, p_final, edge, "Pendiente"))
            conn.commit()
        else:
            st.error(f"⚠️ **SIN VALOR (Edge: {edge:+.2f})**")

with tab2:
    st.markdown("### 📄 Sube el PDF de la Jornada")
    st.write("Sube el archivo de Equibase o MeridianBet para que la app empiece a leerlo.")
    archivo_pdf = st.file_uploader("Selecciona el archivo PDF", type="pdf")
    
    if archivo_pdf is not None:
        with pdfplumber.open(archivo_pdf) as pdf:
            primera_pagina = pdf.pages[0]
            texto = primera_pagina.extract_text()
            st.success("✅ PDF leído con éxito. Aquí está el texto de la página 1:")
            st.text_area("Texto extraído:", texto, height=300)

with tab3:
    st.markdown("### 🧠 Historial de Jugadas")
    st.write("Aquí se guardan todos los caballos que has analizado.")
    df = pd.read_sql_query("SELECT * FROM historial", conn)
    st.dataframe(df)
    
    if not df.empty:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Descargar Base de Datos", csv, "omega_db.csv", "text/csv")
