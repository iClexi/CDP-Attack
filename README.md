# Ataque DoS mediante CDP

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Platform](https://img.shields.io/badge/Platform-Kali%20Linux-red)
![Environment](https://img.shields.io/badge/Environment-GNS3%20%7C%20IOSvL2-orange)
![Use](https://img.shields.io/badge/Use-Controlled%20Lab-yellow)
![Topic](https://img.shields.io/badge/Topic-Network%20Security-purple)

## Información del proyecto

Este repositorio contiene un laboratorio académico de **Seguridad de Redes** donde se demuestra un ataque de **Denegación de Servicio DoS mediante Cisco Discovery Protocol CDP** en una topología controlada de GNS3.

El laboratorio fue realizado por:

**Michael David Robles Fermín**  
**iClexi**  
**Matrícula:** 2025-0845

## Repositorio del proyecto:

[https://github.com/iClexi/CDP-Attack](https://github.com/iClexi/CDP-Attack)

## Video demostrativo

La demostración práctica del ataque y su mitigación está disponible en YouTube:

[Ver video del laboratorio en YouTube](https://www.youtube.com/watch?v=edOAM4gyGzo)

URL directa: https://www.youtube.com/watch?v=edOAM4gyGzo

## Documentación técnica profesional:

[Ver documentación técnica profesional en PDF](docs/documentacion-tecnica-profesional.pdf)

La documentación técnica profesional contiene una explicación más detallada sobre el objetivo del laboratorio, el funcionamiento del script, los parámetros utilizados, la topología, las evidencias capturadas, el impacto observado y las contramedidas aplicadas.

---

## Aviso de uso responsable

Este proyecto fue desarrollado únicamente con fines **educativos, académicos y de laboratorio controlado**.

Los scripts y comandos incluidos en este repositorio deben ejecutarse solamente en entornos propios o autorizados, como GNS3, EVE-NG, PNETLab o laboratorios internos de práctica.

No debe utilizarse este material en redes públicas, empresariales o de terceros sin autorización explícita.

---

## Objetivo del laboratorio

Demostrar cómo un atacante conectado a un puerto de acceso puede abusar del protocolo **Cisco Discovery Protocol CDP** para generar una gran cantidad de anuncios CDP falsificados hacia un switch Cisco IOSvL2.

El objetivo principal es observar el impacto del ataque en el switch, especialmente:

- Incremento en el uso de CPU.
- Generación masiva de vecinos CDP falsos.
- Consumo de recursos por procesamiento de paquetes CDP.
- Posible degradación del rendimiento del dispositivo.

Después de demostrar el impacto, se aplican contramedidas para reducir o eliminar el riesgo.

---

## Objetivo del script

El script `cdp-attack.py` tiene como objetivo generar y enviar múltiples tramas CDP falsas desde Kali Linux hacia el switch.

El script permite:

- Seleccionar la interfaz conectada al switch.
- Generar vecinos CDP falsos con identificadores variables.
- Enviar paquetes CDP en alto volumen.
- Usar múltiples workers para aumentar la carga enviada.
- Ajustar parámetros como duración, tamaño del payload, pool de paquetes y cantidad de procesos.
- Demostrar el impacto del procesamiento de CDP en el switch.

---

## Archivos del repositorio

| Archivo | Descripción |
|---|---|
| `README.md` | Guía principal del laboratorio en formato how-to. |
| `cdp-attack.py` | Script principal para ejecutar el ataque DoS mediante CDP desde Kali Linux. |
| `mitigacion-cdp-attack.md` | Documento de apoyo con detalles sobre mitigación del ataque. |
| `docs/documentacion-tecnica-profesional.pdf` | Documentación técnica formal y más detallada del laboratorio. |
| `images/` | Carpeta con capturas utilizadas como evidencia dentro del README. |

---

## Topología del laboratorio

La topología utilizada en GNS3 está compuesta por una máquina Kali Linux, un switch Cisco IOSvL2 y una PC víctima.

![Topología del laboratorio](images/topology.png)

| Dispositivo | Interfaz | Dirección IP | Rol |
|---|---|---|---|
| R-1 | F0/0 | `20.25.8.45/24` | Gateway de la red |
| SW-1 | e1 / Gi0/1 | N/A | Puerto conectado a Kali |
| SW-1 | e2 / Gi0/2 | N/A | Puerto conectado a PC1 |
| Kali Linux | eth0 | `20.25.8.46/24` | Máquina atacante |
| PC1 | eth0 | `20.25.8.47/24` | Equipo víctima |

> Nota: En GNS3 las interfaces pueden mostrarse como `e0`, `e1` o `e2`, mientras que dentro del IOSvL2 pueden aparecer como `GigabitEthernet0/0`, `GigabitEthernet0/1` o `GigabitEthernet0/2`. Se debe validar el nombre real de la interfaz con `show ip interface brief`.

---

## Requisitos previos

Para reproducir este laboratorio se necesita:

- GNS3 o un entorno de virtualización similar.
- Switch Cisco IOSvL2.
- Máquina Kali Linux.
- Python 3.
- Scapy instalado en Kali.
- Permisos de superusuario en Kali.
- CDP habilitado en el switch antes de ejecutar el ataque.
- Conectividad de capa 2 entre Kali y el switch.

Instalar dependencias en Kali:

```bash
sudo apt update
sudo apt install python3 python3-pip
pip3 install scapy
```

---

## Preparación del laboratorio

### 1. Clonar el repositorio

```bash
git clone https://github.com/iClexi/CDP-Attack.git
cd CDP-Attack
```

### 2. Verificar la interfaz de Kali

```bash
ip -br addr
```

La interfaz conectada al switch debe pertenecer a la red del laboratorio:

```text
20.25.8.0/24
```

En este laboratorio, Kali utiliza:

```text
20.25.8.46/24
```

### 3. Verificar CDP en el switch

Antes del ataque, validar que CDP esté activo:

```cisco
enable
show cdp neighbors
show cdp traffic
show cdp interface
```

### 4. Verificar CPU antes del ataque

```cisco
show processes cpu sorted
```

![CPU antes del ataque](images/cpu_before.png)

En esta captura se observa el estado inicial del switch antes de iniciar el envío masivo de paquetes CDP.

---

## Ejecución del ataque

Ejecutar el script desde Kali Linux:

```bash
sudo python3 cdp-attack.py
```

El script mostrará las interfaces disponibles y solicitará seleccionar la interfaz conectada al switch.

![Ejecución del script en Kali](images/script_execution.png)

Durante la ejecución, el script genera paquetes CDP falsificados con nombres de dispositivos variables. Esto provoca que el switch procese múltiples anuncios CDP como si vinieran de diferentes vecinos.

---

## Observación del impacto

### 1. Uso de CPU durante el ataque

En el switch, ejecutar:

```cisco
show processes cpu sorted
```

![CPU durante el ataque](images/cpu_after.png)

Se observa un aumento en el uso de CPU durante la ejecución del ataque. Este incremento ocurre porque el switch debe procesar una gran cantidad de anuncios CDP falsificados.

### 2. Vecinos CDP falsos

Ejecutar:

```cisco
show cdp neighbors
```

![Vecinos CDP falsos](images/cdp_neighbors.png)

En esta etapa se pueden observar múltiples entradas CDP falsas generadas por el script. Los nombres de los dispositivos falsificados utilizan un prefijo similar a:

```text
CDP-DOS-MICHAEL-...
```

### 3. Cantidad total de entradas CDP

El switch puede mostrar miles de entradas CDP generadas durante el ataque.

![Total de entradas CDP](images/cdp_entries.png)

En la evidencia se observa un total de entradas CDP desplegadas, lo que confirma el efecto del ataque sobre la tabla de vecinos CDP.

---

## Funcionamiento técnico del ataque

CDP es un protocolo de capa 2 utilizado por dispositivos Cisco para descubrir vecinos directamente conectados.

El ataque aprovecha que el switch procesa anuncios CDP recibidos desde el puerto donde está conectado Kali. El script genera tramas CDP falsas con campos modificados, como:

- Device ID.
- Port ID.
- Platform.
- Capabilities.
- Software Version.
- TTL.
- Native VLAN.

Al cambiar constantemente el identificador del dispositivo, el switch interpreta los paquetes como anuncios de vecinos diferentes. Esto puede provocar una gran cantidad de entradas falsas y aumento en el consumo de CPU.

---

## Parámetros del script

| Parámetro | Descripción |
|---|---|
| `-i`, `--iface` | Interfaz utilizada para enviar paquetes CDP. |
| `--workers` | Cantidad de procesos paralelos usados para enviar tráfico. |
| `--pool` | Cantidad de paquetes preconstruidos por worker. |
| `--pps` | Paquetes por segundo. Si es `0`, envía sin límite. |
| `--count` | Cantidad total de paquetes a enviar. |
| `--duration` | Duración del ataque en segundos. |
| `--ttl` | Tiempo de vida anunciado en los paquetes CDP. |
| `--extra` | Tamaño adicional agregado al payload. |
| `--payload-size` | Tamaño del payload del paquete. |
| `--random-src` | Usa direcciones MAC origen aleatorias. |
| `--yes` | Ejecuta sin pedir confirmación interactiva. |

Ejemplo con parámetros:

```bash
sudo python3 cdp-attack.py -i eth0 --workers 4 --pool 3000 --payload-size 1500 --extra 1400 --duration 60 --yes
```

---

## Contramedidas aplicadas

Para mitigar el ataque DoS mediante CDP se aplicaron dos enfoques principales.

### 1. Deshabilitar CDP globalmente

Si CDP no es necesario en el switch, se puede deshabilitar completamente:

```cisco
configure terminal
no cdp run
end
```

Verificación:

```cisco
show cdp neighbors
```

Resultado esperado:

```text
% CDP is not enabled
```

![CDP deshabilitado globalmente](images/cdp_disabled_global.png)

Esta mitigación evita que el switch procese cualquier paquete CDP.

### 2. Deshabilitar CDP por interfaz

Si CDP se necesita en algunos enlaces, pero no en puertos conectados a usuarios o equipos no confiables, se puede deshabilitar solo en la interfaz del atacante.

```cisco
configure terminal
interface gigabitEthernet0/1
no cdp enable
end
```

![CDP deshabilitado por interfaz](images/cdp_disabled_interface.png)

Esta opción es más selectiva, porque mantiene CDP activo en otros puertos donde puede ser útil para administración o diagnóstico.

---

## Verificación posterior a la mitigación

Después de aplicar la mitigación, se recomienda limpiar la tabla CDP y los contadores:

```cisco
clear cdp table
clear cdp counters
```

Luego verificar:

```cisco
show cdp neighbors
show cdp traffic
show processes cpu sorted
```

El resultado esperado es:

- No se generan nuevas entradas CDP falsas desde el puerto atacante.
- La CPU se mantiene estable.
- El switch deja de procesar anuncios CDP provenientes de Kali.

---

## Video demostrativo

La demostración práctica del ataque y su mitigación está disponible en YouTube:

[Ver video del laboratorio en YouTube](https://www.youtube.com/watch?v=edOAM4gyGzo)

En el video se muestra:

1. Topología utilizada en GNS3.
2. Estado inicial del switch antes del ataque.
3. Ejecución del script desde Kali Linux.
4. Incremento en el uso de CPU.
5. Generación de vecinos CDP falsos.
6. Aplicación de la mitigación.
7. Verificación posterior.

---

## Documentación técnica profesional

Para una explicación formal y más detallada del laboratorio, consultar el siguiente documento:

[Ver documentación técnica profesional](docs/documentacion-tecnica-profesional.pdf)

Este documento incluye:

- Objetivo del laboratorio.
- Objetivo del script.
- Requisitos técnicos.
- Parámetros utilizados.
- Funcionamiento interno del script.
- Topología y direccionamiento.
- Capturas de evidencia.
- Contramedidas aplicadas.
- Conclusión técnica.

---

## Conclusión

Este laboratorio demuestra cómo un atacante puede abusar de **Cisco Discovery Protocol CDP** enviando paquetes manipulados hacia un switch Cisco IOSvL2. El resultado es la generación de múltiples entradas falsas en la tabla de vecinos CDP y un aumento en el consumo de recursos del dispositivo.

La práctica evidencia que los protocolos de descubrimiento de capa 2, aunque son útiles para administración y diagnóstico, también pueden representar un riesgo si permanecen habilitados en interfaces no confiables.

La mitigación recomendada consiste en deshabilitar CDP globalmente cuando no sea necesario mediante:

```cisco
no cdp run
```

O deshabilitarlo únicamente en puertos no confiables mediante:

```cisco
interface gigabitEthernet0/1
no cdp enable
```

Con estas medidas, el switch deja de procesar anuncios CDP provenientes del puerto atacante, reduciendo el riesgo de abuso del protocolo y mejorando la estabilidad del dispositivo.

---

## Autor

Laboratorio realizado y documentado por:

**Michael David Robles Fermín**  
**iClexi**  
**Matrícula:** 2025-0845

Repositorio:

[https://github.com/iClexi/CDP-Attack](https://github.com/iClexi/CDP-Attack)

---

## Licencia y uso

Este repositorio se publica con fines académicos. Cualquier uso fuera de un laboratorio autorizado queda fuera del propósito de este proyecto.
