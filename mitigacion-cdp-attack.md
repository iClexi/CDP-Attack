# Mitigación general contra CDP DoS

## Descripción

Esta mitigación se enfoca únicamente en reducir la exposición del protocolo **CDP, Cisco Discovery Protocol**, para evitar que un atacante conectado a un puerto no confiable pueda enviar paquetes CDP falsificados y generar carga innecesaria en el switch.

CDP puede ser útil en enlaces administrados entre dispositivos Cisco, pero no debe estar habilitado en puertos donde se conectan usuarios finales, PCs, servidores no confiables, máquinas Kali Linux o equipos externos.

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

## Ejemplo de topología

```text
Gi0/0 -> Router R1
Gi0/1 -> Kali atacante
Gi0/2 -> PC o VPC
```

En ese caso:

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

## Explicación de la configuración

### 1. Habilitar CDP globalmente

```cisco
cdp run
```

Este comando mantiene CDP activo en el switch a nivel global.
La idea no es apagar CDP en toda la red, sino permitirlo solamente en enlaces confiables.

---

### 2. Permitir CDP en enlaces confiables

```cisco
interface <TRUSTED_INTERFACE>
cdp enable
```

Este comando permite CDP en una interfaz confiable, como un enlace hacia un router, switch o dispositivo administrado.

Ejemplo:

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

Ejemplo:

```cisco
interface range gigabitEthernet0/1 - 2
description Puertos_no_confiables_de_usuario
no cdp enable
```

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
* No deben aparecer vecinos CDP falsos desde puertos de usuario.
* La tabla CDP debe mostrar únicamente vecinos legítimos.
* El proceso `CDP Protocol` no debe elevarse de forma anormal durante el ataque.

---

## Prueba recomendada

1. Ejecutar el ataque CDP desde la máquina atacante.
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
