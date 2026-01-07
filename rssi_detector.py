import subprocess as sp
import streamlit as st
from collections import deque
import os
import time
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go

RSSI_RANGE = 10
MONITOR_INTERVAL = 2
MONITOR_DURATION = 120

def get_rssi():
    try:
        if os.name == 'nt': # Windows
            result_cmd = sp.run(['netsh', 'wlan', 'show', 'interfaces'], capture_output=True, text=True, timeout=2)
            output = result_cmd.stdout
        else: # Linux / POSIX
            # Tentamos o iwconfig primeiro
            result_cmd = sp.run(['iwconfig'], capture_output=True, text=True, timeout=2)
            output = result_cmd.stdout

        result = {'rssi': None, 'banda': None, 'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

        for line in output.splitlines():
            line_lower = line.lower()
            
            # Lógica para Windows
            if os.name == 'nt':
                if 'rssi' in line_lower and ':' in line:
                    result['rssi'] = int(line.split(':')[1].replace('%', '').strip())
            
            # Lógica para Linux (iwconfig)
            else:
                if 'signal level' in line_lower:
                    # O iwconfig retorna algo como: Signal level=-35 dBm
                    partes = line.split('Signal level=')[1].split()
                    valor_rssi = partes[0].replace('dBm', '')
                    result['rssi'] = int(valor_rssi)
                
                if 'frequency' in line_lower:
                    # Tenta pegar a frequência/banda
                    result['banda'] = line.split('Frequency:')[1].split()[0]

        return result
    except Exception as e:
        print(f"Erro detalhado: {e}")
        return None

def monitor_rssi(duration=MONITOR_DURATION, interval=MONITOR_INTERVAL, rssi_range=RSSI_RANGE):
    start_time = datetime.now()
    end_time = start_time + timedelta(seconds=duration)
    
    rssi_history = []
    fading_events = []
    previous_rssi = None
    collect_nb = 0
    
    while datetime.now() < end_time:
        collect_nb += 1
        timer = (datetime.now() - start_time).total_seconds()
        time_limit = duration - timer
        data = get_rssi()

        if data['rssi'] is not None:
            current_rssi = data['rssi']
            rssi_history.append(data)

            if previous_rssi is not None:
                fading_test_detection = current_rssi - previous_rssi
                
                if abs(fading_test_detection) >= rssi_range:
                    fading_event = {
                        'Data e hora do evento': data['timestamp'],
                        'RSSI anterior': previous_rssi,
                        'RSSI atual': current_rssi,
                        'Diferenca de Sinal': fading_test_detection,
                        'Tipo': 'queda' if fading_test_detection < 0 else 'aumento'
                    }
                    fading_events.append(fading_event)
                    print(f"[{collect_nb}] Fading: {previous_rssi} -> {current_rssi} dBm ({fading_test_detection:+d} dBm)")
                else:
                    print(f"[{collect_nb}] Estavel: {current_rssi} dBm")
            else:
                print(f"[{collect_nb}] Inicial: {current_rssi} dBm")
            
            previous_rssi = current_rssi

        else:
            print(f"[{collect_nb}] Erro ao coletar")
        
        print(f"Tempo restante: {time_limit:.0f}s\n")
        
        if datetime.now() < end_time:
            time.sleep(interval)
    
    result = {
        'Tempo total de monitoramento': duration,
        'Coletas realizadas': len(rssi_history),
        'Numero eventos': len(fading_events),        
        'Eventos de Fading': fading_events,
        'Historico de coletas': rssi_history
    }

    return result

def inline_graph(rssi_history, fading_events):
    if not rssi_history:
        return None

    table = pd.DataFrame(rssi_history)
    table['timestamp'] = pd.to_datetime(table['timestamp'])
    
    graph = go.Figure()
    
    graph.add_trace(go.Scatter(
        x=table['timestamp'],
        y=table['rssi'],
        mode='lines+markers',
        name='RSSI',
        line=dict(color='blue', width=2),
        marker=dict(size=8)
    ))
    
    if fading_events:
        fading_tb = pd.DataFrame(fading_events)
        fading_tb['Data e hora do evento'] = pd.to_datetime(fading_tb['Data e hora do evento'])
        
        quedas = fading_tb[fading_tb['Tipo'] == 'queda']
        if not quedas.empty:
            graph.add_trace(go.Scatter(
                x=quedas['Data e hora do evento'],
                y=quedas['RSSI atual'],
                mode='markers',
                name='Queda',
                marker=dict(color='red', size=12, symbol='x')
            ))
        
        aumentos = fading_tb[fading_tb['Tipo'] == 'aumento']
        if not aumentos.empty:
            graph.add_trace(go.Scatter(
                x=aumentos['Data e hora do evento'],
                y=aumentos['RSSI atual'],
                mode='markers',
                name='Aumento',
                marker=dict(color='green', size=12, symbol='triangle-up')
            ))
    
    graph.update_layout(
        title='RSSI ao Longo do Tempo',
        xaxis_title='Horario',
        yaxis_title='RSSI (dBm)',
        height=400
    )
    
    return graph

def pie_graph(fading_events):
    if not fading_events:
        return None
    
    table = pd.DataFrame(fading_events)
    tipo_counts = table['Tipo'].value_counts()
    
    graph = go.Figure(data=[go.Pie(
        labels=tipo_counts.index,
        values=tipo_counts.values,
        marker=dict(colors=['red', 'green'])
    )])
    
    graph.update_layout(
        title='Distribuicao de Eventos',
        height=350
    )
    
    return graph

def history(rssi_history):
    if not rssi_history:
        return None
    
    table = pd.DataFrame(rssi_history)
    
    graph = go.Figure(data=[go.Histogram(
        x=table['rssi'],
        nbinsx=20,
        marker=dict(color='blue')
    )])
    
    graph.update_layout(
        title='Distribuicao do RSSI',
        xaxis_title='RSSI (dBm)',
        yaxis_title='Frequencia',
        height=350
    )
    
    return graph

def bars(fading_events):
    if not fading_events:
        return None
    
    table = pd.DataFrame(fading_events)
    table['Data e hora do evento'] = pd.to_datetime(table['Data e hora do evento'])
    
    colors = ['red' if tipo == 'queda' else 'green' for tipo in table['Tipo']]
    
    graph = go.Figure(data=[go.Bar(
        x=table['Data e hora do evento'],
        y=table['Diferenca de Sinal'],
        marker=dict(color=colors),
        text=table['Diferenca de Sinal']
    )])
    
    graph.update_layout(
        title='Variacoes de Sinal',
        xaxis_title='Horario',
        yaxis_title='Variacao (dBm)',
        height=400
    )
    
    return graph

def ia_prompt(fading_event, rssi_history, api_key):
    try:
        from openai import OpenAI
        
        client = OpenAI(
        api_key="gsk_qQRZgR0S4WcDHrx6PQdWWGdyb3FY5AU6x7QzE1V09W0yXxi6U6aSOQ",
        base_url="https://api.groq.com/openai/v1")

        rssi_medio = sum(h['rssi'] for h in rssi_history) / len(rssi_history)
        rssi_min = min(h['rssi'] for h in rssi_history)
        rssi_max = max(h['rssi'] for h in rssi_history)
        
        prompt = f"""
Analise este evento de fading em rede Wi-Fi e forneca possiveis causas:

Detalhes do Evento:
Data e Hora: {fading_event['Data e hora do evento']}
RSSI Anterior: {fading_event['RSSI anterior']} dBm
RSSI Atual: {fading_event['RSSI atual']} dBm
Variacao: {fading_event['Diferenca de Sinal']} dBm
Tipo: {fading_event['Tipo']}

Contexto:
Total de coletas: {len(rssi_history)}
RSSI medio: {rssi_medio:.1f} dBm
RSSI minimo: {rssi_min} dBm
RSSI maximo: {rssi_max} dBm
"""
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ],
            stream=False
        )

        return response.choices[0].message.content     
        
    except Exception as e:
        return f"Erro ao analisar: {str(e)}"

def ia_section(fading_events, rssi_history):
    st.markdown("---")
    st.subheader("Execute uma consulta com IA")
    
    if not fading_events:
        st.info("Nenhum evento detectado. Execute o monitoramento primeiro.")
        return
    
    if 'api_key' not in st.session_state:
        st.session_state.api_key = ""
    
    api_key = st.text_input(
        "Chave da API da LLM",
        type="password",
        value=st.session_state.api_key
    )
    
    if api_key:
        st.session_state.api_key = api_key
    
    event_options = []
    for i, event in enumerate(fading_events):
        texto = f"Evento {i+1} - {event['Data e hora do evento']} | {event['Tipo'].upper()} de {abs(event['Diferenca de Sinal'])} dBm"
        event_options.append(texto)
    
    selected_index = st.selectbox(
        "Escolha um evento para avaliar:",
        range(len(event_options)),
        format_func=lambda x: event_options[x]
    )
    
    selected_event = fading_events[selected_index]
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Horario", selected_event['Data e hora do evento'].split()[1])
    with col2:
        st.metric("RSSI Anterior", f"{selected_event['RSSI anterior']} dBm")
    with col3:
        st.metric("RSSI Atual", f"{selected_event['RSSI atual']} dBm")
    with col4:
        st.metric("Variacao", f"{selected_event['Diferenca de Sinal']:+d} dBm")
    
    if st.button("Analisar com IA", type="primary", use_container_width=True):
        if not api_key:
            st.error("Insira sua chave da API")
        else:
            with st.spinner("Analisando..."):
                analise = ia_prompt(selected_event, rssi_history, api_key)
                
                if 'analyses' not in st.session_state:
                    st.session_state.analyses = {}
                st.session_state.analyses[selected_index] = analise
    
    if 'analyses' in st.session_state and selected_index in st.session_state.analyses:
        st.markdown("### Conclusao")
        st.markdown(st.session_state.analyses[selected_index])
        
        if st.button("Apagar resposta"):
            del st.session_state.analyses[selected_index]
            st.rerun()

def dashboard():
    st.set_page_config(page_title="R-D+IA", layout="wide")
    st.title("R-D+IA - Detector de Fading de RSSI")
    st.markdown("Monitora o sinal Wi-Fi e detecta eventos de fading")
    
    if 'monitoring' not in st.session_state:
        st.session_state.monitoring = False
        st.session_state.data = deque(maxlen=100)
        st.session_state.fading_events = []        
        st.session_state.stop_event = None
        st.session_state.monitor_thread = None
        st.session_state.monitor_result = None
        st.session_state.RSSI_RANGE = RSSI_RANGE
        st.session_state.MONITOR_DURATION = MONITOR_DURATION
        st.session_state.MONITOR_INTERVAL = MONITOR_INTERVAL

    st.sidebar.header("Configuracoes")
    
    rssi_range_input = st.sidebar.number_input(
        "Faixa de variacao do RSSI (dBm)",
        min_value=1,
        max_value=50,
        value=st.session_state.RSSI_RANGE
    )
    
    duration_input = st.sidebar.number_input(
        "Duracao do monitoramento (segundos)",
        min_value=10,
        max_value=600,
        value=st.session_state.MONITOR_DURATION
    )
    
    interval_input = st.sidebar.number_input(
        "Intervalo entre coletas (segundos)",
        min_value=1,
        max_value=10,
        value=st.session_state.MONITOR_INTERVAL
    )

    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("Iniciar" if not st.session_state.monitoring else "Parar", 
                     use_container_width=True, type="primary"):
            if not st.session_state.monitoring:
                st.session_state.monitoring = True
                st.session_state.RSSI_RANGE = rssi_range_input
                st.session_state.MONITOR_DURATION = duration_input
                st.session_state.MONITOR_INTERVAL = interval_input
                st.success("Monitoramento iniciado")
                
                result = monitor_rssi(
                    duration=st.session_state.MONITOR_DURATION,
                    interval=st.session_state.MONITOR_INTERVAL,
                    rssi_range=st.session_state.RSSI_RANGE
                )
                st.session_state.monitor_result = result
                st.session_state.monitoring = False
                st.rerun()
            else:
                if st.session_state.stop_event:
                    st.session_state.stop_event.set()
                st.session_state.monitoring = False
                st.info("Monitoramento interrompido")
    
    with col2:
        if st.button("Limpar Dados", use_container_width=True):
            st.session_state.data.clear()
            st.session_state.fading_events.clear()
            st.session_state.monitor_result = None
            if 'analyses' in st.session_state:
                st.session_state.analyses = {}
            st.success("Dados limpos")
            st.rerun()
    
    with col3:
        status = "Monitorando" if st.session_state.monitoring else "Parado"
        st.metric("Status", status)

    if st.session_state.monitor_result:
        result = st.session_state.monitor_result
        rssi_history = result['Historico de coletas']
        fading_events = result['Eventos de Fading']
        
        st.markdown("---")
        st.subheader("Resumo")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Duracao", f"{result['Tempo total de monitoramento']}s")
        with col2:
            st.metric("Coletas", result['Coletas realizadas'])
        with col3:
            st.metric("Eventos", result['Numero eventos'])
        with col4:
            if rssi_history:
                rssi_medio = sum(h['rssi'] for h in rssi_history) / len(rssi_history)
                st.metric("Media de RSSI", f"{rssi_medio:.1f} dBm")
        
        st.markdown("---")
        st.subheader("Visualizando os dados do R-D+IA")
        
        fig_linha = inline_graph(rssi_history, fading_events)
        if fig_linha:
            st.plotly_chart(fig_linha, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_hist = history(rssi_history)
            if fig_hist:
                st.plotly_chart(fig_hist, use_container_width=True)
        
        with col2:
            fig_pizza = pie_graph(fading_events)
            if fig_pizza:
                st.plotly_chart(fig_pizza, use_container_width=True)
        
        if fading_events:
            fig_barras = bars(fading_events)
            if fig_barras:
                st.plotly_chart(fig_barras, use_container_width=True)
        
        if fading_events:
            st.markdown("---")
            st.subheader("Detalhes dos eventos")
            df_events = pd.DataFrame(fading_events)
            st.dataframe(df_events, use_container_width=True)
        
        ia_section(fading_events, rssi_history)

    if st.session_state.monitoring:
        time.sleep(1)
        st.rerun()

if __name__ == "__main__":
    dashboard()