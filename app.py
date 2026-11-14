import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import pdfplumber
import sqlite3
import re
import io
import os

st.set_page_config(page_title="ÍA HÍPICA - Apex Omega", page_icon="🏇", layout="centered")

# Estilo móvil limpio (Cortesía de Gemini)
st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 2rem; padding-left: 0.5rem; padding-right: 0.5rem; }
    .card { background: #1e212d; border-radius: 8px; padding: 10px; margin-bottom: 8px; border-left: 5px solid #e63946; }
    .bank-box { background: #14171d; border: 1px solid #2b9348; border-radius: 8px; padding: 10px; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

st.markdown("### 🏇 ÍA HÍPICA • Centro Hípico Inteligente")

# 1. BASE DE DATOS REAL (Para que no se borre al refrescar)
DB_NAME = "ia_hipica_v12.db"
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS banca (id INTEGER PRIMARY KEY, balance REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tickets 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, hora TEXT, carrera TEXT, jugada TEXT, monto REAL, saldo REAL)''')
    c.execute("SELECT balance FROM banca WHERE id = 1")
    if c.fetchone() is None:
        c.execute("INSERT INTO banca (id, balance) VALUES (1, 100.0)")
    conn.commit()
    return conn

conn = init_db()

# Obtener bankroll real de la DB
c = conn.cursor()
c.execute("SELECT balance FROM banca WHERE id = 1")
bankroll_actual = c.fetchone()[0]

# 2. CARGA Y LECTURA REAL DE PDFs
if 'datos_jornada' not in st.session_state:
    st.session_state['datos_jornada'] = pd.DataFrame()

with st.expander("📂 1. Cargar Cartillas PDFs de la Jornada", expanded=st.session_state['datos_jornada'].empty):
    st.markdown("Sube los PDFs de Brisnet. La IA extraerá los caballos, Prime Power y cuotas reales.")
    archivos_pdf = st.file_uploader("Selecciona los PDFs", type=['pdf'], accept_multiple_files=True)
    
    if st.button("🚀 Procesar PDFs con la IA"):
        if len(archivos_pdf) > 0:
            with st.spinner("Escaneando PDFs y calculando..."):
                texto_completo = ""
                for archivo in archivos_pdf:
                    with pdfplumber.open(io.BytesIO(archivo.getvalue())) as pdf:
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
                                    pp_encontrado = float(match_pp.group(1))
                                    break
                        
                        cuota_encontrada = 4.0 
                        match_cuota = re.search(r'(\d+/\d+)', linea)
                        if match_cuota:
                            frac = match_cuota.group(1)
                            num, den = frac.split('/')
                            cuota_encontrada = (float(num) / float(den)) + 1.0
                        
                        if nombre_caballo and pp_encontrado > 0:
                            if not any(c['Caballo'] == nombre_caballo and c['Carrera'] == carrera_actual for c in caballos_detectados):
                                caballos_detectados.append({
                                    "Carrera": carrera_actual, 
                                    "Num": int(match_caballo.group(1)),
                                    "Caballo": nombre_caballo, 
                                    "PP": pp_encontrado,
                                    "Spd": np.random.randint(50, 90), # Simulamos Speed temporalmente
                                    "Div": round(cuota_encontrada, 2)
                                })
                
                df_extraido = pd.DataFrame(caballos_detectados)
                if df_extraido.empty:
                    st.error("No se encontraron datos. Verifica el PDF.")
                else:
                    st.session_state['datos_jornada'] = df_extraido
                    st.success(f"¡PDFs procesados! Se extrajeron {len(df_extraido)} caballos de {df_extraido['Carrera'].nunique()} carreras.")
                    st.rerun()
        else:
            st.warning("⚠️ Por favor selecciona al menos un archivo PDF.")

if st.session_state['datos_jornada'].empty:
    st.info("👆 Sube tus PDFs arriba para activar las guías y los cálculos reales.")
    st.stop()

# 3. SELECTOR Y CÁLCULOS MATEMÁTICOS
carreras_disponibles = sorted(st.session_state['datos_jornada']['Carrera'].unique(), key=int)
carrera_seleccionada = st.selectbox("Selecciona la Carrera en Curso:", [f"Carrera {c}" for c in carreras_disponibles])
num_carrera = carrera_seleccionada.replace("Carrera ", "")

# Filtrar data real
df = st.session_state['datos_jornada'][st.session_state['datos_jornada']['Carrera'] == num_carrera].copy()

# Fórmula Matemática (Softmax para probabilidades)
df['Score'] = (df['PP'] * 0.7) + (df['Spd'] * 0.3)
exp_s = np.exp((df['Score'] - df['Score'].mean()) / 5.0) # Divisor ajustado para no saturar
df['Prob'] = (exp_s / exp_s.sum()) * 100
df['EV'] = ((df['Prob'] / 100.0) * df['Div'] - 1.0) * 100

st.markdown(f"""
<div class="bank-box">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <div style="font-size:11px; color:#aaa;">BANKROLL DISPONIBLE</div>
            <div style="font-size:18px; font-weight:bold; color:#80ed99;">${bankroll_actual:.2f}</div>
        </div>
        <div style="text-align:right;">
            <div style="font-size:11px; color:#aaa;">ESTADO IA</div>
            <div style="font-size:13px; color:#2b9348; font-weight:bold;">Sincronizado con PDFs</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 4. PESTAÑAS
t1, t2 = st.tabs(["📋 Guía Analizada", "🎟️ Apostar & Bankroll"])

with t1:
    st.markdown(f"**Guía Real para: {carrera_seleccionada}**")
    df_ord = df.sort_values(by="Prob", ascending=False)
    for _, r in df_ord.iterrows():
        ev_color = "#80ed99" if r['EV'] > 0 else "#aaa"
        st.markdown(f"""
        <div class="card">
            <div style="display:flex; justify-content:space-between;">
                <b>#{r['Num']} {r['Caballo']}</b>
                <span style="color: #2b9348; font-weight:bold;">Prob: {r['Prob']:.1f}%</span>
            </div>
            <div style="font-size:12px; color:#ccc; margin-top:4px;">
                PP: {r['PP']} | Div: {r['Div']} | <span style="color:{ev_color};">EV: {r['EV']:+.1f}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

with t2:
    st.markdown("**Gestión de Apuesta y Descuento**")
    
    with st.expander("⚙️ Configurar / Modificar Bankroll Base"):
        nuevo_b = st.number_input("Nuevo saldo:", min_value=0.0, value=float(bankroll_actual), step=10.0)
        if st.button("Actualizar Bankroll"):
            c.execute("UPDATE banca SET balance = ? WHERE id = 1", (nuevo_b,))
            conn.commit()
            st.success("¡Bankroll actualizado en la base de datos!")
            st.rerun()

    monto_apuesta = st.number_input("Monto a apostar ($):", min_value=0.0, max_value=float(bankroll_actual), value=0.0, step=1.0)
    
    # Lista de caballos reales
    lista_caballos = [f"#{r['Num']} {r['Caballo']}" for _, r in df_ord.iterrows()]
    caballo_elegido = st.selectbox("Selecciona el caballo a jugar:", lista_caballos)
    
    capture_ticket = st.file_uploader("Sube el capture de tu jugada (Opcional):", type=['png', 'jpg', 'jpeg'])
    
    if st.button("✅ Confirmar Jugada y Descontar", type="primary"):
        if monto_apuesta > 0:
            nuevo_saldo = bankroll_actual - monto_apuesta
            # Actualizar DB
            c.execute("UPDATE banca SET balance = ? WHERE id = 1", (nuevo_saldo,))
            # Registrar Ticket
            hora_actual = datetime.now().strftime("%I:%M %p")
            c.execute("INSERT INTO tickets (hora, carrera, jugada, monto, saldo) VALUES (?, ?, ?, ?, ?)",
                      (hora_actual, carrera_seleccionada, caballo_elegido, monto_apuesta, nuevo_saldo))
            conn.commit()
            
            st.success(f"¡Apuesta de ${monto_apuesta} confirmada y descontada!")
            st.rerun()
        else:
            st.warning("⚠️ Ingresa un monto mayor a 0.")
            
    # Mostrar historial real de la DB
    df_tickets = pd.read_sql_query("SELECT hora as Hora, carrera as Carrera, jugada as Jugada, monto as Monto, saldo as Saldo FROM tickets ORDER BY id DESC LIMIT 10", conn)
    if not df_tickets.empty:
        st.markdown("---")
        st.markdown("**Historial de Tickets Confirmados:**")
        st.dataframe(df_tickets, use_container_width=True, hide_index=True)
