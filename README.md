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

## Archivos del repositorio

| Archivo                                                  | Descripción                                                                                                    |
| -------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| [`cdp-attack.py`](./cdp-attack.py)                       | Script principal utilizado para ejecutar el ataque CDP DoS desde Kali Linux.                                   |
| [`mitigacion-cdp-attack.md`](./mitigacion-cdp-attack.md) | Documento técnico con la mitigación general contra ataques CDP DoS.                                            |
| [`README.md`](./README.md)                               | Documentación principal del laboratorio, uso del script, evidencia esperada y flujo recomendado para el video. |

---

## Descripción

Este laboratorio demuestra un ataque de denegación de servicio lógico mediante el abuso del protocolo **CDP, Cisco Discovery Protocol**.

CDP es un protocolo de capa 2 utilizado por dispositivos Cisco para descubrir vecinos directamente conectados. Al enviar una gran cantidad de paquetes CDP falsificados hacia un switch, el dispositivo puede verse obligado a procesar anuncios maliciosos, consumir recursos de CPU y llenar su tabla de vecinos CDP con entradas falsas.

El objetivo principal del laboratorio es demostrar el impacto del ataque y aplicar una contramedida efectiva para mitigarlo.

---

## Base del direccionamiento IP

El direccionamiento IP del laboratorio fue definido tomando como base la matrícula:

```text
20250845
```

Separando la matrícula en octetos, se obtuvo la dirección base:

```text
20.25.8.45
```

A partir de esta dirección se creó la red del laboratorio:

```text
20.25.8.0/24
```

---

## Objetivo del laboratorio

Demostrar cómo un atacante conectado a un puerto de acceso puede abusar del protocolo CDP para generar carga en un switch Cisco IOSvL2 dentro de una topología controlada.

---

## Objetivo del script

El script [`cdp-attack.py`](./cdp-attack.py) genera múltiples tramas CDP falsificadas y las envía por la interfaz seleccionada. Cada trama contiene valores variables para simular vecinos CDP falsos, provocando que el switch procese una gran cantidad de anuncios CDP.

---

## Topología utilizada

```text
                   +----------------+
                   |      R-1       |
                   | 20.25.8.45     |
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
        |   Kali    |              |    VPC    |
        | 20.25.8.46|              |20.25.8.47 |
        +-----------+              +-----------+
```

---

## Direccionamiento IP

| Dispositivo | Interfaz |  Dirección IP | Descripción                |
| ----------- | -------- | ------------: | -------------------------- |
| R-1         | Fa0/0    | 20.25.8.45/24 | Gateway de la red          |
| SW-1        | Gi0/0    |           N/A | Conexión hacia R-1         |
| SW-1        | Gi0/1    |           N/A | Puerto hacia Kali atacante |
| SW-1        | Gi0/2    |           N/A | Puerto hacia VPC víctima   |
| Kali        | eth1     | 20.25.8.46/24 | Máquina atacante           |
| VPC         | eth0     | 20.25.8.47/24 | Equipo de prueba           |

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

## Configuración IP base del laboratorio

### Router R-1

```cisco
enable
configure terminal

interface fastEthernet0/0
ip address 20.25.8.45 255.255.255.0
no shutdown

end
write memory
```

Si el router usa `GigabitEthernet0/0`, se cambia la interfaz:

```cisco
interface gigabitEthernet0/0
ip address 20.25.8.45 255.255.255.0
no shutdown
```

### VPC

```text
ip 20.25.8.47/24 20.25.8.45
```

### Kali

Si la interfaz del laboratorio es `eth1`:

```bash
sudo ip addr flush dev eth1
sudo ip addr add 20.25.8.46/24 dev eth1
sudo ip link set eth1 up
sudo ip route replace default via 20.25.8.45
```

---

## Pruebas de conectividad

Desde VPC:

```text
ping 20.25.8.45
ping 20.25.8.46
```

Desde Kali:

```bash
ping -c 4 20.25.8.45
ping -c 4 20.25.8.47
```

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
2. eth1 UP 20.25.8.46/24

Selecciona la interfaz conectada al switch [Enter = eth0]:
```

En este laboratorio, la interfaz correcta es la que pertenece a la red:

```text
20.25.8.0/24
```

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

El campo **Device ID** cambia constantemente para provocar que el switch registre múltiples vecinos falsos. El prefijo del ataque se genera automáticamente en cada ejecución usando una marca de tiempo, lo que permite crear nuevos conjuntos de vecinos falsificados en cada prueba.

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

* Aumento del uso de CPU.
* Aumento de paquetes CDP recibidos.
* Entradas CDP falsas generadas por Kali.
* Consumo del proceso `CDP Protocol`.
* Consumo del proceso `IOSv e1000`.
* Posible lentitud en la consola del switch.

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

## Mitigación

La mitigación principal consiste en deshabilitar CDP en puertos de acceso o puertos no confiables.

La documentación completa de mitigación está disponible aquí:

* [`mitigacion-cdp-attack.md`](./mitigacion-cdp-attack.md)

Ejemplo básico aplicado al puerto del atacante:

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
9. Aplicar la contramedida documentada en [`mitigacion-cdp-attack.md`](./mitigacion-cdp-attack.md).
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

Mitigación básica:

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

* Interfaz incorrecta.
* Interfaz apagada.
* Error de permisos.
* Trama demasiado grande.
* El enlace virtual no está activo.

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

* Paquetes CDP recibidos.
* Entradas CDP falsas.
* Proceso `CDP Protocol`.
* Proceso `IOSv e1000`.
* Lentitud en consola.
* Captura en Wireshark.

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
├── README.md
├── cdp-attack.py
├── mitigacion-cdp-attack.md
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

## Conclusión

El laboratorio demuestra que CDP puede ser abusado por un atacante conectado a un puerto de acceso para generar carga innecesaria en un switch Cisco.

La mitigación principal contra CDP DoS es deshabilitar CDP en puertos no confiables mediante `no cdp enable`. Esta práctica permite mantener CDP únicamente en enlaces administrados y reduce la posibilidad de que equipos externos generen carga o entradas CDP falsas.

Para más detalles, revisar el documento de mitigación:

* [`mitigacion-cdp-attack.md`](./mitigacion-cdp-attack.md)

---

## Autor

**Michael Robles / iClexi**
Laboratorio de Seguridad de Redes
Proyecto académico de ataque y mitigación CDP DoS
