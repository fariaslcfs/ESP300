#!/usr/bin/env python3

import subprocess
import time

def reload_device(device):
    try:
        # Executar udevadm para disparar uma atualização do dispositivo
        subprocess.run(['udevadm', 'trigger', '--action=remove', '--subsystem-match=tty'], check=True)
        subprocess.run(['udevadm', 'trigger', '--action=add', '--subsystem-match=tty'], check=True)
        print(f"Dispositivo {device} recarregado com sucesso.")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao recarregar o dispositivo: {e}")

# Substitua pelos caminhos corretos para os dispositivos USB
tty_device = '/dev/ttyUSB0'
gpib_device = '/dev/GPIB0'

# Recarregar os dispositivos USB
reload_device(tty_device)
time.sleep(2)  # Esperar um momento
reload_device(gpib_device)
