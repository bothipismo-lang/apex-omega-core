import streamlit as st
import pdfplumber
import pandas as pd
import sqlite3

# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO PREMIUM
st.set_page_config(page_title="OMEGA-CORE ULTIMATE", page_icon="🏇", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #4CAF50; color: white; font-weight: bold; }
    .stMetric { background-color: #1E2129; padding: 15px; border-radius: 10px; border: 1px solid #3E414B; }
    h1, h2, h3 { color: #00E5FF; }
    </style>
""", unsafe_allow_html=True)

# 2. BASE DE DATOS
def init_db():
    # Usamos la v2 para evitar el error de columnas
    conn = sqlite3.connect('omega_core_v2.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS historial 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, hipodromo TEXT, carrera TEXT, caballo TEXT, cuota REAL, stake REAL, prob REAL, edge REAL, resultado TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS banca (id INTEGER PRIMARY KEY, balance REAL)''')
    c.execute("SELECT balance FROM banca WHERE id = 1")
    if c.fetchone() is None:
        c.execute("INSERT INTO banca (id, balance) VALUES (1, 1000.0)")
    conn.commit()
    return conn

conn = init_db()

# 3. INTERFAZ PRINCIPAL
st.title("🏇 OMEGA-CORE ULTIMATE")
st.markdown("### Terminal de Análisis Hípico Avanzado")
st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["🏆 Análisis de Carrera", "📄 Carga de PDFs", "🧠 Memoria & Resultados", "💰 Bankroll"])

# PESTAÑA 1: ANÁLISIS COMPLETO DE CARRERA
with tab1:
    st.markdown("#### Configuración de la Carrera")
    col1, col2, col3 = st.columns(3)
    with col1:
        hipodromo = st.text_input("Hipódromo:", value="Gulfstream Park")
    with col2:
        carrera_num = st.number_input("Carrera (R#):", min_value=1, value=1)
    with col3:
        stake = st.number_input("Stake (Bs):", min_value=10.0, value=100.0)

    st.markdown("#### Datos de los Caballos (Ingresa los participantes)")
    st.info("Llena los datos de todos los caballos. La app calculará la probabilidad de cada uno y elegirá al ganador.")
    
    # Creamos un formulario con 5 filas por defecto
    with st.form("analisis_carrera"):
        caballos_data = []
        for i in range(1, 6): # 5 caballos
            st.markdown(f"**Caballo {i}**")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                nombre = st.text_input(f"Nombre #{i}", key=f"nom_{i}")
            with c2:
                pp = st.slider(f"Prime Power #{i}", 0.0, 1.0, 0.5, key=f"pp_{i}")
            with c3:
                jockey = st.slider(f"Jockey % #{i}", 0.0, 0.40, 0.10, key=f"jck_{i}")
            with c4:
                cuota = st.number_input(f"Cuota #{i}", min_value=1.01, value=4.00, key=f"cuo_{i}")
            
            if nombre: # Solo agregar si tiene nombre
                caballos_data.append({"nombre": nombre, "pp": pp, "jockey": jockey, "cuota": cuota})
            st.markdown("---")

        boton_analizar = st.form_submit_button("🚀 EJECUTAR ANÁLISIS MASIVO")

    if boton_analizar and len(caballos_data) > 0:
        # Lógica de mercado
        total_q = sum(1 / c['cuota'] for c in caballos_data)
        
        resultados = []
        for c in caballos_data:
            p_mercado = (1 / c['cuota']) / total_q
            # Damos peso a la forma (simulada como 0.5 por ahora para simplificar)
            p_fund = (c['pp'] * 0.7) + (c['jockey'] * 0.3) 
            p_final = (0.50 * p_mercado) + (0.50 * p_fund)
            edge = (p_final * c['cuota']) - 1
            
            resultados.append({
                "Caballo": c['nombre'], "Cuota": c['cuota'], 
                "Probabilidad": f"{p_final*100:.1f}%", "Edge": f"{edge:+.2f}", "p_final": p_final, "edge_val": edge
            })
        
        # Ordenar por probabilidad (Regla Suprema)
        resultados.sort(key=lambda x: x['p_final'], reverse=True)
        df_res = pd.DataFrame(resultados)
        
        st.markdown("### 🏆 Veredicto del Sistema (Regla Suprema)")
        st.dataframe(df_res[["Caballo", "Cuota", "Probabilidad", "Edge"]], use_container_width=True)
        
        ganador = resultados[0]
        st.success(f"🎯 **EL ALGORITMO RECOMIENDA APOSTAR A: {ganador['Caballo']}** (Probabilidad: {ganador['Probabilidad']})")
        
        if ganador['edge_val'] >= 0.05:
            st.info(f"✅ **VALOR DETECTADO.** Se recomienda apostar {stake} Bs a WIN.")
            # Registrar en base de datos y descontar banca
            c = conn.cursor()
            c.execute("INSERT INTO historial (hipodromo, carrera, caballo, cuota, stake, prob, edge, resultado) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                      (hipodromo, f"R{carrera_num}", ganador['Caballo'], ganador['Cuota'], stake, ganador['p_final'], ganador['edge_val'], "Pendiente"))
            c.execute("UPDATE banca SET balance = balance - ? WHERE id = 1", (stake,))
            conn.commit()
            st.warning(f"⚠️ Apuesta registrada. Se han descontado {stake} Bs de la banca.")
        else:
            st.warning("⚠️ **NO HAY VALOR SUFICIENTE.** El favorito no paga lo que vale. La Regla Suprema dice no apostar.")

# PESTAÑA 2: CARGA MASIVA DE PDFs
with tab2:
    st.markdown("### 📄 Carga Múltiple de PDFs (Racecards)")
    st.write("Sube hasta 15 archivos PDF de Equibase, MeridianBet o cualquier otro formato.")
    
    # Acepta múltiples archivos
    archivos_pdf = st.file_uploader("Selecciona los archivos PDF", type="pdf", accept_multiple_files=True)
    
    if archivos_pdf:
        st.success(f"✅ {len(archivos_pdf)} archivos cargados.")
        for i, archivo in enumerate(archivos_pdf):
            with st.expander(f"📄 Archivo {i+1}: {archivo.name}"):
                with pdfplumber.open(archivo) as pdf:
                    texto = pdf.pages[0].extract_text()
                    st.text_area("Texto extraído (Pág 1):", texto, height=150, key=f"pdf_{i}")

# PESTAÑA 3: MEMORIA Y RESULTADOS
with tab3:
    st.markdown("### 🧠 Historial de Apuestas")
    df = pd.read_sql_query("SELECT * FROM historial", conn)
    
    if df.empty:
        st.info("No hay apuestas registradas aún.")
    else:
        st.dataframe(df, use_container_width=True)
        
        st.markdown("#### Resolver Apuestas Pendientes")
        pendientes = df[df['resultado'] == 'Pendiente']
        if not pendientes.empty:
            for index, row in pendientes.iterrows():
                col1, col2, col3 = st.columns([4, 1, 1])
                with col1:
                    st.write(f"**{row['caballo']}** ({row['hipodromo']} {row['carrera']}) | Cuota: {row['cuota']} | Stake: {row['stake']} Bs")
                with col2:
                    if st.button("✅ Ganó", key=f"w_{row['id']}"):
                        ganancia = row['stake'] * row['cuota']
                        c = conn.cursor()
                        c.execute("UPDATE historial SET resultado = 'Ganó' WHERE id = ?", (row['id'],))
                        c.execute("UPDATE banca SET balance = balance + ? WHERE id = 1", (ganancia,))
                        conn.commit()
                        st.rerun()
                with col3:
                    if st.button("❌ Perdió", key=f"l_{row['id']}"):
                        c = conn.cursor()
                        c.execute("UPDATE historial SET resultado = 'Perdió' WHERE id = ?", (row['id'],))
                        conn.commit()
                        st.rerun()

# PESTAÑA 4: BANKROLL
with tab4:
    st.markdown("### 💰 Gestión de Banca")
    c = conn.cursor()
    c.execute("SELECT balance FROM banca WHERE id = 1")
    balance_actual = c.fetchone()[0]
    
    st.metric(label="Balance Actual", value=f"{balance_actual:.2f} Bs")
    
    st.markdown("---")
    st.write("Ajuste Manual (Depósitos o Retiros):")
    nuevo_saldo = st.number_input("Establecer saldo:", min_value=0.0, value=float(balance_actual))
    if st.button("Actualizar Banca"):
        c.execute("UPDATE banca SET balance = ? WHERE id = 1", (nuevo_saldo,))
        conn.commit()
        st.success("Banca actualizada manualmente.")
        st.rerun()
