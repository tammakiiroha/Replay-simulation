"""Generate publication-grade plots from simulation JSON outputs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt

plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams.update(
    {
        "figure.dpi": 220,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 9,
        "axes.titleweight": "semibold",
        "axes.edgecolor": "#333333",
    }
)

BASELINE_PATH = Path("results/ideal_p0.json")
PLOSS_PATH = Path("results/p_loss_sweep.json")
WINDOW_PATH = Path("results/window_sweep.json")
FIG_DIR = Path("figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)

ORDER = ["no_def", "rolling", "window", "challenge"]
PALETTE = {
    "no_def": "#d62728",
    "rolling": "#1f77b4",
    "window": "#ff7f0e",
    "challenge": "#2ca02c",
}


def load_json(path: Path) -> List[Dict]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def plot_baseline() -> None:
    data = load_json(BASELINE_PATH)
    data.sort(key=lambda e: ORDER.index(e["mode"]))
    modes = [entry["mode"] for entry in data]
    attack = [entry["avg_attack_rate"] * 100 for entry in data]
    colors = [PALETTE.get(mode, "gray") for mode in modes]

    fig, ax = plt.subplots(figsize=(5.8, 2.8))
    bars = ax.barh(modes, attack, color=colors, edgecolor="#222", alpha=0.95, height=0.55)
    ax.set_xlabel("Replay success rate (%)")
    ax.set_xlim(left=0, right=max(attack) + 5)
    ax.set_title("Ideal channel baseline (p_loss = 0)")

    for bar, value in zip(bars, attack):
        ax.text(value + 0.5, bar.get_y() + bar.get_height() / 2, f"{value:.1f}%", va="center", weight="semibold")

    fig.tight_layout()
    fig.savefig(FIG_DIR / "baseline_attack.png")
    plt.close(fig)


def plot_ploss_curves() -> None:
    data = load_json(PLOSS_PATH)
    x_ticks = sorted({entry["sweep_value"] for entry in data if entry["sweep_type"] == "p_loss"})

    # Legitimate acceptance (focus on 80-100%)
    fig, ax = plt.subplots(figsize=(6.0, 3.4))
    for mode in ORDER:
        subset = [entry for entry in data if entry["mode"] == mode and entry["sweep_type"] == "p_loss"]
        subset.sort(key=lambda e: e["sweep_value"])
        if not subset:
            continue
        xs = [entry["sweep_value"] for entry in subset]
        ys = [entry["avg_legit_rate"] * 100 for entry in subset]
        ax.plot(xs, ys, marker="o", linewidth=2.3, markersize=6, color=PALETTE.get(mode, "gray"), label=mode)
        ax.fill_between(xs, ys, alpha=0.08, color=PALETTE.get(mode, "gray"))
    ax.set_xlabel("Packet loss probability")
    ax.set_ylabel("Legitimate acceptance (%)")
    ax.set_xticks(x_ticks)
    ax.set_ylim(78, 101)
    ax.set_title("Packet loss vs legitimate acceptance")
    ax.legend(ncol=2, loc="lower left")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "p_loss_legit.png")
    plt.close(fig)

    # Replay success in log scale
    fig, ax = plt.subplots(figsize=(6.0, 3.4))
    for mode in ORDER:
        subset = [entry for entry in data if entry["mode"] == mode and entry["sweep_type"] == "p_loss"]
        subset.sort(key=lambda e: e["sweep_value"])
        if not subset:
            continue
        xs = [entry["sweep_value"] for entry in subset]
        ys = [max(entry["avg_attack_rate"] * 100, 1e-3) for entry in subset]
        ax.plot(xs, ys, marker="o", linewidth=2.3, markersize=6, color=PALETTE.get(mode, "gray"), label=mode)
    ax.set_xlabel("Packet loss probability")
    ax.set_ylabel("Replay success (%) [log]")
    ax.set_xticks(x_ticks)
    ax.set_yscale("log")
    ax.set_ylim(1e-3, 150)
    ax.set_title("Packet loss vs replay success (log scale)")
    ax.legend(ncol=2, loc="lower right")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "p_loss_attack.png")
    plt.close(fig)


def plot_window_tradeoff() -> None:
    data = load_json(WINDOW_PATH)
    subset = [entry for entry in data if entry["mode"] == "window" and entry["sweep_type"] == "window"]
    subset.sort(key=lambda e: e["sweep_value"])
    if not subset:
        return
    xs = [entry["sweep_value"] for entry in subset]
    legit = [entry["avg_legit_rate"] * 100 for entry in subset]
    attack = [entry["avg_attack_rate"] * 100 for entry in subset]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.5, 3.6), sharex=True)

    ax1.bar(xs, legit, color=PALETTE["window"], edgecolor="#222", alpha=0.9, width=0.7)
    ax1.set_ylabel("Legitimate acceptance (%)")
    ax1.set_xlabel("Window size W")
    ax1.set_ylim(80, 101)
    ax1.set_title("Usability")
    for x, y in zip(xs, legit):
        ax1.text(x, y + 0.5, f"{y:.1f}%", ha="center", va="bottom", fontsize=9)

    ax2.bar(xs, attack, color="#9467bd", edgecolor="#222", alpha=0.9, width=0.7)
    ax2.set_ylabel("Replay success (%)")
    ax2.set_xlabel("Window size W")
    ax2.set_ylim(-0.05, max(attack) + 0.2)
    ax2.set_title("Security")
    for x, y in zip(xs, attack):
        ax2.text(x, y + 0.01, f"{y:.3f}%", ha="center", va="bottom", fontsize=9)

    fig.suptitle("Window size vs usability & security (p_loss = 0.05, post attack)")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "window_tradeoff.png")
    plt.close(fig)


def main() -> None:
    missing = [p for p in [BASELINE_PATH, PLOSS_PATH, WINDOW_PATH] if not p.exists()]
    if missing:
        raise SystemExit(f"Missing input files: {missing}")
    plot_baseline()
    plot_ploss_curves()
    plot_window_tradeoff()
    print(f"Saved plots to {FIG_DIR.resolve()}")


if __name__ == "__main__":
    main()
