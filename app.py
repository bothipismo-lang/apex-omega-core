import streamlit as st
import pdfplumber
import pandas as pd
import sqlite3
import re
import os
import io

st.set_page_config(page_title="ÍA HÍPICA", page_icon="🏇", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #00E5FF; color: black; font-weight: bold; }
    h1, h2, h3 { color: #00E5FF; }
    </style>
""", unsafe_allow_html=True)

st.title("🏇 ÍA HÍPICA · APEX-OMEGA ×50")

# --- ARCHIVOS FÍSICOS (Para persistencia total) ---
ARCHIVO_CACHE = "cache_jornada.csv"
DB_NAME = "ia_hipica.db"

# 1. BASE DE DATOS
def init_db():
    conn = sqlite3.connect(DB_NAME)
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

# 2. CARGAR DATOS DESDE EL ARCHIVO FÍSICO (Si existen)
if 'pdf_data' not in st.session_state:
    if os.path.exists(ARCHIVO_CACHE):
        st.session_state.pdf_data = pd.read_csv(ARCHIVO_CACHE)
    else:
        st.session_state.pdf_data = pd.DataFrame()

if 'hipodromo_actual' not in st.session_state:
    st.session_state.hipodromo_actual = "Gulfstream Park"

tab1, tab2, tab3, tab4 = st.tabs(["📄 1. Cargar Jornada", "🏆 2. Calcular Carrera", "📸 3. Registrar Llegada", "💰 4. Banca"])

# PESTAÑA 1: CARGA Y PROCESAMIENTO
with tab1:
    st.markdown("### 1. Sube los PDFs de la Jornada")
    archivos_pdf = st.file_uploader("Selecciona los PDFs", type="pdf", accept_multiple_files=True)
    
    if archivos_pdf:
        if st.button("🧠 PROCESAR Y GUARDAR EN DISCO", use_container_width=True):
            with st.spinner("Separando carreras y guardando en disco..."):
                texto_completo = ""
                for archivo in archivos_pdf:
                    with pdfplumber.open(io.BytesIO(archivo.getvalue())) as pdf:
                        for pagina in pdf.pages:
                            texto_completo += pagina.extract_text() + "\n"
                
                lineas = texto_completo.split('\n')
                caballos_detectados = []
                carrera_actual = "1"
                
                for i, linea in enumerate(lineas):
                    # BUSCAMOS EL TÍTULO DE LA CARRERA (Ej: "Race 1", "Race 2")
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
                    # GUARDAMOS EN EL DISCO DURO (CSV)
                    df_extraido.to_csv(ARCHIVO_CACHE, index=False)
                    st.session_state.pdf_data = df_extraido
                    st.success(f"✅ ¡PDFs procesados y guardados en disco! Carreras: {', '.join(df_extraido['Carrera'].unique())}")
                    st.rerun()

    st.markdown("---")
    st.markdown("### 🚨 Control de Jornada")
    if st.button("🔴 CERRAR JORNADA (Borrar PDFs del Disco)", use_container_width=True):
        if os.path.exists(ARCHIVO_CACHE):
            os.remove(ARCHIVO_CACHE) # Borra el archivo físico
        st.session_state.pdf_data = pd.DataFrame()
        st.success("✅ Jornada cerrada. Memoria limpia.")
        st.rerun()

# PESTAÑA 2: CÁLCULO
with tab2:
    if st.session_state.pdf_data.empty:
        st.warning("⚠️ Primero debes cargar los PDFs en la Pestaña 1.")
    else:
        st.markdown("### Selecciona la carrera")
        carreras = st.session_state.pdf_data['Carrera'].unique()
        carrera_sel = st.selectbox("Número de Carrera:", carreras)
        
        if st.button("🚀 CALCULAR CARRERA", use_container_width=True):
            df_carrera = st.session_state.pdf_data[st.session_state.pdf_data['Carrera'] == carrera_sel].copy()
            
            st.markdown(f"#### 🏇 Carrera {carrera_sel}")
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

# PESTAÑA 3: REGISTRO DE LLEGADA
with tab3:
    st.markdown("### 📸 Registrar Llegada")
    df_pend = pd.read_sql_query("SELECT DISTINCT carrera FROM historial_completo WHERE posicion_final = 'Pendiente'", conn)
    if df_pend.empty:
        st.success("No hay carreras pendientes.")
    else:
        carrera_reg = st.selectbox("Carrera a registrar:", df_pend['carrera'].tolist())
        
        st.markdown("#### Pega el resultado (Copia el texto de la app o escríbelo)")
        texto_resultado = st.text_area("Ejemplo: 1° Sherman Fury, 2° Our Perfect Amanda", height=100)
        
        if st.button("💾 GUARDAR Y ACTUALIZAR BANCA"):
            if not texto_resultado:
                st.error("Ingresa el resultado.")
            else:
                c = conn.cursor()
                df_cabs = pd.read_sql_query(f"SELECT id, caballo FROM historial_completo WHERE carrera = '{carrera_reg}'", conn)
                
                # Parsear el texto
                for _, row in df_cabs.iterrows():
                    nombre_db = row['caballo']
                    if nombre_db in texto_resultado:
                        match_pos = re.search(r'(\d+)[°|º]?\s*' + re.escape(nombre_db), texto_resultado, re.IGNORECASE)
                        if match_pos:
                            pos = match_pos.group(1)
                        elif f"1 {nombre_db}" in texto_resultado:
                            pos = "1"
                        elif f"2 {nombre_db}" in texto_resultado:
                            pos = "2"
                        elif f"3 {nombre_db}" in texto_resultado:
                            pos = "3"
                        else:
                            pos = "Corrió"
                        c.execute("UPDATE historial_completo SET posicion_final = ? WHERE id = ?", (pos, row['id']))
                
                # Verificar si ganó la apuesta
                df_ap = pd.read_sql_query(f"SELECT * FROM historial_completo WHERE carrera = '{carrera_reg}' AND es_apuesta = 1", conn)
                if not df_ap.empty:
                    apuesta = df_ap.iloc[0]
                    if apuesta['posicion_final'] == '1' or f"1 {apuesta['caballo']}" in texto_resultado:
                        ganancia = 50.0 * apuesta['cuota']
                        c.execute("UPDATE banca SET balance = balance + ? WHERE id = 1", (ganancia,))
                        st.success(f"🎉 ¡{apuesta['caballo']} GANÓ! +{ganancia:.2f} Bs.")
                    else:
                        st.error(f"❌ {apuesta['caballo']} no ganó.")
                conn.commit()
                st.success("✅ Base de datos histórica actualizada.")
                st.rerun()

# PESTAÑA 4: BANCA
with tab4:
    st.markdown("### 💰 Banca")
    c = conn.cursor()
    c.execute("SELECT balance FROM banca WHERE id = 1")
    bal = c.fetchone()[0]
    st.metric("Banca Actual", f"{bal:.2f} Bs")
    
    nuevo = st.number_input("Editar saldo manual:", min_value=0.0, value=float(bal), step=100.0)
    if st.button("💾 ACTUALIZAR BANCA"):
        c.execute("UPDATE banca SET balance = ? WHERE id = 1", (nuevo,))
        conn.commit()
        st.success("Banca actualizada.")
        st.rerun()

    st.markdown("### 📊 Historial Histórico")
    df_h = pd.read_sql_query("SELECT * FROM historial_completo ORDER BY id DESC LIMIT 50", conn)
    st.dataframe(df_h, use_container_width=True)
