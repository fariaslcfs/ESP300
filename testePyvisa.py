#!/usr/bin/env python3

import time
import pyvisa

def test_gpib_commands():
    try:
        # Cria o gerenciador de recursos
        rm = pyvisa.ResourceManager()

        # Abre o recurso GPIB
        resource = rm.open_resource("GPIB0::5::INSTR")

        # Define as terminações de escrita e leitura
        resource.write_termination = '\r'
        resource.read_termination = '\r\n'

        print("Conectado ao GPIB.")

        # Testa comandos de consulta
        for i in range(4):
            response = resource.query("*IDN?")
            print(f"Resposta *IDN?: {response}")
            time.sleep(1)

        # Testa comandos de controle
        for i in range(4):
            resource.write("1PR3")
            print("Comando 1PR3 enviado.")
            time.sleep(1)  # Aguarde para ver se o comando é processado

        # Consulta e imprime a posição atual
        for i in range(4):
            position = resource.query("1TP?")
            time.sleep(1)
            print(f"Posição atual do eixo 1: {position}")

    except pyvisa.errors.VisaIOError as e:
        print(f"Erro de comunicação: {e}")

if __name__ == "__main__":
    test_gpib_commands()
