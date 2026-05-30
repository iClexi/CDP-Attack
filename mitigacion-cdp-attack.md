enable
configure terminal

# Mantiene CDP habilitado globalmente.

# CDP no se apaga en toda la red, solo se restringe a enlaces confiables.

cdp run

# Interfaz confiable hacia el router R1.

# Se permite CDP porque este enlace conecta con un dispositivo administrado.

interface gigabitEthernet0/0
description Enlace_confiable_hacia_R1
cdp enable

# El puerto se fuerza como access en la VLAN del laboratorio.

switchport mode access
switchport access vlan 58

# Se deshabilita DTP para evitar negociación automática de trunk.

switchport nonegotiate

# Puertos no confiables.

# Gi0/1 puede representar Kali atacante.

# Gi0/2 puede representar PC o VPC.

# En puertos de usuario no debe procesarse CDP.

interface range gigabitEthernet0/1 - 2
description Puertos_no_confiables_de_usuario

# Mitigación principal contra CDP DoS.

# El switch deja de procesar paquetes CDP recibidos por estos puertos.

no cdp enable

# Fuerza los puertos como access en la VLAN 58.

switchport mode access
switchport access vlan 58

# Evita que estos puertos negocien trunk mediante DTP.

switchport nonegotiate

# Limita tráfico broadcast excesivo.

storm-control broadcast level 1.00

# Limita tráfico multicast excesivo.

# CDP utiliza multicast de capa 2, por eso ayuda como control adicional.

storm-control multicast level 1.00

# Limita tráfico unicast desconocido.

storm-control unicast level 1.00

# Activa Port Security como control adicional de capa 2.

switchport port-security

# Permite una sola MAC por puerto.

switchport port-security maximum 1

# Si ocurre una violación, restringe el tráfico anormal sin apagar totalmente el puerto.

switchport port-security violation restrict

# Aprende automáticamente la MAC legítima del dispositivo conectado.

switchport port-security mac-address sticky

# PortFast se usa en puertos de usuario final.

spanning-tree portfast

# BPDU Guard protege contra BPDUs no autorizadas en puertos de usuario.

spanning-tree bpduguard enable

end
write memory

# Limpia vecinos CDP falsos aprendidos durante la prueba.

clear cdp table

# Reinicia contadores CDP para validar la mitigación desde cero.

clear cdp counters

# Verifica interfaces con CDP activo.

show cdp interface

# Verifica vecinos CDP aprendidos.

show cdp neighbors

# Verifica paquetes CDP enviados, recibidos y errores.

show cdp traffic

# Verifica consumo de CPU relacionado con CDP.

show processes cpu sorted | include CPU|CDP|IOSv e1000|Exec|console

# Verifica Port Security.

show port-security

# Verifica Storm Control.

show storm-control
