#!/usr/bin/env python3
"""
Resolver paralelo (threads) para difusao de calor em uma placa 2D.

Baseado em exemplos classicos de difusao de calor com diferencas finitas.
Adaptado e reestruturado para este trabalho especifico.
"""
from __future__ import annotations

import argparse
import math
import os
import time
from concurrent.futures import ThreadPoolExecutor, wait
from typing import Dict, List, Optional, Tuple

import numpy as np

from heat_diffusion_sequential import build_default_hot_region, create_initial_grid


def split_ranges(start: int, end: int, n_parts: int) -> List[Tuple[int, int]]:
    """
    Divide o intervalo [start, end] inclusive em n_parts fatias aproximadamente iguais.
    """
    length = end - start + 1
    if length <= 0 or n_parts <= 0:
        return []
    base = length // n_parts
    remainder = length % n_parts

    ranges = []
    current = start
    for i in range(n_parts):
        size = base + (1 if i < remainder else 0)
        if size <= 0:
            break
        r_start = current
        r_end = current + size - 1
        ranges.append((r_start, r_end))
        current = r_end + 1
    return ranges


def _update_chunk(
    current: np.ndarray, output: np.ndarray, row_start: int, row_end: int, col_start: int = 1, col_end: Optional[int] = None
) -> None:
    """
    Atualiza um bloco de linhas [row_start, row_end] (inclusive) do grid.
    """
    if col_end is None:
        col_end = current.shape[1] - 2
    if row_start > row_end or col_start > col_end:
        return
    output[row_start : row_end + 1, col_start : col_end + 1] = 0.25 * (
        current[row_start - 1 : row_end, col_start : col_end + 1]
        + current[row_start + 1 : row_end + 2, col_start : col_end + 1]
        + current[row_start : row_end + 1, col_start - 1 : col_end]
        + current[row_start : row_end + 1, col_start + 1 : col_end + 2]
    )


def run_heat_diffusion_parallel(
    nx: int,
    ny: int,
    n_iterations: int,
    n_threads: int,
    initial_hot_region: Optional[Dict[str, float]] = None,
) -> tuple[float, np.ndarray]:
    """
    Executa a simulacao de difusao de calor utilizando threads.

    Retorna:
        tempo_de_execucao (segundos), matriz_final (numpy.ndarray)
    """
    grid = create_initial_grid(nx, ny, initial_hot_region)
    new_grid = grid.copy()

    # Linhas internas que serao divididas entre as threads (exclui bordas).
    interior_start = 1
    interior_end = max(0, nx - 2)
    line_ranges = split_ranges(interior_start, interior_end, max(1, n_threads))

    start_time = time.perf_counter()
    if nx >= 3 and ny >= 3:
        with ThreadPoolExecutor(max_workers=max(1, n_threads)) as executor:
            for _ in range(n_iterations):
                new_grid[...] = grid  # Mantem bordas fixas.
                futures = [
                    executor.submit(_update_chunk, grid, new_grid, r_start, r_end) for (r_start, r_end) in line_ranges
                ]
                wait(futures)
                grid, new_grid = new_grid, grid
    runtime = time.perf_counter() - start_time
    return runtime, grid


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulacao paralela (threads) de difusao de calor (Jacobi).")
    parser.add_argument("--nx", type=int, default=200, help="Numero de pontos no eixo x (linhas).")
    parser.add_argument("--ny", type=int, default=200, help="Numero de pontos no eixo y (colunas).")
    parser.add_argument("--iterations", type=int, default=200, help="Numero de iteracoes.")
    parser.add_argument("--threads", type=int, default=max(1, (math.floor((os.cpu_count() or 2) / 2))), help="Numero de threads.")
    parser.add_argument(
        "--hot",
        action="store_true",
        help="Ativa uma regiao quente central padrao (10%% do tamanho, valor 100).",
    )
    parser.add_argument("--hot-value", type=float, default=100.0, help="Valor da regiao quente padrao.")
    parser.add_argument("--hot-fraction", type=float, default=0.1, help="Fator de tamanho da regiao quente padrao.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    hot_region = None
    if args.hot:
        hot_region = build_default_hot_region(args.nx, args.ny, fraction=args.hot_fraction, value=args.hot_value)

    runtime, final_grid = run_heat_diffusion_parallel(
        args.nx, args.ny, args.iterations, args.threads, initial_hot_region=hot_region
    )
    print(f"Tempo de execucao (paralela threads): {runtime:.4f} s")
    print(f"Resumo grade final -> min: {final_grid.min():.2f}, max: {final_grid.max():.2f}")


if __name__ == "__main__":
    main()
