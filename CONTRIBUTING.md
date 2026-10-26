# Como contribuir / How to contribute

**pt-BR** · [English](#english)

Obrigado por ajudar. Este projeto só funciona se cada afirmação puder ser verificada,
então o processo de revisão é mais rigoroso do que o comum.

## Tipos de contribuição

1. **Nova fonte de dados:** um conector em `pipeline/compilador/sources/`, com testes sem
   acesso à rede (respostas sintéticas no formato da fonte) e um snapshot real commitado
   em `data/raw/`, que o CI reprocessa a cada PR; o manifesto registra URL, licença e
   versão da fonte.
2. **Novo indicador:** um arquivo em `indicators/` com definição, fórmula, fonte, DOI do
   artigo que fundamenta a métrica e críticas conhecidas à métrica.
3. **Nova análise:** uma pasta em `analyses/<slug>/` com `analise.yaml`, `texto.pt.md` e
   `texto.en.md`. Números no texto só entram por marcadores: `v`, `diff` e `pct` para
   dados do repositório, `cite` para números de artigos e `lit` com justificativa
   ([ADR 0007](docs/adr/0007-rastreabilidade-do-conteudo.md)). DOIs novos:
   `uv run compilador verify-dois`.
4. **Nova ficha de política:** um arquivo em `policies/` com desenho da avaliação, tamanho
   do efeito, intervalo de confiança, DOI e validade externa para o Brasil. Fichas de
   políticas que **não** funcionaram são tão bem-vindas quanto as que funcionaram.
5. **Correções:** dados, traduções, acessibilidade, código.

## Regras

- **Tudo em pt-BR e inglês.** O CI falha se faltar um dos idiomas.
- **Nada de número sem fonte.** O CI rejeita números digitados à mão no texto das análises.
- **Linguagem neutra.** Descreva o que os dados mostram; evite adjetivos partidários.
- **Correlação não é causalidade.** Se a análise sugere causa, o método precisa sustentar
  isso (experimento, quase-experimento) e a limitação precisa estar escrita.
- **Decisões metodológicas** novas viram um ADR em `docs/adr/`.
- **Commits pequenos** no formato [Conventional Commits](https://www.conventionalcommits.org/).

## Ambiente

```sh
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

## Revisão

Todo PR passa pelo checklist científico do template. Análises e fichas de políticas
precisam de pelo menos uma revisão de alguém que não seja o autor.

---

## English

Thank you for helping. This project only works if every claim can be verified, so the
review process is stricter than usual.

**Contribution types:** data source connectors (network-free tests with synthetic
responses in the source's format, plus a committed real snapshot in `data/raw/` that CI
rebuilds on every PR), indicators (definition, formula, source, DOI, known criticisms),
analyses (`analise.yaml` + `texto.pt.md` + `texto.en.md`, numbers only through
`v`/`diff`/`pct`, `cite` or `lit` placeholders, see ADR 0007; new DOIs:
`uv run compilador verify-dois`), policy briefs (evaluation design, effect size,
confidence interval, DOI, external validity for Brazil; policies that did **not** work
are equally welcome), and
fixes.

**Rules:** everything in Portuguese and English (CI enforces it); no unsourced numbers
(CI enforces it); neutral language; correlation is not causation, and causal claims need
a design that supports them; new methodological decisions get an ADR in `docs/adr/`;
small commits using Conventional Commits.

**Setup:** `uv sync && uv run pytest && uv run ruff check . && uv run ruff format --check .`

**Review:** every PR goes through the scientific checklist in the template. Analyses and
policy briefs need at least one review by someone other than the author.
