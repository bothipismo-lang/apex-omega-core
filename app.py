import streamlit as st

st.set_page_config(page_title="OMEGA-CORE", page_icon="🏇", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    </style>
""", unsafe_allow_html=True)

st.title("🏇 APEX-OMEGA ×50")
st.subheader("Terminal de Análisis Hípico · OMEGA-CORE")
st.write("---")

with st.form("datos_carrera"):
    st.markdown("### 📝 DATOS DEL CABALLO")
    
    col1, col2 = st.columns(2)
    with col1:
        hipodromo = st.text_input("Hipódromo:", value="Gulfstream Park")
        caballo = st.text_input("Nombre del Caballo:")
    with col2:
        carrera = st.number_input("Carrera (R#):", min_value=1, max_value=15, value=1)
        cuota = st.number_input("Cuota Decimal (ej. 4.50):", min_value=1.01, value=4.00)

    st.markdown("### 📊 VARIABLES FUNDAMENTALES")
    pp = st.slider("Prime Power (0.0 a 1.0):", 0.0, 1.0, 0.75)
    jockey_pct = st.slider("Win % Jockey (ej. 0.22):", 0.0, 0.40, 0.15)
    forma = st.slider("Forma reciente (0.0 a 1.0):", 0.0, 1.0, 0.50)
    
    boton = st.form_submit_button("🚀 EJECUTAR ALGORITMO")

if boton:
    p_fund = (pp * 0.6) + (jockey_pct * 0.3) + (forma * 0.1)
    p_mercado = (1 / cuota) / 0.30 
    p_final = (0.50 * p_mercado) + (0.50 * p_fund)
    edge = (p_final * cuota) - 1

    st.write("---")
    st.markdown("### 🎯 VEREDICTO DEL SISTEMA")
    st.metric(label="Probabilidad de Victoria (p_final)", value=f"{p_final*100:.1f}%")
    
    if edge >= 0.05:
        st.success(f"✅ **VALOR DETECTADO (Edge: {edge:+.2f})**")
        st.info(f"💰 **ACCIÓN:** Apostar 100 Bs a WIN por **{caballo}** en {hipodromo} R{carrera}.")
    else:
        st.error(f"⚠️ **SIN VALOR SUFICIENTE (Edge: {edge:+.2f})**")
        st.warning("El mercado ya tiene descontada la probabilidad real. El sistema recomienda NO apostar.")
