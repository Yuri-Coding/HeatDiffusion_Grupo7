#!/usr/bin/env python3
"""
Worker (cliente) da simulação distribuída de difusão de calor.

Este módulo recebe blocos da matriz enviados pelo master,
realiza o cálculo de um passo da iteração de Jacobi para a sua fatia,
e devolve o bloco atualizado. A comunicação ocorre via sockets.
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
    Envia um dicionário serializado com tamanho prefixado.
    Isso garante que o receptor saiba exatamente quantos bytes ler.
    """
    data = pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL)
    header = struct.pack("!Q", len(data))
    conn.sendall(header + data)


def recv_exact(conn: socket.socket, n_bytes: int) -> bytes:
    """
    Lê exatamente 'n_bytes' do socket, mesmo que venham em múltiplos pacotes.
    Essencial para evitar leituras incompletas.
    """
    chunks: List[bytes] = []
    remaining = n_bytes
    while remaining > 0:
        chunk = conn.recv(remaining)
        if not chunk:
            raise ConnectionError("Conexão interrompida inesperadamente durante leitura.")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def recv_msg(conn: socket.socket) -> Dict:
    """
    Recebe uma mensagem serializada com prefixo de tamanho.
    """
    header = recv_exact(conn, 8)
    (length,) = struct.unpack("!Q", header)
    data = recv_exact(conn, length)
    return pickle.loads(data)


def compute_jacobi_step(chunk: np.ndarray, top_row: np.ndarray, bottom_row: np.ndarray) -> np.ndarray:
    """
    Calcula um passo de Jacobi para o bloco recebido,
    utilizando as linhas fantasmas 'top_row' e 'bottom_row'.

    Apenas colunas internas (1:-1) são atualizadas.
    As bordas laterais seguem fixas, assim como na matriz completa.
    """
    rows, cols = chunk.shape
    new_chunk = chunk.copy()

    # Se o bloco for muito estreito (ex.: 2 colunas),
    # não há vizinhos suficientes para aplicar Jacobi.
    if cols < 3:
        return new_chunk

    for i in range(rows):
        # Linha acima depende se estamos na primeira linha do bloco
        upper = chunk[i - 1, :] if i > 0 else top_row
        # Linha abaixo depende se estamos na última linha do bloco
        lower = chunk[i + 1, :] if i < rows - 1 else bottom_row

        # Atualiza apenas colunas internas
        new_chunk[i, 1:-1] = 0.25 * (
            upper[1:-1] + lower[1:-1] + chunk[i, :-2] + chunk[i, 2:]
        )

    return new_chunk


def worker_loop(master_host: str, master_port: int) -> None:
    """
    Loop principal do worker:
    - Conecta ao master
    - Recebe configuração inicial
    - Repetidamente recebe blocos, processa, envia resultados
    - Encerra ao receber comando 'stop'
    """
    conn = None
    last_err: Optional[Exception] = None

    # Tentativa de conexão com múltiplas tentativas (útil em execuções distribuídas reais)
    for _ in range(20):
        try:
            conn = socket.create_connection((master_host, master_port))
            break
        except OSError as exc:
            last_err = exc
            time.sleep(0.2)

    if conn is None:
        raise ConnectionError(
            f"Não foi possível conectar ao master em {master_host}:{master_port}"
        ) from last_err

    with conn:
        config = recv_msg(conn)
        if config.get("type") != "config":
            raise RuntimeError(f"Mensagem inesperada ao iniciar: {config}")

        expected_cols = int(config.get("ny", 0))

        # Loop de processamento de blocos
        while True:
            msg = recv_msg(conn)
            msg_type = msg.get("type")

            if msg_type == "stop":
                break

            if msg_type != "iteration":
                raise RuntimeError(f"Mensagem inesperada recebida: {msg}")

            # Converte o que chegou em arrays numpy
            chunk = np.asarray(msg["chunk"], dtype=np.float64)
            top_row = np.asarray(msg["top"], dtype=np.float64)
            bottom_row = np.asarray(msg["bottom"], dtype=np.float64)

            # Verificação de consistência da grade
            if chunk.shape[1] != expected_cols:
                raise ValueError(
                    f"Número inesperado de colunas: {chunk.shape[1]} (esperado {expected_cols})"
                )

            # Calcula a próxima iteração para o bloco
            updated_chunk = compute_jacobi_step(chunk, top_row, bottom_row)

            # Envia resultado de volta ao master
            send_msg(conn, {"type": "result", "iter": msg.get("iter"), "chunk": updated_chunk})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Worker da simulação distribuída de difusão de calor.")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host do master para conectar.")
    parser.add_argument("--port", type=int, default=5000, help="Porta do master para conectar.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(f"Worker tentando conexão com {args.host}:{args.port} ...")
    worker_loop(args.host, args.port)
    print("Worker finalizado.")


if __name__ == "__main__":
    main()
