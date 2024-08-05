#!/usr/bin/env python3

import sys
import time
import pyvisa
import serial
from concurrent.futures import ThreadPoolExecutor
from PyQt5.QtGui import QPixmap
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
                time.sleep(1)  # Atraso para permitir o processamento do comando
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
        response = self.query(f"{axis}TP?")
        if response is not None:
            return response.strip()  # Remove espaços extras se houver
        return "Erro"

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
        self.timeout_input.setPlaceholderText("Timeout em (s) Padrão é 5")
        self.timeout_input.setAlignment(Qt.AlignHCenter)
        self.timeout_input.setStyleSheet("background-color: white;")
        self.general_layout.addWidget(self.timeout_input)

        self.connection_status_label = QLabel("Status da conexão: Não conectado") 
        self.connection_status_label.setStyleSheet("background-color: #DAA520") # Inicializa com status de não conectado
        self.connection_status_label.setAlignment(Qt.AlignHCenter)
        self.general_layout.addWidget(self.connection_status_label)

        # Layout horizontal para os frames dos eixos
        self.axis_frame_layout = QHBoxLayout()
        self.layout.addLayout(self.axis_frame_layout)

        # Seção dos eixos
        self.create_axis_frame("EIXO 1", 1)
        self.create_axis_frame("EIXO 2", 2)
        self.create_axis_frame("EIXO 3", 3)

        # Cria um executor para tarefas paralelas
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.update_futures = {}

    def create_axis_frame(self, title, axis_number):
        axis_frame = QFrame()
        axis_frame.setStyleSheet("background-color: #6699CC;")
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

        current_position_display = QLabel("POSIÇÃO ATUAL: ")
        current_position_display.setObjectName(f"eixo{axis_number}_posicao_atual")
        current_position_display.setAlignment(Qt.AlignHCenter)

        position_input = QLineEdit()
        position_input.setObjectName(f"eixo{axis_number}_posicao_input")
        position_input.setPlaceholderText("Insira a posição absoluta")
        position_input.setFixedHeight(25)
        position_input.setFixedWidth(250)
        position_input.setStyleSheet("background-color: white; border: 1px solid black;")
        
        move_to_button = QPushButton("MOVIMENTO ABSOLUTO")
        move_to_button.setFixedWidth(position_input.width())
        move_to_button.setFixedHeight(25)
        move_to_button.clicked.connect(lambda: self.move_to_position(axis_number))
        move_to_button.setStyleSheet("background-color: gray;")

        move_relative_input = QLineEdit()
        move_relative_input.setObjectName(f"eixo{axis_number}_mov_relativo_input")
        move_relative_input.setPlaceholderText("Insira a posição relativa")
        move_relative_input.setFixedHeight(25)
        move_relative_input.setFixedWidth(250)
        move_relative_input.setStyleSheet("background-color: white; border: 1px solid black;")

        move_relative_button = QPushButton("MOVIMENTO RELATIVO")
        move_relative_button.setFixedWidth(move_relative_input.width())
        move_relative_button.setFixedHeight(25)
        move_relative_button.clicked.connect(lambda: self.move_relative_position(axis_number))
        move_relative_button.setStyleSheet("background-color: gray;")

        send_command_input = QLineEdit()
        send_command_input.setObjectName(f"eixo{axis_number}_comando_input")
        send_command_input.setPlaceholderText("Insira comando")
        send_command_input.setFixedHeight(25)
        send_command_input.setFixedWidth(250)
        send_command_input.setStyleSheet("background-color: white; border: 1px solid black;")

        send_command_button = QPushButton("ENVIAR COMANDO")
        send_command_button.setFixedWidth(send_command_input.width())
        send_command_button.setFixedHeight(25)
        send_command_button.clicked.connect(lambda: self.send_command(axis_number))
        send_command_button.setStyleSheet("background-color: gray;")

        update_button = QPushButton("ATUALIZAR POSIÇÃO")
        update_button.setFixedWidth(250)
        update_button.setFixedHeight(25)
        update_button.clicked.connect(lambda: self.update_position_label(axis_number))
        update_button.setStyleSheet("background-color: gray;")

        axis_layout.addSpacing(10)
        axis_layout.addWidget(current_position_display)
        axis_layout.addSpacing(10)
        axis_layout.addWidget(position_input)
        axis_layout.addWidget(move_to_button)
        axis_layout.addSpacing(10)
        axis_layout.addWidget(move_relative_input)
        axis_layout.addWidget(move_relative_button)
        axis_layout.addSpacing(10)
        axis_layout.addWidget(send_command_input)
        axis_layout.addWidget(send_command_button)
        axis_layout.addSpacing(25)
        axis_layout.addWidget(update_button)

    def connect_to_device(self):
        connection_method = self.connection_combo.currentText()
        timeout = int(self.timeout_input.text()) if self.timeout_input.text().isdigit() else 5

        if connection_method.startswith("Serial"):
            port = "/dev/ttyUSB0"  # Alterar conforme necessário
            self.serial_connection = serial.Serial(port, baudrate=19200, timeout=timeout)
            self.device = ESP300(self.serial_connection, timeout)
        else:
            rm = pyvisa.ResourceManager()
            self.gpib_connection = rm.open_resource("GPIB0::5::INSTR")
            self.device = ESP300(self.gpib_connection, timeout)

        self.connection_status_label.setText("Status da conexão: Conectado")
        self.connection_status_label.setStyleSheet("background-color: #32CD32")  # Verde para conectado

    def move_to_position(self, axis_number):
        position = self.findChild(QLineEdit, f"eixo{axis_number}_posicao_input").text()
        if position:
            self.device.move_to(f"{axis_number}", position)
            self.check_motor_status(axis_number)

    def move_relative_position(self, axis_number):
        increment = self.findChild(QLineEdit, f"eixo{axis_number}_mov_relativo_input").text()
        if increment:
            self.device.move_relative(f"{axis_number}", increment)
            self.check_motor_status(axis_number)

    def send_command(self, axis_number):
        command = self.findChild(QLineEdit, f"eixo{axis_number}_comando_input").text()
        if command:
            response = self.device.execute_command(command)
            self.findChild(QLabel, f"eixo{axis_number}_posicao_atual").setText(f"Resposta do comando: {response}")

    def check_motor_status(self, axis_number):
        def check_status():
            while True:
                status = self.device.query(f"{axis_number}MD")
                if status == "1":
                    self.update_position_label(axis_number)
                    break
                time.sleep(1)

        future = self.executor.submit(check_status)
        self.update_futures[axis_number] = future

    def update_position_label(self, axis_number):
        position = self.device.get_position(f"{axis_number}")
        self.findChild(QLabel, f"eixo{axis_number}_posicao_atual").setText(f"POSIÇÃO ATUAL: {position}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
