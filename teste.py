#!/usr/bin/env python3

import sys
import time
import pyvisa
import serial
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QComboBox, QFrame
from PyQt5.QtGui import QPixmap
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

        self.setWindowTitle("CONTROLE DO ESP300")
        self.setGeometry(100, 100, 680, 500)  # Ajustado o tamanho da janela para permitir mais espaço

        # Get the current window flags
        flags = self.windowFlags()

        # Set the window flags to exclude the maximize button
        self.setWindowFlags(flags & ~Qt.WindowMaximizeButtonHint)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)
        self.central_widget.setStyleSheet("background-color: #778899;")

        # Layout horizontal para os frames
        self.main_frame_layout = QHBoxLayout()
        self.layout.addLayout(self.main_frame_layout)

        # Seção geral
        self.general_frame = QFrame()
        self.general_frame.setStyleSheet("background-color: #6699CC;")  # Cor de fundo do frame geral
        self.general_frame.setFrameShape(QFrame.StyledPanel)
        self.general_layout = QVBoxLayout()

        # Adiciona a imagem
        self.image_label = QLabel()
        self.general_layout.addSpacing(10)
        self.image_label.setAlignment(Qt.AlignHCenter)
        pixmap = QPixmap('./logoIEAv.png')  # Substitua pelo caminho da sua imagem
        self.image_label.setPixmap(pixmap)
        self.general_layout.addWidget(self.image_label)

        self.general_layout.setContentsMargins(2, 2, 2, 2)  # Margens menores
        self.general_layout.setSpacing(5)  # Espaçamento menor entre os widgets
        self.general_layout.setAlignment(Qt.AlignHCenter)
        self.general_frame.setLayout(self.general_layout)
        self.main_frame_layout.addWidget(self.general_frame)

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

        self.connect_button = QPushButton("CONECTAR")
        self.connect_button.setFixedHeight(25)
        self.connect_button.setFixedWidth(250)
        self.connect_button.setStyleSheet("background-color: gray;")
        self.connect_button.clicked.connect(self.connect_to_device)
        self.general_layout.addWidget(self.connect_button)
       
        self.timeout_input = QLineEdit()
        self.timeout_input.setFixedHeight(25)
        self.timeout_input.setFixedWidth(250)
        self.timeout_input.setPlaceholderText("Insira o timeout em segundos (5)")
        self.timeout_input.setAlignment(Qt.AlignHCenter)
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
        self.create_axis_frame("EIXO 3\n", 3)

    def create_axis_frame(self, title, axis_number):
        axis_frame = QFrame()
        axis_frame.setStyleSheet("background-color: #6699CC;")  # Verde claro #e0f7e0
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

        position_label = QLabel("POSIÇÃO")
        position_input = QLineEdit()
        position_input.setPlaceholderText("Insira a posição absoluta")
        position_input.setFixedHeight(25)
        position_input.setFixedWidth(250)
        position_input.setStyleSheet("background-color: white; border: 1px solid black;")
        
        move_to_button = QPushButton("MOVIMENTO ABSOLUTO")
        move_to_button.setFixedWidth(position_input.width())
        move_to_button.setFixedHeight(25)
        move_to_button.setFixedWidth(250)
        move_to_button.clicked.connect(lambda: self.move_to_position(axis_number))
        move_to_button.setStyleSheet("background-color: gray;")

        move_relative_label = QLabel("MOVIMENTO RELATIVO")
        move_relative_input = QLineEdit()
        move_relative_input.setPlaceholderText("Insira a posição relativa")
        move_relative_input.setFixedHeight(25)
        move_relative_input.setFixedWidth(250)
        move_relative_input.setStyleSheet("background-color: white; border: 1px solid black;")
        
        move_relative_button = QPushButton("MOVIMENTO RELATIVO")
        move_relative_button.setFixedWidth(position_input.width())
        move_relative_button.setFixedHeight(25)
        move_relative_button.setFixedWidth(250)
        move_relative_button.clicked.connect(lambda: self.move_relative_position(axis_number))
        move_relative_button.setStyleSheet("background-color: gray;")

        custom_command_label = QLabel("COMANDO LIVRE")
        custom_command_input = QLineEdit()
        custom_command_input.setPlaceholderText("Insira o comando")
        custom_command_input.setFixedHeight(25)
        custom_command_input.setFixedWidth(250)
        custom_command_input.setStyleSheet("background-color: white; border: 1px solid black;")

        custom_command_button = QPushButton("ENVIAR COMANDO")
        custom_command_button.setFixedWidth(position_input.width())
        custom_command_button.setFixedHeight(25)
        custom_command_button.setFixedWidth(250)
        custom_command_button.clicked.connect(lambda: self.send_custom_command(axis_number))
        custom_command_button.setStyleSheet("background-color: gray;")

        #axis_layout.addWidget(position_label)
        axis_layout.addWidget(position_input)
        axis_layout.addWidget(move_to_button)
        axis_layout.addSpacing(15)
        #axis_layout.addWidget(move_relative_label)
        axis_layout.addWidget(move_relative_input)
        axis_layout.addWidget(move_relative_button)
        axis_layout.addSpacing(15)
        #xis_layout.addWidget(custom_command_label)
        axis_layout.addWidget(custom_command_input)
        axis_layout.addWidget(custom_command_button)
        axis_layout.addSpacing(22)

    def connect_to_device(self):
        connection_type = self.connection_combo.currentText()
        timeout = float(self.timeout_input.text()) if self.timeout_input.text() else 5

        if connection_type.startswith("Serial"):
            port = connection_type.split(" ")[1]
            self.adapter = serial.Serial(port, baudrate=19200, timeout=timeout)
            self.device = ESP300(self.adapter, timeout)
            self.connection_status_label.setText("Status da conexão: Conectado via Serial")
        elif connection_type.startswith("GPIB"):
            resource_name = connection_type.split(" ")[0]
            rm = pyvisa.ResourceManager()
            self.adapter = rm.open_resource(resource_name)
            self.device = ESP300(self.adapter, timeout)
            self.connection_status_label.setText("Status da conexão: Conectado via GPIB")
        else:
            self.connection_status_label.setText("Método de conexão não suportado")

    def move_to_position(self, axis_number):
        position_input = self.findChild(QLineEdit, f"eixo{axis_number}_posicao_input")
        position = position_input.text()
        if position:
            self.device.move_to(f"#{axis_number}", position)

    def move_relative_position(self, axis_number):
        increment_input = self.findChild(QLineEdit, f"eixo{axis_number}_mov_relativo_input")
        increment = increment_input.text()
        if increment:
            self.device.move_relative(f"#{axis_number}", increment)

    def send_custom_command(self, axis_number):
        command_input = self.findChild(QLineEdit, f"eixo{axis_number}_comando_input")
        command = command_input.text()
        if command:
            self.device.execute_command(command)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
