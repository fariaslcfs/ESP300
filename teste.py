import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QFormLayout, QFrame, QComboBox
from PyQt5.QtCore import QThread, pyqtSignal, Qt
import pyvisa
import serial

class MotorMonitorThread(QThread):
    position_updated = pyqtSignal(str, str)

    def __init__(self, device):
        super().__init__()
        self.device = device
        self.running = True

    def run(self):
        while self.running:
            for axis in ["1", "2"]:
                if not self.device.is_motor_moving(axis):
                    position = self.device.get_position(axis)
                    self.position_updated.emit(axis, position)
            self.msleep(1000)  # Delay for 1 second

    def stop(self):
        self.running = False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Controle de Eixo")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.connection_combo = QComboBox()
        self.connection_combo.addItems(["Serial", "GPIB"])
        self.layout.addWidget(self.connection_combo)

        self.timeout_input = QLineEdit()
        self.timeout_input.setText("5")  # Default timeout
        self.layout.addWidget(self.timeout_input)

        self.connect_button = QPushButton("Conectar")
        self.connect_button.clicked.connect(self.connect_to_device)
        self.layout.addWidget(self.connect_button)

        self.connection_status_label = QLabel("Status da conexão: Desconectado")
        self.layout.addWidget(self.connection_status_label)

        # Adicionando widgets para o eixo 1 e eixo 2 (como antes)

        self.axis_frame_layout = QHBoxLayout()
        self.layout.addLayout(self.axis_frame_layout)

        # Seção dos eixos 1 (com o código do eixo 1 como antes)

        self.axis_frame1 = QFrame()
        self.axis_frame1.setStyleSheet("background-color: #87CEEB;")  # Azul claro
        self.axis_frame1.setFrameShape(QFrame.StyledPanel)
        self.axis_layout1 = QFormLayout()
        self.axis_frame1.setLayout(self.axis_layout1)
        self.axis_frame_layout.addWidget(self.axis_frame1)

        # Adiciona widgets ao layout do eixo 1 (como antes)

        # Seção dos eixos 2 (com o código do eixo 2 como antes)

        self.axis_frame2 = QFrame()
        self.axis_frame2.setStyleSheet("background-color: #8FBC8F;")  # Verde claro
        self.axis_frame2.setFrameShape(QFrame.StyledPanel)
        self.axis_layout2 = QFormLayout()
        self.axis_frame2.setLayout(self.axis_layout2)
        self.axis_frame_layout.addWidget(self.axis_frame2)

        # Adiciona widgets ao layout do eixo 2 (como antes)

        self.device = None
        self.monitor_thread = None

    def connect_to_device(self):
        connection_method = self.connection_combo.currentText()
        timeout = int(self.timeout_input.text())

        try:
            if "Serial" in connection_method:
                port = "/dev/ttyUSB0"  # Ajuste conforme necessário
                self.serial_resource = serial.Serial(port, baudrate=19200, timeout=timeout)
                self.device = ESP300(self.serial_resource, timeout)
            else:
                rm = pyvisa.ResourceManager()
                resource_name = "GPIB0::5::INSTR"
                self.gpib_resource = rm.open_resource(resource_name)
                self.device = ESP300(self.gpib_resource, timeout)

            self.connection_status_label.setText("Status da conexão: Conectado")

            # Inicializa e inicia o monitoramento após a conexão
            if self.device:
                if self.monitor_thread:
                    self.monitor_thread.stop()
                self.monitor_thread = MotorMonitorThread(self.device)
                self.monitor_thread.position_updated.connect(self.update_position_labels)
                self.monitor_thread.start()

        except Exception as e:
            self.connection_status_label.setText(f"Status da conexão: Erro - {e}")

    def update_position_labels(self, axis, position):
        if axis == "1":
            self.axis1_current_position_output.setText(position)
        elif axis == "2":
            self.axis2_current_position_output.setText(position)

    def move_to_position_axis1(self):
        position = self.axis1_position_input.text()
        if position:
            self.device.move_to("1", position)

    def move_relative_position_axis1(self):
        increment = self.axis1_move_relative_input.text()
        if increment:
            self.device.move_relative("1", increment)

    def update_position_axis1(self):
        if not self.device.is_motor_moving("1"):
            self.axis1_current_position_output.setText(self.device.get_position("1"))

    def send_custom_command_axis1(self):
        command = self.axis1_custom_command_input.text()
        if command:
            result = self.device.execute_command(command)
            self.axis1_command_output.setText(result)

    def move_to_position_axis2(self):
        position = self.axis2_position_input.text()
        if position:
            self.device.move_to("2", position)

    def move_relative_position_axis2(self):
        increment = self.axis2_move_relative_input.text()
        if increment:
            self.device.move_relative("2", increment)

    def update_position_axis2(self):
        if not self.device.is_motor_moving("2"):
            self.axis2_current_position_output.setText(self.device.get_position("2"))

    def send_custom_command_axis2(self):
        command = self.axis2_custom_command_input.text()
        if command:
            result = self.device.execute_command(command)
            self.axis2_command_output.setText(result)

    def closeEvent(self, event):
        if self.monitor_thread:
            self.monitor_thread.stop()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
