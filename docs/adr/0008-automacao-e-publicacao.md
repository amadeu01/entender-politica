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
  snapshots e, se algum valor mudou, abre um PR com o trecho do changelog de dados. Uma
  pessoa revisa antes do merge, que dispara a publicação.

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
if any value changed, opens a PR with the data changelog excerpt for human review; merging
it triggers the deploy.

### Consequences
Scheduled and on-push updates without publishing unreviewed data. Required repository
settings: Pages source "GitHub Actions" and allowing GitHub Actions to create pull requests.
