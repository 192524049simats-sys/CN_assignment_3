"""CO3 Q6: QUIC & TLS 1.3 Round-Trip Calculations + Live TLS Handshake Inspection."""
import socket
import ssl
import subprocess
import time


def main():
    print("=== CO3 Q6: TLS 1.2 vs TLS 1.3 vs QUIC HANDSHAKE TIMING ===")
    rtt = 100  # ms
    configs = [
        ("TCP + TLS 1.2", 1 + 2, "1 RTT TCP + 2 RTT TLS 1.2"),
        ("TCP + TLS 1.3", 1 + 1, "1 RTT TCP + 1 RTT TLS 1.3"),
        ("QUIC (1st visit)", 1, "Combined transport + TLS 1.3 in 1 RTT"),
        ("QUIC (0-RTT resume)", 0, "Early data sent in initial packet (0 RTT)"),
    ]
    for name, rtts, note in configs:
        print(f"  {name:<20}: {rtts} RTT = {rtts * rtt:3d} ms | {note}")

    print("\n1. 0-RTT Replay Risk:")
    print("   - An attacker on the network can capture and replay the initial 0-RTT ClientHello + early data.")
    print("   - NEVER send non-idempotent requests (e.g., money transfer, password change, POST payments) in 0-RTT;")
    print("     only safe idempotent GET requests may use 0-RTT.")

    print("\n2. Connection Migration (Wi-Fi -> 5G):")
    print("   - TCP breaks when IP changes because sockets are bound to the 4-tuple (srcIP, srcPort, dstIP, dstPort).")
    print("   - QUIC identifies sessions via a cryptographic Connection ID (CID), surviving IP/port changes seamlessly.")

    print("\n3. Corporate Firewall UDP/443 Blocking:")
    print("   - Firewalls blocking outbound UDP/443 cause QUIC to time out -> banking app must race/fallback via")
    print("     Happy Eyeballs (RFC 8305 / RFC 9114) to TCP + TLS 1.3 over port 443.")

    print("\n--- Live TLS Handshake Inspection (Python ssl + curl HTTP/3 check) ---")
    for host in ("www.google.com", "www.cloudflare.com"):
        try:
            ctx = ssl.create_default_context()
            t0 = time.perf_counter()
            with socket.create_connection((host, 443), timeout=8) as raw:
                t_tcp = (time.perf_counter() - t0) * 1000
                t1 = time.perf_counter()
                with ctx.wrap_socket(raw, server_hostname=host) as tls:
                    t_tls = (time.perf_counter() - t1) * 1000
                    cert = tls.getpeercert()
                    subj = dict(x[0] for x in cert.get("subject", ()))
                    print(f"  {host:<18}: version={tls.version()} | cipher={tls.cipher()[0]} | tcp={t_tcp:.1f}ms | tls={t_tls:.1f}ms | CN={subj.get('commonName','-')}")
        except Exception as exc:
            print(f"  {host}: TLS check error ({exc})")

    # Check alt-svc header for HTTP/3 advertisement
    for url in ("https://www.google.com", "https://www.cloudflare.com"):
        try:
            hdrs = subprocess.check_output(["curl.exe", "-sI", url], text=True, timeout=10)
            alt = [l.strip() for l in hdrs.splitlines() if l.lower().startswith("alt-svc:")]
            print(f"  HTTP/3 Alt-Svc ({url}): {alt[0] if alt else 'none advertised'}")
        except Exception as exc:
            print(f"  Alt-Svc check failed for {url}: {exc}")

    print("\n--- Engineering Decision: Should the Banking App Use QUIC? ---")
    print("  YES: Cuts cold setup from 300 ms (TLS 1.2) / 200 ms (TLS 1.3) to 100 ms (QUIC) and 0 ms on resume,")
    print("       survives Wi-Fi<->5G roaming mid-session, with automatic Happy Eyeballs TCP+TLS 1.3 fallback.")

    print("\n--- Alternative Concept Analysis: Wi-Fi -> 5G Handoff Mid-Transfer (30 s transfer, 100 ms RTT) ---")
    print("  - TCP + TLS 1.3 : Connection resets; must redo DNS/TCP (100 ms) + TLS 1.3 (100 ms) + HTTP resume + slow start (>= 300-500 ms lost).")
    print("  - QUIC          : Connection ID migrates path in 0 handshake RTTs (0 ms lost to handshake; only path validation ping).")


if __name__ == "__main__":
    main()
