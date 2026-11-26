"""CO3 Q7: Telemedicine Protocol Design from First Principles + Live Socket Demo Under 4G Loss/Delay."""
import random
import socket
import threading
import time


def run_telemedicine_sim(loss_prob=0.05, rtt_s=0.20):
    """Simulate X-ray file transfer (TCP) & live chat/telemetry (TCP vs UDP) under 4G delay & loss."""
    payload = b"DICOM-XRAY-DATA-" * 2048  # 32 KB representative X-ray slice

    def tcp_receiver(srv_sock, result):
        conn, _ = srv_sock.accept()
        with conn:
            total = 0
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                total += len(data)
            result["bytes"] = total

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    res = {}
    th = threading.Thread(target=tcp_receiver, args=(srv, res))
    th.start()

    # Emulate 4G RTT + 5% segment loss retransmission delay on sender
    t0 = time.perf_counter()
    cli = socket.create_connection(srv.getsockname())
    chunk_size = 1460
    retransmits = 0
    random.seed(2026)
    for i in range(0, len(payload), chunk_size):
        chunk = payload[i:i + chunk_size]
        if random.random() < loss_prob:
            retransmits += 1
            time.sleep(rtt_s * 0.25)  # scaled simulation of 1 RTT recovery stall
        cli.sendall(chunk)
    cli.close()
    th.join()
    srv.close()
    elapsed = (time.perf_counter() - t0) * 1000
    return res["bytes"], retransmits, elapsed


def main():
    print("=== CO3 Q7: TELEMEDICINE PLATFORM PROTOCOL CHOICE FROM FIRST PRINCIPLES ===")
    print("Stage 1 — Traffic Requirements (Unreliable 4G: 100-300 ms RTT, up to 5% loss):")
    reqs = [
        ("Live Video Consult", "<= 150 ms 1-way", "Tolerates <= 1-2% loss", "Real-time / drop stale", "DTLS/SRTP"),
        ("Patient Records & X-Ray", "<= 5-15 s total", "0% loss (100% reliable)", "Strictly ordered", "TLS 1.3"),
        ("Doctor-Patient Chat", "<= 500 ms", "0% loss", "Strictly ordered", "TLS 1.3"),
        ("Hospital Service DNS", "<= 100 ms", "Retryable", "N/A", "DNSSEC / DoH"),
    ]
    for name, d, l, o, s in reqs:
        print(f"  - {name:<24}: Delay {d:<15} | Loss {l:<23} | Order {o:<16} | Sec {s}")

    print("\nStage 2 — Protocol Comparison & 64 KB TCP Window Limit:")
    tcp_max_bps = (65535 * 8) / 0.300
    xray_20mb_s = (20 * 8 * 1e6) / tcp_max_bps
    print(f"  - Max TCP throughput with 64 KB window @ 300 ms RTT : {tcp_max_bps/1e6:.3f} Mbps")
    print(f"  - 20 MB X-ray transfer time without Window Scaling  : >= {xray_20mb_s:.1f} s (exceeds target!)")
    print("  - Selected Stack:")
    print("      * Live Video    -> RTP/UDP + SRTP (no TCP HoL blocking) + FEC / adaptive bitrate")
    print("      * X-Ray & Chat  -> HTTP/3 over QUIC (or TCP+TLS 1.3 with RFC 7323 Window Scaling >= 512 KB + BBR)")
    print("      * DNS & QoS     -> TTL 300s cached DNS + DiffServ EF (video), AF21 (chat), AF11 (X-ray bulk)")

    print("\nStage 3 — Socket Implementation & Verification (4G: 200 ms RTT scaled, 5% loss):")
    n_bytes, retx, ms_clean = run_telemedicine_sim(loss_prob=0.0, rtt_s=0.0)
    n_bytes2, retx2, ms_loss = run_telemedicine_sim(loss_prob=0.05, rtt_s=0.20)
    print(f"  - Clean link (0% loss)       : delivered {n_bytes:,} B | retransmits={retx} | time={ms_clean:.2f} ms")
    print(f"  - Unreliable 4G (5% loss)    : delivered {n_bytes2:,} B | retransmits={retx2} | time={ms_loss:.2f} ms")

    print("\nStage 4 — Design Defence & 5G Upgrade Impact:")
    print("  - UDP/SRTP prevents 5% 4G loss from freezing video; HTTP/3+QUIC + Window Scaling prevents 64 KB BDP stall on X-rays.")
    print("  - Upgraded to 5G (<20 ms RTT, <0.1% loss): X-ray throughput jumps 15x even with 64 KB window; video jitter drops <5 ms.")

    print("\n--- Alternative Concept Analysis: Commercial Video-Consultation SaaS ---")
    print("  - Key due-diligence questions: (1) P95 glass-to-glass latency & SFU PoP proximity; (2) FEC/concealment at 5% loss;")
    print("    (3) End-to-end encryption, HIPAA/DISHA data residency, BAA & zero PHI logging.")


if __name__ == "__main__":
    main()
