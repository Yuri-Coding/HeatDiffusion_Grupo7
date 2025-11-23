## Difusao de calor - sequencial, threads e sockets

Projeto em Python 3 comparando tres abordagens para o problema classico de difusao de calor em uma placa 2D:
- Sequencial
- Paralela com threads (ThreadPoolExecutor)
- Distribuida via sockets (master + workers)

Cada abordagem usa o metodo de Jacobi com bordas fixas. Uma regiao quente opcional e aplicada no centro (por padrao, 10% do lado, valor 100).

### Estrutura dos arquivos
- `heat_diffusion_sequential.py`: implementacao sequencial com CLI.
- `heat_diffusion_parallel.py`: versao paralela usando threads, divide o grid por linhas.
- `heat_diffusion_distributed_master.py`: master que coordena workers via socket, repassa linhas fantasmas a cada iteracao.
- `heat_diffusion_distributed_worker.py`: worker que calcula um bloco recebido do master.
- `benchmark.py`: executa experimentos e grava `results.csv`.
- `plot_results.py`: gera graficos a partir do CSV.
- `analysis.md`: esqueleto para relatorio dos resultados.

### Dependencias
- Python 3.8+
- numpy
- matplotlib (para gerar graficos)

Instalacao rapida:
```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
pip install numpy matplotlib
```

### Como executar
Sequencial:
```bash
python heat_diffusion_sequential.py --nx 200 --ny 200 --iterations 200 --hot
```

Paralela (threads):
```bash
python heat_diffusion_parallel.py --nx 200 --ny 200 --iterations 200 --threads 4 --hot
```

Distribuida (sockets):
1. Inicie os workers (um processo por worker):
```bash
python heat_diffusion_distributed_worker.py --host 127.0.0.1 --port 5000
```
2. Inicie o master:
```bash
python heat_diffusion_distributed_master.py --nx 200 --ny 200 --iterations 200 --workers 2 --host 0.0.0.0 --port 5000 --hot
```
O master envia uma mensagem `stop` no final; os workers encerram sozinhos.
Observacao: para simplicidade, o master envia o bloco completo de cada worker a cada iteracao (protocolo didatico, com overhead de comunicacao maior).

### Benchmark padrao
Executa tamanhos 50x50, 100x100 e 200x200 com 100 iteracoes, threads 1/2/4 e workers 1/2. Gera `results.csv`.
```bash
python benchmark.py --hot
```
Para ignorar a parte distribuida:
```bash
python benchmark.py --skip-distributed --hot
```

### Geracao de graficos
Depois de ter um `results.csv`, execute:
```bash
python plot_results.py --input results.csv --out-dir .
```
Gera:
- `tempo_vs_tamanho.png`
- `tempo_vs_threads.png`
- `tempo_vs_workers.png`

### Infos da maquina (preencher)
- CPU (modelo, nucleos/threads): TODO
- Memoria RAM: TODO
- Sistema operacional: TODO
- Versao do Python: TODO

Snippet para coletar infos rapidas:
```python
import platform, sys
print(platform.platform())
print(platform.processor())
print("CPUs:", os.cpu_count())
print("Python:", sys.version)
```

### Relatorio e analise
Use `analysis.md` como esqueleto: descreva metodologia, resultados (referencie CSV e PNGs), discussao de escalabilidade, speedup/eficiencia, limites (sobrecarga de threads, custo de comunicacao dos sockets, sincronizacao) e melhorias futuras (melhor particionamento, multiprocessing, reducao de comunicacao, etc.).
