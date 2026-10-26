# 0008 — Automação e publicação / Automation and publishing

- **Status:** aceito / accepted
- **Data / Date:** 2026-10-25

## pt-BR

### Contexto
O site deve se atualizar sozinho, mas uma fonte pode revisar valores antigos, mudar de
formato ou publicar um erro. Publicar direto o que chega das fontes tornaria o site
irreprodutível e sem revisão.

### Decisão
- **`ci.yml`** (todo PR e push na `main`): lint, testes, reprodutibilidade (reconstruir a
  partir dos dados brutos commitados não pode mudar nada) e build do site.
- **`deploy.yml`** (push na `main`): publica no GitHub Pages a partir **só** do que está
  commitado. O site publicado sempre corresponde a um commit.
- **`update-data.yml`** (toda segunda-feira, 06:00 UTC, ou manual): baixa novos
  snapshots e, se algum valor mudou, roda os testes e o build do site e abre um PR com o
  trecho do changelog de dados. Uma pessoa revisa antes do merge, que dispara a
  publicação. Os testes rodam no próprio workflow porque PRs abertos com o `GITHUB_TOKEN`
  não disparam o `ci.yml`.

### Desvio do pedido original
O pedido era rodar "agendado e a cada push" e publicar. A execução agendada **não publica
sozinha**: ela prepara um PR e espera revisão humana. É uma escolha deliberada (dados
revisados pela fonte não vão ao ar sem revisão) que precisa da concordância de quem mantém
o projeto.

### Consequências
- Atualização "agendada e a cada push" sem publicar dado não revisado.
- Configuração necessária no repositório: Pages com origem "GitHub Actions" e permissão
  para o GitHub Actions criar pull requests (Settings → Actions → General).

## English

### Context
The site should update itself, but a source may revise past values, change format or
publish an error. Publishing whatever arrives would make the site unreproducible and
unreviewed.

### Decision
`ci.yml` runs lint, tests, the reproducibility check and the site build on every PR and
push. `deploy.yml` publishes to GitHub Pages on push to `main`, from committed files only.
`update-data.yml` runs weekly (Mondays 06:00 UTC, or manually), fetches new snapshots and,
if any value changed, runs the tests and site build and opens a PR with the data changelog
excerpt for human review; merging it triggers the deploy. Checks run inside the workflow
because PRs opened with `GITHUB_TOKEN` do not trigger `ci.yml`.

**Deviation from the original request:** "scheduled and on every push" publishing. The
scheduled run does **not** publish on its own; it prepares a PR for human review. This is
deliberate and needs the maintainer's agreement.

### Consequences
Scheduled and on-push updates without publishing unreviewed data. Required repository
settings: Pages source "GitHub Actions" and allowing GitHub Actions to create pull requests.
