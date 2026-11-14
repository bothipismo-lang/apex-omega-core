import streamlit as st
import pdfplumber
import pandas as pd
import sqlite3
import re
import os
import shutil

st.set_page_config(page_title="ÍA HÍPICA", page_icon="🏇", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #00E5FF; color: black; font-weight: bold; }
    h1, h2, h3 { color: #00E5FF; }
    </style>
""", unsafe_allow_html=True)

st.title("🏇 ÍA HÍPICA · APEX-OMEGA ×50")

# 1. BASE DE DATOS
def init_db():
    conn = sqlite3.connect('ia_hipica.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS historial_completo 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, hipodromo TEXT, carrera TEXT, fecha TEXT, 
                 caballo TEXT, pp REAL, cuota REAL, prob REAL, edge REAL, es_apuesta BOOLEAN, posicion_final TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS banca (id INTEGER PRIMARY KEY, balance REAL)''')
    c.execute("SELECT balance FROM banca WHERE id = 1")
    if c.fetchone() is None:
        c.execute("INSERT INTO banca (id, balance) VALUES (1, 1000.0)")
    conn.commit()
    return conn

conn = init_db()

# 2. MEMORIA TEMPORAL SEGURA
if 'pdf_data' not in st.session_state:
    st.session_state.pdf_data = pd.DataFrame()
if 'hipodromo_actual' not in st.session_state:
    st.session_state.hipodromo_actual = "Gulfstream Park"

# 3. CREACIÓN DE PESTAÑAS
tab1, tab2, tab3, tab4 = st.tabs(["📄 1. Cargar Jornada", "🏆 2. Calcular Carrera", "📸 3. Registrar Llegada", "💰 4. Banca"])

# PESTAÑA 1
with tab1:
    st.markdown("### 1. Sube los PDFs de la Jornada")
    archivos_pdf = st.file_uploader("Selecciona los PDFs", type="pdf", accept_multiple_files=True)
    
    if archivos_pdf:
        if st.button("🧠 PROCESAR Y GUARDAR EN MEMORIA", use_container_width=True):
            with st.spinner("La ÍA HÍPICA está leyendo los PDFs..."):
                texto_completo = ""
                for archivo in archivos_pdf:
                    with pdfplumber.open(archivo) as pdf:
                        for pagina in pdf.pages:
                            texto_completo += pagina.extract_text() + "\n"
                
                lineas = texto_completo.split('\n')
                caballos_detectados = []
                carrera_actual = "1"
                
                for i, linea in enumerate(lineas):
                    match_race = re.search(r'Race\s*(\d+)', linea, re.IGNORECASE)
                    if match_race:
                        carrera_actual = match_race.group(1)
                    
                    match_caballo = re.match(r'^(\d+)\s+([A-Z][a-zA-Z\s\'\-]+)', linea)
                    if match_caballo:
                        nombre_caballo = match_caballo.group(2).strip()
                        pp_encontrado = 0.0
                        for j in range(i, min(i+15, len(lineas))):
                            if "Prime Power:" in lineas[j]:
                                match_pp = re.search(r'Prime Power:\s*([\d\.]+)', lineas[j])
                                if match_pp:
                                    pp_encontrado = float(match_pp.group(1)) / 100.0 
                                    break
                        
                        cuota_encontrada = 4.0 
                        match_cuota = re.search(r'(\d+/\d+)', linea)
                        if match_cuota:
                            frac = match_cuota.group(1)
                            num, den = frac.split('/')
                            cuota_encontrada = (float(num) / float(den)) + 1.0
                        
                        if nombre_caballo and pp_encontrado > 0:
                            if not any(c['Nombre'] == nombre_caballo and c['Carrera'] == carrera_actual for c in caballos_detectados):
                                caballos_detectados.append({
                                    "Carrera": carrera_actual, "Nombre": nombre_caballo, "PP": pp_encontrado, "Cuota": cuota_encontrada
                                })
                
                df_extraido = pd.DataFrame(caballos_detectados)
                if df_extraido.empty:
                    st.error("No se encontraron datos.")
                else:
                    st.session_state.pdf_data = df_extraido
                    st.success(f"✅ ¡Memoria Cargada! Carreras listas: {df_extraido['Carrera'].nunique()}")
                    st.rerun()

    st.markdown("---")
    st.markdown("### 🚨 Control de Jornada")
    if st.button("🔴 CERRAR JORNADA (Borrar Memoria)", use_container_width=True):
        st.session_state.pdf_data = pd.DataFrame()
        st.success("✅ Jornada cerrada. Memoria temporal borrada.")
        st.rerun()

# PESTAÑA 2
with tab2:
    if st.session_state.pdf_data.empty:
        st.warning("⚠️ Primero debes cargar los PDFs en la Pestaña 1.")
    else:
        st.markdown("### Selecciona la carrera a analizar")
        carreras = st.session_state.pdf_data['Carrera'].unique()
        carrera_sel = st.selectbox("Número de Carrera:", carreras)
        
        if st.button("🚀 CALCULAR CARRERA", use_container_width=True):
            df_carrera = st.session_state.pdf_data[st.session_state.pdf_data['Carrera'] == carrera_sel].copy()
            st.dataframe(df_carrera[["Nombre", "PP", "Cuota"]], use_container_width=True)
            
            total_q = sum(1 / c['Cuota'] for _, c in df_carrera.iterrows())
            resultados = []
            for _, c in df_carrera.iterrows():
                p_mercado = (1 / c['Cuota']) / total_q
                p_final = (0.50 * p_mercado) + (0.50 * c['PP'])
                edge = (p_final * c['Cuota']) - 1
                resultados.append({"Caballo": c['Nombre'], "PP": c['PP'], "Cuota": c['Cuota'], "Prob": f"{p_final*100:.1f}%", "Edge": f"{edge:+.2f}", "p_final": p_final, "edge_val": edge})
            
            resultados.sort(key=lambda x: x['p_final'], reverse=True)
            df_res = pd.DataFrame(resultados)
            st.markdown("### 🏆 VEREDICTO")
            st.dataframe(df_res[["Caballo", "PP", "Cuota", "Prob", "Edge"]], use_container_width=True)
            
            ganador = resultados[0]
            st.success(f"🎯 GANADOR: {ganador['Caballo']} ({ganador['Prob']})")
            
            c = conn.cursor()
            for r in resultados:
                es_apuesta = 1 if r['Caballo'] == ganador['Caballo'] and ganador['edge_val'] >= 0.05 else 0
                c.execute('''INSERT INTO historial_completo (hipodromo, carrera, fecha, caballo, pp, cuota, prob, edge, es_apuesta, posicion_final) 
                             VALUES (?, ?, date('now'), ?, ?, ?, ?, ?, ?, ?)''', 
                          (st.session_state.hipodromo_actual, carrera_sel, r['Caballo'], r['PP'], r['Cuota'], r['p_final'], r['edge_val'], es_apuesta, "Pendiente"))
            
            if ganador['edge_val'] >= 0.05:
                st.warning(f"⚠️ Apuesta registrada a {ganador['Caballo']}.")
                c.execute("UPDATE banca SET balance = balance - 50.0 WHERE id = 1")
            conn.commit()

# PESTAÑA 3
with tab3:
    st.markdown("### 📸 Registrar Llegada")
    df_pend = pd.read_sql_query("SELECT DISTINCT carrera FROM historial_completo WHERE posicion_final = 'Pendiente'", conn)
    if df_pend.empty:
        st.success("No hay carreras pendientes.")
    else:
        carrera_reg = st.selectbox("Carrera a registrar:", df_pend['carrera'].tolist())
        df_cabs = pd.read_sql_query(f"SELECT id, caballo, es_apuesta FROM historial_completo WHERE carrera = '{carrera_reg}' AND posicion_final = 'Pendiente'", conn)
        
        with st.form("form_pos"):
            posiciones = {}
            for _, row in df_cabs.iterrows():
                label = f"⭐ {row['caballo']}" if row['es_apuesta'] == 1 else row['caballo']
                posiciones[row['id']] = st.text_input(f"Posición de {label}:", key=f"pos_{row['id']}")
            
            if st.form_submit_button("💾 GUARDAR RESULTADOS"):
                c = conn.cursor()
                for cab_id, pos in posiciones.items():
                    c.execute("UPDATE historial_completo SET posicion_final = ? WHERE id = ?", (pos, cab_id))
                
                df_ap = pd.read_sql_query(f"SELECT * FROM historial_completo WHERE carrera = '{carrera_reg}' AND es_apuesta = 1", conn)
                if not df_ap.empty and df_ap.iloc[0]['posicion_final'] == '1':
                    ganancia = 50.0 * df_ap.iloc[0]['cuota']
                    c.execute("UPDATE banca SET balance = balance + ? WHERE id = 1", (ganancia,))
                    st.success(f"🎉 ¡{df_ap.iloc[0]['caballo']} GANÓ! +{ganancia:.2f} Bs")
                conn.commit()
                st.rerun()

# PESTAÑA 4
with tab4:
    st.markdown("### 💰 Banca")
    c = conn.cursor()
    c.execute("SELECT balance FROM banca WHERE id = 1")
    bal = c.fetchone()[0]
    st.metric("Banca Actual", f"{bal:.2f} Bs")
    
    nuevo = st.number_input("Editar saldo:", min_value=0.0, value=float(bal))
    if st.button("💾 ACTUALIZAR"):
        c.execute("UPDATE banca SET balance = ? WHERE id = 1", (nuevo,))
        conn.commit()
        st.rerun()

    st.markdown("### 📊 Historial")
    df_h = pd.read_sql_query("SELECT * FROM historial_completo LIMIT 50", conn)
    st.dataframe(df_h, use_container_width=True)
