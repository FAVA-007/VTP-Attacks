# EXPLICACIÓN TÉCNICA: Vulnerabilidad VTP y Explotación

## 🔬 Análisis Profundo del Protocolo VTP

### Estructura del Protocolo VTP

VTP es un protocolo de capa 2 específico de Cisco que se transmite en el interior de tramas 802.1Q sobre puertos troncales. Su función principal es sincronizar la base de datos de VLANs à través de múltiples switches de forma automática.

#### Características Base de VTP
- **Protocolo**: Propietario Cisco
- **Capa OSI**: 2 (Enlace de datos)
- **Transmisión**: Multicast MAC: `01:00:0c:cc:cc:cc`
- **Puerto UDP**: No usa UDP (capa 2 pura)
- **Versiones**: VTPv1, VTPv2, VTPv3
- **Intervalo de actualización**: Cada 5 minutos (por defecto) o por cambio de configuración
- **Cifrado**: Ninguno en v1 y v2 (v3 introduce cifrado)

### Campo de Estructura de Advertisement de VTP

#### Trama Ethernet + VTP Header (VTPv2)
```
┌─────────────────────────────────────────────────────────┐
│ MAC Dest: 01:00:0c:cc:cc:cc (Multicast)                 │
│ MAC Src: <MAC del switch enviador>                      │
│ Type: 0x8100 (802.1Q - VLAN tagging)                    │
│ VLAN ID: 1 (Management VLAN)                             │
└─────────────────────────────────────────────────────────┘
│                                                           │
│  ┌─────────────────── VTP Header ───────────────────┐   │
│  │ Version: 2 (1 byte) - Indica VTPv1 o VTPv2      │   │
│  │ Type: 0x01=Summary Adv, 0x02=Subset Adv         │   │
│  │        0x03=Advertisement Request                │   │
│  │ Reserved: 1 byte (siempre 0)                     │   │
│  │ Sequence Number: 4 bytes                         │   │
│  │ Domain Name Len: 1 byte                          │   │
│  │ Domain Name: variable (max 32 bytes)             │   │
│  │ Revision Number: **4 bytes (CRÍTICO)**           │   │
│  │ Learnt VLAN: 4 bytes                             │   │
│  └─────────────────────────────────────────────────┘   │
│                                                           │
│  ┌─────────────── VLAN Info Objects ────────────────┐   │
│  │ Para cada VLAN en la base de datos:              │   │
│  │ ├─ VLAN ID: 2 bytes                              │   │
│  │ ├─ MTU: 2 bytes                                  │   │
│  │ ├─ Status: 2 bytes                               │   │
│  │ ├─ Type: 1 byte                                  │   │
│  │ ├─ Name Len: 1 byte                              │   │
│  │ └─ Name: variable                                │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### El Campo Crítico: Revision Number

**Propósito**: Indicar la versión actual de la base de datos de VLANs
**Rango**: 0 a 4,294,967,295 (32-bit unsigned integer)
**Comportamiento del Switch**:

```
SI (Revision recibida > Revision local) ENTONCES
    → Aceptar la nueva base de datos VLAN del remitente
    → Actualizar todas las VLANs
    → Propagar advertisement a otros switches
SINO
    → Ignorar el advertisement
FINSI
```

### El Flujo Normal de VTP

```
Configuración Inicial:
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│ SW1 (Server) │          │ SW2 (Client) │          │ SW3 (Client) │
│ Rev: 1       │          │ Rev: 0       │          │ Rev: 0       │
│ VLANS: 1-10  │          │ VLANS: 1     │          │ VLANS: 1     │
└──────────────┘          └──────────────┘          └──────────────┘
        │                        │                        │
        └────────────────────────┴────────────────────────┘
            Advertisement periódico (Multicast)
            "Rev 1: Aquí están las VLANs 1-10"

                    ↓ Después de 30 segundos ↓

┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│ SW1 (Server) │          │ SW2 (Client) │          │ SW3 (Client) │
│ Rev: 1       │          │ Rev: 1       │          │ Rev: 1       │
│ VLANS: 1-10  │          │ VLANS: 1-10  │          │ VLANS: 1-10  │
└──────────────┘          └──────────────┘          └──────────────┘

        Todos sincronizados ✓
```

---

## 💣 El Ataque: VTP Manipulation

### La Vulnerabilidad Fundamental

1. **No hay autenticación real**: Cualquier dispositivo en la red troncal puede anunciar ser un VTP Server
2. **Confianza en número de revisión**: El switch simple comparación de números, no valida la identidad del remitente
3. **Aceptación automática**: El sistema opera en "confianza por defecto"
4. **No hay HMAC o firma digital**: En VTPv1 y v2, no hay verificación criptográfica

### Exploración de la Vulnerabilidad

#### Paso 1: Escucha Pasiva de VTP

El atacante (en una máquina conectada al puerto troncal) captura advertisements VTP legítimos:

```bash
sudo tcpdump -i eth0 -A -n 'ether dst 01:00:0c:cc:cc:cc'
```

**Información capturada**:
```
tcpdump output:
IP 0.0.0.0.unknown > 255.255.255.255.unknown: UDP (Fragment)
    VTP Header:
    Version: 2
    Type: Summary Advertisement (0x01)
    Domain Name: NETWORK_LAB
    Revision: 5
    VLAN Count: 15
    
    VLANs:
    - VLAN 1 (default)
    - VLAN 10 (Management)
    - VLAN 20 (Production)
    - VLAN 50 (Guest)
    ...
```

#### Paso 2: Determinación de Estrategia de Ataque

**Objetivo**: Enviar un advertisement con:
- ✅ Mismo dominio VTP (`NETWORK_LAB`)
- ✅ Número de revisión MAYOR (`999` vs `5`)
- ✅ Cambios maliciosos en la base de datos VLAN
- ✅ Rol de VTP Server

#### Paso 3: Crafting del Advertisement Malicioso

Con Yersinia, se construye una trama VTP personalizada:

```python
# Pseudo-código de lo que hace Yersinia
craft_vtp_advertisement(
    version=2,
    type=1,  # Summary Advertisement
    domain_name="NETWORK_LAB",
    revision_number=999,  # Mayor que cualquier switch legítimo
    vlan_objects=[
        {
            'id': 100,
            'name': 'Hacker_VLAN',  # VLAN nueva controlada por atacante
            'mtu': 1500,
            'status': 0x0C  # Active
        },
        # Opcionalmente: Eliminar VLAN legítimas
        {
            'id': 20,
            'name': 'Production',
            'status': 0x00  # Marked for deletion
        }
    ],
    src_mac="aa:bb:cc:dd:ee:ff",  # MAC del atacante
    dst_mac="01:00:0c:cc:cc:cc"  # Multicast de VTP
)
```

#### Paso 4: Inyección de Advertisement

La máquina atacante envía la trama en nivel 2:

```bash
# Yersinia envía el advertisement inyectado
sudo yersinia vtp -attack 1 -interface eth0
```

Lo que ocurre a nivel de red:

```
Atacante (MAC: aa:bb:cc:dd:ee:ff)
       ↓
Construye VTP Summary Advertisement
├─ Version: 2
├─ Domain: NETWORK_LAB
├─ Revision: 999 ← **CRÍTICO**
└─ New VLAN 100: "Attacker_VLAN"
       ↓
Envía a destino: 01:00:0c:cc:cc:cc (broadcast)
       ↓
┌──────────────┐
│ Switch 1     │  ← Recibe advertisement
│ (Server)     │
│              │ Lógica interna:
│ if (999 > 5) │ ← TRUE
│   aceptar()  │
│              │ Resultado: ¡Cambio aceptado!
└──────────────┘
       ↓
Actualiza VLAN database: Rev 5 → Rev 999
       ↓
Propaga a todos los switches conectados
       ↓
┌──────────────┐  ┌──────────────┐
│ Switch 2     │  │ Switch 3     │
│ Actualiza... │  │ Actualiza... │
└──────────────┘  └──────────────┘
```

### Variantes del Ataque

#### Variante A: VLAN Injection (Inyección de VLAN)

**Objetivo**: Crear una VLAN maliciosa

```
Antes:
┌─────────────────────────────┐
│ Switch VLAN Database        │
├─────────────────────────────┤
│ VLAN 1 (default)            │
│ VLAN 10 (Management)        │
│ VLAN 20 (Production)        │
│ VLAN 50 (Guest)             │
│ Revision: 5                 │
└─────────────────────────────┘

┌─────────────────────────────────────┐
│ Ataque: Advertisement malicioso     │
├─────────────────────────────────────┤
│ Domain: NETWORK_LAB                 │
│ Revision: 999                       │
│ VLAN 1 (default) + INFO...          │
│ VLAN 10 (Management) + INFO...      │
│ VLAN 20 (Production) + INFO...      │
│ VLAN 50 (Guest) + INFO...           │
│ ★ VLAN 100 (Hacker_Net) ★           │ ← NUEVA VLAN
└─────────────────────────────────────┘

Después:
┌─────────────────────────────┐
│ Switch VLAN Database        │
├─────────────────────────────┤
│ VLAN 1 (default)            │
│ VLAN 10 (Management)        │
│ VLAN 20 (Production)        │
│ VLAN 50 (Guest)             │
│ VLAN 100 (Hacker_Net)       │ ✗ Aceptada
│ Revision: 999               │ ✗ Actualizada
└─────────────────────────────┘

Impacto:
- Atacante puede asignar puertos a VLAN 100
- Tráfico de esa VLAN va a equipos del atacante
- Sniffer de datos sin encriptación
```

#### Variante B: VLAN Deletion (Eliminación de VLAN)

**Objetivo**: Inutilizar servicios críticos eliminando VLANs

```
Advertisement malicioso con marcas de deleción:

┌─────────────────────────────────────┐
│ Ataque: VLAN Deletion               │
├─────────────────────────────────────┤
│ Domain: NETWORK_LAB                 │
│ Revision: 999                       │
│ VLAN 1 (default) - Status: Active   │
│ VLAN 10 (Management) - Status: *** DELETE ***
│ VLAN 20 (Production) - Status: *** DELETE ***
│ VLAN 50 (Guest) - Status: Active    │
└─────────────────────────────────────┘

Resultado en switch:
┌─────────────────────────────┐
│ Switch VLAN Database        │
├─────────────────────────────┤
│ VLAN 1 (default) ✓           │
│ VLAN 10 ✗ ELIMINATED         │
│ VLAN 20 ✗ ELIMINATED         │
│ VLAN 50 (Guest) ✓            │
│ Revision: 999               │
└─────────────────────────────┘

Impacto de SIN VLAN 20 (Production):
- Todos los puertos asignados a VLAN 20 quedan sin servicio
- Servidores de producción desconectados
- Bloqueo de tráfico entre departamentos
- DOWNTIME DE RED
```

#### Variante C: VTP Server Takeover

**Objetivo**: Hacerse pasar por el VTP Server legítimo

```
Escenario Original:
┌──────────────────────┐
│ Switch1 (VTP Server) │ ← Autoridad
│ Rev: 25              │
│ Dominates network    │
└──────────────────────┘

Ataque:
Atacante inyecta advertisement con:
- Domain: NETWORK_LAB
- Revision: 1000  ← Superior a 25
- Comportamiento: VTP Server

Resultado:
┌─────────────────────────────────┐
│ Todos los switches ahora ven a  │
│ la máquina atacante como el     │
│ VTP Server de autoridad         │
│                                 │
│ El Switch1 original es          │
│ degradado a VTP Client          │
│ automáticamente                 │
└─────────────────────────────────┘

Consecuencia:
Atacante controla TODA la red de switches
```

---

## 📊 Análisis de Impacto

### Escala Temporal del Ataque

```
T=0s
  └─ Atacante envía advertisement malicioso

T=0.5s
  ├─ Switch 1 recibe y acepta (Rev 999 > Rev 5)
  └─ Actualiza su base de datos

T=1.5s
  ├─ Switch 1 propaga cambios a Switch 2
  ├─ Switch 1 propaga cambios a Switch 3
  └─ Switch 1 propaga cambios a Switch 4

T=3s
  ├─ Switch 2 actualiza su base de datos
  ├─ Switch 2 propaga a Switch 5, 6, 7
  └─ Cambio propagado por toda la red

T=5s
  └─ TODA la infraestructura reconfigurada ✗
```

### Cuadro de Impacto por Escenario

| Escenario | Tiempo a Impacto | Severidad | Recuperación |
|-----------|-----------------|-----------|-------------|
| Inyección de VLAN maliciosa | 5-10 segundos | 🟡 Media | Manual: 30 min |
| Eliminación de VLAN crítica | Inmediato | 🔴 Crítica | Manual: 1-2 horas |
| Takeover de VTP Server | 5 segundos | 🔴 Crítica | Aislamiento + reconfig: 2-4 horas |
| Cascade de eliminaciones | Cascada | 🔴 Crítica | Restauración desde backup: 4+ horas |

---

## 🛡️ ¿Por Qué son Vulnerables los Switches por Defecto?

### 1. Arquitectura de Confianza de VTP

```
Suposiciones incorrectas del protocolo:
├─ Supuesto: "Todos en el dominio VTP son de confianza"
│  └─ Realidad: Red VLAN puede tener switch comprometido
├─ Supuesto: "El dominio VTP es un límite de confianza"
│  └─ Realidad: Un puerto troncal abierto = acceso total
└─ Supuesto: "El número de revisión es suficiente control"
   └─ Realidad: Sin autenticación, es trivial falsificar
```

### 2. Falta de Autenticación Criptográfica

```
VTPv1/v2: "Contraseña VTP"
├─ Almacenamiento: Texto plano o débil hash
├─ Transmisión: Sin cifrado en v1, débil en v2
└─ Validación: Simple coincidencia de string

Comparación:
┌──────────────────────────────────────────┐
│ VTPv1/v2 Password ("cisco123")           │
│ Enviado en broadcast: ❌ Visible         │
│ Cifrado: ❌ No                           │
│ Validación: ❌ Trivial                   │
└──────────────────────────────────────────┘
vs.
┌──────────────────────────────────────────┐
│ VTPv3 Authentication (PSK + HMAC-SHA1)   │
│ Enviado: ✅ Cifrado                      │
│ Validación: ✅ Signature criptográfica   │
│ Resistencia: ✅ Alta                     │
└──────────────────────────────────────────┘
```

### 3. Confianza Implícita en Puertos Troncales

```
Lógica del switch:
┌────────────────┐
│ Trama llegando │
├────────────────┤
│ Destino: mult. │
│ Domain match?  │ ✓ SÍ
│ Procesar como  │
│ VTP válido ✗   │ ← Sin validar quién la envía
└────────────────┘
```

---

## 🔍 Detección de Ataques VTP

### Indicadores de Compromiso (IoCs)

1. **Cambios de Revisión Inesperados**
```cisco
! Antes: Rev 10
! Después: Rev 999 (sin cambios realizados localmente)
! Indicador: ⚠️ COMPROMISO PROBABLE
```

2. **VLANs No Documentadas Aparecidas**
```cisco
show vlan brief
! VLAN 100 Hacker_Net ← No autorizada
! Indicador: ⚠️ INYECCIÓN CONFIRMADA
```

3. **Cambios de Rol de VTP Server**
```cisco
show vtp status
! VTP Domain Name: NETWORK_LAB
! VTP Operating Mode: Server ← Cambió de Client/Transparent
! Indicador: ⚠️ HIJACK PROBABLE
```

4. **Pérdida de Sincronización Entre Switches**
```cisco
SW1# show vtp status
Revision Number: 999

SW2# show vtp status
Revision Number: 5 ← Diferencia > 100

! Indicador: ⚠️ SPLIT BRAIN NETWORK
```

5. **Logs de Cambios VTP No Autorizados**
```
VTP: Received new domain name NETWORK_LAB in VTP message
VTP: Updating revision number as 999
VTP: Creating new VLAN ID 100 in VLAN database
```

### Herramientas de Monitoreo

```bash
# Script de verificación periódica
#!/bin/bash
for switch in switch1 switch2 switch3; do
    echo "Verificando $switch..."
    ssh admin@$switch "show vtp status; show vlan brief" \
        | grep -i "revision\|unknown"
done

# Alertas:
# - Si Revision aumenta sin cambios manuales
# - Si aparecen VLANs desconocidas
# - Si status de VLANs cambia sin solicitud
```

---

## 📚 Referencias Técnicas

### RFC y Documentación
- Cisco VTP Protocol Specification (Proprietary)
- IEEE 802.1Q: Virtual Bridged Local Area Networks
- CVE Database: "VTP" + "DoS"

### Pruebas de Seguridad
- Penetration Test Execution Standard (PTES)
- OWASP Testing Guide - Layer 2

---

**Última actualización**: Febrero 2026
