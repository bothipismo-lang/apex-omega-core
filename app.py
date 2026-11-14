import streamlit as st
import pdfplumber
import pandas as pd
import sqlite3
import re

st.set_page_config(page_title="ÍA HÍPICA", page_icon="🏇", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #00E5FF; color: black; font-weight: bold; }
    h1, h2, h3 { color: #00E5FF; }
    </style>
""", unsafe_allow_html=True)

st.title("🏇 ÍA HÍPICA · APEX-OMEGA ×50")
st.markdown("La Inteligencia Artificial que aprende de los caballos.")

# BASE DE DATOS
def init_db():
    conn = sqlite3.connect('ia_hipica.db')
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

tab1, tab2, tab3, tab4 = st.tabs(["🧠 Análisis Automático", "📄 Leer PDF", "🧠 Memoria", "💰 Banca"])

# PESTAÑA 1: ANÁLISIS AUTOMÁTICO DESDE PDF
with tab1:
    st.markdown("### 1. Sube el PDF de Brisnet (Equibase)")
    archivo_pdf = st.file_uploader("Sube el archivo PDF", type="pdf")
    
    if archivo_pdf:
        st.markdown("### 2. Selecciona la carrera")
        carrera_a_buscar = st.text_input("Escribe el número de carrera (Ej: 1):", value="1")
        hipodromo = st.text_input("Nombre del Hipódromo:", value="Gulfstream Park")
        
        if st.button("🚀 EXTRAER DATOS Y CALCULAR", use_container_width=True):
            with st.spinner("La ÍA HÍPICA está leyendo el PDF..."):
                with pdfplumber.open(archivo_pdf) as pdf:
                    texto_completo = ""
                    for pagina in pdf.pages:
                        texto_completo += pagina.extract_text() + "\n"
                    
                    # LÓGICA DE EXTRACCIÓN DE BRISNET
                    # Brisnet tiene un formato de texto donde los caballos salen con su nombre
                    # y en la misma línea o cerca aparece "Prime Power: X.X"
                    
                    # Vamos a buscar todas las apariciones de "Prime Power:"
                    lineas = texto_completo.split('\n')
                    
                    caballos_detectados = []
                    # Buscamos patrones como: "1 Sista Sol (P 2)" o "7 Miss Silipo (S 4)"
                    # y luego buscamos su Prime Power en las líneas siguientes.
                    
                    # Heurística simple: buscar lineas que empiecen con número y tengan texto, 
                    # luego buscar la palabra Prime Power en las cercanías.
                    for i, linea in enumerate(lineas):
                        # Busca lineas que empiecen con número de caballo (Ej: 1, 2, 3...)
                        match_caballo = re.match(r'^(\d+)\s+([A-Z][a-zA-Z\s\'\-]+)', linea)
                        if match_caballo:
                            num_caballo = match_caballo.group(1)
                            nombre_caballo = match_caballo.group(2).strip()
                            
                            # Buscamos el Prime Power en las siguientes 5 líneas
                            pp_encontrado = 0.0
                            for j in range(i, min(i+15, len(lineas))):
                                if "Prime Power:" in lineas[j]:
                                    match_pp = re.search(r'Prime Power:\s*([\d\.]+)', lineas[j])
                                    if match_pp:
                                        pp_encontrado = float(match_pp.group(1)) / 100.0 # Normalizado a 0-1
                                        break
                            
                            # Buscamos la cuota (ML) en la línea. En Brisnet suele ser algo como "4/1" o "7/2"
                            cuota_encontrada = 4.0 # Por defecto
                            match_cuota = re.search(r'(\d+/\d+)', linea)
                            if match_cuota:
                                frac = match_cuota.group(1)
                                num, den = frac.split('/')
                                cuota_encontrada = (float(num) / float(den)) + 1.0
                            
                            # Si encontramos nombre y PP, lo agregamos
                            if nombre_caballo and pp_encontrado > 0:
                                # Evitar duplicados por nombre
                                if not any(c['Nombre'] == nombre_caballo for c in caballos_detectados):
                                    caballos_detectados.append({
                                        "Nombre": nombre_caballo, 
                                        "PP": pp_encontrado,
                                        "Cuota": cuota_encontrada
                                    })
                    
                    df_extraido = pd.DataFrame(caballos_detectados)
                    
                    if df_extraido.empty:
                        st.error("No se pudieron extraer los datos. Asegúrate de que el PDF sea de Brisnet y tenga el formato correcto.")
                    else:
                        st.success(f"✅ Se extrajeron {len(df_extraido)} caballos del PDF.")
                        st.dataframe(df_extraido, use_container_width=True)
                        
                        # CALCULAR PROBABILIDAD (Fórmula Maestra)
                        total_q = sum(1 / c['Cuota'] for _, c in df_extraido.iterrows())
                        resultados = []
                        for _, c in df_extraido.iterrows():
                            p_mercado = (1 / c['Cuota']) / total_q
                            p_fund = c['PP'] # Usamos solo el PP para el fundamental (simplificado)
                            p_final = (0.50 * p_mercado) + (0.50 * p_fund)
                            edge = (p_final * c['Cuota']) - 1
                            
                            resultados.append({
                                "Caballo": c['Nombre'], 
                                "PP": c['PP'],
                                "Cuota": c['Cuota'], 
                                "Probabilidad": f"{p_final*100:.1f}%", 
                                "Edge": f"{edge:+.2f}", 
                                "p_final": p_final
                            })
                        
                        resultados.sort(key=lambda x: x['p_final'], reverse=True)
                        df_res = pd.DataFrame(resultados)
                        
                        st.markdown("### 🏆 VEREDICTO (Regla Suprema)")
                        st.dataframe(df_res[["Caballo", "PP", "Cuota", "Probabilidad", "Edge"]], use_container_width=True)
                        
                        ganador = resultados[0]
                        st.success(f"🎯 **GANADOR MATEMÁTICO: {ganador['Caballo']}** (Prob: {ganador['Probabilidad']})")
                        
                        # Registramos la apuesta automáticamente
                        c = conn.cursor()
                        c.execute("INSERT INTO historial (hipodromo, carrera, caballo, cuota, stake, prob, edge, resultado) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                                  (hipodromo, f"R{carrera_a_buscar}", ganador['Caballo'], ganador['Cuota'], 50.0, ganador['p_final'], ganador['p_final']*ganador['Cuota']-1, "Pendiente"))
                        c.execute("UPDATE banca SET balance = balance - ? WHERE id = 1", (50.0,))
                        conn.commit()
                        st.warning(f"⚠️ Apuesta registrada automáticamente (50 Bs).")

# PESTAÑA 2: LECTURA DE PDF (Diagnóstico)
with tab2:
    st.markdown("### 📄 Texto Crudo del PDF")
    if archivo_pdf:
        with pdfplumber.open(archivo_pdf) as pdf:
            st.text_area("Texto leído (Pág 1):", pdf.pages[0].extract_text(), height=400)

# PESTAÑA 3: MEMORIA
with tab3:
    df = pd.read_sql_query("SELECT * FROM historial", conn)
    st.dataframe(df, use_container_width=True)
    pendientes = df[df['resultado'] == 'Pendiente']
    if not pendientes.empty:
        for index, row in pendientes.iterrows():
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.write(f"**{row['caballo']}** - {row['hipodromo']} {row['carrera']}")
            if col2.button("✅ Ganó", key=f"w_{row['id']}"):
                ganancia = row['stake'] * row['cuota']
                c = conn.cursor()
                c.execute("UPDATE historial SET resultado = 'Ganó' WHERE id = ?", (row['id'],))
                c.execute("UPDATE banca SET balance = balance + ? WHERE id = 1", (ganancia,))
                conn.commit()
                st.rerun()
            if col3.button("❌ Perdió", key=f"l_{row['id']}"):
                c = conn.cursor()
                c.execute("UPDATE historial SET resultado = 'Perdió' WHERE id = ?", (row['id'],))
                conn.commit()
                st.rerun()

# PESTAÑA 4: BANCA
with tab4:
    c = conn.cursor()
    c.execute("SELECT balance FROM banca WHERE id = 1")
    balance = c.fetchone()[0]
    st.metric("Banca Actual", f"{balance:.2f} Bs")
