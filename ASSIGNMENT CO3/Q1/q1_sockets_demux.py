"""UDP and TCP sockets on one machine: a time server answering three clients."""
import random
import socket
import subprocess
import threading
import time


def udp_server(sock):
    for _ in range(3):
        # TODO 1: Receive a datagram of up to 1024 bytes with recvfrom, and send back
        # "ACK:" followed by the same text to the address it came from
        data, addr = sock.recvfrom(1024)
        sock.sendto(b"ACK:" + data, addr)


def tcp_server(sock):
    conn, _ = sock.accept()
    with conn:
        # TODO 2: Read data in chunks of up to 4096 bytes until the client closes the
        # connection (recv returns b""), adding the length of each chunk to total
        total = 0
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            total += len(chunk)
        print(f"TCP server received {total} bytes in order")


u = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
u.bind(("127.0.0.1", 0))
t = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
t.bind(("127.0.0.1", 0))
t.listen(1)

threading.Thread(target=udp_server, args=(u,)).start()
th = threading.Thread(target=tcp_server, args=(t,))
th.start()

for name in ("lab1", "lab2", "lab3"):
    c = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    c.sendto(name.encode(), u.getsockname())
    reply, _ = c.recvfrom(1024)
    print("UDP", name, "->", reply.decode())
    c.close()

c = socket.create_connection(t.getsockname())
c.sendall(b"x" * 100_000)
c.close()

th.join()
u.close()
t.close()

# --- Follow-up: Demultiplexing, Header Overhead, Loss Simulation & Open Sockets ---
print("\n--- Socket Demultiplexing (Sports-App Server 203.0.113.5) ---")
print("  1. TCP 49.37.2.8:50001 -> 443    => Socket: TCP 203.0.113.5:443 <-> 49.37.2.8:50001 (ESTABLISHED)")
print("  2. TCP 117.96.4.2:50000 -> 443   => Socket: TCP 203.0.113.5:443 <-> 117.96.4.2:50000 (ESTABLISHED)")
print("  3. TCP SYN 106.51.7.7:41000->443 => Socket: TCP 203.0.113.5:443 (LISTEN) -> spawns new conn socket")
print("  4. UDP 49.37.2.8:50000 -> 5004   => Socket: UDP 203.0.113.5:5004 (shared 2-tuple socket)")
print("  Why: TCP demultiplexes on 4-tuple (srcIP, srcPort, dstIP, dstPort); UDP demultiplexes on 2-tuple (dstIP, dstPort).")

print("\n--- Header Overhead (100-byte Score Update + 20B IPv4) ---")
print(f"  UDP + IPv4 : 8 + 20 = 28 B header / 128 B total = {28/128*100:.2f}%")
print(f"  TCP + IPv4 : 20 + 20 = 40 B header / 140 B total = {40/140*100:.2f}%")

print("\n--- Simulated Packet Loss Experiment (1%, 5%, 10% over 100 segments) ---")
random.seed(42)
for loss_rate in (0.01, 0.05, 0.10):
    sent = 100
    udp_deliv = sum(1 for _ in range(sent) if random.random() >= loss_rate)
    # TCP retransmits lost segments until all 100 arrive in order
    tcp_tx = 0
    for _ in range(sent):
        while True:
            tcp_tx += 1
            if random.random() >= loss_rate:
                break
    print(f"  Loss {int(loss_rate*100):2d}%: UDP delivered {udp_deliv:3d}/100 (gaps) | TCP delivered 100/100 in order ({tcp_tx} total transmissions)")

print("\n--- Alternative Concept: Live Video over TCP (2% loss, 60 ms RTT, 500 pkt/s) ---")
lost_per_sec = 500 * 0.02
freezes_per_min = lost_per_sec * 60
print(f"  Lost segments/sec : {lost_per_sec:.1f} -> {freezes_per_min:.0f} HoL stalls/minute, each freezing >= 60 ms (1 RTT)")

print("\n--- Open Sockets Sample (netstat -ano) ---")
ns = subprocess.check_output(["netstat", "-ano"], text=True, timeout=10).splitlines()
for line in ns[:14]:
    print(" ", line)
