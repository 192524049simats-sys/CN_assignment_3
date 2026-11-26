"""CO3 Q3: HTTP/1.1 vs HTTP/2 vs HTTP/3 Page Load Calculations & Live Browser/curl Probe."""
import math
import subprocess


def main():
    print("=== CO3 Q3: HTTP PERFORMANCE — WHY THE HOME PAGE TAKES 8 SECONDS ===")
    rtt_ms = 50
    objs = 80

    t_non_pers = (1 + objs) * 2 * rtt_ms
    t_pers_nopipe = (1 + 1 + objs) * rtt_ms
    t_pers_pipe = (1 + 1 + 1) * rtt_ms
    batches = math.ceil(objs / 6)
    t_6_par = (2 + batches * 2) * rtt_ms

    print(f"Given: 1 HTML + {objs} small objects | RTT = {rtt_ms} ms | Transmission time ~ 0")
    print(f"  1. Non-persistent HTTP (serial)          : {t_non_pers:5d} ms ({t_non_pers/1000:.2f} s) [162 RTTs]")
    print(f"  2. Persistent HTTP/1.1 (no pipelining)   : {t_pers_nopipe:5d} ms ({t_pers_nopipe/1000:.2f} s) [ 82 RTTs]")
    print(f"  3. Persistent HTTP/1.1 (with pipelining) : {t_pers_pipe:5d} ms ({t_pers_pipe/1000:.2f} s) [  3 RTTs]")
    print(f"  4. 6 parallel non-persistent connections : {t_6_par:5d} ms ({t_6_par/1000:.2f} s) [ 30 RTTs]")

    print("\nHTTP/2 vs HTTP/3 (QUIC) under Packet Loss:")
    print("  - HTTP/2 multiplexes all 80 streams over ONE TCP connection -> 1 lost TCP segment stalls ALL streams (TCP HoL blocking).")
    print("  - HTTP/3 runs over QUIC (UDP) with independent streams -> losing a packet stalls ONLY that stream.")

    print("\nCaching Headers for Faster Second Visit:")
    print("  - Cache-Control: public, max-age=86400 -> eliminates network RTTs (0 ms fetch from browser cache).")
    print("  - ETag / If-None-Match -> conditional 304 Not Modified skips payload transfer (~1 RTT validation).")

    print("\n--- Live HTTP/HTTPS Measurement via curl.exe ---")
    for url in ("https://example.com", "https://www.google.com", "https://www.cloudflare.com"):
        try:
            fmt = "%{url_effective} | proto=%{http_version} | conns=%{num_connects} | dns=%{time_namelookup}s | tcp=%{time_connect}s | tls=%{time_appconnect}s | ttfb=%{time_starttransfer}s | total=%{time_total}s"
            out = subprocess.check_output(
                ["curl.exe", "-s", "-o", "NUL", "-w", fmt, url],
                text=True, timeout=15
            )
            print(" ", out.strip())
        except Exception as exc:
            print(f"  {url}: probe error ({exc})")

    print("\n--- Engineering Decision: Top 3 Mobile Load-Time Optimisations ---")
    print("  1. HTTP/3 (QUIC) + Persistent Multiplexing : Cuts 8.1 s -> ~0.15 s (98% reduction, eliminates TCP HoL & 0/1-RTT setup).")
    print("  2. Aggressive Cache-Control + ETag         : Cuts repeat visits to ~0 ms (local cache hit).")
    print("  3. Asset Bundling + Compression (Brotli)   : Reduces 80 requests -> 8 bundles, slashing RTT overhead on high-RTT 4G.")

    print("\n--- Alternative Concept Analysis: Bundling 80 Objects into 8 Bundles ---")
    b_non_pers = (1 + 8) * 2 * rtt_ms
    b_pers = (1 + 1 + 8) * rtt_ms
    print(f"  - Non-persistent (8 bundles): {b_non_pers} ms (down from 8,100 ms)")
    print(f"  - Persistent 1.1 (8 bundles): {b_pers} ms (down from 4,100 ms, vs ~150 ms with HTTP/2 multiplexing)")


if __name__ == "__main__":
    main()
