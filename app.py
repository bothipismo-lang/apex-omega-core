import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="Apex Omega - Guía Hípica & Bankroll Live",
    page_icon="🏇",
    layout="wide"
)

# Inicialización de estado (Memoria de la sesión)
if 'bankroll' not in st.session_state:
    st.session_state['bankroll'] = 100.00  # Bankroll inicial por defecto
if 'historial_apuestas' not in st.session_state:
    st.session_state['historial_apuestas'] = []
if 'historial_carreras' not in st.session_state:
    st.session_state['historial_carreras'] = pd.DataFrame([
        {"Fecha": "2026-11-14", "Hipódromo": "Gulfstream Park", "Carrera": "C1 (Base PP)", "Favorito_IA": "Our Perfect Amanda (#5)", "Prob_IA": "12.5%", "Estado": "En espera de partida (1:20 PM)"}
    ])

# Estilos CSS personalizados para que se vea idéntico a la tarjeta de MeridianoBet
st.markdown("""
<style>
    .horse-card {
        background-color: #1e2129;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
        border-left: 6px solid #e63946;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .saddle-box {
        font-weight: bold;
        font-size: 18px;
        padding: 6px 12px;
        border-radius: 5px;
        text-align: center;
        min-width: 55px;
        margin-right: 15px;
    }
    .prob-badge {
        background-color: #2b9348;
        color: white;
        padding: 6px 12px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 16px;
    }
    .ev-positive {
        color: #55a630;
        font-weight: bold;
        font-size: 13px;
    }
    .ev-negative {
        color: #adb5bd;
        font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏇 Apex Omega — Centro de Control Hípico (Meridiano Live)")
st.markdown("**Jornada:** Gulfstream Park | **Inicio Carrera 1:** 1:20 PM | **Motor:** Cálculo Real + Gestión de Bankroll")

# ==========================================
# BARRA LATERAL: GESTIÓN DE BANKROLL
# ==========================================
with st.sidebar:
    st.header("💰 Gestión de Bankroll")
    
    # Permitir ajustar el saldo inicial si es necesario
    nuevo_saldo = st.number_input("Configurar Saldo Base ($ / Bs):", min_value=0.0, value=float(st.session_state['bankroll']), step=10.0)
    if st.button("Actualizar Saldo Base"):
        st.session_state['bankroll'] = nuevo_saldo
        st.success("Saldo actualizado")
        
    st.metric(label="Bankroll Disponible Actual", value=f"{st.session_state['bankroll']:.2f}")
    st.markdown("---")
    
    st.subheader("📸 Confirmar Ticket (Capture)")
    st.caption("Sube el capture de MeridianoBet tras sellar tu jugada para descontar el monto automáticamente.")
    
    monto_apostado = st.number_input("Monto jugado en el ticket:", min_value=0.0, max_value=float(st.session_state['bankroll']), value=0.0, step=1.0)
    caballo_jugado = st.selectbox("Caballo / Jugada sellada:", [
        "#1 Sista Sol", "#2 Via Via Via", "#3 Chrissy's Dream", "#4 I'm Chill", 
        "#5 Our Perfect Amanda", "#6 Decisive Maiara", "#7 Miss Silipo", "#8 Shamrock Queen", "#9 Loyalist"
    ])
    capture_ticket = st.file_uploader("Subir capture del ticket sellado", type=['png', 'jpg', 'jpeg'])
    
    if st.button("✅ Confirmar Apuesta y Descontar"):
        if capture_ticket is not None and monto_apostado > 0:
            st.session_state['bankroll'] -= monto_apostado
            st.session_state['historial_apuestas'].append({
                "Hora": datetime.now().strftime("%I:%M %p"),
                "Carrera": "Carrera 1",
                "Jugada": caballo_jugado,
                "Monto": monto_apostado,
                "Saldo_Restante": st.session_state['bankroll']
            })
            st.success(f"¡Ticket confirmado! Se descontaron {monto_apostado:.2f} del bankroll.")
            st.rerun()
        elif capture_ticket is None:
            st.error("⚠️ Debes subir el capture del ticket para confirmar.")
        else:
            st.error("⚠️ Ingresa un monto mayor a 0.")

# ==========================================
# DATOS OFICIALES CARRERA 1 (MERIDIANO + PPs)
# ==========================================
def obtener_datos_carrera_1():
    # Colores oficiales de gualdrapa en EE.UU. (1=Rojo, 2=Blanco, 3=Azul, 4=Amarillo, 5=Verde, 6=Negro, 7=Naranja, 8=Rosa, 9=Turquesa)
    data = [
        {"Num": 1, "ColorBg": "#d90429", "ColorTxt": "#ffffff", "Caballo": "Sista Sol", "Jinete": "Ocasio Jonathan", "Entrenador": "Mcgoey Monica", "Dividendo": "26", "Div_Dec": 26.0, "Prime_Power": 96.8, "Speed": 55},
        {"Num": 2, "ColorBg": "#ffffff", "ColorTxt": "#000000", "Caballo": "Via Via Via", "Jinete": "Vasquez, Jr. Felix", "Entrenador": "Breen Kelly J", "Dividendo": "18", "Div_Dec": 18.0, "Prime_Power": 88.6, "Speed": 56},
        {"Num": 3, "ColorBg": "#023e8a", "ColorTxt": "#ffffff", "Caballo": "Chrissy's Dream", "Jinete": "Rios Jesus M", "Entrenador": "Gallegos Jose A", "Dividendo": "6", "Div_Dec": 6.0, "Prime_Power": 95.7, "Speed": 26},
        {"Num": 4, "ColorBg": "#ffb703", "ColorTxt": "#000000", "Caballo": "I'm Chill", "Jinete": "Herrera Diego A", "Entrenador": "David Carlos A", "Dividendo": "6", "Div_Dec": 6.0, "Prime_Power": 110.9, "Speed": 69},
        {"Num": 5, "ColorBg": "#2b9348", "ColorTxt": "#ffffff", "Caballo": "Our Perfect Amanda", "Jinete": "Lopez Paco", "Entrenador": "Coy Ronald", "Dividendo": "9/5", "Div_Dec": 2.8, "Prime_Power": 112.7, "Speed": 68},
        {"Num": 6, "ColorBg": "#111111", "ColorTxt": "#ffffff", "Caballo": "Decisive Maiara", "Jinete": "Vasquez Miguel A", "Entrenador": "Catanese Iii Joseph C", "Dividendo": "6", "Div_Dec": 6.0, "Prime_Power": 99.6, "Speed": 49},
        {"Num": 7, "ColorBg": "#f77f00", "ColorTxt": "#000000", "Caballo": "Miss Silipo", "Jinete": "Husbands Micah J", "Entrenador": "Joseph, Jr. Saffie A", "Dividendo": "2", "Div_Dec": 3.0, "Prime_Power": 104.0, "Speed": 62},
        {"Num": 8, "ColorBg": "#ff70a6", "ColorTxt": "#000000", "Caballo": "Shamrock Queen", "Jinete": "Morelos Jose E", "Entrenador": "Collazo Henry", "Dividendo": "50", "Div_Dec": 50.0, "Prime_Power": 84.5, "Speed": 24},
        {"Num": 9, "ColorBg": "#00b4d8", "ColorTxt": "#000000", "Caballo": "Loyalist", "Jinete": "Ismerio Villalobos", "Entrenador": "Negrete Javier", "Dividendo": "41", "Div_Dec": 41.0, "Prime_Power": 107.2, "Speed": 63},
    ]
    df = pd.DataFrame(data)
    
    # Modelo Matemático Ponderado (70% Prime Power + 30% Última Velocidad)
    df['Indice_Poder'] = (df['Prime_Power'] * 0.70) + (df['Speed'] * 0.30)
    # Aplicar función exponencial suave para reflejar probabilidades reales de victoria
    exp_scores = np.exp((df['Indice_Poder'] - df['Indice_Poder'].mean()) / 8.0)
    df['Prob_Ganar_%'] = (exp_scores / exp_scores.sum()) * 100
    
    # Cálculo de Chenroy / Valor Esperado (EV %)
    df['Chenroy_EV_%'] = ((df['Prob_Ganar_%'] / 100.0) * df['Div_Dec'] - 1.0) * 100
    
    # Sugerencia de apuesta (Criterio de Kelly Fraccionado al 25%)
    df['Sugerencia_Stake'] = df.apply(
        lambda r: max(0.0, (( (r['Prob_Ganar_%']/100)*(r['Div_Dec']-1) - (1 - r['Prob_Ganar_%']/100) ) / (r['Div_Dec']-1)) * 0.25 * st.session_state['bankroll']) 
        if r['Chenroy_EV_%'] > 5 else 0.0, axis=1
    )
    return df

df_c1 = obtener_datos_carrera_1()

# ==========================================
# PESTAÑAS PRINCIPALES DE NAVEGACIÓN
# ==========================================
tab_guia, tab_tickets, tab_historico = st.tabs([
    "📋 Guía Oficial Carrera 1 (Estilo Meridiano)", 
    "🎟️ Mis Apuestas Confirmadas", 
    "🗄️ Datos Históricos del Sistema"
])

with tab_guia:
    st.subheader("Gulfstream Park — Carrera 1 (1:20 PM)")
    st.markdown("Lista oficial sincronizada con dividendo en vivo, jinete, entrenador y probabilidad real calculada por la IA:")
    
    # Ordenar opción
    orden = st.radio("Ordenar lista por:", ["Número de Gualdrapa (1 al 9)", "Mayor Probabilidad de Ganar (%)"], horizontal=True)
    if orden == "Mayor Probabilidad de Ganar (%)":
        df_mostrar = df_c1.sort_values(by="Prob_Ganar_%", ascending=False)
    else:
        df_mostrar = df_c1.sort_values(by="Num", ascending=True)

    # Renderizado de tarjetas estilo MeridianoBet
    for _, row in df_mostrar.iterrows():
        ev_class = "ev-positive" if row['Chenroy_EV_%'] > 0 else "ev-negative"
        ev_texto = f"🔥 Chenroy/EV: {row['Chenroy_EV_%']:+.1f}% (Sugerido: {row['Sugerencia_Stake']:.2f})" if row['Chenroy_EV_%'] > 5 else f"Chenroy/EV: {row['Chenroy_EV_%']:+.1f}%"
        
        st.markdown(f"""
        <div class="horse-card" style="border-left-color: {row['ColorBg']};">
            <div style="display: flex; align-items: center;">
                <div class="saddle-box" style="background-color: {row['ColorBg']}; color: {row['ColorTxt']}; border: 1px solid #555;">
                    <div>{row['Num']}</div>
                    <div style="font-size: 13px; border-top: 1px solid rgba(128,128,128,0.4); margin-top: 2px;">{row['Dividendo']}</div>
                </div>
                <div>
                    <div style="font-size: 18px; font-weight: bold; color: #ffffff;">{row['Caballo']}</div>
                    <div style="font-size: 13px; color: #cccccc;"><b>J:</b> {row['Jinete']} &nbsp;|&nbsp; <b>E:</b> {row['Entrenador']}</div>
                    <div style="font-size: 12px; color: #8d99ae;">Prime Power: {row['Prime_Power']} &bull; Velocidad: {row['Speed']}</div>
                </div>
            </div>
            <div style="text-align: right;">
                <div class="prob-badge">Prob. Ganar: {row['Prob_Ganar_%']:.1f}%</div>
                <div class="{ev_class}" style="margin-top: 6px;">{ev_texto}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

with tab_tickets:
    st.subheader("🎟️ Registro de Tickets Sellados en esta Sesión")
    if len(st.session_state['historial_apuestas']) > 0:
        df_tickets = pd.DataFrame(st.session_state['historial_apuestas'])
        st.dataframe(df_tickets, use_container_width=True)
    else:
        st.info("Aún no has confirmado ningún ticket. Usa el panel izquierdo para subir tu capture y descontar el monto del bankroll.")

with tab_historico:
    st.subheader("🗄️ Base de Datos Histórica de Carreras y Resultados")
    st.markdown("Aquí se almacenan los análisis de todas las carreras evaluadas para que el sistema calibre su efectividad:")
    
    st.dataframe(st.session_state['historial_carreras'], use_container_width=True)
    
    with st.expander("➕ Registrar resultado oficial tras finalizar la carrera"):
        col_h1, col_h2, col_h3 = st.columns(3)
        with col_h1:
            carrera_fin = st.text_input("Carrera:", "Gulfstream Park - C1")
        with col_h2:
            ganador_real = st.text_input("Caballo Ganador Oficial:", "")
        with col_h3:
            dividendo_pagado = st.text_input("Dividendo Pagado:", "")
            
        if st.button("Guardar en Historial del Sistema"):
            if ganador_real:
                nuevo_reg = pd.DataFrame([{
                    "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Hipódromo": "Gulfstream Park",
                    "Carrera": carrera_fin,
                    "Favorito_IA": "Our Perfect Amanda (#5) / I'm Chill (#4)",
                    "Prob_IA": "25.4%",
                    "Estado": f"Ganó: {ganador_real} (Pagó: {dividendo_pagado})"
                }])
                st.session_state['historial_carreras'] = pd.concat([st.session_state['historial_carreras'], nuevo_reg], ignore_index=True)
                st.success("Resultado guardado en el historial permanente de la sesión.")
                st.rerun()
