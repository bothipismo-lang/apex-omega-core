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

# --- BASE DE DATOS (El Corazón Estadístico) ---
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

# --- SISTEMA DE GUARDADO EN DISCO (Para que no se borre al refrescar) ---
CARPETA_PDFS = "pdfs_temporales"

# Crear la carpeta si no existe
if not os.path.exists(CARPETA_PDFS):
    os.makedirs(CARPETA_PDFS)

# Si la memoria temporal está vacía, buscamos si hay PDFs guardados en el disco
if 'pdf_data' not in st.session_state or st.session_state.pdf_data.empty:
    archivos_en_disco = [f for f in os.listdir(CARPETA_PDFS) if f.endswith('.pdf')]
    if archivos_en_disco:
        # Si hay archivos en el disco, los volvemos a procesar automáticamente
        texto_completo = ""
        for archivo_nombre in archivos_en_disco:
            ruta = os.path.join(CARPETA_PDFS, archivo_nombre)
            with pdfplumber.open(ruta) as pdf:
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
        
        st.session_state.pdf_data = pd.DataFrame(caballos_detectados)

if 'hipodromo_actual' not in st.session_state:
    st.session_state.hipodromo_actual = "Gulfstream Park"

tab1, tab2, tab3, tab4 = st.tabs(["📄 1. Cargar Jornada", "🏆 2. Calcular Carrera", "📸 3. Registrar Llegada", "💰 4. Banca"])

# PESTAÑA 1: CARGA MASIVA Y CONTROL DE JORNADA
with tab1:
    st.markdown("### 1. Sube los PDFs de la Jornada")
    
    # Mostrar si ya hay archivos guardados en el disco
    archivos_guardados = os.listdir(CARPETA_PDFS)
    if archivos_guardados:
        st.info(f"📂 **Memoria Persistente Activa:** Hay {len(archivos_guardados)} PDF(s) guardados en la App. No se borrarán al refrescar.")
    
    archivos_pdf = st.file_uploader("Selecciona los PDFs para agregar", type="pdf", accept_multiple_files=True)
    
    if archivos_pdf:
        if st.button("🧠 PROCESAR Y GUARDAR EN DISCO", use_container_width=True):
            with st.spinner("Guardando PDFs y procesando datos..."):
                # 1. Guardar los archivos físicamente en la carpeta
                for archivo in archivos_pdf:
                    ruta_guardado = os.path.join(CARPETA_PDFS, archivo.name)
                    with open(ruta_guardado, "wb") as f:
                        f.write(archivo.getbuffer())
                
                # 2. Leer todos los PDFs de la carpeta (los nuevos y los viejos)
                texto_completo = ""
                for archivo_nombre in os.listdir(CARPETA_PDFS):
                    ruta = os.path.join(CARPETA_PDFS, archivo_nombre)
                    with pdfplumber.open(ruta) as pdf:
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
                    st.error("No se encontraron datos en los PDFs.")
                else:
                    st.session_state.pdf_data = df_extraido
                    st.success(f"✅ ¡PDFs guardados en Disco! Carreras listas: {df_extraido['Carrera'].nunique()}")

    st.markdown("---")
    st.markdown("### 🚨 Control de Jornada")
    if st.button("🔴 CERRAR JORNADA (Borrar PDFs del Disco)", use_container_width=True):
        # Borrar la carpeta y su contenido
        if os.path.exists(CARPETA_PDFS):
            shutil.rmtree(CARPETA_PDFS)
            os.makedirs(CARPETA_PDFS)
        
        st.session_state.pdf_data = pd.DataFrame() # Borra la memoria temporal
        st.success("✅ Jornada cerrada. Los PDFs han sido eliminados del disco.")
        st.rerun()

# PESTAÑA 2: CÁLCULO POR CARRERA
with tab2:
    if 'pdf_data' not in st.session_state or st.session_state.pdf_data.empty:
        st.warning("⚠️ Primero debes cargar los PDFs en la Pestaña 1.")
    else:
        st.markdown("### Selecciona la carrera a analizar")
        carreras_disponibles = st.session_state.pdf_data['Carrera'].unique()
        carrera_seleccionada = st.selectbox("Número de Carrera:", carreras_disponibles)
        
        if st.button("🚀 CALCULAR CARRERA", use_container_width=True):
            df_carrera = st.session_state.pdf_data[st.session_state.pdf_data['Carrera'] == carrera_seleccionada].copy()
            
            st.markdown(f"#### 🏇 Carrera {carrera_seleccionada} - Caballos Participantes")
            st.dataframe(df_carrera[["Nombre", "PP", "Cuota"]], use_container_width=True)
            
            total_q = sum(1 / c['Cuota'] for _, c in df_carrera.iterrows())
            resultados = []
            for _, c in df_carrera.iterrows():
                p_mercado = (1 / c['Cuota']) / total_q
                p_fund = c['PP'] 
                p_final = (0.50 * p_mercado) + (0.50 * p_fund)
                edge = (p_final * c['Cuota']) - 1
                
                resultados.append({
                    "Caballo": c['Nombre'], "PP": c['PP'], "Cuota": c['Cuota'], 
                    "Probabilidad": f"{p_final*100:.1f}%", "Edge": f"{edge:+.2f}", 
                    "p_final": p_final, "edge_val": edge
                })
            
            resultados.sort(key=lambda x: x['p_final'], reverse=True)
            df_res = pd.DataFrame(resultados)
            
            st.markdown("### 🏆 VEREDICTO (Regla Suprema)")
            st.dataframe(df_res[["Caballo", "PP", "Cuota", "Probabilidad", "Edge"]], use_container_width=True)
            
            ganador = resultados[0]
            st.success(f"🎯 **GANADOR MATEMÁTICO: {ganador['Caballo']}** (Prob: {ganador['Probabilidad']})")
            
            c = conn.cursor()
            for r in resultados:
                es_apuesta = 1 if r['Caballo'] == ganador['Caballo'] and ganador['edge_val'] >= 0.05 else 0
                c.execute('''INSERT INTO historial_completo 
                             (hipodromo, carrera, fecha, caballo, pp, cuota, prob, edge, es_apuesta, posicion_final) 
                             VALUES (?, ?, date('now'), ?, ?, ?, ?, ?, ?, ?)''', 
                          (st.session_state.hipodromo_actual, carrera_seleccionada, r['Caballo'], r['PP'], r['Cuota'], r['p_final'], r['edge_val'], es_apuesta, "Pendiente"))
            
            if ganador['edge_val'] >= 0.05:
                st.warning(f"⚠️ Apuesta registrada. Se apostaron 50 Bs a {ganador['Caballo']}.")
                c.execute("UPDATE banca SET balance = balance - 50.0 WHERE id = 1")
            else:
                st.info("No se realizó apuesta (sin valor), pero se guardaron los datos de la carrera.")
            
            conn.commit()

# PESTAÑA 3: REGISTRO DE LLEGADA (Base de Datos)
with tab3:
    st.markdown("### 📸 Registrar Llegada")
    df_pendientes_carreras = pd.read_sql_query("SELECT DISTINCT carrera FROM historial_completo WHERE posicion_final = 'Pendiente'", conn)
    
    if df_pendientes_carreras.empty:
        st.success("No hay carreras pendientes por registrar.")
    else:
        carrera_reg = st.selectbox("Carrera a registrar:", df_pendientes_carreras['carrera'].tolist())
        
        st.markdown(f"#### Posiciones Finales - Carrera {carrera_reg}")
        df_caballos_carrera = pd.read_sql_query(f"SELECT id, caballo, es_apuesta FROM historial_completo WHERE carrera = '{carrera_reg}' AND posicion_final = 'Pendiente'", conn)
        
        with st.form("registro_posiciones"):
            posiciones = {}
            for index, row in df_caballos_carrera.iterrows():
                label = f"⭐ {row['caballo']}" if row['es_apuesta'] == 1 else row['caballo']
                pos = st.text_input(f"Posición de {label} (Ej: 1, 2, 3, N/D):", key=f"pos_{row['id']}")
                posiciones[row['id']] = pos
            
            submit = st.form_submit_button("💾 GUARDAR RESULTADOS Y ACTUALIZAR BANCA")
            
            if submit:
                c = conn.cursor()
                for cab_id, pos in posiciones.items():
                    c.execute("UPDATE historial_completo SET posicion_final = ? WHERE id = ?", (pos, cab_id))
                
                df_apuesta = pd.read_sql_query(f"SELECT * FROM historial_completo WHERE carrera = '{carrera_reg}' AND es_apuesta = 1", conn)
                if not df_apuesta.empty:
                    apuesta = df_apuesta.iloc[0]
                    if apuesta['posicion_final'] == '1':
                        ganancia = 50.0 * apuesta['cuota']
                        c.execute("UPDATE banca SET balance = balance + ? WHERE id = 1", (ganancia,))
                        st.success(f"🎉 ¡{apuesta['caballo']} GANÓ! Se sumaron {ganancia:.2f} Bs a la banca.")
                    else:
                        st.error(f"❌ {apuesta['caballo']} no ganó. La banca se mantiene igual.")
                conn.commit()
                st.rerun()

# PESTAÑA 4: BANCA
with tab4:
    st.markdown("### 💰 Gestión de Banca")
    c = conn.cursor()
    c.execute("SELECT balance FROM banca WHERE id = 1")
    balance_actual = c.fetchone()[0]
    
    st.metric(label="Banca Actual", value=f"{balance_actual:.2f} Bs")
    
    nuevo_saldo = st.number_input("Editar saldo manual (Bs):", min_value=0.0, value=float(balance_actual), step=100.0)
    if st.button("💾 ACTUALIZAR BANCA"):
        c.execute("UPDATE banca SET balance = ? WHERE id = 1", (nuevo_saldo,))
        conn.commit()
        st.success("Banca actualizada.")
        st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Base de Datos Histórica")
    df_hist_total = pd.read_sql_query("SELECT COUNT(*) as total FROM historial_completo WHERE posicion_final != 'Pendiente'", conn)
    st.info(f"La IA ya tiene registros de **{df_hist_total['total'].iloc[0]}** caballos en su memoria a largo plazo.")
    
    df_muestra = pd.read_sql_query("SELECT carrera, caballo, pp, cuota, posicion_final FROM historial_completo LIMIT 50", conn)
    st.dataframe(df_muestra, use_container_width=True)
