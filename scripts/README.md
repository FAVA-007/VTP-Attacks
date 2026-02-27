# Scripts: VTP Attacks

## 📁 Descripción

Esta carpeta contiene scripts y herramientas para ejecutar el ataque VTP de forma automatizada.

## 📋 Archivos Disponibles

### 1. `yersinia_vtp_attack.sh`
**Tipo**: Bash Script
**Propósito**: Automatizar el ataque VTP con Yersinia
**Función**: Inyectar VTP advertisements maliciosos

```bash
bash yersinia_vtp_attack.sh -i eth0 -d NETWORK_LAB -r 999
```

---

### 2. `vtp_monitor.sh`
**Tipo**: Bash Script
**Propósito**: Monitorear cambios de VLAN en tiempo real
**Función**: Detectar si el ataque fue exitoso

```bash
bash vtp_monitor.sh -s 192.168.1.1 -u admin -p password
```

---

### 3. `switch_config_vulnerable.conf`
**Tipo**: Cisco IOS Configuration
**Propósito**: Configuración vulnerable para laboratorio
**Contenido**: Configuración de VTP con dominio NETWORK_LAB sin protección

---

### 4. `switch_config_hardened.conf`
**Tipo**: Cisco IOS Configuration
**Propósito**: Configuración segura (mitigada)
**Contenido**: VTP en modo Transparent con validación de contraseña

---

### 5. `packet_crafter.py`
**Tipo**: Python Script
**Propósito**: Crafting manual de paquetes VTP
**Función**: Crear VTP advertisements personalizados con Scapy

```python
python3 packet_crafter.py --domain NETWORK_LAB --revision 999
```

---

## 🚀 Instalación

```bash
# Clonar scripts
git clone https://github.com/FAVA-007/VTP-Attacks.git
cd VTP-Attacks/scripts

# Hacer ejecutables
chmod +x *.sh

# Ejecutar
sudo ./yersinia_vtp_attack.sh
```

---

## ⚠️ Notas de Seguridad

- **Solo en laboratorio**: Usar en red de prueba controlada
- **Autorización requerida**: Obtener permiso antes de usar
- **Responsabilidad**: El usuario es responsable del uso

---

## 📚 Referencias

- Yersinia GitHub: https://github.com/tomac/yersinia
- Cisco VTP Specification
- Scapy Documentation: https://scapy.readthedocs.io/

---

**Última actualización**: Febrero 2026
