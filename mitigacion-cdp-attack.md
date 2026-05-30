# Mitigación general contra CDP DoS

## Descripción

Esta mitigación se enfoca únicamente en reducir la exposición del protocolo **CDP, Cisco Discovery Protocol**, para evitar que un atacante conectado a un puerto no confiable pueda enviar paquetes CDP falsificados y generar carga innecesaria en el switch.

CDP es un protocolo de capa 2 utilizado por dispositivos Cisco para descubrir vecinos directamente conectados. Puede ser útil en enlaces administrados entre dispositivos de red, pero no debe estar habilitado en puertos donde se conectan usuarios finales, PCs, servidores no confiables, máquinas Kali Linux o equipos externos.

---

## Base del direccionamiento IP del laboratorio

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

## Direccionamiento usado en la topología

| Dispositivo | Rol                        |  Dirección IP | Descripción                           |
| ----------- | -------------------------- | ------------: | ------------------------------------- |
| R1          | Gateway                    | 20.25.8.45/24 | Router principal de la red            |
| Kali        | Atacante                   | 20.25.8.46/24 | Máquina que ejecuta el ataque CDP DoS |
| VPC         | Víctima / equipo de prueba | 20.25.8.47/24 | Equipo final conectado al switch      |
| SW-1        | Switch                     |           N/A | Switch Cisco IOSvL2 de la topología   |

---

## Topología de referencia

```text
                   +----------------+
                   |      R1        |
                   | 20.25.8.45     |
                   | Fa0/0          |
                   +-------+--------+
                           |
                           |
                    Gi0/0  |
                   +-------+--------+
                   |      SW-1      |
                   |    IOSvL2      |
                   +---+--------+---+
                       |        |
                 Gi0/1 |        | Gi0/2
                       |        |
              +--------+        +--------+
              |                          |
        +-----+-----+              +-----+-----+
        |   Kali    |              |    VPC    |
        |20.25.8.46 |              |20.25.8.47 |
        +-----------+              +-----------+
```

---

## Variables que debes cambiar

Antes de aplicar la configuración, reemplaza los valores entre `< >` según tu topología.

| Variable                      | Significado                                  | Ejemplo                            |
| ----------------------------- | -------------------------------------------- | ---------------------------------- |
| `<TRUSTED_INTERFACE>`         | Interfaz confiable donde sí se permitirá CDP | `gigabitEthernet0/0`               |
| `<UNTRUSTED_INTERFACE_RANGE>` | Puerto o rango de puertos no confiables      | `gigabitEthernet0/1 - 2`           |
| `<TRUSTED_DESCRIPTION>`       | Descripción del enlace confiable             | `Enlace_confiable_hacia_R1`        |
| `<UNTRUSTED_DESCRIPTION>`     | Descripción de los puertos no confiables     | `Puertos_no_confiables_de_usuario` |

---

## Ejemplo aplicado a esta topología

En esta práctica:

```text
Gi0/0 -> Router R1 / 20.25.8.45
Gi0/1 -> Kali atacante / 20.25.8.46
Gi0/2 -> VPC / 20.25.8.47
```

Entonces los valores serían:

```text
<TRUSTED_INTERFACE> = gigabitEthernet0/0
<UNTRUSTED_INTERFACE_RANGE> = gigabitEthernet0/1 - 2
<TRUSTED_DESCRIPTION> = Enlace_confiable_hacia_R1
<UNTRUSTED_DESCRIPTION> = Puertos_no_confiables_de_usuario
```

---

## Configuración genérica

```cisco
enable
configure terminal

cdp run

interface <TRUSTED_INTERFACE>
description <TRUSTED_DESCRIPTION>
cdp enable

interface range <UNTRUSTED_INTERFACE_RANGE>
description <UNTRUSTED_DESCRIPTION>
no cdp enable

end
write memory
```

---

## Configuración aplicada al laboratorio

```cisco
enable
configure terminal

cdp run

interface gigabitEthernet0/0
description Enlace_confiable_hacia_R1
cdp enable

interface range gigabitEthernet0/1 - 2
description Puertos_no_confiables_de_usuario
no cdp enable

end
write memory
```

---

## Explicación de la configuración

### 1. Habilitar CDP globalmente

```cisco
cdp run
```

Este comando mantiene CDP activo en el switch a nivel global.

La idea no es apagar CDP en toda la red, sino permitirlo solamente en enlaces confiables donde sea necesario para administración y descubrimiento entre dispositivos Cisco.

---

### 2. Permitir CDP en enlaces confiables

```cisco
interface <TRUSTED_INTERFACE>
cdp enable
```

Este comando permite CDP en una interfaz confiable, como un enlace hacia un router, switch o dispositivo administrado.

En este laboratorio, el enlace confiable es el puerto del switch conectado hacia R1:

```cisco
interface gigabitEthernet0/0
description Enlace_confiable_hacia_R1
cdp enable
```

---

### 3. Deshabilitar CDP en puertos no confiables

```cisco
interface range <UNTRUSTED_INTERFACE_RANGE>
no cdp enable
```

Esta es la mitigación principal contra CDP DoS.

Con este comando, el switch deja de procesar paquetes CDP recibidos por puertos donde pueden conectarse usuarios, atacantes o equipos no administrados.

En este laboratorio, los puertos no confiables son:

```text
Gi0/1 -> Kali atacante / 20.25.8.46
Gi0/2 -> VPC / 20.25.8.47
```

Por eso se aplica:

```cisco
interface range gigabitEthernet0/1 - 2
description Puertos_no_confiables_de_usuario
no cdp enable
```

---

## Nota sobre VLAN

El ataque CDP no depende directamente del direccionamiento IP ni de una VLAN configurada en el switch. CDP trabaja en capa 2.

Si el script de ataque permite anunciar una VLAN dentro del paquete CDP, eso corresponde al TLV **Native VLAN** de CDP. Si no existe una VLAN configurada en el laboratorio, el script puede ejecutarse sin anunciar ninguna VLAN.

La mitigación sigue siendo la misma:

```cisco
no cdp enable
```

en los puertos no confiables.

---

## Limpieza después del ataque

Después de aplicar la mitigación, se recomienda limpiar la tabla de vecinos CDP y los contadores.

```cisco
clear cdp table
clear cdp counters
```

Esto permite verificar la mitigación desde cero.

---

## Verificación

Usa estos comandos para confirmar que la mitigación funciona:

```cisco
show cdp interface
show cdp neighbors
show cdp traffic
show processes cpu sorted | include CPU|CDP|IOSv e1000|Exec|console
```

---

## Resultado esperado

Después de aplicar la mitigación:

* CDP debe permanecer activo solo en interfaces confiables.
* Los puertos no confiables no deben procesar paquetes CDP.
* No deben aparecer vecinos CDP falsos desde Kali.
* La tabla CDP debe mostrar únicamente vecinos legítimos.
* El proceso `CDP Protocol` no debe elevarse de forma anormal durante el ataque.
* Aunque el atacante siga ejecutando el script, el switch no debe aprender vecinos CDP falsificados desde el puerto no confiable.

---

## Prueba recomendada

1. Ejecutar el ataque CDP desde Kali `20.25.8.46`.
2. Verificar aumento de vecinos falsos o consumo del proceso CDP.
3. Aplicar la mitigación.
4. Limpiar tabla y contadores CDP.
5. Ejecutar nuevamente el ataque.
6. Confirmar que ya no aparecen vecinos falsos desde los puertos no confiables.

---

## Mitigación alternativa: apagar CDP globalmente

Si la red no necesita CDP en ningún enlace, se puede apagar completamente:

```cisco
enable
configure terminal
no cdp run
end
write memory
```

Esta opción es más estricta, pero puede reducir la visibilidad administrativa entre dispositivos Cisco.

---

## Recomendación final

La mejor práctica es permitir CDP únicamente donde sea necesario.

Enlaces confiables:

```cisco
cdp enable
```

Puertos no confiables:

```cisco
no cdp enable
```

La mitigación principal contra CDP DoS es deshabilitar CDP en todos los puertos donde puedan conectarse equipos no administrados.
