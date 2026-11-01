# Auditoria dos dados de educação / Education data audit

Data da auditoria / Audit date: 2026-11-01 · Base: `data/processed/observations.csv` (Brasil) e `education/`.

## pt-BR

### Séries de educação no catálogo (Brasil)

| Indicador | Cobertura | Lacunas dentro da série | Observação |
|---|---|---|---|
| `undp_hdr.mys` anos médios de estudo | 1990–2023 | nenhuma | série contínua; adultos, muda devagar |
| `undp_hdr.eys` anos esperados de estudo | 1990–2023 | nenhuma | |
| `undp_hdr.hdi`, `undp_hdr.ihdi` | 1990–2023, 2010–2023 | nenhuma | IDH composto; a metodologia mudou em 2010 |
| `wdi.se_adt_litr_zs` alfabetização de adultos | 1980–2024 | 1981–1999 (exceto 1980), 2001–2003, 2005 | só anos de censo ou pesquisa; **não há dado entre 1980 e 2000** |
| `wdi.se_xpd_totl_gd_zs` gasto público em educação (% PIB) | 1995–2022 | 1996, 1997, 2003 | soma União, estados e municípios; sobe quando o PIB cai |
| `wdi.gb_xpd_rsdv_gd_zs` P&D (% PIB) | 2000–2023 | nenhuma | não é só educação |
| `wdi.sp_pop_scie_rd_p6` pesquisadores por milhão | 2000–2014 | nenhuma | para em 2014 |
| `wdi.se_pre_enrr` matrícula bruta pré-escola | 2007–2020 | 2010 | bruta; pode passar de cem por cento |
| `wdi.se_prm_enrr` matrícula bruta primário | 2012–2024 | 2023 | |
| `wdi.se_sec_enrr` matrícula bruta secundário | 2012–2024 | 2023 | |
| `wdi.se_ter_enrr` matrícula bruta superior | 2012–2024 | 2023 | |
| `siconfi.*` gasto federal em educação, em reais constantes | 2014–2025 | nenhuma | novo (ADR 0014); sem dotação nem bloqueio |

### O que isso significa para os governos

- **Figueiredo a Itamar (1979–1994):** só alfabetização de 1980 e anos médios de estudo a partir de 1990. As tabelas de variação mostram "sem dado" onde falta o ano-base.
- **FHC a Lula 2 (1995–2010):** gasto público (% PIB), anos médios de estudo e alfabetização de 2000 em diante. **Nenhuma série de matrícula por etapa** antes de 2007, nenhuma de gasto federal em reais antes de 2014.
- **Dilma 1 a Lula 3 (2011–hoje):** matrículas por etapa a partir de 2012; gasto federal em reais constantes a partir de 2014 (cobre o corte de 2015, o teto de gastos, 2019 e a recomposição de 2023).
- **Defasagem de publicação:** o Banco Mundial e o PNUD publicam com um a três anos de atraso; o governo atual quase não tem dado.

### Lacunas que nenhuma fonte alcançável cobre (do ambiente de desenvolvimento)

- **Aprendizado** (Saeb/Ideb, Pisa): Inep bloqueado; o Banco Mundial não publica. Sem isso, não dá para ver efeito de política sobre qualidade.
- **Dotação autorizada, bloqueio e contingenciamento por ano:** SIOP e SIGA Brasil só têm consulta; Portal da Transparência exige chave. Cortes aparecem aqui apenas como **execução** (empenhado/pago), que pode diferir do bloqueio.
- **Gasto federal antes de 2014:** a API do Siconfi começa em 2014; há arquivos mensais do Tesouro (2008–2019, planilha de 74 MB) mas em regime de caixa e incluindo despesa financeira, sem comparabilidade de nível com a DCA.
- **Matrículas por rede e nível (Censo Escolar), conclusão, repetência, perfil dos ingressantes:** Inep e SIDRA bloqueados. A taxa de conclusão do ensino primário (`SE.PRM.CMPT.ZS`) vem vazia para o Brasil.
- **Programas específicos** (Pronatec, Fies, ProUni, Ciência sem Fronteiras, Pé-de-Meia): sem série própria; só aparecem como marcos legais.

### Problemas de qualidade encontrados

- A série `GB.XPD` (gasto como % do gasto do governo) vem com zero artificial em 1995 e 1998–2000 na API do Banco Mundial; **não foi adicionada ao catálogo** por isso.
- A matrícula bruta passa de cem por cento (repetentes e idade fora da série); comparar com cuidado.
- Os registros de normas em `education/normas` seguem sem `verified`: sete não têm projeto na Câmara e nenhum resumo foi conferido com o texto oficial (ADR 0012).
- Os perfis de governo (ADR 0013) não têm nenhum item `checked`; os links foram escritos pelo padrão do Planalto, sem abrir as páginas.

## English

### Education series in the catalog (Brazil)

See the table above (identifiers and coverage are the same). Summary of coverage: mean and expected years of schooling and HDI 1990–2023 without gaps; adult literacy only in survey years (nothing between 1980 and 2000); public education spending (% of GDP) 1995–2022 with three gaps; enrollment by level only from 2007 (pre-primary) or 2012 (other levels), missing 2023; federal spending in constant reais 2014–2025 (new, ADR 0014).

### What this means for the governments

Before 1995 there is almost nothing to put beside the laws; from 1995 on there are spending, years of schooling and literacy; enrollment by level and federal spending exist only from 2012 and 2014. The current government has almost no data because of the one-to-three-year publication lag.

### Gaps no reachable source covers (from the development environment)

Learning outcomes (Saeb/Ideb, Pisa); authorized appropriation, withholding and *contingenciamento* per year (cuts appear here only as **execution**, which can differ from the block); federal spending before 2014; the School Census and attainment, repetition and entrant profile; program-level series (Pronatec, Fies, ProUni, Science without Borders, Pé-de-Meia).

### Quality issues found

The World Bank `GB.XPD` series has artificial zeros in 1995 and 1998–2000 and was **not added**; gross enrollment passes one hundred percent; the law records in `education/normas` still lack `verified`; the government profiles (ADR 0013) have no `checked` item.
