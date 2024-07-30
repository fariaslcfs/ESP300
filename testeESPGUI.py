#!/usr/bin/env python3

import sys
import pyvisa
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('ESP300 Controller')
        
        # Resource Manager
        self.rm = pyvisa.ResourceManager()
        self.gpib_device = None

        # Layout and widgets
        layout = QVBoxLayout()

        self.command_input = QLineEdit(self)
        self.command_input.setPlaceholderText('Enter custom GPIB command')
        layout.addWidget(self.command_input)

        self.send_command_button = QPushButton('Send Command', self)
        self.send_command_button.clicked.connect(self.send_custom_command)
        layout.addWidget(self.send_command_button)

        self.command_output = QLabel('Output will be shown here', self)
        layout.addWidget(self.command_output)

        self.connect_button = QPushButton('Connect to ESP300', self)
        self.connect_button.clicked.connect(self.connect_to_esp300)
        layout.addWidget(self.connect_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def connect_to_esp300(self):
        try:
            self.gpib_device = self.rm.open_resource('GPIB0::5::INSTR')
            self.gpib_device.timeout = 3000  # 3 seconds timeout
            self.command_output.setText('Connected to ESP300.')
        except Exception as e:
            self.command_output.setText(f'Connection error: {str(e)}')

    def send_custom_command(self):
        if self.gpib_device is None:
            self.command_output.setText('Not connected to ESP300.')
            return

        command = self.command_input.text() + '\r'
        try:
            response = self.gpib_device.query(command)
            self.command_output.setText(response)
        except Exception as e:
            self.command_output.setText(f'Error sending command: {str(e)}')
            try:
                self.connect_to_esp300()  # Attempt to reconnect
            except Exception as reconnect_e:
                self.command_output.setText(f'Reconnection error: {str(reconnect_e)}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())
