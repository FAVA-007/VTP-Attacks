# Scripts: VTP Attacks

## 📁 Descripción

Esta carpeta contiene scripts y herramientas para ejecutar el ataque VTP de forma automatizada.

## 📋 Archivos Disponibles

### 1. `vtp_attack.py`
**Tipo**: Python Script
**Propósito**: Inyección automática de VTP advertisements
**Función**: Crafting manual de paquetes VTP con Scapy para forzar actualización de VLAN database

```python
python3 vtp_attack.py
```

---

### 2. `switch_config_vulnerable.conf`
**Tipo**: Cisco IOS Configuration
**Propósito**: Configuración vulnerable para laboratorio
**Contenido**: Configuración de VTP con dominio NETWORK_LAB sin protección

---

### 3. `switch_config_hardened.conf`
**Tipo**: Cisco IOS Configuration
**Propósito**: Configuración segura (mitigada)
**Contenido**: VTP en modo Transparent con validación de contraseña

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
