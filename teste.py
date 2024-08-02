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
        self.timeout = timeout# * 60  # Converte minutos para segundos
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
        self.setGeometry(100, 100, 1000, 450)  # Ajustado o tamanho da janela para permitir mais espaço

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)
        self.central_widget.setStyleSheet("background-color: #778899;")

        # Seção geral
        self.general_frame = QFrame()
        self.general_frame.setStyleSheet("background-color: #8FBC8F;")  # Cor de fundo do frame geral
        self.general_frame.setFrameShape(QFrame.StyledPanel)
        self.general_frame.setFixedHeight(170)  # Ajustado para altura menor
        self.general_layout = QVBoxLayout()
        self.general_layout.setContentsMargins(2, 2, 2, 2)  # Margens menores
        self.general_layout.setSpacing(5)  # Espaçamento menor entre os widgets
        self.general_frame.setLayout(self.general_layout)
        self.layout.addWidget(self.general_frame)

        self.connection_label = QLabel("Escolha o método de conexão:")
        self.general_layout.addWidget(self.connection_label)

        self.connection_combo = QComboBox()
        self.connection_combo.setStyleSheet("background-color: white;")
        self.connection_combo.addItem("Serial (/dev/ttyUSB0)")
        self.connection_combo.addItem("GPIB (GPIB0::5::INSTR)")
        self.general_layout.addWidget(self.connection_combo)

        self.connect_button = QPushButton("Conectar")
        self.connect_button.setStyleSheet("background-color: gray;")
        self.connect_button.clicked.connect(self.connect_to_device)
        self.general_layout.addWidget(self.connect_button)

        self.timeout_label = QLabel("Timeout de desconexão (segundos):")
        self.general_layout.addWidget(self.timeout_label)
        self.timeout_input = QLineEdit()
        self.timeout_input.setText("5")  # Valor padrão de 5 segundos
        self.timeout_input.setStyleSheet("background-color: white;")
        self.general_layout.addWidget(self.timeout_input)

        self.connection_status_label = QLabel("Status da conexão: Não conectado")  # Inicializa com status de não conectado
        self.general_layout.addWidget(self.connection_status_label)

        # Layout horizontal para os frames dos eixos
        self.axis_frame_layout = QHBoxLayout()
        self.layout.addLayout(self.axis_frame_layout)

        # Seção dos eixos
        self.axis_frame1 = QFrame()
        self.axis_frame1.setStyleSheet("background-color: #8FBC8F;")  # Verde claro #e0f7e0
        self.axis_frame1.setFrameShape(QFrame.StyledPanel)
        self.axis_layout1 = QFormLayout()
        self.axis_frame1.setLayout(self.axis_layout1)
        self.axis_frame_layout.addWidget(self.axis_frame1)

        self.axis1_title_label = QLabel("EIXO 1\n")
        self.axis1_title_label.setAlignment(Qt.AlignCenter)
        self.axis1_position_label = QLabel("Posição")
        self.axis1_position_input = QLineEdit()
        #self.axis1_position_input.setFixedWidth(150)
        self.axis1_position_input.setFixedHeight(25)
        self.axis1_position_input.setStyleSheet("background-color: white; border: 1px solid black;")
        self.axis1_move_to_button = QPushButton("Mover para a posição")
        #self.axis1_move_to_button.setFixedWidth(150)
        #self.axis1_move_to_button.setFixedHeight(25)
        self.axis1_move_to_button.clicked.connect(self.move_to_position_axis1)
        self.axis1_move_to_button.setStyleSheet("background-color: gray;")


        # Criar um layout horizontal para o botão e centralizá-lo
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.axis1_move_to_button)
        button_layout.setAlignment(Qt.AlignCenter)

        self.axis1_move_relative_label = QLabel("Movimento relativo")
        self.axis1_move_relative_input = QLineEdit()
        self.axis1_move_relative_input.setAlignment(Qt.AlignVCenter)
        #self.axis1_move_relative_input.setFixedWidth(150)
        self.axis1_move_relative_input.setFixedHeight(25)
        self.axis1_move_relative_input.setStyleSheet("background-color: white; border: 1px solid black;")
        self.axis1_move_relative_button = QPushButton("Mover relativo")
        #self.axis1_move_relative_button.setFixedWidth(150)
        #self.axis1_move_relative_button.setFixedHeight(25)
        self.axis1_move_relative_button.clicked.connect(self.move_relative_position_axis1)
        self.axis1_move_relative_button.setStyleSheet("background-color: gray;")

        self.axis1_current_position_label = QLabel("Posição atual do eixo")
        self.axis1_current_position_output = QLabel("")
        self.axis1_current_position_output.setAlignment(Qt.AlignVCenter)
        #self.axis1_current_position_output.setFixedWidth(150)
        self.axis1_current_position_output.setFixedHeight(25)
        self.axis1_current_position_output.setStyleSheet("background-color: white; border: 1px solid black;")
        self.axis1_update_position_button = QPushButton("Atualizar posição")
        #self.axis1_update_position_button.setFixedWidth(150)
        #self.axis1_update_position_button.setFixedHeight(25)
        self.axis1_update_position_button.clicked.connect(self.update_position_axis1)
        self.axis1_update_position_button.setStyleSheet("background-color: gray;")

        self.axis1_custom_command_label = QLabel("Comando personalizado")
        self.axis1_custom_command_input = QLineEdit()
        self.axis1_custom_command_input.setAlignment(Qt.AlignVCenter)
        #self.axis1_custom_command_input.setFixedWidth(150)
        self.axis1_custom_command_input.setFixedHeight(25)
        self.axis1_custom_command_input.setStyleSheet("background-color: white; border: 1px solid black;")
        self.axis1_send_command_button = QPushButton("Enviar comando")
        #self.axis1_send_command_button.setFixedWidth(150)
        #self.axis1_send_command_button.setFixedHeight(25)
        self.axis1_send_command_button.clicked.connect(self.send_custom_command_axis1)
        self.axis1_send_command_button.setStyleSheet("background-color: gray;")

        self.axis1_command_output = QLabel("")

        # Adiciona widgets ao layout do eixo 1
        self.axis_layout1.addRow(self.axis1_title_label)
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
        self.axis_frame2.setStyleSheet("background-color: #8FBC8F;")  # Verde claro #e0f7e0
        self.axis_frame2.setFrameShape(QFrame.StyledPanel)
        self.axis_layout2 = QFormLayout()
        self.axis_frame2.setLayout(self.axis_layout2)
        self.axis_frame_layout.addWidget(self.axis_frame2)

        self.axis2_title_label = QLabel("EIXO 2\n")
        self.axis2_title_label.setAlignment(Qt.AlignCenter)
        self.axis2_position_label = QLabel("Posição")
        self.axis2_position_input = QLineEdit()
        self.axis2_position_input.setAlignment(Qt.AlignVCenter)
        #self.axis2_position_input.setFixedWidth(150)
        self.axis2_position_input.setFixedHeight(25)
        self.axis2_position_input.setStyleSheet("background-color: white; border: 1px solid black;")
        self.axis2_move_to_button = QPushButton("Mover para a posição")
        #self.axis2_move_to_button.setFixedWidth(150)
        #self.axis2_move_to_button.setFixedHeight(25)
        self.axis2_move_to_button.clicked.connect(self.move_to_position_axis2)
        self.axis2_move_to_button.setStyleSheet("background-color: gray;")

        self.axis2_move_relative_label = QLabel("Movimento relativo")
        self.axis2_move_relative_input = QLineEdit()
        self.axis2_move_relative_input.setAlignment(Qt.AlignVCenter)
        #self.axis2_move_relative_input.setFixedWidth(150)
        self.axis2_move_relative_input.setFixedHeight(25)
        self.axis2_move_relative_input.setStyleSheet("background-color: white; border: 1px solid black;")
        self.axis2_move_relative_button = QPushButton("Mover relativo")
        #self.axis2_move_relative_button.setFixedWidth(150)
        #self.axis2_move_relative_button.setFixedHeight(25)
        self.axis2_move_relative_button.clicked.connect(self.move_relative_position_axis2)
        self.axis2_move_relative_button.setStyleSheet("background-color: gray;")

        self.axis2_current_position_label = QLabel("Posição atual do eixo")
        self.axis2_current_position_output = QLabel("")
        self.axis2_current_position_output.setAlignment(Qt.AlignVCenter)
        #self.axis2_current_position_output.setFixedWidth(150)
        self.axis2_current_position_output.setFixedHeight(25)
        self.axis2_current_position_output.setStyleSheet("background-color: white; border: 1px solid black;")
        self.axis2_update_position_button = QPushButton("Atualizar posição")
        #self.axis2_update_position_button.setFixedWidth(150)
        #self.axis2_update_position_button.setFixedHeight(25)
        self.axis2_update_position_button.clicked.connect(self.update_position_axis2)
        self.axis2_update_position_button.setStyleSheet("background-color: gray;")

        self.axis2_custom_command_label = QLabel("Comando personalizado")
        self.axis2_custom_command_input = QLineEdit()
        self.axis2_custom_command_input.setAlignment(Qt.AlignVCenter)
        #self.axis2_custom_command_input.setFixedWidth(150)
        self.axis2_custom_command_input.setFixedHeight(25)
        self.axis2_custom_command_input.setStyleSheet("background-color: white; border: 1px solid black;")
        self.axis2_send_command_button = QPushButton("Enviar comando")
        #self.axis2_send_command_button.setFixedWidth(150)
        #self.axis2_send_command_button.setFixedHeight(25)
        self.axis2_send_command_button.clicked.connect(self.send_custom_command_axis2)
        self.axis2_send_command_button.setStyleSheet("background-color: gray;")

        self.axis2_command_output = QLabel("")

        # Adiciona widgets ao layout do eixo 2
        self.axis_layout2.addRow(self.axis2_title_label)
        self.axis_layout2.addRow(self.axis2_position_label, self.axis2_position_input)
        self.axis_layout2.addRow(self.axis2_move_to_button)
        self.axis_layout2.addRow(self.axis2_move_relative_label, self.axis2_move_relative_input)
        self.axis_layout2.addRow(self.axis2_move_relative_button)
        self.axis_layout2.addRow(self.axis2_current_position_label, self.axis2_current_position_output)
        self.axis_layout2.addRow(self.axis2_update_position_button)
        self.axis_layout2.addRow(self.axis2_custom_command_label, self.axis2_custom_command_input)
        self.axis_layout2.addRow(self.axis2_send_command_button)
        self.axis_layout2.addRow(self.axis2_command_output)

    def connect_to_device(self):
        connection_method = self.connection_combo.currentText()
        timeout = int(self.timeout_input.text())
        try:
            if connection_method == "Serial (/dev/ttyUSB0)":
                self.adapter = serial.Serial('/dev/ttyUSB0', baudrate=19200, bytesize=8, parity='N', stopbits=1)
                self.device = ESP300(self.adapter, timeout)
                self.connection_status_label.setText("Status da conexão: Conectado via Serial")
            else:
                rm = pyvisa.ResourceManager()
                self.adapter = rm.open_resource('GPIB0::5::INSTR')
                self.device = ESP300(self.adapter, timeout)
                self.connection_status_label.setText("Status da conexão: Conectado via GPIB")
        except Exception as e:
            self.connection_status_label.setText(f"Status da conexão: Falha ao conectar. {e}")

    def check_connection(self):
        if not self.device:
            self.connection_status_label.setText("Status da conexão: Não conectado")
            return False
        return True

    def move_to_position_axis1(self):
        if not self.check_connection():
            return
        position = self.axis1_position_input.text()
        if position:
            self.device.move_to('1', position)
            self.update_position_axis1()

    def move_to_position_axis2(self):
        if not self.check_connection():
            return
        position = self.axis2_position_input.text()
        if position:
            self.device.move_to('2', position)
            self.update_position_axis2()

    def move_relative_position_axis1(self):
        if not self.check_connection():
            return
        increment = self.axis1_move_relative_input.text()
        if increment:
            self.device.move_relative('1', increment)
            self.update_position_axis1()

    def move_relative_position_axis2(self):
        if not self.check_connection():
            return
        increment = self.axis2_move_relative_input.text()
        if increment:
            self.device.move_relative('2', increment)
            self.update_position_axis2()

    def update_position_axis1(self):
        if not self.check_connection():
            return
        position = self.device.get_position('1')
        if position:
            cleaned_position = position.replace('\n', '')  # Remove caracteres de nova linha
            self.axis1_current_position_output.setText(cleaned_position)
        else:
            self.axis1_current_position_output.setText("Erro ao atualizar posição")

    def update_position_axis2(self):
        if not self.check_connection():
            return
        position = self.device.get_position('2')
        if position:
            cleaned_position = position.replace('\n', '')  # Remove caracteres de nova linha
            self.axis2_current_position_output.setText(cleaned_position)
        else:
            self.axis2_current_position_output.setText("Erro ao atualizar posição")

    def send_custom_command_axis1(self):
        if not self.check_connection():
            return
        command = self.axis1_custom_command_input.text()
        if command:
            response = self.device.execute_command(command)
            self.axis1_command_output.setText(response if response else "Erro ao enviar comando")

    def send_custom_command_axis2(self):
        if not self.check_connection():
            return
        command = self.axis2_custom_command_input.text()
        if command:
            response = self.device.execute_command(command)
            self.axis2_command_output.setText(response if response else "Erro ao enviar comando")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())