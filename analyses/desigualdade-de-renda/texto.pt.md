## O que os dados mostram

### Anos 1980: desigualdade alta e crescente

Pela antiga PNAD, o Gini da renda domiciliar per capita era
{{ v("ipeadata.disoc_rdcg", "BRA", 1981) }} em 1981 e chegou a
{{ v("ipeadata.disoc_rdcg", "BRA", 1989) }} em 1989, o valor mais alto da série. Foi uma
década de renda estagnada e inflação crescente: o PIB per capita variou
{{ pct("wdi.ny_gdp_pcap_kd", "BRA", 1980, 1990) }} entre 1980 e 1990, e a inflação ao
consumidor chegou a {{ v("wdi.fp_cpi_totl_zg", "BRA", 1989) }}% em 1989.

### Anos 1990: menos pobreza, mesma desigualdade

Entre 1993 e 1995, período do Plano Real, a taxa de pobreza medida com as linhas regionais
do Ipea passou de {{ v("ipeadata.disoc_ppy", "BRA", 1993) }}% para
{{ v("ipeadata.disoc_ppy", "BRA", 1995) }}%. O Gini quase não se moveu:
{{ v("ipeadata.disoc_rdcg", "BRA", 1993) }} em 1993 e
{{ v("ipeadata.disoc_rdcg", "BRA", 1995) }} em 1995. Barros, Henriques e Mendonça (2000)
descreveram esse quadro, nas palavras e no juízo dos autores, como uma "estabilidade
inaceitável" da desigualdade.

### De 2001 a 2014: queda contínua

O Gini da PNAD antiga variou {{ diff("ipeadata.disoc_rdcg", "BRA", 2001, 2014) }} entre
2001 e 2014, de {{ v("ipeadata.disoc_rdcg", "BRA", 2001) }} para
{{ v("ipeadata.disoc_rdcg", "BRA", 2014) }}. No mesmo período, a taxa de pobreza com
linhas regionais foi de {{ v("ipeadata.disoc_ppy", "BRA", 2003) }}% em 2003 para
{{ v("ipeadata.disoc_ppy", "BRA", 2014) }}% em 2014.

### Desde 2012: PNAD Contínua

A série oficial atual do IBGE começa em {{ v("ibge_sidra.gini_pnadc", "BRA", 2012) }} em
2012. Depois da recessão de 2015 e 2016, quando o PIB per capita variou
{{ pct("wdi.ny_gdp_pcap_kd", "BRA", 2014, 2016) }} em dois anos, o índice subiu para
{{ v("ibge_sidra.gini_pnadc", "BRA", 2018) }} em 2018. Em 2020 foi a
{{ v("ibge_sidra.gini_pnadc", "BRA", 2020) }} e voltou a
{{ v("ibge_sidra.gini_pnadc", "BRA", 2021) }} em 2021; nesses dois anos a renda vem da 5ª
visita da pesquisa, e não da 1ª, por causa da pandemia. Em 2024 o valor foi
{{ v("ibge_sidra.gini_pnadc", "BRA", 2024) }}. O gráfico mostra o intervalo de {{ lit("95%", "nível de confiança do intervalo calculado a partir do coeficiente de variação do IBGE; ver o catálogo") }} de cada
ano: diferenças pequenas entre anos vizinhos podem não ser estatisticamente significativas.

### O Brasil e os vizinhos

A queda dos anos 2000 não foi exclusiva do Brasil. Entre 2002 e 2014, pelo Gini do Banco
Mundial (escala de {{ lit("0 a 100", "escala do índice publicada pelo Banco Mundial") }}), o Brasil variou {{ diff("wdi.si_pov_gini", "BRA", 2002, 2014) }},
o México {{ diff("wdi.si_pov_gini", "MEX", 2002, 2014) }} e a Colômbia
{{ diff("wdi.si_pov_gini", "COL", 2002, 2014) }}; a Argentina urbana variou
{{ diff("wdi.si_pov_gini", "ARG", 2003, 2014) }} entre 2003 e 2014. Quando vários países
mudam juntos, fatores comuns à região provavelmente pesam,
ao lado de políticas nacionais.

### Desigualdade além da renda

Em 2023, o IDH do Brasil foi {{ v("undp_hdr.hdi", "BRA", 2023) }} e o IDH ajustado à
desigualdade, {{ v("undp_hdr.ihdi", "BRA", 2023) }}. A diferença é o quanto de
desenvolvimento humano se perde pela desigualdade em saúde, educação e renda.

## O que a literatura atribui

Os estudos revisados por pares apontam vários fatores, e nenhum explica sozinho a queda.
A valorização do salário mínimo, as transferências focalizadas como o Bolsa Família e
mudanças no mercado de trabalho, como a queda do retorno à experiência, aparecem com pesos
diferentes conforme o período, a medida de renda e o método. As evidências a favor e
contra estão listadas abaixo, cada uma com o artigo de origem.
