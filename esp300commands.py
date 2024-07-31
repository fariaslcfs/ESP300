#!/usr/bin/python3

import time

import pyvisa
from pymeasure.instruments import Instrument
from pymeasure.adapters import VISAAdapter, SerialAdapter

class ESP300(Instrument):
    def __init__(self, adapter, **kwargs):
        super().__init__(
            adapter,
            "Newport ESP300 Motion Controller",
            includeSCPI=False,
            **kwargs
        )

    def move_to(self, axis, position):
        try:
            self.write(f"{axis}PA{position}")
            self.write(f"{axis}WS")
        except Exception as e:
            print(f"Erro ao mover o eixo {axis} para a posição {position}: {e}")

    def move_by(self, axis, distance):
        try:
            self.write(f"{axis}PR{distance}")
        except Exception as e:
            print(f"Erro ao mover o eixo {axis} por {distance}: {e}")

    def stop(self, axis):
        try:
            self.write(f"{axis}ST")
        except Exception as e:
            print(f"Erro ao parar o eixo {axis}: {e}")

    def get_position(self, axis):
        try:
            return self.ask(f"{axis}TP")
        except Exception as e:
            print(f"Erro ao consultar a posição do eixo {axis}: {e}")
            return None

    def set_velocity(self, axis, velocity):
        try:
            self.write(f"{axis}VA{velocity}")
        except Exception as e:
            print(f"Erro ao definir a velocidade do eixo {axis} para {velocity}: {e}")

    def get_velocity(self, axis):
        try:
            return self.ask(f"{axis}VA?")
        except Exception as e:
            print(f"Erro ao consultar a velocidade do eixo {axis}: {e}")
            return None

    def zero_position(self, axis):
        try:
            self.write(f"{axis}DH0")
        except Exception as e:
            print(f"Erro ao zerar a posição do eixo {axis}: {e}")

    def set_acceleration(self, axis, acceleration):
        try:
            self.write(f"{axis}AC{acceleration}")
        except Exception as e:
            print(f"Erro ao definir a aceleração do eixo {axis} para {acceleration}: {e}")

    def get_acceleration(self, axis):
        try:
            return self.ask(f"{axis}AC?")
        except Exception as e:
            print(f"Erro ao consultar a aceleração do eixo {axis}: {e}")
            return None

    def set_deceleration(self, axis, deceleration):
        try:
            self.write(f"{axis}AG{deceleration}")
        except Exception as e:
            print(f"Erro ao definir a desaceleração do eixo {axis} para {deceleration}: {e}")

    def get_deceleration(self, axis):
        try:
            return self.ask(f"{axis}AG?")
        except Exception as e:
            print(f"Erro ao consultar a desaceleração do eixo {axis}: {e}")
            return None

    def enable_axis(self, axis):
        try:
            self.write(f"{axis}MO")
        except Exception as e:
            print(f"Erro ao habilitar o eixo {axis}: {e}")

    def disable_axis(self, axis):
        try:
            self.write(f"{axis}MF")
        except Exception as e:
            print(f"Erro ao desabilitar o eixo {axis}: {e}")

def main():
    print("Escolha o método de conexão:")
    print("1. Serial (padrão: /dev/ttyUSB0)")
    print("2. GPIB (padrão: GPIB0::5::INSTR)")
    choice = input("Digite o número correspondente à sua escolha (padrão é 1): ")

    if choice == "1" or choice == "":
        port = "/dev/ttyUSB0"
        adapter = SerialAdapter(port)
    elif choice == "2":
        port = "GPIB0::5::INSTR"
        adapter = VISAAdapter(port)
    else:
        print("Escolha inválida. Encerrando o programa.")
        return

    try:
        esp300 = ESP300(adapter)
    except Exception as e:
        print(f"Erro ao criar a instância do ESP300: {e}")
        return

    try:
        # Exemplo de uso
        esp300.enable_axis(1)
        esp300.move_to(1, 10)  # Move o eixo 1 para a posição 10
        time.sleep(0.1)
        position = esp300.get_position(1)
        if position is not None:
            print(f"Posição atual do eixo 1: {position}")
        #esp300.disable_axis(1)
    except Exception as e:
        print(f"Erro durante a operação com o ESP300: {e}")

if __name__ == "__main__":
    main()
