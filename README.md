# VTP Attacks - Ataque de Manipulación VTP

## 📋 Descripción General

Este repositorio contiene un análisis detallado y demostraciones prácticas sobre vulnerabilidades en el protocolo **VTP (VLAN Trunking Protocol)** de Cisco, específicamente cómo un atacante puede explotar la negociación automática de dominios VTP para convertirse en VTP Server y manipular la base de datos de VLANs en switches Cisco.

## 🔍 ¿Qué es VTP?

VTP (VLAN Trunking Protocol) es un protocolo de capa 2 específico de Cisco que permite la administración centralizada de VLANs en múltiples switches de una red. Su propósito es simplificar la propagación de cambios de VLAN automáticamente a través de toda la red de switches interconectados.

### Funcionamiento Normal de VTP:
- Un **VTP Server** propaga cambios de VLAN a todos los switches conectados
- Los demás switches pueden ser **VTP Clients** (reciben cambios) o **VTP Transparent** (no participan)
- Los cambios se transmiten mediante actualizaciones periódicas basadas en un **número de revisión**
- El switch con el número de revisión más alto es la autoridad en la configuración de VLANs

## 🎯 El Ataque: Manipulación Maliciosa de VTP

### Vulnerabilidad Explotada

La vulnerabilidad principal surge de que:

1. **No hay autenticación fuerte por defecto**: VTP solo utiliza una contraseña opcional de dominio en texto claro (o no cifrada en versiones antiguas)
2. **El número de revisión es la métrica crítica**: Cualquier switch que anuncie un número de revisión más alto se convierte automáticamente en la autoridad de VLAN
3. **Aceptación automática de roles**: Un switch puede negociar automáticamente convertirse en VTP Server
4. **Falta de validación de fuente**: No hay verificación criptográfica de la identidad del remitente

### Escenarios de Ataque

#### Escenario 1: Inyección de Nuevo Dominio VTP
Un atacante en la red (con acceso físico a un puerto del switch) puede:
1. Conectar una máquina atacante al puerto de un switch
2. Inyectar advertisements VTP falsos con:
   - Un **número de revisión alto** (ej: 999)
   - Un **nombre de dominio VTP** válido
   - Rol de **VTP Server**
3. El switch víctima aceptará al atacante como nuevo VTP Server
4. El atacante puede entonces:
   - **Añadir VLANs maliciosas** que apunten a IPs controladas del atacante
   - **Borrar VLANs críticas** de la organización
   - **Modificar las asignaciones de puerto** a VLANs

#### Escenario 2: Suplantación del VTP Server Existente
1. El atacante obtiene información sobre el dominio VTP actual observando tráfico
2. Con un número de revisión superior, suplanta al servidor legítimo
3. Todos los cambios benignos de VLAN se reemplazan por la base de datos del atacante

## 🛠️ Herramienta Utilizada

### Yersinia
**Yersinia** es una herramienta profesional de penetration testing que implementa ataques De capa 2. Para este caso, usamos su capacidad para generar y enviar tramas VTP maliciosas.

- **Modo**: Interactivo/CLI
- **Utilidad**: Permite crafting manual de advertencias VTP
- **Variantes soportadas**: VTPv1 y VTPv2

## 📊 Impacto del Ataque

| Impacto | Severidad | Descripción |
|---------|-----------|------------|
| **Pérdida de Conectividad** | 🔴 Alta | Eliminación de VLANs operativas produciendo desconexión de dispositivos |
| **Manipulación de Tráfico** | 🔴 Alta | Redirección de tráfico a subnets controladas por el atacante |
| **Downtime de Red** | 🔴 Crítica | Inaccesibilidad total de servicios dependientes de VLANs |
| **Robo de Datos** | 🔴 Crítica | Análisis de tráfico capturado después de manipular VLANs |
| **Falsificación de Identidad** | 🟡 Media | El atacante asume control sobre la configuración de switches |

## 🛡️ Mitigación y Defensa

### 1. Configuración de Contraseña VTP (Fundamental)
```
Switch(config)# vtp domain <nombre_dominio>
Switch(config)# vtp mode server
Switch(config)# vtp password <contraseña_fuerte>
```
⚠️ **Limitación**: En VTPv1 y v2, la contraseña viaja sin cifrar en las actualizaciones

### 2. Modo VTP Transparent (Recomendado)
```
Switch(config)# vtp mode transparent
```
- El switch **NO participa** en la propagación de VTP
- Solo actúa como paso a través del tráfico VTP
- Los cambios deben hacerse de forma individual y manual
- **Elimina completamente la vulnerabilidad a ataques VTP**

### 3. VTPv3 (Más Seguro)
- Introduce autenticación con **PSK (Pre-Shared Key) cifrada**
- Permite múltiples VTP Servers
- Validación más robusta de cambios
```
Switch(config)# vtp version 3
```

### 4. Control Físico y de Acceso
- Limitar acceso físico a puertos de switches
- Implementar **Port Security** para bloquear MACs desconocidas
- Usar **BPDU Guard** en puertos de acceso de usuario

### 5. Monitoreo
- Alertas sobre cambios de VLAN no autorizados
- Logging de cambios de configuración de VTP
- Verificación periódica de `show vtp status`

## 📁 Estructura del Repositorio

```
VTP-Attacks/
├── README.md                          # Este archivo
├── GUIA_DE_USO.md                    # Instrucciones paso a paso para el ataque
├── EXPLICACION_TECNICA.md            # Análisis profundo del protocolo VTP
├── MITIGACION.md                     # Estrategias de defensa
├── GITHUB_SETUP.sh                   # Script para subir a GitHub
├── imagenes/                         # Carpeta para evidencia fotográfica
│   ├── image_d0dccb.png             # Captura de interfaz Yersinia
│   ├── image_switch_config.png      # Configuración vulnerable del switch
│   ├── image_vlan_database.png      # Base de datos VLAN antes/después
│   └── image_attack_flow.png        # Diagrama del flujo de ataque
└── configuraciones/
    ├── switch_vulnerable.conf        # Configuración vulnerable
    └── switch_seguro.conf            # Configuración con mitigación
```

## ⚡ Inicio Rápido

1. **Revisar la arquitectura**: Lee `GUIA_DE_USO.md`
2. **Entender el ataque**: Consulta `EXPLICACION_TECNICA.md`
3. **Ver defensa**: Revisa `MITIGACION.md`
4. **Implementar localmente**: Usa el simulador Cisco Packet Tracer o GNS3
5. **Subir a GitHub**: Ejecuta los comandos en `GITHUB_SETUP.sh`

## 🚀 Requisitos Técnicos

- **Sistema Operativo**: Linux (Debian/Ubuntu) o máquina virtual
- **Herramientas Principales**:
  - Yersinia (penetration testing)
  - Wireshark (análisis de tráfico)
  - GNS3 o Cisco Packet Tracer (simulación)
- **Conocimiento**: Layer 2 switching, conceptos de VLAN, protocolos Cisco
- **Acceso**: Red de laboratorio controlada o simulada

## ⚠️ Aviso Legal y Ético

Este repositorio es **solo con fines educativos**. 

- ✅ **Permitido**: Usar en laboratorios académicos, redes de prueba propias
- ❌ **Prohibido**: Ejecutar ataques en redes sin autorización explícita
- ⚖️ **Legal**: El acceso no autorizado a sistemas informáticos es ilegal

**Cualquier uso malintencionado es responsabilidad del usuario final.**

## 👨‍🎓 Contexto Académico

Proyecto de ciberseguridad y administración de redes para análisis de vulnerabilidades de protocolo VTP en switches Cisco. Parte de una serie de tres ataques de capa 2:

1. 🔗 [VTP Attacks](https://github.com/FAVA-007/VTP-Attacks)
2. 🔄 [DTP VLAN Hopping](https://github.com/FAVA-007/DTP-VLAN-Hopping)
3. 🕵️ [DNS Spoofing/Poisoning](https://github.com/FAVA-007/DNS-Spoofing-DNS-Poisoning)

## 📧 Contacto y Recursos

- **Autor**: Estudiante de Ciberseguridad
- **Institución**: ITLA (Instituto Tecnológico Latinoamericano)
- **Fecha**: Febrero 2026

## 📚 Referencias Técnicas

- Cisco VTP Protocol Specification
- CVE-2004-0693: VTP Denial of Service
- IEEE 802.1D: Spanning Tree Protocol
- GNS3 Documentation: Layer 2 Protocols

---

**Última actualización**: Febrero 2026  
**Estado**: Completado ✅
