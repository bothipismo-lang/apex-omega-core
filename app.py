import streamlit as st
import pdfplumber
import pandas as pd
import sqlite3
import re
import os
import io

st.set_page_config(page_title="ÍA HÍPICA · APEX-OMEGA", page_icon="🏇", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #00E5FF; color: black; font-weight: bold; border: none; }
    .stButton>button:hover { background-color: #00b3cc; color: white; }
    h1, h2, h3 { color: #00E5FF; }
    </style>
""", unsafe_allow_html=True)

st.title("🏇 ÍA HÍPICA · APEX-OMEGA ×50 (Dixie Edition)")

DB_NAME = "ia_hipica.db"
ARCHIVO_CACHE = "cache_jornada.csv"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS historial_completo 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, hipodromo TEXT, carrera TEXT, fecha TEXT, 
                     caballo TEXT, pp REAL, cuota REAL, prob REAL, edge REAL, es_apuesta BOOLEAN, posicion_final TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS banca (id INTEGER PRIMARY KEY, balance REAL)''')
        c.execute("SELECT balance FROM banca WHERE id = 1")
        if c.fetchone() is None:
            c.execute("INSERT INTO banca (id, balance) VALUES (1, 1000.0)")
        conn.commit()

init_db()

# --- CARGAR DESDE EL DISCO DURO (PERSISTENTE AL REFRESCAR) ---
if 'df_jornada' not in st.session_state:
    if os.path.exists(ARCHIVO_CACHE):
        st.session_state.df_jornada = pd.read_csv(ARCHIVO_CACHE)
        # Asegurar que Carrera sea texto para evitar problemas de formato
        st.session_state.df_jornada['Carrera'] = st.session_state.df_jornada['Carrera'].astype(str)
    else:
        st.session_state.df_jornada = pd.DataFrame()

if 'hipodromo_actual' not in st.session_state:
    st.session_state.hipodromo_actual = "Horseshoe Indianapolis"

tab1, tab2, tab3, tab4 = st.tabs(["📄 1. Cargar Jornada", "🏆 2. Calcular Carrera", "📸 3. Registrar Llegada", "💰 4. Banca y Estadísticas"])

# --- PESTAÑA 1: CARGA Y PROCESAMIENTO ---
with tab1:
    st.markdown("### 1. Sube los PDFs de la Jornada")
    archivos_pdf = st.file_uploader("Selecciona los PDFs de la cartelera", type="pdf", accept_multiple_files=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if archivos_pdf:
            if st.button("🧠 PROCESAR Y GUARDAR EN DISCO", use_container_width=True):
                with st.spinner("Analizando PDFs y guardando en disco..."):
                    texto_completo = ""
                    for archivo in archivos_pdf:
                        with pdfplumber.open(io.BytesIO(archivo.getvalue())) as pdf:
                            for pagina in pdf.pages:
                                texto_extraido = pagina.extract_text()
                                if texto_extraido:
                                    texto_completo += texto_extraido + "\n"
                    
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
                                if float(den) > 0:
                                    cuota_encontrada = (float(num) / float(den)) + 1.0
                            
                            if nombre_caballo and pp_encontrado > 0:
                                if not any(c['Nombre'] == nombre_caballo and c['Carrera'] == str(carrera_actual) for c in caballos_detectados):
                                    caballos_detectados.append({
                                        "Carrera": str(carrera_actual), "Nombre": nombre_caballo, "PP": pp_encontrado, "Cuota": cuota_encontrada
                                    })
                    
                    df_extraido = pd.DataFrame(caballos_detectados)
                    if df_extraido.empty:
                        st.error("No se pudieron extraer datos válidos de los PDFs.")
                    else:
                        # GUARDAR EN DISCO DURO (CSV) PARA QUE SOBREVIVA AL F5 / REFRESCO
                        df_extraido.to_csv(ARCHIVO_CACHE, index=False)
                        st.session_state.df_jornada = df_extraido
                        st.success(f"✅ ¡Jornada guardada en disco! Carreras listas: {', '.join(df_extraido['Carrera'].unique())}")
                        st.rerun()

    with col2:
        st.markdown("### 🚨 Control de Jornada")
        if not st.session_state.df_jornada.empty:
            st.success("🟢 Datos en disco detectados y activos.")
        else:
            st.warning("⚠️ No hay datos guardados.")
            
        if st.button("🔴 CERRAR Y BORRAR DATOS DE DISCO", use_container_width=True):
            if os.path.exists(ARCHIVO_CACHE):
                os.remove(ARCHIVO_CACHE)
            st.session_state.df_jornada = pd.DataFrame()
            st.success("✅ Archivos temporales borrados del disco.")
            st.rerun()

# --- PESTAÑA 2: CÁLCULO ---
with tab2:
    if st.session_state.df_jornada.empty:
        st.warning("⚠️ Primero sube y procesa los PDFs en la Pestaña 1.")
    else:
        st.markdown("### 🏆 Motor de Cálculo y Valor (*Edge*)")
        carreras = sorted(st.session_state.df_jornada['Carrera'].unique(), key=lambda x: int(x) if x.isdigit() else x)
        carrera_sel = st.selectbox("Seleccione el Número de Carrera:", carreras)
        
        df_carrera = st.session_state.df_jornada[st.session_state.df_jornada['Carrera'] == carrera_sel].copy()
        
        st.markdown(f"#### 🏇 Inscritos - Carrera {carrera_sel}")
        st.dataframe(df_carrera[["Nombre", "PP", "Cuota"]], use_container_width=True, hide_index=True)
        
        if st.button("🚀 CALCULAR PRONÓSTICO DE ESTA CARRERA", use_container_width=True):
            total_q = sum(1 / c['Cuota'] for _, c in df_carrera.iterrows() if c['Cuota'] > 0)
            resultados = []
            for _, c in df_carrera.iterrows():
                p_mercado = (1 / c['Cuota']) / total_q if total_q > 0 else 0
                p_final = (0.50 * p_mercado) + (0.50 * c['PP'])
                edge = (p_final * c['Cuota']) - 1
                resultados.append({
                    "Caballo": c['Nombre'], "PP": c['PP'], "Cuota": c['Cuota'], 
                    "Prob": f"{p_final*100:.1f}%", "Edge": f"{edge:+.2f}", 
                    "p_final": p_final, "edge_val": edge
                })
            
            resultados.sort(key=lambda x: x['p_final'], reverse=True)
            df_res = pd.DataFrame(resultados)
            
            st.markdown("### 🎯 VEREDICTO APEX-OMEGA")
            st.dataframe(df_res[["Caballo", "PP", "Cuota", "Prob", "Edge"]], use_container_width=True, hide_index=True)
            
            ganador = resultados[0]
            st.success(f"🥇 SELECCIÓN PRINCIPAL: **{ganador['Caballo']}** (Probabilidad: {ganador['Prob']}, Edge: {ganador['Edge']})")

# --- PESTAÑA 3: REGISTRO DE LLEGADA ---
with tab3:
    st.markdown("### 📸 Registrar Llegada de la Carrera")
    if st.session_state.df_jornada.empty:
        st.warning("⚠️ Primero carga los datos en la Pestaña 1.")
    else:
        carreras_reg = sorted(st.session_state.df_jornada['Carrera'].unique(), key=lambda x: int(x) if x.isdigit() else x)
        carrera_reg = st.selectbox("Seleccione la Carrera a registrar:", carreras_reg, key="reg_carrera")
        
        texto_resultado = st.text_area("Pega el orden de llegada (Ej: 1° Takeitandrun, 2° Kingsbury Road)", height=100)
        
        if st.button("💾 GUARDAR RESULTADOS", use_container_width=True):
            if not texto_resultado:
                st.error("Por favor ingresa el texto de los resultados.")
            else:
                with get_db_connection() as conn:
                    c = conn.cursor()
                    df_cabs = st.session_state.df_jornada[st.session_state.df_jornada['Carrera'] == carrera_reg]
                    
                    for _, row in df_cabs.iterrows():
                        nombre_db = row['Nombre']
                        pos = "Unplaced"
                        
                        patron_exacto = re.search(r'(\d+)[°|º]?\s*' + re.escape(nombre_db), texto_resultado, re.IGNORECASE)
                        if patron_exacto:
                            pos = patron_exacto.group(1)
                        else:
                            for p_num in ["1", "2", "3", "4", "5"]:
                                if f"{p_num}° {nombre_db}" in texto_resultado or f"{p_num} {nombre_db}" in texto_resultado:
                                    pos = p_num
                                    break
                        
                        c.execute('''INSERT INTO historial_completo (hipodromo, carrera, fecha, caballo, pp, cuota, prob, edge, es_apuesta, posicion_final) 
                                     VALUES (?, ?, date('now'), ?, 0, 0, 0, 0, 0, ?)''', 
                                  (st.session_state.hipodromo_actual, carrera_reg, nombre_db, pos))
                    conn.commit()
                    st.success("✅ ¡Resultados registrados correctamente en la base de datos!")

# --- PESTAÑA 4: BANCA Y ESTADÍSTICAS ---
with tab4:
    st.markdown("### 💰 Gestión de Banca")
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT balance FROM banca WHERE id = 1")
        bal = c.fetchone()[0]
        st.metric("Saldo Actual en Banca", f"{bal:.2f} Bs")
        
        nuevo = st.number_input("Ajustar saldo manual de la banca:", min_value=0.0, value=float(bal), step=100.0)
        if st.button("💾 ACTUALIZAR SALDO MANUAL"):
            c.execute("UPDATE banca SET balance = ? WHERE id = 1", (nuevo,))
            conn.commit()
            st.success("Banca actualizada.")
            st.rerun()

        st.markdown("---")
        st.markdown("### 📊 Historial de Registros")
        df_h = pd.read_sql_query("SELECT * FROM historial_completo ORDER BY id DESC LIMIT 50", conn)
        st.dataframe(df_h, use_container_width=True, hide_index=True)
