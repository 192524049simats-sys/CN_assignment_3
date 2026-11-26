"""M/M/1 model of a router output link: arrivals at rate lam, service at rate mu."""
import heapq
import os
import random
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def mm1(lam, mu):
    # TODO 1: Return the utilisation rho = lam/mu, the average number in the system L =
    # rho/(1-rho) and the average delay W = 1/(mu-lam). Return None if lam >= mu (the
    # queue grows without limit)
    if lam >= mu:
        return None
    rho = lam / mu
    L = rho / (1.0 - rho)
    W = 1.0 / (mu - lam)
    return rho, L, W


mu = 1000                                   # packets per second the link can send
for lam in (500, 800, 900, 950, 990, 1000):
    r = mm1(lam, mu)
    if r is None:
        print(f"load {lam:4d} pkt/s: unstable, queue grows without limit")
    else:
        rho, L, W = r
        print(f"load {lam:4d} pkt/s: rho {rho:.2f}  L {L:6.1f} pkts  "
              f"W {W * 1000:6.1f} ms")

# --- Follow-up: Threshold, Token Bucket, DiffServ, Simulation & Capacity ---
print("\n--- Follow-up Calculations ---")
print("  - Delay first exceeds 20 ms when 1/(1000 - lam) > 0.020 => lam > 950 pkt/s (at 950 pkt/s, W = 20.0 ms).")
_, _, w450 = mm1(450, 1000)
_, _, w900 = mm1(900, 1000)
print(f"  - Doubling 450 -> 900 pkt/s: W goes {w450*1000:.2f} ms -> {w900*1000:.2f} ms (~{w900/w450:.1f}x; at 900, 1-rho drops 5.5x -> ~10x!).")
# Note: 1/(1000-450) = 1/550 = 1.818 ms, 1/(1000-900) = 10 ms -> 5.5x (or vs ~1ms at 0/low load; exact formula shown!).
print(f"  - Link capacity for W < 10 ms at lam = 1,500 pkt/s: mu > 1500 + 1/0.010 = 1,600 pkt/s.")

# Token bucket: B = 1 MB = 8 Mb, r = 2 Mbps, R = 10 Mbps
burst_sec = 8.0 / (10.0 - 2.0)
print(f"  - Token bucket (1 MB = 8 Mb, r=2 Mbps, R=10 Mbps): burst duration T = 8 / (10 - 2) = {burst_sec:.2f} s")
print("  - DiffServ classes: Video Call -> EF (DSCP 46) | Backup -> Best Effort / Scavenger (CS1/BE) | Interactive Web -> AF21.")

# Discrete-event FIFO vs Strict Priority simulation (10,000 packets: 200 pkt/s video + 750 pkt/s backup on 1000 pkt/s link)
random.seed(7)


def sim_queue(priority=False, n_pkts=8000):
    t = 0.0
    busy_until = 0.0
    video_delays = []
    # Poisson arrivals at total lam=950 pkt/s (20% video, 80% backup)
    # Using discrete pending heaps for priority simulation
    events = []
    cur = 0.0
    for _ in range(n_pkts):
        cur += random.expovariate(950.0)
        is_vid = (random.random() < 0.21)
        events.append((cur, 0 if (priority and is_vid) else 1, is_vid, random.expovariate(1000.0)))

    idx = 0
    q = []
    now = 0.0
    while idx < len(events) or q:
        if not q and idx < len(events):
            now = max(now, events[idx][0])
        while idx < len(events) and events[idx][0] <= now:
            arr, prio, is_vid, svc = events[idx]
            heapq.heappush(q, (prio, arr, is_vid, svc))
            idx += 1
        prio, arr, is_vid, svc = heapq.heappop(q)
        finish = now + svc
        if is_vid:
            video_delays.append((finish - arr) * 1000.0)
        now = finish
    return sum(video_delays) / len(video_delays), max(video_delays)


fifo_avg, fifo_max = sim_queue(priority=False)
prio_avg, prio_max = sim_queue(priority=True)
print(f"\n--- FIFO vs Strict-Priority Queue Simulation (95% total load: 200 video + 750 backup) ---")
print(f"  FIFO Video Delay     : avg = {fifo_avg:5.2f} ms, max = {fifo_max:6.2f} ms")
print(f"  Priority Video Delay : avg = {prio_avg:5.2f} ms, max = {prio_max:6.2f} ms")

print("\n--- Alternative Concept Analysis: Double Link (2,000 pkt/s) vs Strict Priority ---")
_, _, w_2k = mm1(1800, 2000)
print(f"  - Double link (mu=2000, lam=1800): W = {w_2k*1000:.2f} ms (still degrades if backup bursts > 2000 pkt/s!)")
print(f"  - Strict priority (DiffServ EF) on 1000 pkt/s link: video avg delay = {prio_avg:.2f} ms -> QoS wins cleanly!")

# Plot M/M/1 delay curve
loads = list(range(50, 995, 25))
delays = [mm1(l, 1000)[2] * 1000 for l in loads]
fig, ax = plt.subplots(figsize=(9.5, 4.6), dpi=150)
ax.set_facecolor("#0F172A")
fig.patch.set_facecolor("#0F172A")
ax.plot(loads, delays, color="#38BDF8", lw=2.5, label="M/M/1 Mean Delay W = 1 / (mu - lam)")
ax.axhline(20.0, color="#F59E0B", ls="--", lw=1.5, label="20 ms Threshold (lam = 950 pkt/s)")
ax.set_xlabel("Arrival Rate lambda (packets/s)", color="#E2E8F0")
ax.set_ylabel("Mean Router Delay W (ms)", color="#E2E8F0")
ax.set_title("CO3 Q5: M/M/1 Router Queue Delay vs Load (mu = 1,000 pkt/s)", color="#F8FAFC", fontweight="bold")
ax.tick_params(colors="#CBD5E1")
ax.grid(color="#334155", alpha=0.5)
ax.legend(facecolor="#1E293B", edgecolor="#475569", labelcolor="white")
plt.tight_layout()
out_png = os.path.join(os.path.dirname(__file__), "q5_mm1_delay.png")
plt.savefig(out_png, facecolor=fig.get_facecolor())
plt.close(fig)
print(f"Saved M/M/1 delay plot: {out_png}")
