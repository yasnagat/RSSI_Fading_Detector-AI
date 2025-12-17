import subprocess as sp
import time
from datetime import datetime, timedelta

RSSI_THRESHOLD = 5
MONITOR_INTERVAL = 2
MONITOR_DURATION = 10

def get_rssi():
    try:
        result_cmd = sp.run(['netsh', 'wlan', 'show', 'interfaces'], capture_output=True, text=True, timeout=2)
        output = result_cmd.stdout

        result = {'rssi': None, 'banda': None,'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

        for line in output.splitlines():
            line = line.strip()

            if 'rssi' in line.lower() and ':' in line:
                    rssi_str = line.split(':')[1].strip()
                    result['rssi'] = int(rssi_str)

            elif 'banda' in line.lower() and ':' in line:
                    banda_str = line.split(':')[1].strip()
                    result['banda'] = banda_str

        return result
    
    except sp.TimeoutExpired:
        print("Timeout ao executar comando netsh")
        return None

def monitor_rssi(duration=MONITOR_DURATION, interval=MONITOR_INTERVAL):

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

                if abs(fading_test_detection) >= RSSI_THRESHOLD:
                    fading_event = {
                        'Data e hora do evento': data['timestamp'],
                        'RSSI anterior': previous_rssi,
                        'RSSI atual': current_rssi,
                        'Diferença de Sinal': fading_test_detection,
                        'Tipo': 'queda' if fading_test_detection < 0 else 'aumento'
                    }

                    fading_events.append(fading_event)
                    
                    print(f"⚠️  [ #{collect_nb}] Evento de fading identificado")
                    print(f"    {previous_rssi} dBm → {current_rssi} dBm ({fading_test_detection:+d} dBm)")
                else:
                    print(f"✅ [ #{collect_nb}] RSSI: {current_rssi} dBm (RSSI estável)")
            else:
                print(f"✅ [#{collect_nb}] RSSI inicial: {current_rssi} dBm")
            
            previous_rssi = current_rssi
        else:
            print(f"❌ [ #{collect_nb}] Erro ao coletar dados. Tente novamente")
        
        print(f"⏱️  Tempo restante: {time_limit:.0f}s\n")
        
        if datetime.now() < end_time:
            time.sleep(interval)
    
    final_result = {
        'Tempo de monitoramento': duration,
        'Coletas bem sucedidas': len(rssi_history),
        'Nº de eventos de fading': len(fading_events),        
        'Eventos de Fading': fading_events,
        'Histórico de coletas': rssi_history
    }

    return final_result

if __name__ == "__main__":
    resultado = monitor_rssi()
    print("Relatório Final:", resultado)
