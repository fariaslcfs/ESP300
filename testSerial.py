#!/usr/bin/env python3

import serial
import time

def test_serial(port):
    try:
        # Inicializa a conexão serial com handshake CTS/RTS
        ser = serial.Serial(
            port,
            baudrate=19200,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=1,
            rtscts=True  # Habilita o handshake CTS/RTS
        )
        
        # Exibe a configuração atual da porta serial
        print(f"Port: {ser.portstr}")
        print(f"Baudrate: {ser.baudrate}")
        print(f"Bytesize: {ser.bytesize}")
        print(f"Parity: {ser.parity}")
        print(f"Stopbits: {ser.stopbits}")
        print(f"Handshake: {'RTS/CTS' if ser.rtscts else 'None'}")
        
        # Limpa o buffer de entrada
        ser.flushInput()
        
        # Envia um comando para o dispositivo com terminação \r
        command = 'VE\r'  # Exemplo de comando com terminação \r
        print(f"Enviando: {command}")
        ser.write(command.encode())
        
        # Adiciona um atraso para garantir que o dispositivo tenha tempo de resposta
        time.sleep(1)
        
        # Lê a resposta do dispositivo, que termina com \r\n
        response = b''
        while not response.endswith(b'\r\n'):
            response += ser.read(1)
        
        response = response.decode('ascii', errors='ignore').strip()  # Decodifica e remove espaços em branco
        print(f"Resposta: {response}")
        
        # Fecha a conexão
        ser.close()
    except Exception as e:
        print(f"Erro: {e}")

# Substitua '/dev/ttyUSB0' pela porta correta se necessário
test_serial('/dev/ttyUSB0')
