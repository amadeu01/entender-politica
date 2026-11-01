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
3. **Votos:** os placares **não são digitados**. Cada norma lista os projetos que a
   originaram, na numeração de cada casa (`camara:` e `senado:`, por exemplo a PEC 15/2015
   da Câmara é a PEC 26/2020 do Senado). `compilador fetch-votes` consulta as APIs de dados
   abertos da Câmara e do Senado e grava snapshots com manifesto (`camara_votos`,
   `senado_votos`): para cada votação em plenário com voto individual, guarda o detalhe, o
   voto de cada parlamentar e, na Câmara, as orientações de bancada. Votações simbólicas
   não têm registro individual e não são guardadas. O build resume cada votação em totais,
   votos por partido e orientações, e gera um CSV com os votos individuais. Eventos de
   votação escritos à mão (`committee_vote`, `plenary_vote`) só registram que a votação
   aconteceu, a casa e a forma. A licença das duas fontes é registrada como
   `LicenseRef-*` com verificação pendente, como no ADR 0006.
4. **Métricas ao lado das normas:** a tabela de cada subtema mostra o valor das séries
   do Brasil no ano de cada evento. É descritiva (ADR 0003): a série mudar depois de uma
   norma não demonstra que a norma causou a mudança. Séries de adultos, como anos médios
   de estudo, mudam devagar por construção.
5. **Métricas planejadas** (`planned_metrics`) listam séries ainda não coletadas, com o
   código na fonte a conferir. Só entram no catálogo junto com o snapshot real.
6. **Verificação em dois níveis:** `identity_checked` (data) indica que número, ano e projeto
   de origem foram conferidos no registro oficial de tramitação da Câmara (a entrada
   "Transformado na Lei ..."); exige um projeto em `camara`. `verified` (data) indica que o
   registro inteiro foi conferido com o texto oficial. Sem `verified`, o site mostra o
   aviso, dizendo o que foi conferido.

### Consequências
- Estrutura e navegação prontas; o conteúdo cresce por pull request, como as análises.
- Votações em plenário de projetos listados em `camara:` ou `senado:` aparecem com placar; as demais só como registro. O Senado exige descobrir o número do projeto na numeração própria da casa, o que ainda foi feito só para o Fundeb.
- Os registros iniciais foram redigidos sem acesso às fontes oficiais. Em 2026-11-01, número e ano de 16 dos 23 foram conferidos na Câmara; os outros 7 (sem projeto na Câmara) e os resumos de todos precisam de conferência humana antes de receberem `verified`.

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
3. Tallies are never typed. Each law lists the bills behind it in each chamber's own
   numbering (`camara:` and `senado:`). `compilador fetch-votes` queries the Câmara and
   Senado open-data APIs and writes manifest-backed snapshots (`camara_votos`,
   `senado_votos`): for each plenary vote with individual records it stores the detail,
   every legislator's vote and, in the Câmara, bench orientations. Symbolic votes have no
   individual record and are not stored. The build summarizes each vote as totals, votes
   by party and orientations, and writes a CSV of individual votes. Hand-written vote
   events (`committee_vote`, `plenary_vote`) only record that a vote happened, the chamber
   and the form. Both sources' license is recorded as `LicenseRef-*`, verification
   pending, as in ADR 0006.
4. Each sub-topic table shows Brazil's series values in the year of each event. It is
   descriptive (ADR 0003) and does not show causation.
5. `planned_metrics` list series not collected yet, with the source code to confirm; they
   join the catalog only together with a real snapshot.
6. Two levels of checking: `identity_checked` (a date) means the number, year and
   originating bill were matched against the Câmara's official procedural record (the
   "Transformado na Lei ..." entry) and needs a bill in `camara`; `verified` (a date) means
   the whole record was checked against the official text. Without `verified` the site
   shows a notice saying what was checked.

### Consequences
Structure and navigation are ready and content grows by pull request. Plenary votes of bills listed in `camara:` or `senado:` show tallies; others are only a record that the vote happened. The Senado needs the bill's number in its own numbering, which has only been found for Fundeb so far. The seed records were written without
access to official sources and need human checking before `verified` is set.
