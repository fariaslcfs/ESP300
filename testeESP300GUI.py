#!/usr/bin/env python3

import sys
import time
import pyvisa
import serial
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QComboBox, QFrame, QFormLayout
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
                time.sleep(1)  # Atraso aumentado para permitir o processamento do comando
                response = self.resource.read_until(b'\r\n').decode().strip()
            else:
                response = self.resource.query(command)
            return response
        except (pyvisa.errors.VisaIOError, serial.SerialException) as e:
            print(f"Erro ao enviar comando: {e}")
            self.reconnect()
            return None
        except Exception as e:
            print(f"Erro inesperado: {e}")
            self.reconnect()
            return None

    def write(self, command):
        try:
            if isinstance(self.resource, serial.Serial):
                command = command if command.endswith('\r') else command + '\r'
                self.resource.write(command.encode())
            else:
                self.resource.write(command)
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
        self.setGeometry(200, 200, 1000, 450)  # Ajustado o tamanho da janela para ser menor

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Seção geral
        self.general_frame = QFrame()
        self.general_frame.setStyleSheet("background-color: lightgray;")  # Cor de fundo do frame geral
        self.general_frame.setFrameShape(QFrame.StyledPanel)
        
        # Defina altura fixa e ajuste o layout
        self.general_frame.setFixedHeight(160)  # Definir uma altura fixa para o frame geral
        self.general_layout = QVBoxLayout()
        self.general_layout.setSpacing(2)  # Reduz o espaçamento entre widgets
        self.general_layout.setContentsMargins(2, 2, 2, 2)  # Ajusta as margens ao redor do layout
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

        # Novo rótulo para status de conexão
        self.status_label = QLabel("Status de Conexão: Desconectado")
        self.general_layout.addWidget(self.status_label)

        # Layout horizontal para os frames dos eixos
        self.axis_frame_layout = QHBoxLayout()
        self.layout.addLayout(self.axis_frame_layout)
        self.layout.addStretch()  # Adiciona um espaço flexível no final do layout

        # Seção dos eixos
        self.axis_frame1 = QFrame()
        self.axis_frame1.setStyleSheet("background-color: #e0f7e0;")  # Verde claro
        self.axis_frame1.setFrameShape(QFrame.StyledPanel)
        self.axis_layout1 = QFormLayout()
        self.axis_frame1.setLayout(self.axis_layout1)
        self.axis_frame_layout.addWidget(self.axis_frame1)

        self.axis1_position_label = QLabel("Posição:")
        self.axis1_position_input = QLineEdit()
        self.axis1_position_input.setFixedWidth(120)  # Ajuste a largura para menor
        self.axis1_move_to_button = QPushButton("Mover para a posição")
        self.axis1_move_to_button.clicked.connect(self.move_to_position_axis1)
        self.axis1_move_to_button.setStyleSheet("background-color: lightgray;")

        self.axis1_move_relative_label = QLabel("Movimento relativo:")
        self.axis1_move_relative_input = QLineEdit()
        self.axis1_move_relative_input.setFixedWidth(120)  # Ajuste a largura para menor
        self.axis1_move_relative_button = QPushButton("Mover relativo")
        self.axis1_move_relative_button.clicked.connect(self.move_relative_position_axis1)
        self.axis1_move_relative_button.setStyleSheet("background-color: lightgray;")

        self.axis1_current_position_label = QLabel("Posição atual do eixo:")
        self.axis1_current_position_output = QLabel("")
        self.axis1_update_position_button = QPushButton("Atualizar posição")
        self.axis1_update_position_button.clicked.connect(self.update_position_axis1)
        self.axis1_update_position_button.setStyleSheet("background-color: lightgray;")

        self.axis1_custom_command_label = QLabel("Comando personalizado:")
        self.axis1_custom_command_input = QLineEdit()
        self.axis1_custom_command_input.setFixedWidth(120)  # Ajuste a largura para menor
        self.axis1_send_command_button = QPushButton("Enviar comando")
        self.axis1_send_command_button.clicked.connect(self.send_custom_command_axis1)
        self.axis1_send_command_button.setStyleSheet("background-color: lightgray;")

        self.axis1_command_output = QLabel("")

        # Adiciona widgets ao layout do eixo 1
        self.axis_layout1.addRow(self.axis1_position_label, self.axis1_position_input)
        self.axis_layout1.addRow(self.axis1_move_to_button)
        self.axis_layout1.addRow(self.axis1_move_relative_label, self.axis1_move_relative_input)
        self.axis_layout1.addRow(self.axis1_move_relative_button)
        self.axis_layout1.addRow(self.axis1_current_position_label, self.axis1_current_position_output)
        self.axis_layout1.addRow(self.axis1_update_position_button)
        self.axis_layout1.addRow(self.axis1_custom_command_label, self.axis1_custom_command_input)
        self.axis_layout1.addRow(self.axis1_send_command_button)
        self.axis_layout1.addRow(self.axis1_command_output)

        self.axis_frame2 = QFrame()
        self.axis_frame2.setStyleSheet("background-color: #e0f7e0;")  # Verde claro
        self.axis_frame2.setFrameShape(QFrame.StyledPanel)
        self.axis_layout2 = QFormLayout()
        self.axis_frame2.setLayout(self.axis_layout2)
        self.axis_frame_layout.addWidget(self.axis_frame2)

        self.axis2_position_label = QLabel("Posição:")
        self.axis2_position_input = QLineEdit()
        self.axis2_position_input.setFixedWidth(120)  # Ajuste a largura para menor
        self.axis2_move_to_button = QPushButton("Mover para a posição")
        self.axis2_move_to_button.clicked.connect(self.move_to_position_axis2)
        self.axis2_move_to_button.setStyleSheet("background-color: lightgray;")

        self.axis2_move_relative_label = QLabel("Movimento relativo:")
        self.axis2_move_relative_input = QLineEdit()
        self.axis2_move_relative_input.setFixedWidth(120)  # Ajuste a largura para menor
        self.axis2_move_relative_button = QPushButton("Mover relativo")
        self.axis2_move_relative_button.clicked.connect(self.move_relative_position_axis2)
        self.axis2_move_relative_button.setStyleSheet("background-color: lightgray;")

        self.axis2_current_position_label = QLabel("Posição atual do eixo:")
        self.axis2_current_position_output = QLabel("")
        self.axis2_update_position_button = QPushButton("Atualizar posição")
        self.axis2_update_position_button.clicked.connect(self.update_position_axis2)
        self.axis2_update_position_button.setStyleSheet("background-color: lightgray;")

        self.axis2_custom_command_label = QLabel("Comando personalizado:")
        self.axis2_custom_command_input = QLineEdit()
        self.axis2_custom_command_input.setFixedWidth(120)  # Ajuste a largura para menor
        self.axis2_send_command_button = QPushButton("Enviar comando")
        self.axis2_send_command_button.clicked.connect(self.send_custom_command_axis2)
        self.axis2_send_command_button.setStyleSheet("background-color: lightgray;")

        self.axis2_command_output = QLabel("")

        # Adiciona widgets ao layout do eixo 2
        self.axis_layout2.addRow(self.axis2_position_label, self.axis2_position_input)
        self.axis_layout2.addRow(self.axis2_move_to_button)
        self.axis_layout2.addRow(self.axis2_move_relative_label, self.axis2_move_relative_input)
        self.axis_layout2.addRow(self.axis2_move_relative_button)
        self.axis_layout2.addRow(self.axis2_current_position_label, self.axis2_current_position_output)
        self.axis_layout2.addRow(self.axis2_update_position_button)
        self.axis_layout2.addRow(self.axis2_custom_command_label, self.axis2_custom_command_input)
        self.axis_layout2.addRow(self.axis2_send_command_button)
        self.axis_layout2.addRow(self.axis2_command_output)

        self.controller = None

    def connect_to_device(self):
        try:
            connection_type = self.connection_combo.currentText()
            if connection_type == "Serial (/dev/ttyUSB0)":
                port = "/dev/ttyUSB0"
                self.controller = ESP300(serial.Serial(port, baudrate=19200, timeout=1), timeout=20)
            elif connection_type == "GPIB (GPIB0::5::INSTR)":
                rm = pyvisa.ResourceManager()
                resource = rm.open_resource("GPIB0::5::INSTR")
                self.controller = ESP300(resource, timeout=20)
            else:
                self.controller = None
                self.status_label.setText("Status de Conexão: Método de conexão não reconhecido.")
                return

            self.controller.query("*IDN?")
            self.status_label.setText("Status de Conexão: Conectado com sucesso.")
        except Exception as e:
            self.status_label.setText(f"Status de Conexão: Erro ao conectar: {e}")

    def move_to_position_axis1(self):
        position = self.axis1_position_input.text()
        if not position:
            self.axis1_command_output.setText("Posição não pode estar vazia.")
            return

        try:
            self.controller.move_to("1", position)
            self.axis1_current_position_output.setText(f"Movendo eixo 1 para a posição {position}.")
        except Exception as e:
            self.axis1_command_output.setText(f"Erro: {e}")

    def move_relative_position_axis1(self):
        increment = self.axis1_move_relative_input.text()
        if not increment:
            self.axis1_command_output.setText("Incremento não pode estar vazio.")
            return

        try:
            self.controller.move_relative("1", increment)
            self.axis1_current_position_output.setText(f"Movendo eixo 1 relativo {increment}.")
        except Exception as e:
            self.axis1_command_output.setText(f"Erro: {e}")

    def update_position_axis1(self):
        try:
            position = self.controller.get_position("1")
            self.axis1_current_position_output.setText(f"Posição atual do eixo 1: {position}")
        except Exception as e:
            self.axis1_current_position_output.setText(f"Erro: {e}")

    def send_custom_command_axis1(self):
        command = self.axis1_custom_command_input.text()
        if not command:
            self.axis1_command_output.setText("Comando não pode estar vazio.")
            return

        try:
            response = self.controller.execute_command(command)
            if response is None:
                self.axis1_command_output.setText("Nenhuma resposta recebida.")
            else:
                self.axis1_command_output.setText(response)
        except Exception as e:
            self.axis1_command_output.setText(f"Erro: {e}")
            print(f"Erro ao enviar comando personalizado: {e}")

    def move_to_position_axis2(self):
        position = self.axis2_position_input.text()
        if not position:
            self.axis2_command_output.setText("Posição não pode estar vazia.")
            return

        try:
            self.controller.move_to("2", position)
            self.axis2_current_position_output.setText(f"Movendo eixo 2 para a posição {position}.")
        except Exception as e:
            self.axis2_command_output.setText(f"Erro: {e}")

    def move_relative_position_axis2(self):
        increment = self.axis2_move_relative_input.text()
        if not increment:
            self.axis2_command_output.setText("Incremento não pode estar vazio.")
            return

        try:
            self.controller.move_relative("2", increment)
            self.axis2_current_position_output.setText(f"Movendo eixo 2 relativo {increment}.")
        except Exception as e:
            self.axis2_command_output.setText(f"Erro: {e}")

    def update_position_axis2(self):
        try:
            position = self.controller.get_position("2")
            self.axis2_current_position_output.setText(f"Posição atual do eixo 2: {position}")
        except Exception as e:
            self.axis2_current_position_output.setText(f"Erro: {e}")

    def send_custom_command_axis2(self):
        command = self.axis2_custom_command_input.text()
        if not command:
            self.axis2_command_output.setText("Comando não pode estar vazio.")
            return

        try:
            response = self.controller.execute_command(command)
            if response is None:
                self.axis2_command_output.setText("Nenhuma resposta recebida.")
            else:
                self.axis2_command_output.setText(response)
        except Exception as e:
            self.axis2_command_output.setText(f"Erro: {e}")
            print(f"Erro ao enviar comando personalizado: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
