# 0006 — Licenças das fontes / Source licenses

- **Status:** aceito, com verificação pendente / accepted, verification pending
- **Data / Date:** 2026-10-25

## pt-BR

### Contexto
Toda observação carrega a licença da fonte (ADR 0002). Algumas fontes usam licenças
padronizadas; órgãos públicos brasileiros costumam publicar termos próprios sem
identificador SPDX.

### Decisão

| Fonte | Identificador registrado | Base |
|---|---|---|
| Banco Mundial (WDI, WGI) | `CC-BY-4.0` | [Termos de uso de datasets do Banco Mundial](https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets) |
| PNUD (HDR) | `CC-BY-3.0-IGO` | [Termos de uso do HDRO](https://hdr.undp.org/terms-use), conferidos em 2026-10-25 |
| IBGE (SIDRA) | `LicenseRef-IBGE-reuse-with-attribution` | Termos de uso do IBGE: reutilização permitida com citação da fonte |
| Ipeadata | `LicenseRef-Ipeadata-reuse-with-attribution` | Reprodução permitida com citação da fonte |
| V-Dem | `CC-BY-SA-4.0` | [Página do dataset V-Dem](https://v-dem.net/data/the-v-dem-dataset/), conferida em 2026-10-25. **Compartilha igual:** dados e gráficos derivados do V-Dem são distribuídos sob CC BY-SA 4.0, não CC BY 4.0 |

Identificadores `LicenseRef-*` seguem a convenção SPDX para licenças sem identificador
oficial.

### Verificação pendente
Os termos do IBGE e do Ipeadata **não foram conferidos automaticamente** nesta fase (a
página de termos do IBGE bloqueia acesso automatizado). Uma pessoa precisa conferir os
textos atuais e atualizar este ADR com os links exatos.

### Consequências
O site mostra a licença de cada gráfico a partir do dado, não de texto fixo. Se uma
licença mudar, basta mudar o conector; a próxima coleta registra a nova licença.

## English

### Context
Every observation carries its source license (ADR 0002). Some sources use standard
licenses; Brazilian public bodies usually publish their own terms without an SPDX
identifier.

### Decision
World Bank (WDI, WGI): `CC-BY-4.0`. UNDP HDR: `CC-BY-3.0-IGO` (terms checked on
2026-10-25). IBGE SIDRA: `LicenseRef-IBGE-reuse-with-attribution`. Ipeadata:
`LicenseRef-Ipeadata-reuse-with-attribution`. V-Dem: `CC-BY-SA-4.0` (share-alike:
V-Dem-derived data and charts are distributed under CC BY-SA 4.0, not CC BY 4.0; checked
on 2026-10-25). `LicenseRef-*` follows the SPDX convention
for licenses without an official identifier.

### Verification pending
IBGE and Ipeadata terms were **not checked automatically** in this phase (IBGE's terms page
blocks automated access). A person must check the current texts and update this ADR with
exact links.

### Consequences
The site shows each chart's license from the data, not from fixed text. If a license
changes, only the connector changes; the next collection records the new license.
