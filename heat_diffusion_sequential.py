#!/usr/bin/env python3
"""
Resolver sequencial para difusao de calor em uma placa 2D.

Baseado em exemplos classicos de difusao de calor com diferencas finitas.
Adaptado e reestruturado para este trabalho especifico.
"""
from __future__ import annotations

import argparse
import time
from typing import Dict, Optional

import numpy as np


def apply_hot_region(grid: np.ndarray, region: Dict[str, float]) -> None:
    """
    Aplica uma regiao quente no grid.

    region espera as chaves: x_start, x_end, y_start, y_end, value.
    Todas as coordenadas sao consideradas inclusive e limitadas ao grid.
    """
    x_start = int(region.get("x_start", 0))
    x_end = int(region.get("x_end", grid.shape[0] - 1))
    y_start = int(region.get("y_start", 0))
    y_end = int(region.get("y_end", grid.shape[1] - 1))
    value = float(region.get("value", 100.0))

    x_start = max(0, min(x_start, grid.shape[0] - 1))
    x_end = max(0, min(x_end, grid.shape[0] - 1))
    y_start = max(0, min(y_start, grid.shape[1] - 1))
    y_end = max(0, min(y_end, grid.shape[1] - 1))

    grid[x_start : x_end + 1, y_start : y_end + 1] = value


def build_central_hot_region(nx: int, ny: int, fraction: float = 0.1, value: float = 100.0) -> Dict[str, float]:
    """
    Constroi uma regiao quente quadrada centralizada.

    fraction define a proporcao aproximada do lado em relacao ao grid (ex.: 0.1 = 10%).
    """
    side_x = max(1, int(nx * fraction))
    side_y = max(1, int(ny * fraction))
    x_start = (nx - side_x) // 2
    y_start = (ny - side_y) // 2
    return {
        "x_start": x_start,
        "x_end": x_start + side_x - 1,
        "y_start": y_start,
        "y_end": y_start + side_y - 1,
        "value": value,
    }


def initialize_grid(nx: int, ny: int, initial_hot_region: Optional[Dict[str, float]] = None) -> np.ndarray:
    """
    Cria o grid inicial com bordas fixas e opcional regiao quente interna.
    """
    temperature_grid = np.zeros((nx, ny), dtype=np.float64)
    if initial_hot_region:
        apply_hot_region(temperature_grid, initial_hot_region)
    return temperature_grid


def run_heat_diffusion_sequential(
    nx: int, ny: int, n_iterations: int, initial_hot_region: Optional[Dict[str, float]] = None
) -> tuple[float, np.ndarray]:
    """
    Executa a simulacao sequencial da difusao de calor.

    Retorna:
        tempo_de_execucao (segundos), matriz_final (numpy.ndarray)
    """
    temperature_grid = initialize_grid(nx, ny, initial_hot_region)
    next_grid = temperature_grid.copy()

    t_start = time.perf_counter()
    if nx >= 3 and ny >= 3:
        for _ in range(n_iterations):
            # Mantem as bordas fixas copiando os valores anteriores para next_grid.
            next_grid[...] = temperature_grid
            next_grid[1:-1, 1:-1] = 0.25 * (
                temperature_grid[:-2, 1:-1] + temperature_grid[2:, 1:-1] + temperature_grid[1:-1, :-2] + temperature_grid[1:-1, 2:]
            )
            # Troca os buffers (sem copiar dados).
            temperature_grid, next_grid = next_grid, temperature_grid
    runtime = time.perf_counter() - t_start
    return runtime, temperature_grid


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulacao sequencial de difusao de calor (Jacobi).")
    parser.add_argument("--nx", type=int, default=200, help="Numero de pontos no eixo x (linhas).")
    parser.add_argument("--ny", type=int, default=200, help="Numero de pontos no eixo y (colunas).")
    parser.add_argument("--iterations", type=int, default=200, help="Numero de iteracoes.")
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
        hot_region = build_central_hot_region(args.nx, args.ny, fraction=args.hot_fraction, value=args.hot_value)

    runtime, final_grid = run_heat_diffusion_sequential(args.nx, args.ny, args.iterations, hot_region)
    print(f"Tempo de execucao (sequencial): {runtime:.4f} s")
    print(f"Resumo grade final -> min: {final_grid.min():.2f}, max: {final_grid.max():.2f}")


if __name__ == "__main__":
    main()
