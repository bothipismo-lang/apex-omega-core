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

# --- INICIALIZAR BASE DE DATOS Y BANCA ---
def init_db():
    conn = sqlite3.connect('omega_core.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS historial 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, hipodromo TEXT, carrera TEXT, caballo TEXT, cuota REAL, stake REAL, prob REAL, edge REAL, resultado TEXT)''')
    # Creamos tabla para la banca
    c.execute('''CREATE TABLE IF NOT EXISTS banca 
                 (id INTEGER PRIMARY KEY, balance REAL)''')
    # Si la banca está vacía, inicializamos con 1000
    c.execute("SELECT balance FROM banca WHERE id = 1")
    if c.fetchone() is None:
        c.execute("INSERT INTO banca (id, balance) VALUES (1, 1000.0)")
    conn.commit()
    return conn

conn = init_db()

# --- CREAR PESTAÑAS ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Calculadora", "📄 Leer PDF", "🧠 Memoria", "💰 Bankroll"])

# PESTAÑA 1: CALCULADORA
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
        
        stake = st.number_input("Stake (Apuesta en Bs):", min_value=1.0, value=100.0)
        
        boton = st.form_submit_button("🚀 CALCULAR Y REGISTRAR")

    if boton:
        p_fund = (pp * 0.6) + (jockey_pct * 0.3) + (forma * 0.1)
        p_mercado = (1 / cuota) / 0.30 
        p_final = (0.50 * p_mercado) + (0.50 * p_fund)
        edge = (p_final * cuota) - 1

        st.metric(label="Probabilidad de Victoria", value=f"{p_final*100:.1f}%")
        
        if edge >= 0.05:
            st.success(f"✅ **VALOR DETECTADO (Edge: {edge:+.2f})**")
            st.info(f"💰 **ACCIÓN:** Apostar {stake} Bs a WIN por **{caballo}**")
            
            # Guardar en el historial como Pendiente y restar de la banca
            c = conn.cursor()
            c.execute("INSERT INTO historial (hipodromo, carrera, caballo, cuota, stake, prob, edge, resultado) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                      (hipodromo, f"R{carrera}", caballo, cuota, stake, p_final, edge, "Pendiente"))
            # Restamos el stake de la banca actual
            c.execute("UPDATE banca SET balance = balance - ? WHERE id = 1", (stake,))
            conn.commit()
            st.warning(f"⚠️ Se han descontado {stake} Bs de tu banca para esta apuesta.")
        else:
            st.error(f"⚠️ **SIN VALOR (Edge: {edge:+.2f})**")

# PESTAÑA 2: LECTOR DE PDF
with tab2:
    st.markdown("### 📄 Sube el PDF de la Jornada")
    archivo_pdf = st.file_uploader("Selecciona el archivo PDF", type="pdf")
    if archivo_pdf is not None:
        with pdfplumber.open(archivo_pdf) as pdf:
            primera_pagina = pdf.pages[0]
            texto = primera_pagina.extract_text()
            st.success("✅ PDF leído con éxito:")
            st.text_area("Texto extraído:", texto, height=300)

# PESTAÑA 3: MEMORIA (Historial y Resolución)
with tab3:
    st.markdown("### 🧠 Historial y Resultados")
    st.write("Aquí puedes marcar si una apuesta pendiente ganó o perdió.")
    
    df = pd.read_sql_query("SELECT * FROM historial", conn)
    st.dataframe(df)
    
    # Buscar apuestas pendientes para resolver
    pendientes = df[df['resultado'] == 'Pendiente']
    if not pendientes.empty:
        st.markdown("#### Resolver Apuesta Pendiente:")
        for index, row in pendientes.iterrows():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{row['caballo']}** en {row['hipodromo']} {row['carrera']} | Cuota: {row['cuota']} | Stake: {row['stake']} Bs")
            with col2:
                if st.button(f"Ganó", key=f"win_{row['id']}"):
                    ganancia = (row['stake'] * row['cuota']) # Retorno total
                    c = conn.cursor()
                    c.execute("UPDATE historial SET resultado = 'Ganó' WHERE id = ?", (row['id'],))
                    c.execute("UPDATE banca SET balance = balance + ? WHERE id = 1", (ganancia,))
                    conn.commit()
                    st.success(f"¡Victoria! Se sumaron {ganancia:.2f} Bs")
                    st.rerun()
                
                if st.button(f"Perdió", key=f"lose_{row['id']}"):
                    c = conn.cursor()
                    c.execute("UPDATE historial SET resultado = 'Perdió' WHERE id = ?", (row['id'],))
                    conn.commit()
                    st.error(f"Derrota. Se mantienen las pérdidas.")
                    st.rerun()
    else:
        st.info("No hay apuestas pendientes por resolver.")

# PESTAÑA 4: BANKROLL (La nueva banca automática)
with tab4:
    st.markdown("### 💰 Gestión de Banca")
    
    # Obtener balance actual
    c = conn.cursor()
    c.execute("SELECT balance FROM banca WHERE id = 1")
    balance_actual = c.fetchone()[0]
    
    st.metric(label="Banca Actual", value=f"{balance_actual:.2f} Bs")
    
    st.markdown("---")
    st.write("Si necesitas ajustar la banca manualmente (por ejemplo, al depositar o retirar dinero):")
    ajuste = st.number_input("Nuevo saldo total (Bs):", min_value=0.0, value=float(balance_actual))
    if st.button("Actualizar Banca Manualmente"):
        c.execute("UPDATE banca SET balance = ? WHERE id = 1", (ajuste,))
        conn.commit()
        st.success("Banca actualizada.")
        st.rerun()
