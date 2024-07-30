#!/usr/bin/env python3

import sys
import time
import pyvisa
import serial
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel, QComboBox

class ESP300:
    def __init__(self, adapter, timeout):
        self.adapter = adapter
        self.timeout = timeout * 60  # Converte minutos para segundos
        if isinstance(adapter, serial.Serial):
            self.adapter.timeout = self.timeout
        else:
            self.adapter.timeout = self.timeout * 1000  # Converte segundos para milissegundos
        self.resource = adapter

    def query(self, command):
        try:
            if isinstance(self.resource, serial.Serial):
                command = command if command.endswith('\r') else command + '\r'
                self.resource.write(command.encode())
                time.sleep(0.1)  # Pequeno atraso para permitir a resposta
                response = self.resource.read_until(b'\r\n').decode().strip()
            else:
                response = self.resource.query(command)  # Enviar comando com terminação adequada
            return response
        except (pyvisa.errors.VisaIOError, serial.SerialException) as e:
            print(f"Erro ao enviar comando: {e}")
            self.reconnect()
            return None

    def write(self, command):
        try:
            if isinstance(self.resource, serial.Serial):
                command = command if command.endswith('\r') else command + '\r'
                self.resource.write(command.encode())
            else:
                self.resource.write(command)  # Enviar comando com terminação adequada
        except (pyvisa.errors.VisaIOError, serial.SerialException) as e:
            print(f"Erro ao enviar comando: {e}")
            self.reconnect()

    def move_to(self, axis, position):
        status = self.query(f"{axis}MD?")
        if status is None:
            print("Erro ao verificar o status do eixo.")
            return
        if status == "1":  # O eixo está parado
            self.write(f"{axis}PA{position}")
            print(f"Comando {axis}PA{position} enviado.")
            self.write(f"{axis}WS")  # Comando para esperar até o motor parar
            print(f"Comando {axis}WS enviado.")
        else:
            print(f"O eixo {axis} está em movimento. Não é possível enviar o comando de movimento.")

    def move_relative(self, axis, increment):
        status = self.query(f"{axis}MD?")
        if status is None:
            print("Erro ao verificar o status do eixo.")
            return
        if status == "1":  # O eixo está parado
            self.write(f"{axis}PR{increment}")
            print(f"Comando {axis}PR{increment} enviado.")
            self.write(f"{axis}WS")  # Comando para esperar até o motor parar
            print(f"Comando {axis}WS enviado.")
        else:
            print(f"O eixo {axis} está em movimento. Não é possível enviar o comando de movimento relativo.")

    def get_position(self, axis):
        return self.query(f"{axis}TP?")

    def execute_command(self, command):
        return self.query(command)

    def reconnect(self):
        print("Tentando reconectar...")
        try:
            if isinstance(self.resource, serial.Serial):
                self.resource.close()
                time.sleep(2)
                self.resource.open()
            else:
                self.resource.close()
                time.sleep(2)
                self.resource.open()
            print("Reconexão realizada.")
            # Reconfigura o timeout após reconectar
            self.adapter.timeout = self.timeout if isinstance(self.resource, serial.Serial) else self.timeout * 1000
        except Exception as e:
            print(f"Erro ao tentar reconectar: {e}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Controle do ESP300")
        self.setGeometry(100, 100, 400, 400)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.connection_label = QLabel("Escolha o método de conexão:")
        self.layout.addWidget(self.connection_label)

        self.connection_combo = QComboBox()
        self.connection_combo.addItem("Serial (/dev/ttyUSB0)")
        self.connection_combo.addItem("GPIB (GPIB0::5::INSTR)")
        self.layout.addWidget(self.connection_combo)

        self.connect_button = QPushButton("Conectar")
        self.connect_button.clicked.connect(self.connect_to_device)
        self.layout.addWidget(self.connect_button)

        self.axis_label = QLabel("Número do eixo:")
        self.layout.addWidget(self.axis_label)

        self.axis_input = QLineEdit()
        self.axis_input.setText("1")  # Inicializa com o número do eixo 1
        self.layout.addWidget(self.axis_input)

        self.position_label = QLabel("Posição:")
        self.layout.addWidget(self.position_label)

        self.position_input = QLineEdit()
        self.layout.addWidget(self.position_input)

        self.move_to_button = QPushButton("Mover para a posição")
        self.move_to_button.clicked.connect(self.move_to_position)
        self.layout.addWidget(self.move_to_button)

        self.move_relative_label = QLabel("Movimento relativo:")
        self.layout.addWidget(self.move_relative_label)

        self.move_relative_input = QLineEdit()
        self.layout.addWidget(self.move_relative_input)

        self.move_relative_button = QPushButton("Mover relativo")
        self.move_relative_button.clicked.connect(self.move_relative_position)
        self.layout.addWidget(self.move_relative_button)

        self.current_position_label = QLabel("Posição atual do eixo:")
        self.layout.addWidget(self.current_position_label)

        self.current_position_output = QLabel("")
        self.layout.addWidget(self.current_position_output)

        self.update_position_button = QPushButton("Atualizar posição")
        self.update_position_button.clicked.connect(self.update_position)
        self.layout.addWidget(self.update_position_button)

        self.custom_command_label = QLabel("Comando personalizado:")
        self.layout.addWidget(self.custom_command_label)

        self.custom_command_input = QLineEdit()
        self.layout.addWidget(self.custom_command_input)

        self.send_command_button = QPushButton("Enviar comando")
        self.send_command_button.clicked.connect(self.send_custom_command)
        self.layout.addWidget(self.send_command_button)

        self.timeout_label = QLabel("Timeout de desconexão (minutos):")
        self.layout.addWidget(self.timeout_label)

        self.timeout_input = QLineEdit()
        self.timeout_input.setText("20")  # Valor padrão de 20 minutos
        self.layout.addWidget(self.timeout_input)

    def connect_to_device(self):
        choice = self.connection_combo.currentIndex()
        timeout = int(self.timeout_input.text())
        try:
            if choice == 0:
                port = "/dev/ttyUSB0"
                self.adapter = serial.Serial(port, baudrate=19200, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=3, rtscts=True)
            elif choice == 1:
                port = "GPIB0::5::INSTR"
                self.adapter = pyvisa.ResourceManager().open_resource(port)
                self.adapter.write_termination = '\r'
                self.adapter.read_termination = '\r\n'
            else:
                print("Escolha inválida.")
                return

            self.esp300 = ESP300(self.adapter, timeout)
            print("Conectado ao ESP300.")
            self.update_position()
        except Exception as e:
            print(f"Erro ao conectar ao ESP300: {e}")

    def move_to_position(self):
        if not hasattr(self, 'esp300'):
            print("Erro: Não conectado ao ESP300.")
            return

        try:
            axis = self.axis_input.text()
            position = float(self.position_input.text())
            self.esp300.move_to(axis, position)
            self.update_position()
        except Exception as e:
            print(f"Erro: {e}")

    def move_relative_position(self):
        if not hasattr(self, 'esp300'):
            print("Erro: Não conectado ao ESP300.")
            return

        try:
            axis = self.axis_input.text()
            increment = float(self.move_relative_input.text())
            self.esp300.move_relative(axis, increment)
            self.update_position()
        except Exception as e:
            print(f"Erro: {e}")

    def update_position(self):
        if not hasattr(self, 'esp300'):
            print("Erro: Não conectado ao ESP300.")
            return

        try:
            axis = self.axis_input.text()
            position = self.esp300.get_position(axis)
            if position is not None:
                self.current_position_output.setText(f"{position}")
        except Exception as e:
            print(f"Erro ao atualizar a posição: {e}")

    def send_custom_command(self):
        if not hasattr(self, 'esp300'):
            print("Erro: Não conectado ao ESP300.")
            return

        try:
            command = self.custom_command_input.text()
            response = self.esp300.execute_command(command)
            if response is not None:
                print(f"Resposta do comando: {response}")
        except Exception as e:
            print(f"Erro ao enviar comando: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

