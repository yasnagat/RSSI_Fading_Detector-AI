import subprocess as sp
import time
import streamlit as st
from datetime import datetime
from collections import deque

RSSI_THRESHOLD = 5  # dBm
MONITOR_INTERVAL = 5  # segundos
INTERFACE = 'Wi-Fi'



# def get_rssi(INTERFACE):


def dashboard():
    st.set_page_config(page_title="Detector de Fading de RSSI", layout="wide")
    st.title("Detector de Eventos de Fading de RSSI")
    st.write("O R-D+AI monitora o seu sinal Wi-Fi, detecta eventos de fading no período de 2 minutos e apresenta um diagnóstico do evento que você escolher.")
    
    if 'monitoring' not in st.session_state:
        st.session_state.monitoring = False
        st.session_state.data = deque(maxlen=100)
        st.session_state.fading_events = []
        st.session_state.stop_event = None
        st.session_state.monitor_thread = None

    col1, col2, col3 = st.columns([1, 2, 2])
    
    with col1:
        if st.button("Iniciar Monitoramento" if not st.session_state.monitoring else "Parar Monitoramento"):
            if not st.session_state.monitoring:

                st.success("Monitoramento iniciado!")
            else:
                if st.session_state.stop_event:
                    st.session_state.stop_event.set()
                st.session_state.monitoring = False
                st.info("Monitoramento interrompido.")
    
    with col2:
        if st.button("Limpar Dados"):
            st.session_state.data.clear()
            st.session_state.fading_events.clear()
            st.success("Dados limpos!")
    
    with col3:
        st.metric("Status", "🟢 Monitorando" if st.session_state.monitoring else "🔴 Parado")

    if st.session_state.monitoring:
        time.sleep(1)
        st.rerun()

# def llm_integration(fading_events):

if __name__ == "__main__":
    dashboard()