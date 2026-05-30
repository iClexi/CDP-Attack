# CDP DoS Attack Lab

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Platform](https://img.shields.io/badge/Platform-Kali%20Linux-red)
![Lab](https://img.shields.io/badge/Environment-GNS3%20%7C%20IOSvL2-orange)
![Status](https://img.shields.io/badge/Use-Controlled%20Lab-yellow)
![Security](https://img.shields.io/badge/Topic-Network%20Security-purple)

## Aviso de uso responsable

Este proyecto fue desarrollado únicamente con fines educativos, académicos y de laboratorio controlado.
El script debe ejecutarse solamente en entornos propios o autorizados, como GNS3, EVE-NG, PNETLab o laboratorios internos de pruebas.

No debe utilizarse en redes públicas, empresariales o de terceros sin autorización explícita.

---

## Descripción

Este laboratorio demuestra un ataque de denegación de servicio lógico mediante el abuso del protocolo **CDP, Cisco Discovery Protocol**.

CDP es un protocolo de capa 2 utilizado por dispositivos Cisco para descubrir vecinos directamente conectados. Al enviar una gran cantidad de paquetes CDP falsificados hacia un switch, el dispositivo puede verse obligado a procesar anuncios inválidos o maliciosos, consumir recursos de CPU y llenar su tabla de vecinos CDP con entradas falsas.

El objetivo principal del laboratorio es demostrar el impacto del ataque y aplicar una contramedida efectiva para mitigarlo.

---

## Objetivo del laboratorio

Demostrar cómo un atacante conectado a un puerto de acceso puede abusar del protocolo CDP para generar carga en un switch Cisco IOSvL2 dentro de una topología controlada.

---

## Objetivo del script

El script `cdp-attack.py` genera múltiples tramas CDP falsificadas y las envía por la interfaz seleccionada. Cada trama contiene valores variables para simular vecinos CDP falsos, provocando que el switch procese una gran cantidad de anuncios CDP.

---

## Topología utilizada

```text
                   +----------------+
                   |      R-1       |
                   | 192.168.58.1   |
                   | Fa0/0          |
                   +-------+--------+
                           |
                           |
                    Gi0/0  |
                   +-------+--------+
                   |     SW-1       |
                   |   IOSvL2       |
                   +---+--------+---+
                       |        |
                 Gi0/1 |        | Gi0/2
                       |        |
              +--------+        +--------+
              |                          |
        +-----+-----+              +-----+-----+
        |   Kali    |              |   VPC     |
        |192.168.58.3              |192.168.58.2
        +-----------+              +-----------+
```

---

## Direccionamiento IP

| Dispositivo | Interfaz |    Dirección IP | Descripción                |
| ----------- | -------- | --------------: | -------------------------- |
| R-1         | Fa0/0    | 192.168.58.1/24 | Gateway de la red          |
| SW-1        | Gi0/0    |             N/A | Conexión hacia R-1         |
| SW-1        | Gi0/1    |             N/A | Puerto hacia Kali atacante |
| SW-1        | Gi0/2    |             N/A | Puerto hacia VPC víctima   |
| Kali        | eth1     | 192.168.58.3/24 | Máquina atacante           |
| VPC         | eth0     | 192.168.58.2/24 | Equipo de prueba           |

---

## Requisitos

### Sistema atacante

* Kali Linux
* Python 3
* Permisos de superusuario
* Conectividad directa de capa 2 hacia el switch
* Interfaz conectada a la red del laboratorio

### Dispositivo de red

* Switch Cisco IOSvL2
* CDP habilitado en el puerto conectado al atacante
* Laboratorio en GNS3, EVE-NG, PNETLab o entorno equivalente

---

## Instalación

Clonar el repositorio:

```bash
git clone https://github.com/iClexi/CDP-Attack.git
cd CDP-Attack
```

Dar permisos de ejecución:

```bash
chmod +x cdp-attack.py
```

Verificar sintaxis del script:

```bash
python3 -m py_compile cdp-attack.py
```

---

## Uso básico

Ejecutar el script:

```bash
sudo python3 cdp-attack.py
```

El script mostrará las interfaces disponibles y pedirá seleccionar la interfaz conectada al switch.

Ejemplo:

```text
Interfaces disponibles:

1. eth0 UP 192.168.202.x/24
2. eth1 UP 192.168.58.3/24

Selecciona la interfaz conectada al switch [Enter = eth0]:
```

En este laboratorio, la interfaz correcta es la que pertenece a la red `192.168.58.0/24`.

---

## Uso directo

Ejecutar directamente por una interfaz específica:

```bash
sudo python3 cdp-attack.py -i eth1 --yes
```

---

## Parámetros disponibles

| Parámetro        | Descripción                                                       |   Valor por defecto |
| ---------------- | ----------------------------------------------------------------- | ------------------: |
| `-i`, `--iface`  | Interfaz de red utilizada para enviar las tramas CDP              | Pregunta al usuario |
| `--pps`          | Paquetes por segundo. Si es `0`, envía sin límite                 |                 `0` |
| `--count`        | Cantidad total de paquetes a enviar. Si es `0`, no tiene límite   |                 `0` |
| `--duration`     | Duración del ataque en segundos. Si es `0`, corre indefinidamente |                 `0` |
| `--ttl`          | Tiempo de vida de los anuncios CDP                                |               `255` |
| `--prefix`       | Prefijo usado para los vecinos CDP falsos                         |          Automático |
| `--extra`        | Tamaño adicional agregado al campo de software CDP                |              `1450` |
| `--pool`         | Cantidad de tramas CDP preconstruidas por worker                  |            `200000` |
| `--workers`      | Procesos paralelos. Si es `0`, usa todos los hilos detectados     |                 `0` |
| `--vlan`         | VLAN nativa anunciada en los paquetes CDP                         |                `58` |
| `--payload-size` | Tamaño máximo controlado del payload                              |              `1500` |
| `--random-src`   | Usa MAC origen aleatoria en cada trama                            |         Desactivado |
| `--yes`          | Inicia sin pedir confirmación                                     |         Desactivado |

---

## Funcionamiento técnico

El script construye tramas CDP falsas utilizando encapsulación de capa 2 con LLC/SNAP.
Cada paquete contiene TLVs de CDP como:

* Device ID
* Address
* Port ID
* Capabilities
* Platform
* Native VLAN
* Duplex
* Software Version

El campo **Device ID** cambia constantemente para provocar que el switch registre múltiples vecinos falsos.
El prefijo del ataque se genera automáticamente en cada ejecución usando una marca de tiempo, lo que permite crear nuevos conjuntos de vecinos falsificados en cada prueba.

Ejemplo de nombres generados:

```text
CDP-DOS-MICHAEL-1780001234-0-1201-88123
CDP-DOS-MICHAEL-1780001234-1-5520-44291
CDP-DOS-MICHAEL-1780001234-2-9311-77610
```

---

## Evidencia esperada del ataque

Antes de ejecutar el ataque, el switch debe tener bajo consumo de CPU y pocos vecinos CDP.

Comandos de verificación inicial:

```cisco
enable
terminal length 0
clear cdp table
clear cdp counters
show processes cpu sorted | include CPU|CDP|IOSv e1000|UDLD|Exec|console
show cdp traffic
show cdp neighbors
```

Durante la ejecución del script, se espera observar:

* Aumento del uso de CPU
* Aumento de paquetes CDP recibidos
* Entradas CDP falsas generadas por Kali
* Consumo del proceso `CDP Protocol`
* Consumo del proceso `IOSv e1000`
* Posible lentitud en la consola del switch

Comandos para validar el ataque:

```cisco
show processes cpu sorted | include CPU|CDP|IOSv e1000|UDLD|Exec|console
show cdp traffic
show cdp neighbors
show cdp entry *
```

---

## Ejemplo de resultado esperado

```text
CPU utilization for five seconds: 49%/0%; one minute: 22%; five minutes: 11%
CDP Protocol              13.91%
IOSv e1000                12.95%
```

```text
CDP counters:
Total packets output: 261, Input: 29322
CDP version 2 advertisements output: 261, Input: 29322
```

```text
Total cdp entries displayed : 11787
```

Estos resultados evidencian que el switch está procesando una gran cantidad de anuncios CDP falsificados.

---

## Captura con Wireshark

Para validar el tráfico en Wireshark, iniciar captura en el enlace entre Kali y el switch.

Filtros recomendados:

```text
cdp
```

```text
eth.dst == 01:00:0c:cc:cc:cc
```

El destino multicast `01:00:0c:cc:cc:cc` corresponde al tráfico CDP.

---

## Contramedida aplicada

La mitigación principal consiste en deshabilitar CDP en puertos de acceso o puertos no confiables.

En este laboratorio, Kali está conectado a `GigabitEthernet0/1`, por lo tanto se aplica:

```cisco
configure terminal
interface gigabitEthernet0/1
no cdp enable
end
write memory
```

Luego se limpian las entradas y contadores CDP:

```cisco
clear cdp table
clear cdp counters
```

---

## Verificación de la mitigación

Después de aplicar la contramedida, ejecutar nuevamente el script y validar que el switch no aprenda vecinos CDP falsos desde el puerto del atacante.

Comandos de verificación:

```cisco
show cdp interface gigabitEthernet0/1
show cdp neighbors
show cdp traffic
show processes cpu sorted | include CPU|CDP|IOSv e1000|UDLD|Exec|console
```

Resultado esperado:

* La interfaz hacia Kali no debe procesar CDP.
* No deben generarse nuevas entradas CDP falsas desde `Gi0/1`.
* El proceso `CDP Protocol` debe reducir su consumo.
* La tabla de vecinos CDP debe mantenerse limpia o mostrar únicamente vecinos legítimos.

---

## Flujo recomendado para el video

1. Mostrar la topología en GNS3.
2. Mostrar nombre y matrícula.
3. Mostrar fecha y hora del sistema.
4. Mostrar que CDP está activo.
5. Mostrar el estado inicial del switch.
6. Ejecutar el script desde Kali.
7. Mostrar aumento de CPU y entradas CDP falsas.
8. Mostrar captura en Wireshark.
9. Aplicar la contramedida.
10. Ejecutar nuevamente el script.
11. Confirmar que la mitigación funciona.
12. Cerrar con una conclusión técnica.

---

## Comandos útiles para grabación

En Kali:

```bash
ip -br a
sudo python3 cdp-attack.py -i eth1 --yes
```

En el switch:

```cisco
terminal length 0
clear cdp table
clear cdp counters
show processes cpu sorted | include CPU|CDP|IOSv e1000|UDLD|Exec|console
show cdp traffic
show cdp neighbors
show cdp entry *
```

Mitigación:

```cisco
configure terminal
interface gigabitEthernet0/1
no cdp enable
end
write memory
clear cdp table
clear cdp counters
```

---

## Troubleshooting

### El script muestra `packets=0`

Posibles causas:

* Interfaz incorrecta
* Interfaz apagada
* Error de permisos
* Trama demasiado grande
* El enlace virtual no está activo

Verificar interfaces:

```bash
ip -br a
ip -br link
```

Levantar interfaz:

```bash
sudo ip link set eth1 up
```

Ejecutar con permisos:

```bash
sudo python3 cdp-attack.py -i eth1 --yes
```

---

### El CPU sube y baja

Es normal en IOSvL2. El procesamiento ocurre por ráfagas y el entorno virtual introduce variaciones.
La evidencia no depende únicamente del porcentaje de CPU, sino también de:

* Paquetes CDP recibidos
* Entradas CDP falsas
* Proceso `CDP Protocol`
* Proceso `IOSv e1000`
* Lentitud en consola
* Captura en Wireshark

---

### No aparecen vecinos falsos

Verificar que CDP esté activo:

```cisco
show cdp
show cdp interface gigabitEthernet0/1
```

Activar CDP si fue deshabilitado anteriormente:

```cisco
configure terminal
cdp run
interface gigabitEthernet0/1
cdp enable
end
```

---

## Estructura recomendada del repositorio

```text
CDP-Attack/
├── cdp-attack.py
├── README.md
├── captures/
│   ├── cpu-before.png
│   ├── cpu-during.png
│   ├── cdp-neighbors.png
│   └── mitigation.png
├── docs/
│   └── technical-report.md
└── video/
    └── youtube-link.txt
```

---

## Temas sugeridos para GitHub

```text
cdp
cisco
gns3
iosvl2
network-security
cybersecurity
dos-attack
lab
python
packet-crafting
```

---
## Mitigación del ataque CDP DoS

La mitigación del ataque CDP DoS se basa en reducir la exposición del protocolo CDP en puertos no confiables. CDP es útil para administración y descubrimiento entre dispositivos Cisco, pero no debe estar habilitado en puertos de usuario final, laboratorios con máquinas atacantes, equipos externos o interfaces donde no exista una necesidad administrativa clara.

### Controles aplicados

### 1. Deshabilitar CDP en puertos no confiables

La contramedida principal consiste en apagar CDP en los puertos conectados a usuarios o equipos no confiables.

```cisco
interface range gigabitEthernet0/1 - 2
no cdp enable
```

Con esto, el switch deja de procesar anuncios CDP provenientes de Kali o de cualquier equipo conectado a esos puertos.

### 2. Mantener CDP solo en enlaces confiables

CDP puede mantenerse habilitado únicamente en enlaces administrados entre dispositivos de red, por ejemplo entre el switch y el router.

```cisco
interface gigabitEthernet0/0
cdp enable
```

Esta práctica permite conservar visibilidad administrativa sin exponer CDP en puertos de acceso.

### 3. Configurar los puertos como access

Los puertos de usuario deben configurarse explícitamente como access para evitar negociación dinámica o comportamientos no deseados.

```cisco
interface range gigabitEthernet0/1 - 2
switchport mode access
switchport access vlan 58
switchport nonegotiate
```

### 4. Aplicar storm-control

CDP utiliza tráfico multicast de capa 2. Aunque la mitigación principal es deshabilitar CDP, storm-control ayuda a limitar tráfico excesivo broadcast, multicast o unicast desconocido en puertos de acceso.

```cisco
interface range gigabitEthernet0/1 - 2
storm-control broadcast level 1.00
storm-control multicast level 1.00
storm-control unicast level 1.00
```

### 5. Aplicar Port Security

Port Security limita la cantidad de direcciones MAC permitidas por puerto. Esto no reemplaza `no cdp enable`, pero ayuda a endurecer el puerto ante ataques de capa 2 combinados.

```cisco
interface range gigabitEthernet0/1 - 2
switchport port-security
switchport port-security maximum 1
switchport port-security violation restrict
switchport port-security mac-address sticky
```

### 6. Endurecimiento STP en puertos de usuario

Aunque BPDU Guard no mitiga directamente CDP DoS, protege los puertos de acceso contra ataques relacionados con STP.

```cisco
interface range gigabitEthernet0/1 - 2
spanning-tree portfast
spanning-tree bpduguard enable
```

---

## Verificación de la mitigación

Después de aplicar la configuración, se limpian las entradas CDP y los contadores:

```cisco
clear cdp table
clear cdp counters
```

Luego se valida el estado del switch:

```cisco
show cdp interface
show cdp neighbors
show cdp traffic
show processes cpu sorted | include CPU|CDP|IOSv e1000|Exec|console
show port-security
show storm-control
```

### Resultado esperado

Después de aplicar la mitigación:

* Los puertos no confiables no deben procesar CDP.
* No deben aparecer vecinos falsos generados desde Kali.
* La tabla CDP debe mostrar solo vecinos legítimos.
* El proceso `CDP Protocol` no debe elevarse de forma anormal.
* El switch debe mantener estabilidad aunque el script siga enviando tráfico desde el atacante.

---

## Conclusión

El laboratorio demuestra que CDP puede ser abusado por un atacante conectado a un puerto de acceso para generar carga innecesaria en un switch Cisco.
La mitigación general recomendada consiste en aplicar una defensa por capas. Primero se deshabilita CDP en puertos no confiables, luego se restringen los puertos como access, se desactiva la negociación dinámica, se limita tráfico excesivo con storm-control y se endurecen los puertos con Port Security y BPDU Guard.

La medida más importante contra CDP DoS es `no cdp enable` en puertos de usuario. Los demás controles complementan la protección general de capa 2.

Este tipo de práctica ayuda a comprender la importancia de endurecer configuraciones de capa 2 y aplicar controles preventivos en redes empresariales.

---

## Autor

**Michael Robles / iClexi**
Laboratorio de Seguridad de Redes
Proyecto académico de ataque y mitigación CDP DoS
