"""Export simulation JSON summaries as Markdown tables."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

RESULTS_DIR = Path("results")
OUTPUT = Path("docs/metrics_tables.md")
ORDER = ["no_def", "rolling", "window", "challenge"]
MODE_LABELS = {
    "no_def": "no_def",
    "rolling": "rolling",
    "window": "window",
    "challenge": "challenge",
}


def load(path: Path) -> List[Dict]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def make_ploss_tables() -> str:
    data = load(RESULTS_DIR / "p_loss_sweep.json")
    header = "| p_loss | " + " | ".join(MODE_LABELS[m] for m in ORDER) + " |"
    divider = "| --- | " + " | ".join("---" for _ in ORDER) + " |"
    rows_legit = [header, divider]
    rows_attack = [header, divider]

    for p in sorted({entry["sweep_value"] for entry in data if entry["sweep_type"] == "p_loss"}):
        row_l = [f"{p:.2f}"]
        row_a = [f"{p:.2f}"]
        for mode in ORDER:
            entry = next(
                (e for e in data if e["sweep_value"] == p and e["mode"] == mode and e["sweep_type"] == "p_loss"),
                None,
            )
            if entry is None:
                row_l.append("-")
                row_a.append("-")
            else:
                row_l.append(pct(entry["avg_legit_rate"]))
                row_a.append(pct(entry["avg_attack_rate"]))
        rows_legit.append("| " + " | ".join(row_l) + " |")
        rows_attack.append("| " + " | ".join(row_a) + " |")

    legit_table = "\n".join(rows_legit)
    attack_table = "\n".join(rows_attack)
    return f"### Packet-loss sweep — legitimate acceptance\n\n{legit_table}\n\n" \
        f"### Packet-loss sweep — replay success\n\n{attack_table}\n"


def make_window_table() -> str:
    specific = sorted(RESULTS_DIR.glob("window_w*_p05.json"))
    rows: List[str] = []
    header = "| Window W | Legitimate (%) | Replay success (%) |\n| --- | --- | --- |"

    if specific:
        for path in specific:
            entry = load(path)[0]
            rows.append(
                "| {0:d} | {1:.2f}% | {2:.4f}% |".format(
                    int(entry["window_size"]), entry["avg_legit_rate"] * 100, entry["avg_attack_rate"] * 100
                )
            )
    else:
        data = load(RESULTS_DIR / "window_sweep.json")
        subset = [e for e in data if e["mode"] == "window" and e["sweep_type"] == "window"]
        subset.sort(key=lambda e: e["sweep_value"])
        for entry in subset:
            rows.append(
                "| {0:d} | {1:.2f}% | {2:.4f}% |".format(
                    int(entry["sweep_value"]), entry["avg_legit_rate"] * 100, entry["avg_attack_rate"] * 100
                )
            )

    return "### Window sweep (p_loss = 0.05, post attack)\n\n" + "\n".join([header, *rows]) + "\n"


def main() -> None:
    sections = ["# Aggregated metrics tables\n", make_ploss_tables(), make_window_table()]
    OUTPUT.write_text("\n\n".join(sections), encoding="utf-8")
    print(f"Wrote markdown tables to {OUTPUT}")


if __name__ == "__main__":
    main()
