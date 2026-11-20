import pandas as pd, numpy as np, json
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter
tot=json.load(open('resultados/totais.json'))
aud=pd.read_csv('resultados/01_auditoria_qualidade.csv')
ped=pd.read_csv('resultados/base_pedidos.csv',parse_dates=['data_pedido'])
amo=pd.read_csv('resultados/amostra_300.csv')
HD=PatternFill('solid',fgColor='1F3A8A');HF=Font(color='FFFFFF',bold=False,name='Arial',size=10)
BF=Font(name='Arial',size=10);TF=Font(name='Arial',size=16,color='1F3A8A');ST=Font(name='Arial',size=12,color='1F3A8A')
AMA=PatternFill('solid',fgColor='FFF4C2');VERM=PatternFill('solid',fgColor='FFD9D9');VERD=PatternFill('solid',fgColor='D9F7E8')
wb=Workbook()
def sheet(nome,first=False):
    ws=wb.active if first else wb.create_sheet();ws.title=nome;ws.sheet_view.showGridLines=False;return ws
def head(ws,r,cols,c0=1):
    for i,c in enumerate(cols):
        x=ws.cell(r,c0+i,c);x.fill=HD;x.font=HF;x.alignment=Alignment(horizontal='center',vertical='center',wrap_text=True)
def put(ws,r,row,c0=1,fill=None,wrap=False):
    for i,v in enumerate(row):
        if isinstance(v,(np.floating,)):v=float(v)
        if isinstance(v,(np.integer,)):v=int(v)
        x=ws.cell(r,c0+i,v);x.font=BF
        if fill:x.fill=fill
        if wrap:x.alignment=Alignment(wrap_text=True,vertical='top')
def widths(ws,w):
    for i,x in enumerate(w):ws.column_dimensions[get_column_letter(i+1)].width=x
# 1 Leia-me
ws=sheet('Leia-me',True);widths(ws,[34,110])
ws['A1']='Projeto: causas dos desvios nos indicadores de logística';ws['A1'].font=TF
ws['A2']='Tratamento da base DataCo — prévia para o Luis acompanhar, antes do dashboard';ws['A2'].font=ST
L=[('Fonte','DataCo Smart Supply Chain for Big Data Analysis, Mendeley Data, versão 5 (DOI 10.17632/8gx2fvg2k6.5)'),
('Autores','Fabian Constante, Fernando Silva e António Pereira (publicada em 12/03/2019)'),
('Licença','CC BY 4.0 (uso permitido citando a fonte). Conferida na página da base.'),
('Atenção sobre a origem','A página não diz se os dados são reais, anonimizados ou simulados. Os números abaixo mostram um padrão muito regular (veja a aba Primeiros resultados). Isso será dito no projeto.'),
('Arquivo original','DataCoSupplyChainDataset.csv: %s linhas e 53 colunas (cada linha é um item de pedido), de 01/2015 a 01/2018'%format(tot['itens'],',').replace(',','.')),
('Unidade de análise','O PEDIDO. A entrega e o prazo são do pedido inteiro (todos os itens do pedido têm o mesmo status). Contar por item inflaria o peso dos pedidos grandes.'),
('Pedidos','%s no total; %s cancelados (fora do cálculo de atraso); %s válidos'%tuple(format(tot[k],',').replace(',','.') for k in ['pedidos_total','pedidos_cancelados','pedidos_validos'])),
('Definição de atraso','Atrasou = status "Late delivery" = prazo real em dias maior que o prazo previsto. As duas definições coincidem em 100% dos pedidos não cancelados (conferido).'),
('Taxa de atraso geral','%s de %s pedidos válidos = %s%%'%(format(tot['atrasados'],',').replace(',','.'),format(tot['pedidos_validos'],',').replace(',','.'),str(round(tot['pct']*100,1)).replace('.',','))),
('Dados pessoais','As colunas de cliente (e-mail, nome, senha, rua, CEP) foram retiradas e não vão para o projeto nem para o portfólio. (E-mail e senha já vêm mascarados como XXXXXXXXX.)'),
('Abas desta planilha','Auditoria · Decisões do tratamento · Primeiros resultados · Dicionário · Pedidos tratados (65.752 linhas) · Amostra de itens (300 linhas)'),
('Status','Prévia do tratamento. Nada foi publicado. O dashboard só começa depois da sua aprovação desta etapa.')]
for i,(a,b) in enumerate(L):
    r=4+i;put(ws,r,[a,b],wrap=True);ws.cell(r,1).fill=AMA
    ws.row_dimensions[r].height=34 if len(b)>100 else 20
# 2 Auditoria
ws=sheet('Auditoria');widths(ws,[44,52,16,10,36])
head(ws,1,['Checagem','Regra','Linhas afetadas','%','Decisão'])
for i,x in aud.iterrows():
    f=VERM if (x.linhas_afetadas>0 and x.checagem.startswith(('Nulos','Coluna pessoal','Prazo','Status'))) else None
    put(ws,2+i,[x.checagem,x.regra,x.linhas_afetadas,x.pct,x.decisao if isinstance(x.decisao,str) else ''],fill=f)
ws.freeze_panes='A2'
# 3 Decisões
ws=sheet('Decisões do tratamento');widths(ws,[30,60,50,60])
head(ws,1,['Assunto','O que encontrei','Decisão','Motivo'])
D=[('Dados pessoais de clientes','E-mail, nome, sobrenome, senha, rua e CEP estão na base (e-mail e senha mascarados)','Retirar as 6 colunas','Não servem para a análise e não devem aparecer em portfólio público'),
('Colunas vazias ou quase','Descrição do produto: 100% vazia. CEP do destino: 86,2% vazio','Retirar','Sem informação para analisar'),
('Link da imagem do produto','URL de imagem','Retirar','Não é dado de análise'),
('Pedidos cancelados','2.855 pedidos (7.754 itens) com entrega cancelada','Ficam na base, marcados, e saem do cálculo de atraso','Pedido cancelado não tem entrega para medir'),
('Unidade de análise','Em média 2,75 itens por pedido; status e prazo iguais em todos os itens','Analisar por PEDIDO','Evita contar o mesmo atraso várias vezes'),
('Definição de atraso','Status "Late delivery" e "real > previsto" dão o mesmo resultado nos pedidos não cancelados','Usar o status e manter a regra dos dias como conferência','Definição única e conferida'),
('Same Day com prazo 0','9.737 itens com prazo previsto 0 dia (todos Same Day)','Manter','Não é erro: é o prazo do envio no mesmo dia'),
('Lucro negativo','33.784 itens (18,7%) com lucro negativo','Manter','É resultado real da venda, não erro de dado'),
('Cobertura por mês','Out/2017 a Jan/2018 têm cerca de 2.100 itens por mês; os outros meses têm cerca de 5.200','Ficam fora de comparações mensais','Meses incompletos distorcem a tendência'),
('Datas','Todas as datas válidas e envio nunca antes do pedido','Converter para data','Sem correção necessária'),
('Repetidos','Nenhum item repetido, nenhuma linha duplicada','Nada a remover','Conferido por script'),
('Nomes das colunas','Nomes em inglês, alguns com espaços extras','Renomear para português, sem espaços','Mais claro para quem lê (veja o Dicionário)')]
for i,x in enumerate(D):put(ws,2+i,x,wrap=True);ws.row_dimensions[2+i].height=44
ws.freeze_panes='A2'
# 4 Resultados
ws=sheet('Primeiros resultados');widths(ws,[26,14,14,16,16,14,14,14,14])
tabs={k:pd.read_csv(f'resultados/tab_{k}.csv') for k in ['modo','mercado','segmento','ano','dist','cobertura']}
r=1
ws.cell(r,1,'Atraso por modo de envio (pedidos válidos)').font=ST;r+=1
head(ws,r,['Modo de envio','Pedidos','Atrasados','Prazo previsto (dias)','Prazo real mín.','Prazo real máx.','Prazo real médio','% atraso']);r+=1
for _,x in tabs['modo'].iterrows():
    put(ws,r,[x.modo_envio,x.pedidos,int(x.atrasados),x.prazo_previsto,x.real_min,x.real_max,x.real_medio,float(x.pct_atraso)]);ws.cell(r,8).number_format='0.0%';r+=1
r+=1
for k,tt,col in [('mercado','Atraso por mercado','mercado'),('segmento','Atraso por segmento de cliente','segmento'),('ano','Atraso por ano do pedido','ano')]:
    ws.cell(r,1,tt).font=ST;r+=1;head(ws,r,[col.capitalize(),'Pedidos','Atrasados','% atraso']);r+=1
    for _,x in tabs[k].iterrows():
        put(ws,r,[str(x[col]),x.pedidos,int(x.atrasados),float(x.pct_atraso)]);ws.cell(r,4).number_format='0.0%';r+=1
    r+=1
ws.cell(r,1,'Quantos pedidos por prazo real (dias) em cada modo').font=ST;r+=1
dist=tabs['dist'];head(ws,r,['Modo de envio']+[f'{c} dia(s)' for c in dist.columns[1:]]);r+=1
for _,x in dist.iterrows():put(ws,r,list(x));r+=1
r+=1
ws.cell(r,1,'O que isso mostra (leitura do analista)').font=ST;r+=1
for s in ['1. O modo de envio explica quase todo o atraso: First Class atrasa em 100% dos pedidos porque promete 1 dia e entrega sempre em 2.',
 '2. Em Second Class e Standard, o prazo real se espalha quase igual entre 2 e 6 dias (cerca de 20% em cada valor). Em dados reais isso seria incomum.',
 '3. Mercado, segmento e ano ficam todos entre 56% e 59% de atraso: não separam bons e maus resultados.',
 '4. Conclusão provisória: nesta base, a "causa" do atraso é a definição do prazo prometido por modo de envio, e não diferenças entre regiões, clientes ou épocas.',
 '5. Cuidado: a origem da base não é detalhada pelo autor, então isso vale para esta base e não pode ser afirmado sobre uma empresa real.']:
    ws.cell(r,1,s).font=BF;r+=1
# 5 Dicionário
ws=sheet('Dicionário');widths(ws,[24,34,60])
head(ws,1,['Coluna nova','Coluna original','O que representa'])
DIC=[('id_pedido','Order Id','Código do pedido'),('id_item','Order Item Id','Código do item dentro do pedido'),('data_pedido','order date (DateOrders)','Data e hora do pedido'),('data_envio','shipping date (DateOrders)','Data e hora do envio'),
('modo_envio','Shipping Mode','Standard Class, Second Class, First Class ou Same Day'),('prazo_previsto_dias','Days for shipment (scheduled)','Dias prometidos para a entrega'),('prazo_real_dias','Days for shipping (real)','Dias que a entrega levou'),
('status_entrega','Delivery Status','Atrasada, no prazo, antecipada ou cancelada'),('diferenca_dias','calculada','Prazo real menos prazo previsto (positivo = atrasou)'),('atrasou','calculada','1 = atrasou, 0 = não atrasou, vazio = entrega cancelada'),
('cancelado','calculada','1 = entrega cancelada'),('ano_mes','calculada','Ano e mês do pedido'),('cobertura_completa','calculada','0 = mês com cobertura incompleta (a partir de out/2017)'),
('mercado','Market','Africa, Europe, LATAM, Pacific Asia ou USCA'),('regiao_destino','Order Region','Região do destino'),('pais_destino / cidade_destino','Order Country / Order City','Destino do pedido'),
('departamento / categoria / produto','Department Name / Category Name / Product Name','Classificação do produto'),('segmento_cliente','Customer Segment','Consumer, Corporate ou Home Office'),
('quantidade / preco_unitario / desconto / venda_item','Order Item Quantity / Product Price / Discount / Sales','Valores do item'),('lucro_pedido','Order Profit Per Order','Lucro do pedido'),('tipo_pagamento / status_pedido','Type / Order Status','Forma de pagamento e situação do pedido')]
for i,x in enumerate(DIC):put(ws,2+i,x)
# 6 Pedidos
ws=sheet('Pedidos tratados')
cols=['id_pedido','data_pedido','modo_envio','prazo_previsto_dias','prazo_real_dias','diferenca_dias','status_entrega','atrasou','mercado','segmento_cliente','ano','itens','cancelado']
p=ped.rename(columns={'prev':'prazo_previsto_dias','real':'prazo_real_dias','status':'status_entrega','segmento':'segmento_cliente'});p['diferenca_dias']=p.prazo_real_dias-p.prazo_previsto_dias
p['data_pedido']=p.data_pedido.dt.strftime('%Y-%m-%d %H:%M')
head(ws,1,cols);widths(ws,[12,18,16,14,14,12,18,10,14,16,8,8,10])
for row in p[cols].itertuples(index=False):ws.append([None if (isinstance(v,float) and np.isnan(v)) else (int(v) if isinstance(v,(np.integer,)) else (float(v) if isinstance(v,np.floating) else v)) for v in row])
ws.freeze_panes='A2';ws.auto_filter.ref=f'A1:{get_column_letter(len(cols))}{len(p)+1}'
# 7 Amostra
ws=sheet('Amostra de itens')
head(ws,1,list(amo.columns));widths(ws,[11]*len(amo.columns))
for row in amo.itertuples(index=False):ws.append([None if (isinstance(v,float) and np.isnan(v)) else (int(v) if isinstance(v,(np.integer,)) else (float(v) if isinstance(v,np.floating) else v)) for v in row])
ws.freeze_panes='A2'
wb.save('DataCo_tratamento.xlsx')
