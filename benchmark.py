#!/usr/bin/env python3
"""
Benchmark para comparar as abordagens de difusao de calor:
- Sequencial
- Paralela com threads
- Distribuida com sockets (master + workers)
"""
from __future__ import annotations

import argparse
import csv
import socket
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple

from heat_diffusion_distributed_master import run_heat_diffusion_distributed_master
from heat_diffusion_parallel import run_heat_diffusion_parallel
from heat_diffusion_sequential import build_central_hot_region, run_heat_diffusion_sequential

def find_free_port() -> int:
    """
    Retorna uma porta TCP livre para uso temporario.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def run_distributed_case(
    nx: int, ny: int, iterations: int, n_workers: int, hot_region: Optional[Dict[str, float]]
) -> float:
    """
    Sobe workers como subprocessos locais, executa o master e mede o tempo.
    """
    port = find_free_port()
    worker_procs: List[subprocess.Popen] = []
    runtime = float("nan")
    try:
        for _ in range(n_workers):
            proc = subprocess.Popen(
                [sys.executable, "heat_diffusion_distributed_worker.py", "--host", "127.0.0.1", "--port", str(port)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            worker_procs.append(proc)

        # Pequena espera para os workers subirem e conectarem.
        time.sleep(0.3)
        runtime, _ = run_heat_diffusion_distributed_master(
            nx, ny, iterations, n_workers, host="127.0.0.1", port=port, initial_hot_region=hot_region
        )
    finally:
        for proc in worker_procs:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.terminate()
    return runtime


def write_results_csv(path: str, rows: List[Dict[str, str]]) -> None:
    """
    Grava resultados em CSV com cabecalho fixo.
    """
    fieldnames = ["approach", "nx", "ny", "iterations", "n_threads", "n_workers", "runtime_seconds"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def run_benchmarks(
    sizes: List[Tuple[int, int]],
    iterations: int,
    thread_counts: List[int],
    worker_counts: List[int],
    include_distributed: bool,
    hot_region: Optional[Dict[str, float]],
) -> List[Dict[str, str]]:
    """
    Executa todos os experimentos e retorna linhas prontas para CSV.
    """
    results: List[Dict[str, str]] = []

    for nx, ny in sizes:
        # Sequencial
        runtime, _ = run_heat_diffusion_sequential(nx, ny, iterations, hot_region)
        results.append(
            {
                "approach": "sequential",
                "nx": str(nx),
                "ny": str(ny),
                "iterations": str(iterations),
                "n_threads": "",
                "n_workers": "",
                "runtime_seconds": f"{runtime:.6f}",
            }
        )

        # Paralelo (threads)
        for n_threads in thread_counts:
            runtime, _ = run_heat_diffusion_parallel(nx, ny, iterations, n_threads, hot_region)
            results.append(
                {
                    "approach": "parallel_threads",
                    "nx": str(nx),
                    "ny": str(ny),
                    "iterations": str(iterations),
                    "n_threads": str(n_threads),
                    "n_workers": "",
                    "runtime_seconds": f"{runtime:.6f}",
                }
            )

        # Distribuido
        if include_distributed:
            for n_workers in worker_counts:
                runtime = run_distributed_case(nx, ny, iterations, n_workers, hot_region)
                results.append(
                    {
                        "approach": "distributed_sockets",
                        "nx": str(nx),
                        "ny": str(ny),
                        "iterations": str(iterations),
                        "n_threads": "",
                        "n_workers": str(n_workers),
                        "runtime_seconds": f"{runtime:.6f}",
                    }
                )

    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark das implementacoes de difusao de calor.")
    parser.add_argument(
        "--sizes",
        type=str,
        default="50x50,100x100,200x200",
        help="Lista de tamanhos no formato NxM separados por virgula. Ex.: 50x50,100x100",
    )
    parser.add_argument("--iterations", type=int, default=100, help="Numero de iteracoes em cada execucao.")
    parser.add_argument("--threads", type=str, default="1,2,4", help="Lista de threads para testar (ex.: 1,2,4).")
    parser.add_argument("--workers", type=str, default="1,2", help="Lista de workers para testar (ex.: 1,2).")
    parser.add_argument("--output", type=str, default="results.csv", help="Caminho do CSV de saida.")
    parser.add_argument(
        "--skip-distributed", action="store_true", help="Ignora os testes distribuidos (sockets)."
    )
    parser.add_argument(
        "--hot",
        action="store_true",
        help="Ativa uma regiao quente central padrao (10%% do tamanho, valor 100).",
    )
    parser.add_argument("--hot-value", type=float, default=100.0, help="Valor da regiao quente padrao.")
    parser.add_argument("--hot-fraction", type=float, default=0.1, help="Fator de tamanho da regiao quente padrao.")
    return parser.parse_args()


def parse_list_arg(text: str) -> List[int]:
    return [int(x.strip()) for x in text.split(",") if x.strip()]


def parse_size_list(text: str) -> List[Tuple[int, int]]:
    sizes: List[Tuple[int, int]] = []
    for chunk in text.split(","):
        if "x" not in chunk:
            continue
        nx_str, ny_str = chunk.split("x", 1)
        try:
            sizes.append((int(nx_str), int(ny_str)))
        except ValueError:
            continue
    return sizes


def main() -> None:
    args = parse_args()
    sizes = parse_size_list(args.sizes)
    thread_counts = parse_list_arg(args.threads)
    worker_counts = parse_list_arg(args.workers)

    # constroi regiao padrao apenas quando precisar em cada execucao para respeitar o tamanho.
    def compute_hot_region(nx: int, ny: int) -> Optional[Dict[str, float]]:
        if args.hot:
            return build_central_hot_region(nx, ny, fraction=args.hot_fraction, value=args.hot_value)
        return None

    results: List[Dict[str, str]] = []
    for nx, ny in sizes:
        local_hot = compute_hot_region(nx, ny)
        results.extend(
            run_benchmarks(
                sizes=[(nx, ny)],
                iterations=args.iterations,
                thread_counts=thread_counts,
                worker_counts=worker_counts,
                include_distributed=not args.skip_distributed,
                hot_region=local_hot,
            )
        )

    write_results_csv(args.output, results)
    print(f"Benchmark finalizado. Resultados em {args.output}")


if __name__ == "__main__":
    main()