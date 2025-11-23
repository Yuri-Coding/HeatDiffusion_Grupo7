## Metodologia
- Experimentos: grades 50x50, 100x100, 200x200; 100 iteracoes Jacobi; bordas fixas; regiao quente desativada no benchmark (padrao do script). Uma execucao por combinacao (sem repeticoes/média).
- Abordagens: sequencial; threads com 1, 2 e 4 trabalhadores (ThreadPoolExecutor, divisao por faixas de linha); distribuida via sockets com 1 e 2 workers (master repassa bloco completo e linhas fantasmas a cada iteracao).
- Medicao de tempo: `time.perf_counter` medindo apenas a simulacao; sem descarte de aquecimento.
- Hardware/OS/Python: nao informado (preencher CPU, RAM, SO, versao Python) para contextualizar os tempos.
- Dados fonte: `results.csv` gerado via `benchmark.py`; graficos esperados em `tempo_vs_tamanho.png`, `tempo_vs_threads.png`, `tempo_vs_workers.png` usando `plot_results.py`.

## Resultados
Tempos (s) observados no `results.csv` (uma execucao por caso):

| abordagem             | nx  | ny  | iter | threads | workers | tempo (s)  |
|-----------------------|-----|-----|------|---------|---------|------------|
| sequencial            | 50  | 50  | 100  | -       | -       | 0.000925   |
| threads               | 50  | 50  | 100  | 1       | -       | 0.006330   |
| threads               | 50  | 50  | 100  | 2       | -       | 0.010696   |
| threads               | 50  | 50  | 100  | 4       | -       | 0.017067   |
| distribuido (sockets) | 50  | 50  | 100  | -       | 1       | 0.022332   |
| distribuido (sockets) | 50  | 50  | 100  | -       | 2       | 0.016998   |
| sequencial            | 100 | 100 | 100  | -       | -       | 0.002372   |
| threads               | 100 | 100 | 100  | 1       | -       | 0.008692   |
| threads               | 100 | 100 | 100  | 2       | -       | 0.012917   |
| threads               | 100 | 100 | 100  | 4       | -       | 0.021097   |
| distribuido (sockets) | 100 | 100 | 100  | -       | 1       | 0.039690   |
| distribuido (sockets) | 100 | 100 | 100  | -       | 2       | 0.031432   |
| sequencial            | 200 | 200 | 100  | -       | -       | 0.034443   |
| threads               | 200 | 200 | 100  | 1       | -       | 0.048733   |
| threads               | 200 | 200 | 100  | 2       | -       | 0.053379   |
| threads               | 200 | 200 | 100  | 4       | -       | 0.057484   |
| distribuido (sockets) | 200 | 200 | 100  | -       | 1       | 0.201914   |
| distribuido (sockets) | 200 | 200 | 100  | -       | 2       | 0.059247   |

Speedup observado vs sequencial (S = Tseq / T):
- 50x50x100: threads 1/2/4 => 0.15 / 0.09 / 0.05 (todos mais lentos); distrib 1 => 0.04; distrib 2 => 0.05.
- 100x100x100: threads 1/2/4 => 0.27 / 0.18 / 0.11; distrib 1 => 0.06; distrib 2 => 0.08.
- 200x200x100: threads 1/2/4 => 0.71 / 0.65 / 0.60; distrib 1 => 0.17; distrib 2 => 0.58.

Observacao: nenhum caso superou o sequencial; o melhor tempo paralelo/distribuido foi thread=1 em 200x200 (speedup ~0.71) e distributed workers=2 em 200x200 (speedup ~0.58).

## Discussao
- Escalabilidade: tempos crescem com o tamanho da grade como esperado, mas nao ha ganho com threads/workers nos tamanhos testados; overhead domina.
- Eficiencia: o custo de sincronizar a cada iteracao e copiar blocos supera o trabalho util em grades pequenas e iteracoes moderadas.
- Limitacoes:
  - Sobrecarga de threads (troca de contexto, saturacao de cache) torna execucoes multi-thread mais lentas que 1 thread.
  - Custo de comunicacao via sockets elevado porque o master envia o bloco completo + linhas fantasmas em toda iteracao.
  - Sincronizacao estrita por iteracao (barreira Jacobi) impede sobreposicao de comunicacao/compute.
  - Restricoes de hardware nao informadas; desempenho pode variar conforme CPU/nucleos e rede/loopback.
- Possiveis melhorias:
  - Melhor particionamento/balanceamento (ex.: granularidade adaptativa, blocos mais largos para reduzir fronteiras).
  - Usar multiprocessing ou processos com afinidade para contornar GIL em workloads CPU-bound.
  - Reduzir comunicacao no distribuido (troca direta de fronteiras entre vizinhos, enviar so ghost rows em vez do bloco completo, compressao opcional).
  - Tecnicas de vetorizacao/Numba para acelerar o kernel numerico e aumentar a razao computacao/comunicacao.

## Conclusao
- Nos cenarios testados, o sequencial foi mais rapido; paralelismo por threads ou sockets nao trouxe speedup devido ao overhead e ao tamanho relativamente pequeno dos problemas.
- Para buscar ganhos: experimentar grades maiores (ex.: 400x400, 800x800) e mais iteracoes, repetir execucoes para medias/DP, otimizar comunicacao e considerar multiprocessing/Numba.
