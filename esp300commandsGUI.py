#!/usr/bin/env python3

import sys
import time
import pyvisa
import serial
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QComboBox, QFrame
from PyQt5.QtCore import Qt

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
        self.write(f"{axis}PA{position}")
        print(f"Comando {axis}PA{position} enviado.")
        self.write(f"{axis}WS")  # Comando para esperar até o motor parar
        print(f"Comando {axis}WS enviado.")

    def move_relative(self, axis, increment):
        self.write(f"{axis}PR{increment}")
        print(f"Comando {axis}PR{increment} enviado.")
        self.write(f"{axis}WS")  # Comando para esperar até o motor parar
        print(f"Comando {axis}WS enviado.")

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
        except Exception as e:
            print(f"Erro ao tentar reconectar: {e}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Controle do ESP300")
        self.setGeometry(100, 100, 800, 500)  # Tamanho da janela ajustado

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Seção geral
        self.general_frame = QFrame()
        self.general_frame.setStyleSheet("background-color: lightgray;")  # Cor de fundo do frame geral
        self.general_layout = QVBoxLayout()
        self.general_frame.setLayout(self.general_layout)
        self.layout.addWidget(self.general_frame)

        self.connection_label = QLabel("Escolha o método de conexão:")
        self.general_layout.addWidget(self.connection_label)

        self.connection_combo = QComboBox()
        self.connection_combo.addItem("Serial (/dev/ttyUSB0)")
        self.connection_combo.addItem("GPIB (GPIB0::5::INSTR)")
        self.general_layout.addWidget(self.connection_combo)

        self.connect_button = QPushButton("Conectar")
        self.connect_button.setStyleSheet("background-color: lightgray;")
        self.connect_button.clicked.connect(self.connect_to_device)
        self.general_layout.addWidget(self.connect_button)

        self.timeout_label = QLabel("Timeout de desconexão (minutos):")
        self.general_layout.addWidget(self.timeout_label)

        self.timeout_input = QLineEdit()
        self.timeout_input.setText("20")  # Valor padrão de 20 minutos
        self.timeout_input.setStyleSheet("background-color: lightgray;")
        self.general_layout.addWidget(self.timeout_input)

        # Seção dos eixos
        self.axis_frame = QFrame()
        self.axis_frame.setStyleSheet("background-color: lightgray;")  # Cor de fundo do frame dos eixos
        self.axis_frame.setFrameShape(QFrame.StyledPanel)
        self.axis_layout = QHBoxLayout()  # Layout horizontal para os eixos
        self.axis_frame.setLayout(self.axis_layout)
        self.layout.addWidget(self.axis_frame)

        # Eixo 1
        self.axis_frame1 = QFrame()
        self.axis_frame1.setStyleSheet("background-color: #e0f7e0;")  # Verde claro
        self.axis_frame1.setFrameShape(QFrame.StyledPanel)
        self.axis_layout1 = QVBoxLayout()
        self.axis_frame1.setLayout(self.axis_layout1)
        self.axis_layout.addWidget(self.axis_frame1)

        self.axis1_label = QLabel("Eixo 1")
        self.axis_layout1.addWidget(self.axis1_label)

        self.axis1_position_label = QLabel("Posição:")
        self.axis1_position_label.setStyleSheet("padding-right: 5px;")
        self.axis_layout1.addWidget(self.axis1_position_label)

        self.axis1_position_input = QLineEdit()
        self.axis1_position_input.setStyleSheet("background-color: lightgray;")
        self.axis_layout1.addWidget(self.axis1_position_input)

        self.axis1_move_to_button = QPushButton("Mover para a posição")
        self.axis1_move_to_button.setStyleSheet("background-color: lightgray;")
        self.axis1_move_to_button.clicked.connect(self.move_to_position_axis1)
        self.axis_layout1.addWidget(self.axis1_move_to_button)

        self.axis1_move_relative_label = QLabel("Movimento relativo:")
        self.axis1_move_relative_label.setStyleSheet("padding-right: 5px;")
        self.axis_layout1.addWidget(self.axis1_move_relative_label)

        self.axis1_move_relative_input = QLineEdit()
        self.axis1_move_relative_input.setStyleSheet("background-color: lightgray;")
        self.axis_layout1.addWidget(self.axis1_move_relative_input)

        self.axis1_move_relative_button = QPushButton("Mover relativo")
        self.axis1_move_relative_button.setStyleSheet("background-color: lightgray;")
        self.axis1_move_relative_button.clicked.connect(self.move_relative_position_axis1)
        self.axis_layout1.addWidget(self.axis1_move_relative_button)

        self.axis1_current_position_label = QLabel("Posição atual do eixo:")
        self.axis_layout1.addWidget(self.axis1_current_position_label)

        self.axis1_current_position_output = QLabel("")
        self.axis_layout1.addWidget(self.axis1_current_position_output)

        self.axis1_update_position_button = QPushButton("Atualizar posição")
        self.axis1_update_position_button.setStyleSheet("background-color: lightgray;")
        self.axis1_update_position_button.clicked.connect(self.update_position_axis1)
        self.axis_layout1.addWidget(self.axis1_update_position_button)

        self.axis1_custom_command_label = QLabel("Comando personalizado:")
        self.axis1_custom_command_label.setStyleSheet("padding-right: 5px;")
        self.axis_layout1.addWidget(self.axis1_custom_command_label)

        self.axis1_custom_command_input = QLineEdit()
        self.axis1_custom_command_input.setStyleSheet("background-color: lightgray;")
        self.axis_layout1.addWidget(self.axis1_custom_command_input)

        self.axis1_send_command_button = QPushButton("Enviar comando")
        self.axis1_send_command_button.setStyleSheet("background-color: lightgray;")
        self.axis1_send_command_button.clicked.connect(self.send_custom_command_axis1)
        self.axis_layout1.addWidget(self.axis1_send_command_button)

        # Eixo 2
        self.axis_frame2 = QFrame()
        self.axis_frame2.setStyleSheet("background-color: #e0f7e0;")  # Verde claro
        self.axis_frame2.setFrameShape(QFrame.StyledPanel)
        self.axis_layout2 = QVBoxLayout()
        self.axis_frame2.setLayout(self.axis_layout2)
        self.axis_layout.addWidget(self.axis_frame2)

        self.axis2_label = QLabel("Eixo 2")
        self.axis_layout2.addWidget(self.axis2_label)

        self.axis2_position_label = QLabel("Posição:")
        self.axis2_position_label.setStyleSheet("padding-right: 5px;")
        self.axis_layout2.addWidget(self.axis2_position_label)

        self.axis2_position_input = QLineEdit()
        self.axis2_position_input.setStyleSheet("background-color: lightgray;")
        self.axis_layout2.addWidget(self.axis2_position_input)

        self.axis2_move_to_button = QPushButton("Mover para a posição")
        self.axis2_move_to_button.setStyleSheet("background-color: lightgray;")
        self.axis2_move_to_button.clicked.connect(self.move_to_position_axis2)
        self.axis_layout2.addWidget(self.axis2_move_to_button)

        self.axis2_move_relative_label = QLabel("Movimento relativo:")
        self.axis2_move_relative_label.setStyleSheet("padding-right: 5px;")
        self.axis_layout2.addWidget(self.axis2_move_relative_label)

        self.axis2_move_relative_input = QLineEdit()
        self.axis2_move_relative_input.setStyleSheet("background-color: lightgray;")
        self.axis_layout2.addWidget(self.axis2_move_relative_input)

        self.axis2_move_relative_button = QPushButton("Mover relativo")
        self.axis2_move_relative_button.setStyleSheet("background-color: lightgray;")
        self.axis2_move_relative_button.clicked.connect(self.move_relative_position_axis2)
        self.axis_layout2.addWidget(self.axis2_move_relative_button)

        self.axis2_current_position_label = QLabel("Posição atual do eixo:")
        self.axis_layout2.addWidget(self.axis2_current_position_label)

        self.axis2_current_position_output = QLabel("")
        self.axis_layout2.addWidget(self.axis2_current_position_output)

        self.axis2_update_position_button = QPushButton("Atualizar posição")
        self.axis2_update_position_button.setStyleSheet("background-color: lightgray;")
        self.axis2_update_position_button.clicked.connect(self.update_position_axis2)
        self.axis_layout2.addWidget(self.axis2_update_position_button)

        self.axis2_custom_command_label = QLabel("Comando personalizado:")
        self.axis2_custom_command_label.setStyleSheet("padding-right: 5px;")
        self.axis_layout2.addWidget(self.axis2_custom_command_label)

        self.axis2_custom_command_input = QLineEdit()
        self.axis2_custom_command_input.setStyleSheet("background-color: lightgray;")
        self.axis_layout2.addWidget(self.axis2_custom_command_input)

        self.axis2_send_command_button = QPushButton("Enviar comando")
        self.axis2_send_command_button.setStyleSheet("background-color: lightgray;")
        self.axis2_send_command_button.clicked.connect(self.send_custom_command_axis2)
        self.axis_layout2.addWidget(self.axis2_send_command_button)

        # Configura a conexão com o dispositivo
        self.device = None

    def connect_to_device(self):
        try:
            method = self.connection_combo.currentText()
            timeout = int(self.timeout_input.text())

            if method.startswith("Serial"):
                port = "/dev/ttyUSB0"  # Pode ser ajustado conforme necessário
                self.device = ESP300(serial.Serial(port, baudrate=19200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE), timeout)
            elif method.startswith("GPIB"):
                resource_name = "GPIB0::5::INSTR"  # Pode ser ajustado conforme necessário
                rm = pyvisa.ResourceManager()
                self.device = ESP300(rm.open_resource(resource_name), timeout)

            print("Conectado com sucesso.")
        except Exception as e:
            print(f"Erro ao conectar: {e}")

    def move_to_position_axis1(self):
        position = self.axis1_position_input.text()
        if position:
            self.device.move_to('1', position)

    def move_relative_position_axis1(self):
        increment = self.axis1_move_relative_input.text()
        if increment:
            self.device.move_relative('1', increment)

    def update_position_axis1(self):
        position = self.device.get_position('1')
        if position:
            self.axis1_current_position_output.setText(position)

    def send_custom_command_axis1(self):
        command = self.axis1_custom_command_input.text()
        if command:
            response = self.device.execute_command(command)
            print(f"Resposta do comando: {response}")

    def move_to_position_axis2(self):
        position = self.axis2_position_input.text()
        if position:
            self.device.move_to('2', position)

    def move_relative_position_axis2(self):
        increment = self.axis2_move_relative_input.text()
        if increment:
            self.device.move_relative('2', increment)

    def update_position_axis2(self):
        position = self.device.get_position('2')
        if position:
            self.axis2_current_position_output.setText(position)

    def send_custom_command_axis2(self):
        command = self.axis2_custom_command_input.text()
        if command:
            response = self.device.execute_command(command)
            print(f"Resposta do comando: {response}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

