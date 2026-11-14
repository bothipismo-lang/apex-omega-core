import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Apex Omega", page_icon="🏇", layout="centered")

# Estilo móvil limpio
st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 2rem; padding-left: 0.5rem; padding-right: 0.5rem; }
    .card { background: #1e212d; border-radius: 8px; padding: 10px; margin-bottom: 8px; border-left: 5px solid #e63946; }
</style>
""", unsafe_allow_html=True)

# Estado global
if 'bankroll' not in st.session_state: st.session_state['bankroll'] = 100.0
if 'tickets' not in st.session_state: st.session_state['tickets'] = []

st.markdown("### 🏇 Apex Omega • Gulfstream C1")
st.info(f"💰 **Bankroll:** ${st.session_state['bankroll']:.2f} | ⏱️ **Partida:** 1:20 PM")

# Datos oficiales Carrera 1
data = [
    {"Num": 1, "Caballo": "Sista Sol", "Jinete": "Ocasio J.", "Div": 26.0, "PP": 96.8, "Spd": 55},
    {"Num": 2, "Caballo": "Via Via Via", "Jinete": "Vasquez F.", "Div": 18.0, "PP": 88.6, "Spd": 56},
    {"Num": 3, "Caballo": "Chrissy's Dream", "Jinete": "Rios J.", "Div": 6.0, "PP": 95.7, "Spd": 26},
    {"Num": 4, "Caballo": "I'm Chill", "Jinete": "Herrera D.", "Div": 6.0, "PP": 110.9, "Spd": 69},
    {"Num": 5, "Caballo": "Our Perfect Amanda", "Jinete": "Lopez Paco", "Div": 2.8, "PP": 112.7, "Spd": 68},
    {"Num": 6, "Caballo": "Decisive Maiara", "Jinete": "Vasquez M.", "Div": 6.0, "PP": 99.6, "Spd": 49},
    {"Num": 7, "Caballo": "Miss Silipo", "Jinete": "Husbands M.", "Div": 3.0, "PP": 104.0, "Spd": 62},
    {"Num": 8, "Caballo": "Shamrock Queen", "Jinete": "Morelos J.", "Div": 50.0, "PP": 84.5, "Spd": 24},
    {"Num": 9, "Caballo": "Loyalist", "Jinete": "Ismerio V.", "Div": 41.0, "PP": 107.2, "Spd": 63},
]
df = pd.DataFrame(data)

# Cálculo de probabilidades y EV
df['Score'] = (df['PP'] * 0.7) + (df['Spd'] * 0.3)
exp_s = np.exp((df['Score'] - df['Score'].mean()) / 8.0)
df['Prob'] = (exp_s / exp_s.sum()) * 100
df['EV'] = ((df['Prob'] / 100.0) * df['Div'] - 1.0) * 100

# Pestañas
t1, t2 = st.tabs(["📋 Guía C1", "🎟️ Bankroll"])

with t1:
    st.markdown("**Lista Oficial & Probabilidades:**")
    df_ord = df.sort_values(by="Prob", ascending=False)
    for _, r in df_ord.iterrows():
        st.markdown(f"""
        <div class="card">
            <div style="display:flex; justify-content:space-between;">
                <b>#{r['Num']} {r['Caballo']}</b>
                <span style="color: #2b9348; font-weight:bold;">{r['Prob']:.1f}%</span>
            </div>
            <div style="font-size:12px; color:#aaa;">J: {r['Jinete']} | Div: {r['Div']} | EV: {r['EV']:+.0f}%</div>
        </div>
        """, unsafe_allow_html=True)

with t2:
    st.markdown("**Registrar Apuesta**")
    monto = st.number_input("Monto apostado ($):", min_value=0.0, max_value=float(st.session_state['bankroll']), value=0.0)
    caballo_sel = st.selectbox("Caballo:", [f"#{r['Num']} {r['Caballo']}" for _, r in df.iterrows()])
    
    if st.button("Confirmar y Descontar"):
        if monto > 0:
            st.session_state['bankroll'] -= monto
            st.session_state['tickets'].append({"Caballo": caballo_sel, "Monto": monto})
            st.success("¡Descontado con éxito!")
            st.rerun()
        else:
            st.warning("Ingresa un monto válido.")
            
    if st.session_state['tickets']:
        st.write("Apuestas realizadas:")
        st.dataframe(pd.DataFrame(st.session_state['tickets']), use_container_width=True)
