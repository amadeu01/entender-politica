# 0004 — Todo conteúdo em pt-BR e inglês / All content in Portuguese and English

- **Status:** aceito / accepted
- **Data / Date:** 2026-10-25

## pt-BR

### Contexto
O público principal lê em português, mas a comparação internacional e a revisão por
pesquisadores de fora do Brasil exigem inglês. Traduções feitas depois tendem a ficar
incompletas ou desatualizadas.

### Decisão
- Todo texto visível existe nos dois idiomas desde o primeiro commit.
- Em YAML, campos de texto são objetos `{pt: ..., en: ...}` (`compilador.i18n.Text`);
  nenhum pode ficar vazio.
- Cada análise tem `texto.pt.md` e `texto.en.md`. O CI exige os dois e exige que os
  marcadores de números (`{{ v(...) }}`) sejam os mesmos nas duas versões: a tradução não
  tem como mudar um número.
- Site: pt-BR em `/`, inglês em `/en/`, troca de idioma em toda página, números e datas
  formatados conforme o idioma.
- Glossário de termos técnicos em `docs/glossario.yaml` para manter a tradução
  consistente.
- O código (identificadores, comentários) é escrito em inglês.

### Consequências
Escrever análises e fichas leva cerca do dobro do tempo; a revisão de tradução entra no
checklist de PR.

## English

### Context
The main audience reads Portuguese, but international comparison and review by
researchers outside Brazil require English. Translations added later tend to be
incomplete or stale.

### Decision
All visible text exists in both languages from the first commit. YAML text fields are
`{pt, en}` objects (`compilador.i18n.Text`), never empty. Every analysis has
`texto.pt.md` and `texto.en.md`; CI requires both and requires identical number
placeholders in both, so a translation cannot change a number. The site serves Portuguese
at `/` and English at `/en/` with a language switch on every page and locale-aware number
and date formatting. A glossary in `docs/glossario.yaml` keeps terms consistent. Code is
written in English.

### Consequences
Writing analyses and briefs takes roughly twice as long; translation review is part of
the PR checklist.
