# Causas dos desvios nos indicadores de logística

[![Dashboard ao vivo](https://img.shields.io/badge/Dashboard-ao%20vivo-ff3d81)](https://luiscarlossoarespro-cyber.github.io/causas-desvios-indicadores-logistica/dashboard/)

**Demonstração do dashboard em uso (1 min 47 s):**

https://github.com/user-attachments/assets/d6ed445a-2fb6-4a26-b989-161deaa29bd7


**Pergunta:** o indicador mostra que os pedidos atrasam. **O que explica o atraso e o que fazer?**

Projeto de análise de dados com a base pública DataCo Supply Chain (65.752 pedidos). O dashboard é interativo: os filtros de **Ano** e **Mês** recalculam todos os números, gráficos e o simulador.

## Resposta em uma frase
Os atrasos não vêm de região, cliente, categoria ou época: vêm do **prazo que a empresa promete em cada modo de envio**.

## O que os dados mostraram
| Achado | Número |
|---|---|
| Pedidos que atrasam (válidos: 62.897) | **57,3%** (IC 95%: 56,9% a 57,7%) |
| Atrasos de 1 dia / até 2 dias | 58,6% / 86,4% dos atrasos |
| First Class (promete 1 dia, leva 2) | **100%** de atraso |
| Second Class / Same Day / Standard Class | 80,0% / 48,4% / 39,8% |
| Países, categorias e meses fora do esperado | **nenhum** (controle de falsos alarmes FDR 5%; gráfico de controle) |
| Clientes que reincidem além do acaso | **não** (p = 0,67) |
| Lucro médio por pedido: atrasado × no prazo | 59,37 × 62,06 (p = 0,34, sem diferença significativa) |
| Simulação: First Class prometendo 2 dias | atraso cai de 57,3% para **42,0%** |
| Simulação: os 4 modos ajustados | 19,8% (o prazo médio prometido sobe de 2,9 para 4,1 dias) |

Prometer mais dias reduz o atraso, mas aumenta a espera do cliente: o simulador mostra essa troca.

## O que tem no dashboard
Cards no topo com comparação com a base toda · Onde o atraso acontece (por modo, gravidade, de onde vêm os atrasos, promessa × capacidade) · O que **não** explica (meses, países, categorias, clientes, lucro) · Simulador de prazos · Ranking com analítico em CSV · Plano de ação e indicadores recomendados · Como conferi e limites · Decisão recomendada.

## Como conferi os números
- Auditoria da base e regras de exclusão documentadas (cancelados e suspeita de fraude ficam fora; out/2017 a jan/2018 têm cobertura parcial e ficam fora do gráfico mensal).
- Segundo método: **SQL direto no arquivo original** (DuckDB): 23 + 14 checagens dos números-chave, 0 divergências.
- O próprio dashboard foi conferido em 10 recortes de Ano e Mês contra SQL: **241 verificações, 0 divergências** (`src/09_conferencia_dashboard.py`, resultado em `resultados/09_conferencia_dashboard.csv`).

## Limitações (importante)
- O autor da base **não informa se os dados são reais ou simulados**, e a regularidade dos prazos sugere simulação. Por isso, nada aqui é afirmação sobre uma empresa real.
- A base não separa as etapas do processo (separação, transporte), então não mostra a causa física do atraso.
- A moeda dos valores não está informada.

## Estrutura
`src/` scripts numerados (01 auditoria, 02 tratamento, 03 planilhas, 04 e 06 análise, 05 e 07 conferência SQL, 08 dashboard, 09 conferência do dashboard, 10 demonstração) · `resultados/` tabelas geradas · `dashboard/` página interativa.
Os dados brutos e a base tratada não estão no repositório (tamanho); baixe a base original abaixo e rode os scripts na ordem.

## Ferramentas
Python (pandas, scipy, scikit-learn), SQL (DuckDB), Google Sheets, HTML/CSS/JavaScript, Playwright.

## O que fiz eu × o que fez a IA
- **Eu (Luis):** tive a ideia a partir do meu post sobre indicadores, escolhi e aprovei a base pública, defini o que o projeto precisava mostrar, validei a base e as planilhas e decidi o visual do dashboard (cores, movimento, filtros).
- **IA (Claude, da Anthropic):** escreveu os scripts em Python e SQL, calculou as análises e montou o código do dashboard, sob a minha direção.

## Fonte dos dados e licença
DataCo Smart Supply Chain for Big Data Analysis, Mendeley Data, licença **CC BY 4.0**: https://data.mendeley.com/.
