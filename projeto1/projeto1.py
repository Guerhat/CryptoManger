from datetime import datetime, timezone

import httpx
import reflex as rx


ASSETS = [
    {"symbol": "BTC", "name": "Bitcoin", "price": "US$ 67.842,10", "change": "+2,84%", "tone": "teal", "route": "/bitcoin", "role": "Reserva digital"},
    {"symbol": "ETH", "name": "Ethereum", "price": "US$ 3.542,76", "change": "+1,42%", "tone": "blue", "route": "/ethereum", "role": "Infraestrutura"},
    {"symbol": "SOL", "name": "Solana", "price": "US$ 168,31", "change": "-0,68%", "tone": "orange", "route": "/solana", "role": "Aplicacoes"},
]


class ChartState(rx.State):
    period: str = "mes"
    selected_symbol: str = "BTC"
    market_data: dict[str, list[dict[str, str | float]]] = {}
    current_prices: dict[str, str] = {}
    daily_changes: dict[str, str] = {}

    async def load_data(self):
        symbols = [asset["symbol"] for asset in ASSETS]
        endpoint = "https://api.binance.com/api/v3/klines"
        ticker_endpoint = "https://api.binance.com/api/v3/ticker/price"
        loaded_data: dict[str, list[dict[str, str | float]]] = {}
        loaded_prices: dict[str, str] = {}
        loaded_changes: dict[str, str] = {}

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                for symbol in symbols:
                    pair = f"{symbol}USDT"
                    for period, interval, limit in (("semana", "1h", 168), ("mes", "1d", 30), ("ano", "1d", 365)):
                        response = await client.get(endpoint, params={"symbol": pair, "interval": interval, "limit": limit})
                        response.raise_for_status()
                        candles = response.json()
                        loaded_data[f"{symbol}:{period}"] = [
                            {
                                "label": self.format_candle_label(candle[0], period),
                                "value": float(candle[4]),
                            }
                            for candle in candles
                        ]
                    ticker = await client.get(ticker_endpoint, params={"symbol": pair})
                    ticker.raise_for_status()
                    ticker_data = ticker.json()
                    loaded_prices[symbol] = self.format_price(float(ticker_data["price"]))
                    loaded_changes[symbol] = f"{float(ticker_data['priceChangePercent']):+.2f}%"
        except (httpx.HTTPError, ValueError, KeyError):
            return

        self.market_data = loaded_data
        self.current_prices = loaded_prices
        self.daily_changes = loaded_changes

    @staticmethod
    def format_candle_label(timestamp: int, period: str) -> str:
        date = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
        if period == "semana":
            return date.strftime("%d/%m %Hh")
        if period == "mes":
            return date.strftime("%d/%m")
        return date.strftime("%b %d")

    @staticmethod
    def format_price(price: float) -> str:
        return f"US$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @rx.var
    def active_price(self) -> str:
        return self.current_prices.get(self.selected_symbol, "Consultando API...")

    @rx.var
    def chart_data(self) -> list[dict[str, str | float]]:
        api_data = self.market_data.get(f"{self.selected_symbol}:{self.period}")
        if api_data:
            return api_data
        if self.period == "semana":
            return [
                {
                    "label": f"{day} {hour:02d}h",
                    "value": 62 + ((day * 7 + hour * 3) % 25),
                }
                for day in range(7)
                for hour in range(24)
            ]
        if self.period == "mes":
            return [
                {"label": f"Dia {day:02d}", "value": 48 + ((day * 9) % 37)}
                for day in range(1, 31)
            ]
        return [
            {"label": f"Sem {week:02d}", "value": 63 + ((week * 11) % 31)}
            for week in range(1, 53)
        ]

    @rx.var
    def chart_description(self) -> str:
        descriptions = {
            "semana": "Dados reais da Binance: alteracoes a cada hora nos ultimos 7 dias.",
            "mes": "Dados reais da Binance: alteracoes de cada dia nos ultimos 30 dias.",
            "ano": "Dados reais da Binance: 365 dias ate hoje, identificados por mes.",
        }
        return descriptions[self.period]

    @rx.var
    def chart_color(self) -> str:
        return "#c45b58" if self.period == "ano" else "#3977c5"

    def set_period(self, period: str):
        self.period = period

    def select_asset(self, symbol: str):
        self.selected_symbol = symbol


def nav_bar() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.link(rx.hstack(rx.box("C", class_name="brand-mark"), rx.text("CriptoManger", class_name="brand-name"), spacing="2"), href="/"),
            rx.spacer(),
            rx.hstack(
                rx.menu.root(
                    rx.menu.trigger(rx.button("Mercado", class_name="nav-link menu-trigger")),
                    rx.menu.content(
                        rx.menu.item("Visao geral", on_select=rx.redirect("/#mercado")),
                        rx.menu.item(rx.hstack(rx.box("B", class_name="menu-coin-icon btc"), rx.text("Bitcoin"), spacing="2"), on_select=rx.redirect("/bitcoin")),
                        rx.menu.item(rx.hstack(rx.box("E", class_name="menu-coin-icon eth"), rx.text("Ethereum"), spacing="2"), on_select=rx.redirect("/ethereum")),
                        rx.menu.item(rx.hstack(rx.box("S", class_name="menu-coin-icon sol"), rx.text("Solana"), spacing="2"), on_select=rx.redirect("/solana")),
                        class_name="market-menu",
                    ),
                ),
                rx.link("Aprenda", href="/#aprenda", class_name="nav-link"),
                rx.link("Riscos", href="/#riscos", class_name="nav-link"),
                spacing="6",
                display=["none", "none", "flex"],
            ),
            width="100%", max_width="1180px", margin="0 auto", align="center", justify="between",
        ),
            border_bottom="1px solid #8f692d", padding="18px 24px", background="var(--gold)",
        position="sticky", top="0", z_index="10", backdrop_filter="blur(14px)",
    )


def metric_card(label: str, value: str, note: str, tone: str = "teal") -> rx.Component:
    return rx.box(
        rx.text(label, class_name="metric-label"), rx.text(value, class_name="metric-value"),
        rx.text(note, class_name=f"metric-note {tone}"), class_name="metric-card",
    )


def market_row(asset: dict[str, str]) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.link(rx.hstack(
            rx.box(asset["symbol"][0], class_name=f"coin-icon {asset['tone']}"),
            rx.vstack(rx.text(asset["name"], class_name="coin-name"), rx.text(asset["symbol"], class_name="coin-symbol"), spacing="0", align="start"),
            spacing="3",
        ), href=asset["route"])),
        rx.table.cell(rx.text(rx.cond(ChartState.current_prices[asset["symbol"]] != "", ChartState.current_prices[asset["symbol"]], asset["price"]), class_name="price-text")),
        rx.table.cell(rx.text(rx.cond(ChartState.daily_changes[asset["symbol"]] != "", ChartState.daily_changes[asset["symbol"]], asset["change"]), class_name="positive-text")),
        rx.table.cell(rx.text(asset["role"], class_name="role-text")),
        rx.table.cell(rx.link("Abrir perfil ->", href=asset["route"], class_name="table-link")),
    )


def market_table() -> rx.Component:
    return rx.table.root(
        rx.table.header(rx.table.row(
            rx.table.column_header_cell("Ativo"), rx.table.column_header_cell("Cotacao indicativa"),
            rx.table.column_header_cell("24h"), rx.table.column_header_cell("Tese de uso"), rx.table.column_header_cell(""),
        )),
        rx.table.body(rx.foreach(ASSETS, market_row)), width="100%", variant="surface", class_name="market-table",
    )


def section_heading(kicker: str, title: str, text: str) -> rx.Component:
    return rx.vstack(
        rx.text(kicker, class_name="section-kicker"), rx.heading(title, class_name="section-title"), rx.text(text, class_name="section-copy"),
        spacing="2", align="start",
    )


def footer() -> rx.Component:
    return rx.box(
        rx.hstack(rx.text("CriptoManger", class_name="footer-brand"), rx.spacer(), rx.text("Dados ilustrativos para fins educacionais", class_name="footer-note"), width="100%", max_width="1180px", margin="0 auto"),
        border_top="1px solid #dbe4e1", padding="28px 24px",
    )


def home() -> rx.Component:
    return rx.box(
        nav_bar(),
        rx.box(
            rx.box(
                rx.hstack(
                    rx.vstack(
                        rx.text("RADAR DE ATIVOS DIGITAIS", class_name="eyebrow"),
                        rx.heading("Entenda o movimento antes de seguir o movimento.", class_name="hero-title"),
                        rx.text("Leituras claras sobre criptoativos, fundamentos e cenarios possiveis para quem quer investir com mais contexto.", class_name="hero-copy"),
                        rx.hstack(rx.link("Explorar mercado", href="#mercado", class_name="primary-action"), rx.link("Como ler os cenarios", href="#aprenda", class_name="secondary-action"), spacing="3"),
                        spacing="5", align="start", max_width="670px",
                    ),
                    rx.box(
                        rx.text("SINAL DO DIA", class_name="signal-label"), rx.text("Contexto > impulso", class_name="signal-title"),
                        rx.text("O preco conta apenas uma parte da historia.", class_name="signal-copy"),
                        rx.box(rx.hstack(rx.text("BTC", class_name="signal-asset"), rx.spacer(), rx.text("+2,84%", class_name="positive-text"), width="100%"), rx.box(class_name="sparkline sparkline-one"), class_name="signal-chart"),
                        class_name="signal-card",
                    ),
                    spacing="9", align="center", justify="between", width="100%",
                ),
                max_width="1180px", margin="0 auto", padding="92px 24px 80px",
            ),
            rx.box(
                rx.hstack(metric_card("Mercado total", "US$ 2,41 tri", "+1,7% na semana"), metric_card("Dominancia BTC", "53,8%", "Leve alta semanal", "blue"), metric_card("Sentimento", "Cautela", "Volatilidade moderada", "orange"), spacing="4", width="100%"),
                max_width="1180px", margin="0 auto", padding="0 24px 84px",
            ),
            rx.box(
                rx.vstack(section_heading("VISAO DE MERCADO", "Uma tela para começar a pesquisa.", "Valores abaixo sao ilustrativos. Use-os para navegar pelos fundamentos, nao como cotacao em tempo real."), market_table(), spacing="7", align="stretch", width="100%"),
                id="mercado", class_name="section-band",
            ),
            rx.box(
                rx.hstack(
                    rx.vstack(section_heading("APRENDA A LER", "Tres perguntas antes de qualquer aporte.", "Investir em ativos digitais exige tese, prazo e uma noção honesta do que pode dar errado."), spacing="7", align="start", flex="1"),
                    rx.vstack(
                        rx.box(rx.text("01", class_name="step-number"), rx.text("Qual problema o ativo resolve?", class_name="step-title"), rx.text("Tecnologia e utilidade importam mais do que o ticker isolado.", class_name="step-copy"), class_name="step-card"),
                        rx.box(rx.text("02", class_name="step-number"), rx.text("Qual e o seu horizonte?", class_name="step-title"), rx.text("Um plano de longo prazo nao combina com decisoes tomadas a cada candle.", class_name="step-copy"), class_name="step-card"),
                        rx.box(rx.text("03", class_name="step-number"), rx.text("Quanto voce aceita perder?", class_name="step-title"), rx.text("Volatilidade e parte do produto. Dimensione o risco antes da entrada.", class_name="step-copy"), class_name="step-card"),
                        spacing="3", flex="1",
                    ),
                    spacing="9", align="start",
                ),
                id="aprenda", max_width="1180px", margin="0 auto", padding="100px 24px",
            ),
            rx.box(
                rx.hstack(
                    rx.vstack(rx.text("AVISO IMPORTANTE", class_name="section-kicker"), rx.heading("Cenarios nao sao promessas.", class_name="disclaimer-title"), rx.text("As leituras deste site sao hipoteticas, baseadas em premissas e sujeitas a falhas. Nada aqui constitui recomendacao financeira, oferta ou garantia de retorno. Consulte um profissional habilitado e faca sua propria pesquisa.", class_name="disclaimer-copy"), spacing="3", align="start", flex="1"),
                    rx.text("Leia os perfis com senso critico.", class_name="disclaimer-aside"), spacing="8", align="center",
                ),
                id="riscos", class_name="disclaimer-band",
            ),
        ),
        footer(), class_name="site-shell",
    )


def lineage_item(year: str, title: str, text: str) -> rx.Component:
    return rx.hstack(
        rx.text(year, class_name="timeline-year"),
        rx.box(rx.box(class_name="timeline-dot"), rx.box(class_name="timeline-line"), class_name="timeline-marker"),
        rx.vstack(rx.text(title, class_name="timeline-title"), rx.text(text, class_name="timeline-copy"), spacing="1", align="start"),
        spacing="4", align="start",
    )


def price_chart() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.text("MOVIMENTO DE PRECO", class_name="section-kicker"),
                rx.text("Historico comparativo", class_name="chart-title"),
                rx.text(ChartState.chart_description, class_name="chart-copy"),
                spacing="1", align="start",
            ),
            rx.spacer(),
            rx.hstack(
                rx.button("Semana", on_click=ChartState.set_period("semana"), class_name="period-button"),
                rx.button("Mes", on_click=ChartState.set_period("mes"), class_name="period-button"),
                rx.button("Ano", on_click=ChartState.set_period("ano"), class_name="period-button"),
                spacing="1",
            ),
            align="start", width="100%",
        ),
        rx.hstack(
            rx.text("Linha em alta", class_name="legend blue"),
            rx.text("Linha em baixa", class_name="legend red"),
            spacing="4", margin_top="22px",
        ),
        rx.recharts.line_chart(
            rx.recharts.cartesian_grid(stroke_dasharray="3 3", opacity=0.28),
            rx.recharts.x_axis(data_key="label"),
            rx.recharts.y_axis(),
            rx.recharts.tooltip(),
            rx.recharts.line(data_key="value", type="monotone", stroke=ChartState.chart_color, stroke_width=3, dot=False),
            data=ChartState.chart_data,
            width="100%", height=290,
        ),
        class_name="chart-card",
    )


def asset_page(symbol: str, name: str, tagline: str, color: str, price: str, market_cap: str, role: str, lineage: list[tuple[str, str, str]], scenarios: list[tuple[str, str, str]]) -> rx.Component:
    return rx.box(
        nav_bar(),
        rx.box(
            rx.box(
                rx.link("<- Voltar ao mercado", href="/#mercado", class_name="back-link"),
                rx.hstack(
                    rx.vstack(rx.hstack(rx.box(symbol[0], class_name=f"asset-icon {color}"), rx.vstack(rx.text(symbol, class_name="asset-symbol"), rx.heading(name, class_name="asset-name"), spacing="0", align="start"), spacing="4"), rx.text(tagline, class_name="asset-tagline"), spacing="5", align="start"),
                    rx.vstack(rx.text("COTACAO ATUAL · BINANCE", class_name="metric-label"), rx.text(rx.cond(ChartState.active_price == "Consultando API...", price, ChartState.active_price), class_name="asset-price"), rx.text("Valor em tempo real", class_name="metric-note teal"), spacing="1", align="end"),
                    justify="between", align="end", width="100%", margin_top="48px",
                ),
                rx.hstack(metric_card("Papel no ecossistema", role, "Leitura de uso", color), metric_card("Capitalizacao", market_cap, "Estimativa didatica", "blue"), metric_card("Risco principal", "Alta volatilidade", "Pode superar cenarios", "orange"), spacing="4", width="100%", margin_top="48px"),
                price_chart(),
                max_width="1180px", margin="0 auto", padding="44px 24px 88px",
            ),
            rx.box(
                rx.hstack(
                    rx.vstack(section_heading("LINHAGEM", "Como este ativo chegou ate aqui.", "Uma linha do tempo curta ajuda a separar origem, evolucao e narrativa de mercado."), rx.vstack(*[lineage_item(*item) for item in lineage], spacing="5", class_name="timeline"), spacing="8", align="start", flex="1"),
                    rx.vstack(section_heading("CENARIOS", "O que pode mover a tese.", "Nao sao previsoes: sao cenarios condicionais para organizar perguntas e riscos."), rx.vstack(*[rx.box(rx.text(label, class_name="scenario-label"), rx.text(title, class_name="scenario-title"), rx.text(text, class_name="scenario-copy"), class_name="scenario-card") for label, title, text in scenarios], spacing="3", width="100%"), spacing="8", align="start", flex="1"),
                    spacing="9", align="start", width="100%",
                ),
                max_width="1180px", margin="0 auto", padding="0 24px 100px",
            ),
            rx.box(rx.text("DISCLAIMER DE CENARIO", class_name="section-kicker"), rx.text("Este perfil e educacional e teorico. Movimentos futuros dependem de fatores imprevisiveis, como liquidez, regulacao, tecnologia e comportamento coletivo. Nao e recomendacao de compra ou venda.", class_name="disclaimer-copy"), max_width="1180px", margin="0 auto", padding="0 24px 80px"),
        ),
        footer(), class_name="site-shell",
    )


def bitcoin() -> rx.Component:
    return asset_page("BTC", "Bitcoin", "Uma rede monetaria digital escassa, sem emissor central.", "teal", "US$ 67.842,10", "US$ 1,34 tri", "Reserva digital", [("2008", "O protocolo nasce", "O whitepaper propoe dinheiro eletronico peer-to-peer sem intermediarios."), ("2009", "Primeiro bloco", "A rede entra em operacao e estabelece a prova de trabalho como mecanismo de consenso."), ("2024", "Nova fase de acesso", "Produtos regulados ampliam o acesso, sem remover o risco de volatilidade.")], [("CENARIO A", "Adocao gradual", "Mais participantes e infraestrutura podem sustentar a demanda, caso a liquidez acompanhe."), ("CENARIO B", "Pressao macro", "Juros, regulacao ou aversao a risco podem reduzir apetite por ativos volateis.")])


def ethereum() -> rx.Component:
    return asset_page("ETH", "Ethereum", "Uma camada programavel para contratos, aplicacoes e ativos digitais.", "blue", "US$ 3.542,76", "US$ 426 bi", "Infraestrutura", [("2013", "A proposta", "A visao de uma blockchain programavel amplia o uso para alem de pagamentos."), ("2015", "A rede e lancada", "Contratos inteligentes passam a permitir aplicacoes construidas sobre uma base compartilhada."), ("2022", "Mudanca de consenso", "A rede migra para proof of stake e muda sua dinamica de seguranca e emissao.")], [("CENARIO A", "Mais atividade on-chain", "Aplicacoes uteis e escalabilidade podem ampliar a procura por espaco na rede."), ("CENARIO B", "Competicao", "Outras redes, custos e complexidade podem limitar a captura de valor pelo protocolo.")])


def solana() -> rx.Component:
    return asset_page("SOL", "Solana", "Uma rede de alta velocidade focada em aplicacoes e experiencias on-chain.", "orange", "US$ 168,31", "US$ 81 bi", "Aplicacoes", [("2017", "A ideia de tempo", "O projeto explora uma referencia temporal para ordenar eventos em uma rede distribuida."), ("2020", "Mainnet beta", "A rede com altas taxas de processamento comeca a atrair builders e validadores."), ("2024", "Crescimento de apps", "DeFi, jogos e experiencias de consumo tornam a atividade mais visivel.")], [("CENARIO A", "Efeito de rede", "Mais usuarios e aplicacoes podem reforcar liquidez e utilidade, se a confiabilidade persistir."), ("CENARIO B", "Concentracao", "Falhas, congestionamento ou dependencia de poucos participantes podem elevar o risco.")])


app = rx.App(stylesheets=["/styles.css"])
app.add_page(home, route="/", on_load=ChartState.load_data)
app.add_page(bitcoin, route="/bitcoin", on_load=[ChartState.select_asset("BTC"), ChartState.load_data])
app.add_page(ethereum, route="/ethereum", on_load=[ChartState.select_asset("ETH"), ChartState.load_data])
app.add_page(solana, route="/solana", on_load=[ChartState.select_asset("SOL"), ChartState.load_data])
