# MITIGACIÓN: Defensa contra Ataques VTP

## 🛡️ Estrategias de Defensa Multicapas

VTP es un protocolo inseguro por diseño. Las medidas de mitigación van desde actualizaciones de configuración hasta cambios arquitectónicos.

---

## 1️⃣ Nivel Básico: Contraseña de Dominio VTP

### Implementación

```cisco
Switch(config)# vtp domain NETWORK_LAB
Switch(config)# vtp password MiContraseña123Fuerte
Switch(config)# vtp mode server
```

### Limitaciones

❌ **VTPv1/v2**: La contraseña viaja sin cifrar en el tráfico
```
Captura con Wireshark:
Frame 42: 62 bytes on wire (496 bits)
...
VTP: Password = "MiContraseña123Fuerte"  ← ¡VISIBLE EN PCAP!
```

❌ **Fácil de crackear**: Diccionarios de contraseñas VTP comunes

❌ **Sin protección contra cambios masivos**: Solo verifica dominio, no origen

### Cuándo usar
✅ Solo como medida complementaria
✅ En entornos de confianza parcial
✅ Temporales mientras se implementa otra solución

### Configuración Segura
```cisco
! Establecer contraseña fuerte y única
Switch(config)# vtp password $Ch1ff0nV0It0r0V4s@2024!
Switch(config)# vtp mode server

! Verificar configuración
Switch# show vtp password
Password: *** (hidden)
```

---

## 2️⃣ Nivel Intermedio: Modo VTP Transparent (RECOMENDADO)

### ¿Qué es Modo Transparent?

En modo Transparent, el switch **NO participa** en la sincronización automática de VLANs. Actúa como un "pasito" neutral.

### Implementación

```cisco
! Cambiar a modo Transparent
Switch(config)# vtp mode transparent

! Verificar cambio
Switch# show vtp status
VTP Operating Mode: Transparent
Configuration Revision Number: 0
```

### Ventajas

✅ **Bloquea completamente ataques VTP**: No acepta cambios remotos
✅ **Simplicidad operacional**: Un switch, una configuración local
✅ **Independencia arquitectónica**: No depende de otros switches
✅ **Seguridad por diseño**: Sin atacable de VTP

### Desventajas

❌ Cambios manuales en cada switch (sin propagación automática)
❌ Administración más laboriosa en redes grandes
❌ Mayor posibilidad de inconsistencias de configuración

### Caso de Uso Típico

```
Red Pequeña/Mediana: 3-10 switches
└─ Todos en modo Transparent
   └─ Admin manual de VLANs en cada uno
   └─ Aprovisionamiento vía CLI o Ansible

Red Grande: 50+ switches
├─ Switches core: Transparent
├─ Switches distribución: Transparent
├─ Switches acceso: Transparent
└─ Aprovisionamiento centralizado con sistema de orquestación
```

### Configuración Completa Ejemplo

```cisco
! ==================== SWITCH 1 ====================
Switch1# configure terminal
Switch1(config)# vtp mode transparent
Switch1(config)# vlan 10
Switch1(config-vlan)# name Management
Switch1(config-vlan)# exit
Switch1(config)# vlan 20
Switch1(config-vlan)# name Production
Switch1(config)# vlan 50
Switch1(config-vlan)# name Guest

! ==================== SWITCH 2 ====================
! Configuración IDÉNTICA, hecha MANUALMENTE
Switch2# configure terminal
Switch2(config)# vtp mode transparent
Switch2(config)# vlan 10
Switch2(config-vlan)# name Management
! ... (repetir para todas las VLANs)

! Resultado: Ambos switches tienen las mismas VLANs
! pero NO por sincronización: POR CONFIGURACIÓN MANUAL IDÉNTICA
```

---

## 3️⃣ Nivel Avanzado: VTPv3 con Autenticación

### Mejoras de VTPv3

```cisco
! Cambiar a VTPv3
Switch(config)# vtp version 3
Switch(config)# vtp primary  # Designar servidor primario

! Autenticación PSK (Pre-Shared Key)
Switch(config)# vtp password SecureKey123!

Switch# show vtp status
VTP Version running: 3
VTP Domain Name: NETWORK_LAB
VTP Mode: Primary
VTP Primary Server: Self
Authentication Type: Secret (SHA-1 HMAC)
```

### Características Criptográficas

```
VTPv3 Uses:
├─ HMAC-SHA1 para autenticación
├─ Cifrado de contraseña en tráfico
├─ Validación de integridad de mensajes
└─ Soporte para múltiples servidores primarios

Estructura de seguridad:
┌─────────────────────────────────────────┐
│ Advertencia VTP recibida                │
├─────────────────────────────────────────┤
│ 1. Verificar HMAC-SHA1 ✓                │
│ 2. Si HMAC != esperado → Descartar ✗   │
│ 3. Si válido, verificar origen ✓        │
│ 4. Si origen autorizado, aceptar ✓      │
└─────────────────────────────────────────┘
```

### Implementación Paso a Paso

```cisco
! ========== SERVIDOR PRIMARIO ==========
Primary# configure terminal
Primary# vtp version 3
Primary# vtp primary vlan
Changing VTP version from 1 to 3
Changing VTP mode to SERVER for vlan feature

Primary# vtp password MyV3Password123
Primary# vtp mode primary

! ========== SERVIDORES SECUNDARIOS ==========
Secondary# configure terminal
Secondary# vtp version 3
Secondary# vtp password MyV3Password123  ← Misma PSK
Secondary# vtp mode server
Secondary# vtp primary ipaddress <IP_del_primario>

! ========== VERIFICACIÓN ==========
# show vtp status
VTP Version running: 3
VTP Feature Version: 3
VTP Mode: Primary Server
VTP Domain Name: NETWORK_LAB
```

### Limitaciones de VTPv3

❌ Solo en switches Cisco modernos (Catalyst 3650+)
❌ No compatible con VTPv1/v2 en la misma red
❌ Aún requiere dominio VTP válido preconfigurado

---

## 4️⃣ Control de Puertos: Port Security

Impedir que dispositivos válidos/no autorizados accedan al puerto troncal.

```cisco
! En puerto de acceso de usuario (protección contra conexión atacante)
Switch(config)# interface GigabitEthernet0/0/5
Switch(config-if)# switchport mode access
Switch(config-if)# switchport access vlan 10
Switch(config-if)# switchport port-security
Switch(config-if)# switchport port-security maximum 1
Switch(config-if)# switchport port-security mac-address sticky
Switch(config-if)# switchport port-security violation restrict

! Verificar
Switch# show port-security interface Gi0/0/5
Port Security: Enabled
Port Status: Secure-up
Violation Mode: Restrict
Maximum MAC Addresses: 1
Total MAC Addresses: 1
Configured MAC Addresses: 0
Sticky MAC Addresses: 1
Last Source Address: aabb.ccdd.ee00
Security Violation Count: 0
```

### BPDU Guard (Protección contra Spanning Tree)

```cisco
! En puertos de acceso (no troncales)
Switch(config)# interface range Gi0/0/1-24
Switch(config-if-range)# spanning-tree bpduguard enable

! En puertos troncales: USAR CON CUIDADO
Switch(config)# interface Gi0/0/48
Switch(config-if)# switchport trunk encapsulation dot1q
Switch(config-if)# switchport mode trunk
! NO usar BPDU Guard aquí (bloquearía switches legítimos)
```

---

## 5️⃣ Deshabilitación de DTP (Dynamic Trunking Protocol)

VTP se propaga principalmente por puertos troncales. Deshabilitar DTP en puertos de usuario:

```cisco
! En puertos de usuario (NO troncal)
Switch(config)# interface range Gi0/0/1-24
Switch(config-if-range)# switchport nonegotiate

! En puertos troncales entre switches
Switch(config)# interface Gi0/0/48
Switch(config-if)# switchport mode trunk  ← Modo fijo
Switch(config-if)# switchport nonegotiate  ← Sin negociación

! Verificar
Switch# show interface trunk
Port        Mode      Encapsulation  Status  Native vlan
Gi0/0/48    on        802.1q         trunking  1
         ^
      Fijo (no negotiado)
```

**Impacto en VTP**:
```
Sin puertos troncales dinámicos:
├─ Atacante no puede crear puerto troncal dinámicamente
├─ VTP se propaga solo en puertos con trunking manual
└─ Control explícito de dónde se propagan cambios
```

---

## 6️⃣ Estrategia de Arquitectura: Separación de Dominios

Usar múltiples dominios VTP en lugar de uno central:

```
Arquitectura Original (1 dominio, alto riesgo):
┌────────────────────────────────────────┐
│ Dominio: NETWORK_LAB (único)           │
├────────────────────────────────────────┤
│ SW1 (Core) ← Compromiso → Toda la red  │
├────────────────────────────────────────┤
│ SW2, SW3, SW4, SW5, SW6, SW7, SW8      │ Cascada de impacto
│ Todo sincronizado → Todo afectado      │
└────────────────────────────────────────┘

Arquitectura Segura (múltiples dominios):
┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐
│ Dominio: CORE_LAB  │  │ Dominio: BUILD_LAB │  │ Dominio: GUEST_LAB │
├────────────────────┤  ├────────────────────┤  ├────────────────────┤
│ SW1, SW2           │  │ SW3, SW4           │  │ SW5, SW6           │
│ (Networking core)  │  │ (Build environ)    │  │ (Guest network)    │
│                    │  │                    │  │                    │
│ Compromiso local → │  │ Compromiso local → │  │ Compromiso local → │
│ Aislado a 2 switches│ │ Aislado a 2 switches│ │ Aislado a 2 switches│
└────────────────────┘  └────────────────────┘  └────────────────────┘
```

---

## 7️⃣ Monitoreo y Detección

### Script de Verificación Periódica

```bash
#!/bin/bash
# check_vtp_integrity.sh

SWITCHES=("192.168.1.1" "192.168.1.2" "192.168.1.3")
EXPECTED_REVISION=10
ALERT_EMAIL="admin@itla.edu.do"

for switch_ip in "${SWITCHES[@]}"; do
    echo "Verificando $switch_ip..."
    
    # Obtener revision actual
    CURRENT_REV=$(sshpass -p "password" ssh -o StrictHostKeyChecking=no \
                  admin@$switch_ip "show vtp status" | grep "Revision" \
                  | awk '{print $NF}')
    
    # Alertar si hay cambios inesperados
    if [ "$CURRENT_REV" -gt "$EXPECTED_REVISION" ]; then
        echo "⚠️ ALERTA: Revisión anómala en $switch_ip: $CURRENT_REV"
        echo "Revisión esperada: $EXPECTED_REVISION" | \
            mail -s "ALERTA VTP: Posible compromiso en $switch_ip" $ALERT_EMAIL
    fi
    
    # Verificar VLANs no conocidas
    UNKNOWN_VLANS=$(sshpass -p "password" ssh -o StrictHostKeyChecking=no \
                    admin@$switch_ip "show vlan brief" | \
                    grep -v "VLAN.*Name" | grep -v "1.*default" | \
                    grep -v "10.*Management" | grep -v "20.*Production")
    
    if [ ! -z "$UNKNOWN_VLANS" ]; then
        echo "⚠️ ALERTA: VLANs desconocidas en $switch_ip"
        echo "$UNKNOWN_VLANS" | mail -s "ALERTA: VLANs no autorizadas" $ALERT_EMAIL
    fi
done
```

### Alertas en Wireshark

```
Configurar filtros para detectar anómalas:

1. Cambios de Revisión Inesperados
Display Filter: vtp && vtp.revision > 50
√ Alerta si revision sube > 50 (anomalía)

2. Advertising desdeMACs desconocidas
Display Filter: vtp && !(eth.src == 00:1a:2b:3c:4d:5e)
√ Alerta si VTP no viene del switch conocido

3. Cambios de Configuración VTP
Display Filter: vtp.type == 0x02
√ Mostrar subset advertisements (cambios reales)
```

---

## 📋 Checklist de Implementación

```
[ ] 1. Inventariar todos los switches de red
    └─ IP, modelo, software version

[ ] 2. Documentar configuración VTP actual
    └─ Dominios, servidores, clientes, transparent

[ ] 3. Planificar transición a Transparent o VTPv3
    └─ Cronograma de cambios
    └─ Ventana de mantenimiento

[ ] 4. Implementar por etapas
    └─ Fase 1: Switches no críticos
    └─ Fase 2: Switches de distribución
    └─ Fase 3: Switches core

[ ] 5. Deshabilitar DTP en puertos de usuario
    └─ switchport nonegotiate en Gi0/0/1-24

[ ] 6. Configurar monitoreo
    └─ Script de verificación periódica
    └─ Alertas en SIEM

[ ] 7. Entrenar personal
    └─ Cambios de procedimiento (manual vs automático)
    └─ Troubleshooting de inconsistencias

[ ] 8. Documentar todos los cambios
    └─ Baseline de configuración
    └─ Runway de VLANs autorizadas
```

---

## 🎯 Resumen de Controles por Escenario

| Escenario de Ataque | Control Primario | Control Secundario | Control Terciario |
|-----|-----|-----|-----|
| **VLAN Injection** | Modo Transparent | VTPv3 + PSK | Port Security |
| **VLAN Deletion** | Modo Transparent | VTPv3 + PSK | Backup de config |
| **Server Takeover** | Modo Transparent | VTPv3 + Auth | BPDU Guard |
| **Cascada de cambios** | Modo Transparent | Dominios separados | Monitoreo 24/7 |

---

## 🔐 Ejemplo: Configuración Segura Completa

```cisco
! ==================== SWITCH CORE ====================
Switch# configure terminal

! 1. Modo Transparent (principal defensa)
Switch(config)# vtp mode transparent

! 2. Deshabilitar DTP en puertos de usuario
Switch(config)# interface range Gi0/0/1-24
Switch(config-if-range)# switchport mode access
Switch(config-if-range)# switchport nonegotiate
Switch(config-if-range)# switchport port-security
Switch(config-if-range)# exit

! 3. Puertos troncales: Manual + seguro
Switch(config)# interface Gi0/0/47-48
Switch(config-if-range)# switchport mode trunk
Switch(config-if-range)# switchport trunk encapsulation dot1q
Switch(config-if-range)# switchport nonegotiate
Switch(config-if-range)# switchport trunk allowed vlan 1,10,20,50
Switch(config-if-range)# spanning-tree portfast disable
Switch(config-if-range)# exit

! 4. Configuración local de VLANs
Switch(config)# vlan 1
Switch(config-vlan)# name default
Switch(config-vlan)# vlan 10
Switch(config-vlan)# name Management
Switch(config-vlan)# vlan 20
Switch(config-vlan)# name Production
Switch(config-vlan)# vlan 50
Switch(config-vlan)# name Guest
Switch(config-vlan)# exit

! 5. Guardar configuración
Switch(config)# exit
Switch# copy running-config startup-config
```

---

**Última actualización**: Febrero 2026  
**Nivel de Seguridad Recomendado**: Modo Transparent en redes con potencial de compromiso físico
