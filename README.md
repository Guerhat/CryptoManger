# CriptoManger

Site informativo sobre criptoativos, fundamentos de investimento e cenarios teoricos de movimentacao futura. O front-end usa Reflex e roda dentro de um ambiente virtual Python.

## Paginas

- `/`: radar de mercado, perguntas para pesquisa e aviso de risco.
- `/bitcoin`: linhagem, papel no ecossistema e cenarios do Bitcoin.
- `/ethereum`: linhagem, papel no ecossistema e cenarios do Ethereum.
- `/solana`: linhagem, papel no ecossistema e cenarios da Solana.

As cotacoes e os candles dos graficos sao consultados em tempo de execucao na API publica da Binance, nos pares BTCUSDT, ETHUSDT e SOLUSDT. A API pode impor limites de requisicao ou ficar indisponivel; nesse caso, o site preserva uma visualizacao de fallback.

Os cenarios de movimentacao sao teoricos e nao sao previsoes nem recomendacoes financeiras.

## Executar

No PowerShell, na raiz do projeto:

```powershell
.\.venv\Scripts\Activate.ps1
reflex run
```

Depois, abra http://localhost:3000.

Para recriar o ambiente em outra maquina:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```
