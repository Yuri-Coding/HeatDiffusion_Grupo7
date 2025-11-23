#!/usr/bin/env python3
"""
Worker (cliente) para difusao de calor distribuida via sockets.

Baseado em exemplos classicos de difusao de calor com diferencas finitas.
Adaptado e reestruturado para este trabalho especifico.
"""
from __future__ import annotations

import argparse
import pickle
import socket
import struct
import time
from typing import Dict, List, Optional

import numpy as np


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


def update_chunk(chunk: np.ndarray, top: np.ndarray, bottom: np.ndarray) -> np.ndarray:
    """
    Calcula um passo de Jacobi para o bloco recebido usando linhas fantasmas.
    """
    rows, cols = chunk.shape
    new_chunk = chunk.copy()
    if cols < 3:
        return new_chunk

    for i in range(rows):
        upper = chunk[i - 1, :] if i > 0 else top
        lower = chunk[i + 1, :] if i < rows - 1 else bottom
        new_chunk[i, 1:-1] = 0.25 * (upper[1:-1] + lower[1:-1] + chunk[i, :-2] + chunk[i, 2:])
    return new_chunk


def worker_loop(host: str, port: int) -> None:
    """
    Loop principal: recebe fatias, processa iteracoes e devolve resultados.
    """
    conn = None
    last_err: Optional[Exception] = None
    for _ in range(20):
        try:
            conn = socket.create_connection((host, port))
            break
        except OSError as exc:
            last_err = exc
            time.sleep(0.2)
    if conn is None:
        raise ConnectionError(f"Nao foi possivel conectar ao master em {host}:{port}") from last_err

    with conn:
        config = recv_msg(conn)
        if config.get("type") != "config":
            raise RuntimeError(f"Esperava mensagem de config, recebi: {config}")
        expected_cols = int(config.get("ny", 0))

        while True:
            msg = recv_msg(conn)
            msg_type = msg.get("type")
            if msg_type == "stop":
                break
            if msg_type != "iteration":
                raise RuntimeError(f"Mensagem inesperada: {msg}")

            chunk = np.asarray(msg["chunk"], dtype=np.float64)
            top = np.asarray(msg["top"], dtype=np.float64)
            bottom = np.asarray(msg["bottom"], dtype=np.float64)

            if chunk.shape[1] != expected_cols:
                raise ValueError(f"Chunk recebido com numero de colunas inesperado: {chunk.shape[1]} vs {expected_cols}")

            updated = update_chunk(chunk, top, bottom)
            send_msg(conn, {"type": "result", "iter": msg.get("iter"), "chunk": updated})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Worker para simulacao distribuida de difusao de calor.")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host do master para conectar.")
    parser.add_argument("--port", type=int, default=5000, help="Porta do master para conectar.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(f"Worker conectando em {args.host}:{args.port} ...")
    worker_loop(args.host, args.port)
    print("Worker finalizado.")


if __name__ == "__main__":
    main()
