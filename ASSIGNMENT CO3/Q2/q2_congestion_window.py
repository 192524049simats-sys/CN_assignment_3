"""TCP congestion window over 20 round trips: slow start, avoidance and loss."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def simulate(losses, ssthresh=16, reno=True):
    cwnd, trace = 1, []
    for rtt in range(1, 21):
        trace.append(cwnd)
        # TODO 1: If this RTT is in losses: set ssthresh = max(cwnd // 2, 2) and set
        # cwnd to ssthresh (Reno, fast recovery) or to 1 (Tahoe). Otherwise double
        # cwnd in slow start (cwnd < ssthresh, capped at ssthresh) or add 1 in
        # congestion avoidance
        if rtt in losses:
            ssthresh = max(cwnd // 2, 2)
            cwnd = ssthresh if reno else 1
        elif cwnd < ssthresh:
            cwnd = min(cwnd * 2, ssthresh)
        else:
            cwnd += 1
    return trace


traces = {}
for label, reno in (("Reno ", True), ("Tahoe", False)):
    tr = simulate({8, 14}, reno=reno)
    traces[label.strip()] = tr
    print(label, " ".join(f"{w:2d}" for w in tr), f"| segments sent {sum(tr)}")

extra = sum(traces["Reno"]) - sum(traces["Tahoe"])
print(f"\nExtra segments delivered by Reno over Tahoe: {extra} (+{extra/sum(traces['Tahoe'])*100:.1f}%)")

# --- Follow-up: Hostel Graph Analysis, Throughput & CUBIC vs BBR ---
print("\n--- Hostel Wireshark Graph Analysis ---")
print("  - Initial ssthresh = 16 (doubled 1->2->4->8->16, then +1 linear from RTT 5 to 8).")
print("  - After RTT 8 (cwnd=19): ssthresh = floor(19/2) = 9 (3 dup ACKs -> Fast Recovery, cwnd=9).")
print("  - After RTT 14 (cwnd=14): ssthresh = floor(14/2) = 7 (Timeout RTO -> cwnd drops to 1).")
print("  - Sender variant: TCP Reno (exhibits Fast Recovery at RTT 8, unlike Tahoe which drops to 1 on every loss).")
thr_rtt7_mbps = (18 * 1460 * 8) / 0.040 / 1e6
print(f"  - Throughput at RTT 7 (cwnd=18, MSS=1460 B, RTT=40 ms): {thr_rtt7_mbps:.3f} Mbps")
print("  - AIMD convergence: Additive Increase (+1/RTT) + Multiplicative Decrease (/2) shrinks the larger")
print("    flow by more segments on loss, driving both flows toward the 45-degree equal-share line.")

print("\n--- Alternative Concept: 1% Random (Non-Congestion) Loss — Reno vs BBR ---")
print("  - Reno treats every 1% random loss as congestion and halves cwnd ~every 100 pkts (Mathis limit ~0.87*MSS/(RTT*sqrt(p))).")
print("  - BBR paces at estimated bottleneck BW x min_RTT without halving rate on isolated random loss -> far higher throughput.")
print("  - Hostel Server Recommendation: Use BBR for high-BDP Wi-Fi/WAN downloads with random loss (CUBIC if shallow FIFO fairness needed).")

# Plot both traces
fig, ax = plt.subplots(figsize=(10, 4.8), dpi=150)
ax.set_facecolor("#0F172A")
fig.patch.set_facecolor("#0F172A")
rtts = list(range(1, 21))
ax.plot(rtts, traces["Reno"], marker="o", lw=2.3, color="#38BDF8", label=f"TCP Reno (total={sum(traces['Reno'])} segs)")
ax.plot(rtts, traces["Tahoe"], marker="s", lw=2.3, ls="--", color="#F97316", label=f"TCP Tahoe (total={sum(traces['Tahoe'])} segs)")
ax.axvline(8, color="#EF4444", ls=":", alpha=0.8, label="Loss event @ RTT 8 & 14")
ax.axvline(14, color="#EF4444", ls=":", alpha=0.8)
ax.set_xticks(rtts)
ax.set_xlabel("Round-Trip Time (RTT)", color="#E2E8F0")
ax.set_ylabel("Congestion Window (segments)", color="#E2E8F0")
ax.set_title("CO3 Q2: TCP Reno vs TCP Tahoe Congestion Window (losses @ RTT 8, 14)", color="#F8FAFC", fontweight="bold")
ax.tick_params(colors="#CBD5E1")
ax.grid(color="#334155", alpha=0.5)
ax.legend(facecolor="#1E293B", edgecolor="#475569", labelcolor="white")
plt.tight_layout()
out_png = os.path.join(os.path.dirname(__file__), "q2_cwnd_plot.png")
plt.savefig(out_png, facecolor=fig.get_facecolor())
plt.close(fig)
print(f"Saved congestion window plot: {out_png}")
