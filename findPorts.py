#!/usr/bin/python3

import pyvisa
import os
import sys

def find_ports():
    try:
        rm = pyvisa.ResourceManager()
        resources = rm.list_resources()
        if not resources:
            print("Nenhuma porta encontrada.")
        else:
            print("Portas disponíveis:")
            for resource in resources:
                print(resource)
        print("\nPara conexões seriais, as portas geralmente têm nomes como /dev/ttyUSB0 ou /dev/ttyS0 no Linux.")
        print("Para conexões GPIB, as portas geralmente têm nomes como GPIB0::5::INSTR.\n")
    except Exception as e:
        print(f"Erro ao listar portas: {e}")
        sys.exit(1)

def check_permissions():
    user = os.getlogin()
    groups = os.getgroups()
    print(f"Usuário: {user}")
    print(f"Grupos: {groups}")
    if 20 in groups:  # GID 20 é geralmente dialout no Ubuntu
        print("Usuário tem permissões adequadas para acessar dispositivos seriais.")
    else:
        print("Usuário não tem permissões adequadas para acessar dispositivos seriais.")
        print("Execute o seguinte comando para adicionar o usuário ao grupo dialout:")
        print(f"sudo usermod -aG dialout {user}")
        sys.exit(1)

if __name__ == "__main__":
    check_permissions()
    find_ports()

