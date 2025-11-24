#!/usr/bin/env python3
"""
Master (servidor) para difusao de calor distribuida via sockets.

Baseado em exemplos classicos de difusao de calor com diferencas finitas.
Adaptado e reestruturado para este trabalho especifico.
"""
from __future__ import annotations

import argparse
import pickle
import socket
import struct
import time
from typing import Dict, List, Optional, Tuple

import numpy as np

# Importa helpers renomeados da versao sequencial.
from heat_diffusion_sequential import build_central_hot_region, initialize_grid


def send_msg(conn: socket.socket, payload: Dict) -> None:
    """
    Envia uma mensagem serializada com prefixo de tamanho.
    """
    data = pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL)
    header = struct.pack("!Q", len(data))
    conn.sendall(header + data)


def recv_exact(conn: socket.socket, n_bytes: int) -> bytes:
    """
    Le exatamente n_bytes do socket.
    """
    chunks: List[bytes] = []
    remaining = n_bytes
    while remaining > 0:
        chunk = conn.recv(remaining)
        if not chunk:
            raise ConnectionError("Conexao encerrada inesperadamente.")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def recv_msg(conn: socket.socket) -> Dict:
    """
    Recebe uma mensagem com prefixo de tamanho.
    """
    header = recv_exact(conn, 8)
    (length,) = struct.unpack("!Q", header)
    data = recv_exact(conn, length)
    return pickle.loads(data)


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


def _collect_connections(host: str, port: int, n_workers: int) -> List[Tuple[socket.socket, Tuple[str, int]]]:
    """
    Bloqueia ate receber n_workers conexoes de workers.
    """
    connections: List[Tuple[socket.socket, Tuple[str, int]]] = []
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(n_workers)
    try:
        for _ in range(n_workers):
            conn, addr = server.accept()
            connections.append((conn, addr))
    finally:
        server.close()
    return connections


def _dispatch_config(connections: List[socket.socket], ranges: List[Tuple[int, int]], ny: int, n_iterations: int) -> None:
    """
    Envia configuracoes iniciais aos workers.
    """
    for conn, (row_start, row_end) in zip(connections, ranges):
        send_msg(
            conn,
            {
                "type": "config",
                "ny": ny,
                "iterations": n_iterations,
                "row_start": row_start,
                "row_end": row_end,
            },
        )


def _send_iteration_data(
    conn: socket.socket, iteration: int, chunk: np.ndarray, top: np.ndarray, bottom: np.ndarray
) -> None:
    """
    Envia dados de uma iteracao para um worker.
    """
    send_msg(conn, {"type": "iteration", "iter": iteration, "chunk": chunk, "top": top, "bottom": bottom})


def _recv_result(conn: socket.socket) -> Dict:
    """
    Recebe resultado de um worker.
    """
    return recv_msg(conn)


def run_heat_diffusion_distributed_master(
    nx: int,
    ny: int,
    n_iterations: int,
    n_workers: int,
    host: str = "0.0.0.0",
    port: int = 5000,
    initial_hot_region: Optional[Dict[str, float]] = None,
) -> tuple[float, np.ndarray]:
    """
    Inicia o servidor/master e coordena workers conectados via socket.

    Retorna:
        tempo_de_execucao (segundos), matriz_final (numpy.ndarray)
    """
    if n_workers <= 0:
        raise ValueError("n_workers deve ser positivo.")
    if nx < 3 or ny < 3:
        raise ValueError("nx e ny devem ser pelo menos 3 para executar a versao distribuida.")

    temperature_grid = initialize_grid(nx, ny, initial_hot_region)
    next_grid = temperature_grid.copy()

    # Interior exclui bordas.
    interior_start = 1
    interior_end = max(0, nx - 2)
    line_ranges = split_ranges(interior_start, interior_end, n_workers)
    if len(line_ranges) < n_workers:
        raise ValueError("Numero de workers excede linhas internas disponiveis.")

    connections_info = _collect_connections(host, port, n_workers)
    connections = [c for c, _ in connections_info]

    _dispatch_config(connections, line_ranges, ny, n_iterations)

    start_time = time.perf_counter()
    if nx >= 3 and ny >= 3:
        for iteration in range(n_iterations):
            # Preserva as bordas copiando o buffer anterior.
            next_grid[...] = temperature_grid

            # Envia fatias para cada worker com linhas "fantasma" (top/bottom).
            # Nota: protocolo envia o bloco completo do worker a cada iteracao.
            for conn, (row_start, row_end) in zip(connections, line_ranges):
                chunk = temperature_grid[row_start : row_end + 1, :]
                top = temperature_grid[row_start - 1, :]
                bottom = temperature_grid[row_end + 1, :]
                _send_iteration_data(conn, iteration, chunk, top, bottom)

            # Coleta resultados e escreve no buffer next_grid.
            for conn, (row_start, row_end) in zip(connections, line_ranges):
                msg = _recv_result(conn)
                if msg.get("type") != "result" or msg.get("iter") != iteration:
                    raise RuntimeError(f"Mensagem inesperada do worker: {msg}")
                updated_chunk = np.asarray(msg["chunk"], dtype=np.float64)
                next_grid[row_start : row_end + 1, :] = updated_chunk

            # Troca buffers.
            temperature_grid, next_grid = next_grid, temperature_grid

    runtime = time.perf_counter() - start_time

    # Encerra workers (envia 'stop' e fecha conexoes).
    for conn in connections:
        try:
            send_msg(conn, {"type": "stop"})
        except OSError:
            pass
        conn.close()

    return runtime, temperature_grid


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Master para simulacao distribuida de difusao de calor.")
    parser.add_argument("--nx", type=int, default=200, help="Numero de pontos no eixo x (linhas).")
    parser.add_argument("--ny", type=int, default=200, help="Numero de pontos no eixo y (colunas).")
    parser.add_argument("--iterations", type=int, default=200, help="Numero de iteracoes.")
    parser.add_argument("--workers", type=int, default=2, help="Numero de workers esperados.")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host para bind do servidor.")
    parser.add_argument("--port", type=int, default=5000, help="Porta para bind do servidor.")
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

    print(f"Aguardando {args.workers} workers em {args.host}:{args.port} ...")
    runtime, final_grid = run_heat_diffusion_distributed_master(
        args.nx,
        args.ny,
        args.iterations,
        args.workers,
        host=args.host,
        port=args.port,
        initial_hot_region=hot_region,
    )
    print(f"Tempo de execucao (distribuida/master): {runtime:.4f} s")
    print(f"Resumo grade final -> min: {final_grid.min():.2f}, max: {final_grid.max():.2f}")


if __name__ == "__main__":
    main()
