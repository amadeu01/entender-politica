# 0007 — Rastreabilidade do conteúdo / Content traceability

- **Status:** aceito / accepted
- **Data / Date:** 2026-10-25

## pt-BR

### Contexto
O site promete que todo número tem fonte. Textos escritos à mão tendem a acumular números
copiados, arredondados ou desatualizados. A verificação precisa ser automática.

### Decisão
1. **Nenhum número digitado no texto.** O build rejeita qualquer número em análises e
   fichas de políticas, exceto anos (1900–2099, inclusive "1980s"), ordinais ("5ª", "3rd")
   e números colados a nomes ("COVID-19", "G20").
2. **Números entram por marcadores:**

   | Marcador | Origem do número |
   |---|---|
   | `{{ v("indicador", "GEO", ano) }}` | dado do repositório |
   | `{{ diff("indicador", "GEO", ano0, ano1) }}` | diferença entre dois anos do dado |
   | `{{ pct("indicador", "GEO", ano0, ano1) }}` | variação percentual entre dois anos |
   | `{{ cite("texto", "doi", "local") }}` | número citado de um artigo revisado por pares (o DOI precisa estar nas referências; "local" diz onde: resumo, tabela, página) |
   | `{{ lit("texto", "justificativa") }}` | qualquer outro caso, com justificativa escrita |

   Cada número aparece no site como link para uma tabela "de onde vem este número" com
   fonte, versão e data de coleta (dados) ou DOI e local (artigos).
3. **Traduções citam os mesmos dados:** a sequência de marcadores `v`, `diff` e `pct` tem
   que ser idêntica em pt-BR e inglês.
4. **DOIs verificados:** `compilador verify-dois` consulta a Crossref e grava metadados e
   BibTeX em `data/reference/dois.json`. O build offline exige que todo DOI citado esteja
   nesse registro e que o ano da citação coincida com o ano registrado pela Crossref.
5. **Neutralidade verificável:**
   - toda análise tem pelo menos uma evidência a favor e uma contra a hipótese;
   - toda ficha de política tem pelo menos um resultado nulo, negativo ou misto, ou um
     campo `contrary_evidence_search` dizendo onde a evidência contrária foi procurada;
   - `causal_claims: true` só é aceito com desenho causal (experimento, diferenças em
     diferenças, regressão descontínua, controle sintético, variáveis instrumentais).
6. **Nível de evidência** das fichas: alto quando há experimento aleatorizado ou revisão
   sistemática; moderado com outro desenho causal; baixo nos demais casos.
7. **Números de artigos só de fontes conferidas.** Ao escrever, só use `cite` com um número
   que você leu na fonte (o resumo, uma tabela, uma página). Nada de memória.

### Consequências
- Erros de digitação e números inventados quebram o CI.
- Escrever fica mais lento; em troca, revisar fica mais fácil: o revisor confere a fonte de
  cada `cite` e `lit`, e os dados se conferem sozinhos.
- O verificador não entende semântica: ele garante a origem do número, não que a frase
  em volta o interprete corretamente. Isso continua sendo papel da revisão humana.
- Lacunas conhecidas do verificador: números por extenso ("dois anos") e quantidades entre
  1900 e 2099, que se confundem com anos. A revisão humana cobre esses casos.
- O texto fora dos marcadores é escapado antes de virar HTML: contribuições não podem
  injetar marcação no site.

## English

### Context
The site promises every number has a source. Handwritten text accumulates copied, rounded
or stale numbers; verification must be automatic.

### Decision
1. No typed numbers in text, except years (1900–2099, including "1980s"), ordinals and
   numbers glued to names ("COVID-19", "G20").
2. Numbers enter through placeholders: `v`, `diff` and `pct` (repository data), `cite`
   (a number quoted from a peer-reviewed paper, whose DOI must be among the references,
   with its location), and `lit` (anything else, with a written justification). Each
   number links to a "where this number comes from" table.
3. Translations must use the identical sequence of data placeholders.
4. `compilador verify-dois` checks DOIs on Crossref and stores metadata and BibTeX in
   `data/reference/dois.json`; the offline build requires every cited DOI to be there and
   the citation year to match Crossref.
5. Verifiable neutrality: every analysis has evidence for and against; every policy brief
   has a null, negative or mixed finding or documents where contrary evidence was sought;
   `causal_claims: true` requires a causal design.
6. Policy evidence level: high with a randomized experiment or systematic review;
   moderate with another causal design; low otherwise.
7. Quote numbers from papers only after reading them in the source (abstract, table,
   page), never from memory.

### Consequences
Typos and invented numbers break CI. Writing is slower; reviewing is easier. The checker
guarantees where a number comes from, not that the sentence interprets it correctly; that
remains the job of human review. Known gaps: spelled-out numbers and quantities between
1900 and 2099 (read as years). Text outside placeholders is HTML-escaped, so contributions
cannot inject markup.
