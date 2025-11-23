#!/usr/bin/env python3
"""
Gera graficos a partir do CSV de resultados do benchmark.
"""
from __future__ import annotations

import argparse
import csv
import os
from collections import Counter
from typing import Dict, List, Tuple

import matplotlib

# Backend nao interativo para gerar PNGs sem janela grafica.
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_results(path: str) -> List[Dict]:
    rows: List[Dict] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                rows.append(
                    {
                        "approach": r["approach"],
                        "nx": int(r["nx"]),
                        "ny": int(r["ny"]),
                        "iterations": int(r["iterations"]),
                        "n_threads": int(r["n_threads"]) if r["n_threads"] else None,
                        "n_workers": int(r["n_workers"]) if r["n_workers"] else None,
                        "runtime": float(r["runtime_seconds"]),
                    }
                )
            except (KeyError, ValueError):
                continue
    return rows


def plot_tempo_vs_tamanho(rows: List[Dict], output_path: str) -> None:
    approaches = sorted({r["approach"] for r in rows})
    sizes = sorted({(r["nx"], r["ny"]) for r in rows})
    if not approaches or not sizes:
        return

    plt.figure(figsize=(8, 5))
    for approach in approaches:
        xs: List[int] = []
        ys: List[float] = []
        for nx, ny in sizes:
            candidates = [r["runtime"] for r in rows if r["approach"] == approach and r["nx"] == nx and r["ny"] == ny]
            if not candidates:
                continue
            xs.append(nx)
            ys.append(min(candidates))  # Melhor tempo registrado para o tamanho.
        if xs:
            plt.plot(xs, ys, marker="o", label=approach)

    plt.xlabel("Tamanho da grade (nx, assumindo nx=ny)")
    plt.ylabel("Tempo (s)")
    plt.title("Tempo vs Tamanho da grade")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def _most_common_size(rows: List[Dict]) -> Tuple[int, int]:
    counter = Counter((r["nx"], r["ny"]) for r in rows)
    return counter.most_common(1)[0][0]


def plot_tempo_vs_threads(rows: List[Dict], output_path: str) -> None:
    parallel_rows = [r for r in rows if r["approach"] == "parallel_threads"]
    if not parallel_rows:
        return
    target_size = _most_common_size(parallel_rows)
    data = sorted(
        [(r["n_threads"], r["runtime"]) for r in parallel_rows if (r["nx"], r["ny"]) == target_size],
        key=lambda x: x[0],
    )
    if not data:
        return

    xs, ys = zip(*data)
    plt.figure(figsize=(7, 4))
    plt.plot(xs, ys, marker="s", color="tab:blue")
    plt.xlabel("Numero de threads")
    plt.ylabel("Tempo (s)")
    plt.title(f"Tempo vs Threads (tamanho {target_size[0]}x{target_size[1]})")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_tempo_vs_workers(rows: List[Dict], output_path: str) -> None:
    distributed_rows = [r for r in rows if r["approach"] == "distributed_sockets"]
    if not distributed_rows:
        return
    target_size = _most_common_size(distributed_rows)
    data = sorted(
        [(r["n_workers"], r["runtime"]) for r in distributed_rows if (r["nx"], r["ny"]) == target_size],
        key=lambda x: x[0],
    )
    if not data:
        return

    xs, ys = zip(*data)
    plt.figure(figsize=(7, 4))
    plt.plot(xs, ys, marker="^", color="tab:green")
    plt.xlabel("Numero de workers")
    plt.ylabel("Tempo (s)")
    plt.title(f"Tempo vs Workers (tamanho {target_size[0]}x{target_size[1]})")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera graficos a partir do CSV de benchmarks.")
    parser.add_argument("--input", type=str, default="results.csv", help="Caminho do CSV de entrada.")
    parser.add_argument("--out-dir", type=str, default=".", help="Diretorio de saida dos PNGs.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_results(args.input)
    if not rows:
        print("Nenhum dado valido encontrado no CSV.")
        return

    tempo_tamanho_path = os.path.join(args.out_dir, "tempo_vs_tamanho.png")
    tempo_threads_path = os.path.join(args.out_dir, "tempo_vs_threads.png")
    tempo_workers_path = os.path.join(args.out_dir, "tempo_vs_workers.png")

    plot_tempo_vs_tamanho(rows, tempo_tamanho_path)
    plot_tempo_vs_threads(rows, tempo_threads_path)
    plot_tempo_vs_workers(rows, tempo_workers_path)
    print("Graficos gerados.")


if __name__ == "__main__":
    main()
