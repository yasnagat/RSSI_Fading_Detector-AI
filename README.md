# O que é RSSI
O RSSI (Received Signal Strength Indicator) é uma medida técnica que indica o nível de potência de um sinal de rádio recebido por um dispositivo.

Unidade de Medida: É expresso em dBm (decibéis por miliwatt).

Escala: Quanto mais próximo de 0 dBm, mais forte é o sinal (ex: -30 dBm é excelente).

Utilidade: No seu projeto, o RSSI é o dado fundamental para monitorar a estabilidade da conexão sem fio em tempo real.

# Definição de Evento de Fading
O Fading (desvanecimento) refere-se às variações na atenuação que um sinal sofre ao se propagar pelo ar. Em sistemas de comunicação sem fio, um "evento de fading" ocorre quando a intensidade do sinal oscila devido a fatores externos.

Neste software, detectamos dois tipos de eventos baseados no diferencial (delta) entre medições:

Fading Positivo (Aumento): Quando o sinal ganha intensidade rapidamente.

Fading Negativo (Queda): Quando o sinal sofre uma perda brusca de potência, geralmente causada por obstáculos físicos ou interferência de múltiplos caminhos.

# Instalação e Requisitos
Para garantir que todas as dependências do software funcionem corretamente, utilize o arquivo requirements.txt.

#### Como usar o requirements.txt:
1. Crie um ambiente virtual:<br/>python3 -m venv venv <br/>
source venv/bin/activate

2. Instale as dependências com o seguinte comando:<br/> pip install -r requirements.txt
