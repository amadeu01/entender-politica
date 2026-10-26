# 0003 — Comparação entre governos e causalidade / Comparing governments and causality

- **Status:** aceito / accepted
- **Data / Date:** 2026-10-25

## pt-BR

### Contexto
O site compara o Brasil de 1980 até hoje, governo a governo. Associar a evolução de um
indicador a um governo sugere que aquele governo causou a mudança. Na maioria dos casos,
os dados não sustentam essa leitura:

- **Defasagem:** políticas de educação e saúde mostram efeito anos depois, às vezes em
  outro governo.
- **Fatores externos:** ciclo das commodities, crises internacionais (1982, 2008),
  pandemia, juros americanos.
- **Outros atores:** Congresso, Judiciário, estados e municípios, Banco Central.
- **Trocas no meio do ano:** em 1985, 1992 e 2016 o ano tem mais de um presidente, e dados
  anuais não permitem dividir o ano entre eles.

### Decisão
1. **Linha do tempo com faixas de governo**, não ranking ou placar por governo.
2. **Tabela de variação por período** com defasagem selecionável de 0, 1 ou 2 anos.
   Atribuição de ano: um ano pertence ao período que esteve em exercício em 1º de julho
   desse ano (ver `governments.Governments.at`). Anos com troca de presidente são
   sinalizados na tabela.
3. **Sempre com comparação:** toda série do Brasil aparece ao lado da média da América
   Latina e Caribe e de países de referência (inicialmente México, Chile, Colômbia e
   Argentina). Se todos mudaram juntos, a mudança provavelmente não é obra de um governo.
4. **Aviso fixo** em toda página de comparação: "Esta visualização é descritiva e não
   demonstra que um governo causou a mudança."
5. **Afirmações causais** só em análises cujo método sustente causalidade (experimento,
   diferenças-em-diferenças, controle sintético, regressão descontínua), sempre com a
   referência revisada por pares.
6. Os períodos ficam em `data/reference/governos.yaml`, com interinidades como períodos
   próprios e fontes oficiais. O arquivo não registra partido, para evitar erros em casos
   de filiação ambígua; isso pode ser revisto em ADR futuro.

### Consequências
- Responde à pergunta "o que mudou em cada governo" sem fingir que responde "por quê".
- Ainda pode ser usado de forma partidária; o aviso e a comparação internacional reduzem,
  mas não eliminam esse risco.

### Alternativas consideradas
- **Só linha do tempo, sem números por governo:** mais segura, mas responde menos à
  pergunta do público.
- **Ranking ou nota por governo:** descartado. Transmite causalidade que os dados não
  sustentam e convida ao uso partidário.

## English

### Context
The site compares Brazil from 1980 to today, government by government. Tying an
indicator's trajectory to a government suggests causation, which the data rarely
supports: policy effects lag (often into the next government), external shocks dominate
(commodity cycle, 1982 and 2008 crises, the pandemic), other actors matter (Congress,
courts, states, central bank), and some years (1985, 1992, 2016) had more than one
president.

### Decision
1. Timelines with government bands; no ranking or scorecard.
2. A per-period change table with a selectable lag of 0, 1 or 2 years. A year belongs to
   the period in office on July 1 of that year; years with a change of president are
   flagged.
3. Always with comparison: every Brazilian series is shown with the Latin America &
   Caribbean average and reference countries (initially Mexico, Chile, Colombia,
   Argentina).
4. A fixed notice on every comparison page: "This visualization is descriptive and does
   not show that a government caused the change."
5. Causal claims only in analyses whose design supports them, with peer-reviewed
   references.
6. Periods live in `data/reference/governos.yaml`, with acting presidencies as their own
   periods and official sources. Party affiliation is not recorded for now.

### Consequences
Answers "what changed under each government" without pretending to answer "why". It can
still be used in a partisan way; the notice and international comparison reduce but do
not remove that risk.

### Alternatives considered
Timeline only (safer, less useful); ranking or scorecard (rejected).
