# 0012 — Módulo de educação / Education module

- **Status:** aceito / accepted
- **Data / Date:** 2026-11-01

## pt-BR

### Contexto
Queremos mostrar, para cada parte da educação (infantil, fundamental, médio, técnica,
graduação, pós-graduação e ciência, financiamento, planejamento), as normas que a
moldam, as votações e alterações na história delas e as métricas disponíveis, lado a lado.
O conector do repositório `llm-legislativo` não traz votos (só proposições, temas e
tramitação), então os votos vêm de outra fonte.

### Decisão
1. **Conteúdo em `education/`:** `submodulos.yaml` (subtemas, indicadores e métricas
   planejadas) e `normas/<slug>.yaml` (uma emenda, lei ou projeto, com eventos datados:
   apresentação, votação em comissão ou plenário, sanção, alteração, revogação, sucessão).
   O build valida, compila `education.json` e a página `/educacao/` mostra uma aba por subtema.
2. **Sem número digitado na prosa**, como na ADR 0007 (anos, décadas e ordinais passam).
   Identificadores de normas (`Lei 9.394/1996`) são campos estruturados.
3. **Votos:** um evento de votação registra apenas que ocorreu, a casa e a forma
   (nominal, simbólica, conclusiva). **Placar por parlamentar e orientação de bancada não
   são digitados:** devem vir de um snapshot dos dados abertos da Câmara (`votacoes`,
   `votacoesVotos`, `votacoesOrientacoes`, `votacoesProposicoes`) e do Senado, num
   conector próprio com manifesto, como as demais fontes. O conector ainda não existe.
4. **Métricas ao lado das normas:** a tabela de cada subtema mostra o valor das séries
   do Brasil no ano de cada evento. É descritiva (ADR 0003): a série mudar depois de uma
   norma não demonstra que a norma causou a mudança. Séries de adultos, como anos médios
   de estudo, mudam devagar por construção.
5. **Métricas planejadas** (`planned_metrics`) listam séries ainda não coletadas, com o
   código na fonte a conferir. Só entram no catálogo junto com o snapshot real.
6. **Verificação:** `verified` (data) indica que o registro foi conferido com o texto
   oficial. Sem ele, o site mostra o aviso "Registro ainda não conferido".

### Consequências
- Estrutura e navegação prontas; o conteúdo cresce por pull request, como as análises.
- Enquanto não houver conector de votos, a seção de votações é qualitativa.
- Os registros iniciais foram redigidos sem acesso às fontes oficiais e precisam de
  conferência humana antes de receberem `verified`.

## English

### Context
For each part of education, show the laws that shape it, the votes and amendments in
their history, and the available metrics side by side. `llm-legislativo` carries no
votes (only propositions, themes and procedural history), so votes need another source.

### Decision
1. Content in `education/`: `submodulos.yaml` and `normas/<slug>.yaml` with dated events.
   The build validates it and compiles `education.json`; `/en/education/` has one tab per
   sub-topic.
2. No hand-typed numbers in prose (ADR 0007); law identifiers are structured fields.
3. Vote events record only that a vote happened, the chamber and the form. Per-legislator
   tallies and party orientations are never typed: they must come from a snapshot of the
   Câmara and Senado open data through a dedicated connector with a manifest. That
   connector does not exist yet.
4. Each sub-topic table shows Brazil's series values in the year of each event. It is
   descriptive (ADR 0003) and does not show causation.
5. `planned_metrics` list series not collected yet, with the source code to confirm; they
   join the catalog only together with a real snapshot.
6. `verified` (a date) marks a record checked against the official text; without it the
   site shows a "not yet checked" notice.

### Consequences
Structure and navigation are ready and content grows by pull request. Until a votes
connector exists the votes section is qualitative. The seed records were written without
access to official sources and need human checking before `verified` is set.
