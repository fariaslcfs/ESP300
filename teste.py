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
        self.timeout = timeout
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
                time.sleep(5)
                self.resource.open()
            print("Reconexão realizada.")
        except Exception as e:
            print(f"Erro ao tentar reconectar: {e}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Controle do ESP300")
        self.setGeometry(100, 100, 700, 450)  # Ajustado o tamanho da janela para permitir mais espaço

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)
        self.central_widget.setStyleSheet("background-color: #778899;")

        # Seção geral
        self.general_frame = QFrame()
        self.general_frame.setStyleSheet("background-color: #8FBC9F;")  # Cor de fundo do frame geral
        self.general_frame.setFrameShape(QFrame.StyledPanel)
        #self.general_frame.setFixedHeight(170)  # Ajustado para altura menor
        self.general_layout = QVBoxLayout()
        self.general_layout.setContentsMargins(2, 2, 2, 2)  # Margens menores
        self.general_layout.setSpacing(10)  # Espaçamento menor entre os widgets
        self.general_layout.setAlignment(Qt.AlignHCenter)
        self.general_frame.setLayout(self.general_layout)
        self.layout.addWidget(self.general_frame)

        self.connection_label = QLabel("MÉTODO DE CONEXÃO")
        self.connection_label.setAlignment(Qt.AlignHCenter)
        self.general_layout.addWidget(self.connection_label)

        self.connection_combo = QComboBox()
        self.connection_combo.setFixedHeight(25)
        self.connection_combo.setFixedWidth(250)
        self.connection_combo.setStyleSheet("background-color: white; ")
        self.connection_combo.addItem("Serial (/dev/ttyUSB0)")
        self.connection_combo.addItem("GPIB (GPIB0::5::INSTR)")
        self.general_layout.addWidget(self.connection_combo)

        self.connect_button = QPushButton("Conectar")
        self.connect_button.setFixedHeight(25)
        self.connect_button.setFixedWidth(250)
        self.connect_button.setStyleSheet("background-color: gray;")
        self.connect_button.clicked.connect(self.connect_to_device)
        self.general_layout.addWidget(self.connect_button)
       
        #self.timeout_label = QLabel("Timeout de desconexão (s):")
        #self.general_layout.addWidget(self.timeout_label)
        self.timeout_input = QLineEdit()
        self.timeout_input.setFixedHeight(25)
        self.timeout_input.setFixedWidth(250)
        self.timeout_input.setPlaceholderText("Insira o timeout em segunds (5)")
        self.timeout_input.setAlignment(Qt.AlignHCenter)
        #self.timeout_input.setText("5")  # Valor padrão de 5 segundos
        self.timeout_input.setStyleSheet("background-color: white;")
        self.general_layout.addWidget(self.timeout_input)

        self.connection_status_label = QLabel("Status da conexão: Não conectado")  # Inicializa com status de não conectado
        self.connection_status_label.setAlignment(Qt.AlignHCenter)
        self.general_layout.addWidget(self.connection_status_label)

        # Layout horizontal para os frames dos eixos
        self.axis_frame_layout = QHBoxLayout()
        self.layout.addLayout(self.axis_frame_layout)

        # Seção dos eixos
        self.create_axis_frame("EIXO 1\n", 1)
        self.create_axis_frame("EIXO 2\n", 2)

    def create_axis_frame(self, title, axis_number):
        axis_frame = QFrame()
        axis_frame.setStyleSheet("background-color: #8FBC9F;")  # Verde claro #e0f7e0
        axis_frame.setFrameShape(QFrame.StyledPanel)
        axis_layout = QVBoxLayout()
        axis_layout.setAlignment(Qt.AlignHCenter)
        axis_layout.setContentsMargins(10, 10, 10, 10)
        axis_layout.setSpacing(2)
        axis_frame.setLayout(axis_layout)
        self.axis_frame_layout.addWidget(axis_frame)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignHCenter)
        axis_layout.addWidget(title_label)

        position_label = QLabel("Posição")
        position_input = QLineEdit()
        position_input.setPlaceholderText("Insira a posição absoluta")
        position_input.setFixedHeight(25)
        position_input.setFixedWidth(250)
        position_input.setStyleSheet("background-color: white; border: 1px solid black;")
        
        move_to_button = QPushButton("Movimento absoluto")
        move_to_button.setFixedWidth(position_input.width())
        move_to_button.setFixedHeight(25)
        move_to_button.setFixedWidth(250)
        move_to_button.clicked.connect(lambda: self.move_to_position(axis_number))
        move_to_button.setStyleSheet("background-color: gray;")

        move_relative_label = QLabel("Movimento relativo")
        move_relative_input = QLineEdit()
        move_relative_input.setPlaceholderText("Insira a posição relativa")
        move_relative_input.setFixedHeight(25)
        move_relative_input.setFixedWidth(250)
        move_relative_input.setStyleSheet("background-color: white; border: 1px solid black;")
        
        move_relative_button = QPushButton("Movimento relativo")
        move_relative_button.setFixedWidth(position_input.width())
        move_relative_button.setFixedHeight(25)
        move_relative_button.setFixedWidth(250)
        move_relative_button.clicked.connect(lambda: self.move_relative_position(axis_number))
        move_relative_button.setStyleSheet("background-color: gray;")

        custom_command_label = QLabel("Comando livre")
        custom_command_input = QLineEdit()
        custom_command_input.setPlaceholderText("Insira o comando desejado")
        custom_command_input.setFixedHeight(25)
        custom_command_input.setFixedWidth(250)
        custom_command_input.setStyleSheet("background-color: white; border: 1px solid black;")
        
        send_command_button = QPushButton("Enviar comando")
        send_command_button.setFixedWidth(position_input.width())
        send_command_button.setFixedHeight(25)
        send_command_button.setFixedWidth(250)
        send_command_button.clicked.connect(lambda: self.send_custom_command(axis_number))
        send_command_button.setStyleSheet("background-color: gray;")

        current_position_label = QLabel("Posição atual do eixo")
        current_position_output = QLabel("")
        current_position_label.setAlignment(Qt.AlignHCenter)
        current_position_output.setFixedHeight(25)
        current_position_output.setFixedWidth(250)
        current_position_output.setStyleSheet("background-color: lightgray; border: 1px solid black;")
        
        update_position_button = QPushButton("Atualizar posição")
        update_position_button.setFixedWidth(position_input.width())
        update_position_button.setFixedHeight(25)
        update_position_button.setFixedWidth(250)
        update_position_button.clicked.connect(lambda: self.update_position(axis_number))
        update_position_button.setStyleSheet("background-color: gray;")

        command_output = QLabel("")

        # Adiciona widgets ao layout do eixo
        axis_layout.addWidget(position_input)
        axis_layout.addWidget(move_to_button)
        axis_layout.addSpacing(10)
        axis_layout.addWidget(move_relative_input)
        axis_layout.addWidget(move_relative_button)
        axis_layout.addSpacing(10)
        axis_layout.addWidget(custom_command_input)
        axis_layout.addWidget(send_command_button)
        axis_layout.addSpacing(13)
        axis_layout.addWidget(current_position_label)
        axis_layout.addWidget(current_position_output)
        axis_layout.addWidget(update_position_button)
        axis_layout.addSpacing(10)
        axis_layout.addWidget(command_output)

    def connect_to_device(self):
        # Implementar lógica de conexão aqui
        self.connection_status_label.setText("Status da conexão: Conectado")

    def move_to_position(self, axis_number):
        # Implementar lógica de mover para a posição para o eixo especificado
        pass

    def move_relative_position(self, axis_number):
        # Implementar lógica de movimento relativo para o eixo especificado
        pass

    def update_position(self, axis_number):
        # Implementar lógica de atualização da posição para o eixo especificado
        pass

    def send_custom_command(self, axis_number):
        # Implementar lógica para enviar comando personalizado para o eixo especificado
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
