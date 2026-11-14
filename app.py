import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
from datetime import datetime

# Configuración optimizada para vista móvil (centered evita que se aplaste o desborde en teléfonos)
st.set_page_config(
    page_title="Apex Omega Mobile",
    page_icon="🏇",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==========================================
# ESTILOS CSS MOBILE-FIRST (COMPACTO & PRO)
# ==========================================
st.markdown("""
<style>
    /* Reducir márgenes superiores e inferiores de Streamlit en móvil */
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }
    /* Tarjeta de caballo compacta para celular */
    .mobile-card {
        background: linear-gradient(145deg, #1b1e26, #232732);
        border-radius: 10px;
        padding: 8px 10px;
        margin-bottom: 7px;
        border: 1px solid #2e3440;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    .saddle-mini {
        font-weight: 800;
        font-size: 14px;
        padding: 4px 6px;
        border-radius: 6px;
        text-align: center;
        min-width: 42px;
        margin-right: 10px;
        line-height: 1.1;
    }
    .horse-title {
        font-size: 14px;
        font-weight: 700;
        color: #f8f9fa;
        margin: 0;
        line-height: 1.2;
    }
    .horse-sub {
        font-size: 11px;
        color: #adb5bd;
        margin: 2px 0 0 0;
        line-height: 1.1;
    }
    .prob-pill {
        background-color: #2b9348;
        color: #ffffff;
        padding: 3px 8px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 12px;
        display: inline-block;
    }
    .ev-tag-pos {
        color: #80ed99;
        font-weight: 700;
        font-size: 10.5px;
        margin-top: 3px;
    }
    .ev-tag-neg {
        color: #6c757d;
        font-size: 10.5px;
        margin-top: 3px;
    }
    .bankroll-banner {
        background-color: #14171d;
        border: 1px solid #2b9348;
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# INICIALIZACIÓN ROBUSTA DE ESTADO
# ==========================================
if 'bankroll' not in st.session_state:
    st.session_state['bankroll'] = 100.0
