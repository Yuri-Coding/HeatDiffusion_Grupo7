## Metodologia
- Experimentos: grades 50x50, 100x100, 200x200, 400x400 e 800x800 com 100 iteracoes Jacobi; bordas fixas; regiao quente desativada. Dataset extra: 400x400 e 800x800 tambem com 200 iteracoes.
- Abordagens: sequencial; threads com 1, 2 e 4 trabalhadores (ThreadPoolExecutor, divisao por faixas de linha); distribuida via sockets com 1, 2 e 4 workers (master repassa bloco completo + linhas fantasmas a cada iteracao).
- Medicao de tempo: `time.perf_counter` medindo apenas a simulacao; sem descarte de aquecimento.
- Hardware/OS/Python: nao informado (preencher CPU, RAM, SO, versao Python) para contextualizar os tempos.
- Dados fonte: `results.csv` (iteracao 100) e `results_iter200.csv` (iteracao 200 nos tamanhos grandes) gerados via `benchmark.py`; graficos em `tempo_vs_tamanho.png`, `tempo_vs_threads.png`, `tempo_vs_workers.png` e `iter200/*.png` produzidos por `plot_results.py`.

## Resultados
Tempos (s) no `results.csv` (100 iteracoes, sem regiao quente):

| abordagem             | nx  | ny  | iter | threads | workers | tempo (s)  |
|-----------------------|-----|-----|------|---------|---------|------------|
| sequencial            | 50  | 50  | 100  | -       | -       | 0.001599   |
| threads               | 50  | 50  | 100  | 1       | -       | 0.011876   |
| threads               | 50  | 50  | 100  | 2       | -       | 0.018873   |
| threads               | 50  | 50  | 100  | 4       | -       | 0.027570   |
| distribuido (sockets) | 50  | 50  | 100  | -       | 1       | 0.036838   |
| distribuido (sockets) | 50  | 50  | 100  | -       | 2       | 0.028941   |
| distribuido (sockets) | 50  | 50  | 100  | -       | 4       | 0.033096   |
| sequencial            | 100 | 100 | 100  | -       | -       | 0.003575   |
| threads               | 100 | 100 | 100  | 1       | -       | 0.016415   |
| threads               | 100 | 100 | 100  | 2       | -       | 0.021078   |
| threads               | 100 | 100 | 100  | 4       | -       | 0.035219   |
| distribuido (sockets) | 100 | 100 | 100  | -       | 1       | 0.060908   |
| distribuido (sockets) | 100 | 100 | 100  | -       | 2       | 0.045028   |
| distribuido (sockets) | 100 | 100 | 100  | -       | 4       | 0.053809   |
| sequencial            | 200 | 200 | 100  | -       | -       | 0.039413   |
| threads               | 200 | 200 | 100  | 1       | -       | 0.059680   |
| threads               | 200 | 200 | 100  | 2       | -       | 0.056805   |
| threads               | 200 | 200 | 100  | 4       | -       | 0.070584   |
| distribuido (sockets) | 200 | 200 | 100  | -       | 1       | 0.254716   |
| distribuido (sockets) | 200 | 200 | 100  | -       | 2       | 0.084905   |
| distribuido (sockets) | 200 | 200 | 100  | -       | 4       | 0.070671   |
| sequencial            | 400 | 400 | 100  | -       | -       | 0.189553   |
| threads               | 400 | 400 | 100  | 1       | -       | 0.211661   |
| threads               | 400 | 400 | 100  | 2       | -       | 0.148828   |
| threads               | 400 | 400 | 100  | 4       | -       | 0.133015   |
| distribuido (sockets) | 400 | 400 | 100  | -       | 1       | 0.666881   |
| distribuido (sockets) | 400 | 400 | 100  | -       | 2       | 0.491561   |
| distribuido (sockets) | 400 | 400 | 100  | -       | 4       | 0.490701   |
| sequencial            | 800 | 800 | 100  | -       | -       | 0.894716   |
| threads               | 800 | 800 | 100  | 1       | -       | 0.814166   |
| threads               | 800 | 800 | 100  | 2       | -       | 0.555875   |
| threads               | 800 | 800 | 100  | 4       | -       | 0.460847   |
| distribuido (sockets) | 800 | 800 | 100  | -       | 1       | 2.203719   |
| distribuido (sockets) | 800 | 800 | 100  | -       | 2       | 1.575788   |
| distribuido (sockets) | 800 | 800 | 100  | -       | 4       | 1.535139   |

Tempos (s) no `results_iter200.csv` (200 iteracoes, apenas tamanhos grandes):

| abordagem             | nx  | ny  | iter | threads | workers | tempo (s)  |
|-----------------------|-----|-----|------|---------|---------|------------|
| sequencial            | 400 | 400 | 200  | -       | -       | 0.338561   |
| threads               | 400 | 400 | 200  | 1       | -       | 0.360094   |
| threads               | 400 | 400 | 200  | 2       | -       | 0.334579   |
| threads               | 400 | 400 | 200  | 4       | -       | 0.269793   |
| distribuido (sockets) | 400 | 400 | 200  | -       | 1       | 1.405030   |
| distribuido (sockets) | 400 | 400 | 200  | -       | 2       | 1.215480   |
| distribuido (sockets) | 400 | 400 | 200  | -       | 4       | 0.850298   |
| sequencial            | 800 | 800 | 200  | -       | -       | 1.567302   |
| threads               | 800 | 800 | 200  | 1       | -       | 1.635721   |
| threads               | 800 | 800 | 200  | 2       | -       | 1.135940   |
| threads               | 800 | 800 | 200  | 4       | -       | 0.907638   |
| distribuido (sockets) | 800 | 800 | 200  | -       | 1       | 4.396430   |
| distribuido (sockets) | 800 | 800 | 200  | -       | 2       | 3.112788   |
| distribuido (sockets) | 800 | 800 | 200  | -       | 4       | 2.872709   |

Speedup vs sequencial (S = Tseq / T):
- 400x400x100: threads 2 => 1.27x; threads 4 => 1.43x; distribuido 4 => 0.39x (continua mais lento).
- 800x800x100: threads 2 => 1.61x; threads 4 => 1.94x; distribuido 4 => 0.58x.
- 400x400x200: threads 4 => 1.25x; distribuido 4 => 0.40x.
- 800x800x200: threads 4 => 1.73x; distribuido 4 => 0.55x.
- Grades pequenas (50/100/200): todos os paralelos seguem abaixo de 1x devido ao overhead.

## Discussao
- Escalabilidade: para 50-200 o overhead domina; a partir de 400 pontos por lado as threads passam a trazer ganho (ate ~1.9x em 800x800x100). O distribuido segue atrasado mesmo com 4 workers.
- Efeito das iteracoes: dobrar as iteracoes melhora a razao computacao/comunicacao; threads mantiveram ganho (1.25-1.73x), mas sockets ainda nao compensaram o custo de enviar blocos inteiros a cada passo.
- Overheads principais: copia de blocos completos e sincronizacao por iteracao no master/worker; troca de contexto e limites de cache no multithreading; ausencia de afinidade/processos para fugir do GIL.
- Limitacoes: apenas 1 execucao por combinacao (sem media/DP); hardware nao descrito; sem afinidade de CPU ou ajustes de buffer de rede.
- Possiveis melhorias: trocar protocolo para enviar so ghost rows entre vizinhos; evitar recopia do bloco inteiro; usar multiprocessing/Numba para aumentar computacao util; rodar varias repeticoes e medir dispersao; testar tamanhos ainda maiores para sockets.

## Conclusao
- Com tamanhos maiores (400+), a versao com threads finalmente supera o sequencial (ate ~1.9x em 800x800x100); para tamanhos pequenos continua mais lenta.
- A versao distribuida com sockets ainda fica atras da sequencial em todos os cenarios testados, embora 4 workers reduzam o tempo comparado a 1-2.
- Proximos passos uteis: repetir testes para medias/IC, relatar hardware, experimentar otimizacoes de comunicacao e alternativas como multiprocessing/Numba para empurrar ganhos em cargas maiores.
