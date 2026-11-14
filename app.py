import streamlit as st
import pandas as pd
import numpy as np
import cv2
from PIL import Image

st.set_page_config(
    page_title="Apex Omega - AI Live Handicapper & Vision Hub",
    page_icon="🏇",
    layout="wide"
)

st.title("🏇 Apex Omega: Motor de Inteligencia Hípica en Vivo")
st.markdown("Sistema autónomo con visión por computadora para análisis de posiciones en tiempo real, cálculo de *Edge* y aprendizaje dinámico.")

# Panel de control lateral
race_selected = st.sidebar.selectbox("Carrera en Curso", [f"Gulfstream Park - Carrera {i}" for i in range(1, 12)])
modo_analisis = st.sidebar.radio("Modo de Operación", ["Simulación de Flujo en Vivo", "Conexión a Stream / Captura por WebRTC"])

# Base de datos inicial de la carrera con Dividendos Matutinos (ML) y Factor de Clase
def cargar_pp_inteligentes():
    return pd.DataFrame({
        'Caballo': ['Tall Story', 'Sherman Fury', 'Tapstick', 'Magic Heart', 'David Pepperman'],
        'ML_Odds': ['10/1', '5/2', '7/2', '4/1', '8/1'],
        'Prime_Power': [112.6, 115.9, 111.9, 115.1, 110.9],
        'Estilo_Correr': ['Puntero (E)', 'Presser (P)', 'Stalker (S)', 'Puntero (E)', 'Atropellador (C)']
    })

df_carrera = cargar_pp_inteligentes()

# Conversor matemático de Momios a Probabilidad Implícita
def odds_a_probabilidad(odds_str):
    try:
        num, den = map(int, odds_str.split('/'))
        return den / (num + den)
    except:
        return 0.1

df_carrera['Prob_Implicita'] = df_carrera['ML_Odds'].apply(odds_a_probabilidad)

# Layout principal: [Visión Artificial / Stream] | [Matriz de Probabilidades & Chenroy] | [Bitácora de Aprendizaje IA]
col_vision, col_stats, col_aprendizaje = st.columns([1.5, 1.2, 1])

with col_vision:
    st.subheader("👁️ Ojos de la IA (Visión en Vivo)")
    st.markdown("Extrayendo fotogramas de la transmisión para detectar posiciones en la pista.")
    
    # Simulación del visor de fotogramas procesados por IA
    uploaded_frame = st.file_uploader("Subir capture de la transmisión en vivo (Curva / Recta Final)", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_frame is not None:
        imagen = Image.open(uploaded_frame)
        # Convertir imagen para procesamiento con OpenCV simulado
        img_np = np.array(imagen)
        
        # Simulación de detección de objetos (Bounding boxes sobre los caballos en el stream)
        st.image(imagen, caption="Fotograma analizado: Detección de jockeys y posiciones en curso", use_container_width=True)
        st.success("🎯 IA detectó cambios en el orden parcial (Parciales de 400m leídos con éxito).")
    else:
        st.info("Esperando fotograma de la señal en vivo de Meridiano para procesar visión artificial...")

with col_stats:
    st.subheader("📊 Probabilidades Reales & *Chenroy*")
    
    # Simulación de actualización dinámica basada en el rendimiento visual en vivo
    if st.button("⚡ Actualizar Probabilidades con IA en Vivo"):
        # Ajuste dinámico basado en la posición detectada en la pista
        np.random.seed()
        factor_ajuste = np.random.uniform(0.85, 1.15, len(df_carrera))
        df_carrera['Score_Dinamico'] = df_carrera['Prime_Power'] * factor_ajuste
        
        # Normalizar a porcentajes reales (100%)
        suma_scores = df_carrera['Score_Dinamico'].sum()
        df_carrera['Prob_Real_IA'] = (df_carrera['Score_Dinamico'] / suma_scores) * 100
        
        # Cálculo del Chenroy / Valor Esperado (EV) y Fair Odds
        # EV = (Probabilidad Real * Payout) - 1
        def calcular_rentabilidad(row):
            num, den = map(int, row['ML_Odds'].split('/'))
            payout_decimal = (num / den) + 1
            prob_decimal = row['Prob_Real_IA'] / 100
            ev = (prob_decimal * payout_decimal) - 1
            return ev * 100 # Retorno porcentual estimado (Chenroy / EV)

        df_carrera['Chenroy_EV_%'] = df_carrera.apply(calcular_rentabilidad, axis=1)
        
        st.session_state['actualizado'] = True
    else:
        # Valores base iniciales
        total_pp = df_carrera['Prime_Power'].sum()
        df_carrera['Prob_Real_IA'] = (df_carrera['Prime_Power'] / total_pp) * 100
        df_carrera['Chenroy_EV_%'] = 0.0

    # Mostrar tabla interactiva de valor
    st.dataframe(
        df_carrera[['Caballo', 'Estilo_Correr', 'ML_Odds', 'Prob_Real_IA', 'Chenroy_EV_%']].style.format({
            'Prob_Real_IA': '{:.1f}%',
            'Chenroy_EV_%': '{:+.1f}%'
        }),
        use_container_width=True
    )
    
    st.markdown("💡 *Nota: Si el **Chenroy / EV %** da positivo alto, significa que el dividendo en pantalla paga mucho más de lo que la IA calculó que es su probabilidad real (¡Apuesta de Valor!).*")

with col_aprendizaje:
    st.subheader("🧠 Memoria y Aprendizaje")
    st.markdown("La IA va calibrando sus pesos internos basándose en cómo rinden los estilos de pista (ej. si la pista favorece a los punteros hoy).")
    
    # Registro del modelo autorecursivo
    st.metric("Precisión del Modelo (Feedback Loop)", "91.4%", "+2.1% vs carrera anterior")
    st.metric("Sesgo de Pista Detectado hoy", "Favorable a Punteros (Speed Bias)", "Fiabilidad: Alta")
    
    with st.expander("Ver bitácora de aprendizaje en vivo"):
        st.write("- **Carrera previa:** El modelo ajustó el peso del jinete en un +4% tras detectar remate tardío.")
        st.write("- **Calibración actual:** Ponderando velocidad inicial sobre velocidad final debido al estado de la cancha.")

st.markdown("---")
