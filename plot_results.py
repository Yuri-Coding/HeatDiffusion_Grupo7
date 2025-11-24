#!/usr/bin/env python3
"""
Gera gráficos a partir do CSV de resultados do benchmark.

Minimamente reformatado para clareza dos comentários e nomes locais,
sem alterar a lógica ou saída (PNG).
"""
from __future__ import annotations

import argparse
import csv
import os
from collections import Counter
from typing import Dict, List, Tuple

import matplotlib

# Backend não interativo para gerar PNGs sem janela gráfica.
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_results(path: str) -> List[Dict]:
    """
    Carrega o CSV de resultados e converte campos para tipos adequados.

    Retorna uma lista de dicionários com chaves:
      - approach, nx, ny, iterations, n_threads, n_workers, runtime
    Linhas malformadas são ignoradas.
    """
    results: List[Dict] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                results.append(
                    {
                        "approach": row["approach"],
                        "nx": int(row["nx"]),
                        "ny": int(row["ny"]),
                        "iterations": int(row["iterations"]),
                        "n_threads": int(row["n_threads"]) if row["n_threads"] else None,
                        "n_workers": int(row["n_workers"]) if row["n_workers"] else None,
                        "runtime": float(row["runtime_seconds"]),
                    }
                )
            except (KeyError, ValueError):
                # Ignora linhas que não seguem o formato esperado
                continue
    return results


def plot_tempo_vs_tamanho(results: List[Dict], output_path: str) -> None:
    """
    Plota o melhor tempo registrado (mínimo) para cada abordagem em função de nx.
    Assume que os tamanhos relevantes são quadrados (nx ~= ny).
    """
    approaches = sorted({r["approach"] for r in results})
    grid_sizes = sorted({(r["nx"], r["ny"]) for r in results})
    if not approaches or not grid_sizes:
        return

    plt.figure(figsize=(8, 5))
    for approach in approaches:
        grid_xs: List[int] = []
        runtimes: List[float] = []
        for nx, ny in grid_sizes:
            # Seleciona os tempos que correspondem à abordagem e ao tamanho
            candidates = [r["runtime"] for r in results if r["approach"] == approach and r["nx"] == nx and r["ny"] == ny]
            if not candidates:
                continue
            grid_xs.append(nx)
            # Mantém o melhor tempo (mínimo) para comparação
            runtimes.append(min(candidates))
        if grid_xs:
            plt.plot(grid_xs, runtimes, marker="o", label=approach)

    plt.xlabel("Tamanho da grade (nx, assumindo nx=ny)")
    plt.ylabel("Tempo (s)")
    plt.title("Tempo vs Tamanho da grade")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def _most_common_grid_size(results: List[Dict]) -> Tuple[int, int]:
    """
    Retorna o par (nx, ny) mais comum na lista de resultados.
    Usado para criar gráficos que comparam variações de threads/workers
    mantendo um tamanho de problema fixo.
    """
    counter = Counter((r["nx"], r["ny"]) for r in results)
    return counter.most_common(1)[0][0]


def plot_tempo_vs_threads(results: List[Dict], output_path: str) -> None:
    """
    Plota tempo em função do número de threads para a implementação paralela.
    Usa o tamanho de problema mais comum nos resultados paralelos como referência.
    """
    parallel_results = [r for r in results if r["approach"] == "parallel_threads"]
    if not parallel_results:
        return
    target_size = _most_common_grid_size(parallel_results)
    data = sorted(
        [(r["n_threads"], r["runtime"]) for r in parallel_results if (r["nx"], r["ny"]) == target_size and r["n_threads"] is not None],
        key=lambda x: x[0],
    )
    if not data:
        return

    xs, ys = zip(*data)
    plt.figure(figsize=(7, 4))
    plt.plot(xs, ys, marker="s")
    plt.xlabel("Número de threads")
    plt.ylabel("Tempo (s)")
    plt.title(f"Tempo vs Threads (tamanho {target_size[0]}x{target_size[1]})")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_tempo_vs_workers(results: List[Dict], output_path: str) -> None:
    """
    Plota tempo em função do número de workers para a implementação distribuída.
    Usa o tamanho de problema mais comum nos resultados distribuídos como referência.
    """
    distributed_results = [r for r in results if r["approach"] == "distributed_sockets"]
    if not distributed_results:
        return
    target_size = _most_common_grid_size(distributed_results)
    data = sorted(
        [(r["n_workers"], r["runtime"]) for r in distributed_results if (r["nx"], r["ny"]) == target_size and r["n_workers"] is not None],
        key=lambda x: x[0],
    )
    if not data:
        return

    xs, ys = zip(*data)
    plt.figure(figsize=(7, 4))
    plt.plot(xs, ys, marker="^")
    plt.xlabel("Número de workers")
    plt.ylabel("Tempo (s)")
    plt.title(f"Tempo vs Workers (tamanho {target_size[0]}x{target_size[1]})")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera gráficos a partir do CSV de benchmarks.")
    parser.add_argument("--input", type=str, default="results.csv", help="Caminho do CSV de entrada.")
    parser.add_argument("--out-dir", type=str, default=".", help="Diretório de saída dos PNGs.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = load_results(args.input)
    if not results:
        print("Nenhum dado válido encontrado no CSV.")
        return

    tempo_tamanho_path = os.path.join(args.out_dir, "tempo_vs_tamanho.png")
    tempo_threads_path = os.path.join(args.out_dir, "tempo_vs_threads.png")
    tempo_workers_path = os.path.join(args.out_dir, "tempo_vs_workers.png")

    plot_tempo_vs_tamanho(results, tempo_tamanho_path)
    plot_tempo_vs_threads(results, tempo_threads_path)
    plot_tempo_vs_workers(results, tempo_workers_path)
    print("Gráficos gerados.")


if __name__ == "__main__":
    main()
