import pandas as pd, numpy as np
d=pd.read_csv('raw/DataCoSupplyChainDataset.csv',encoding='latin-1')
d.columns=[c.strip() for c in d.columns]
L=[]
def add(nome,regra,n,dec=''):
    L.append(dict(checagem=nome,regra=regra,linhas_afetadas=int(n),pct=round(100*n/len(d),2),decisao=dec))
add('Total de linhas','Linhas no arquivo (cada linha = 1 item de pedido)',len(d),'base de partida')
add('Item de pedido repetido','Order Item Id duplicado',d['Order Item Id'].duplicated().sum(),'manter 1')
add('Linha 100% repetida','todas as colunas iguais',d.duplicated().sum(),'remover se houver')
d['dt_pedido']=pd.to_datetime(d['order date (DateOrders)'],errors='coerce')
d['dt_envio']=pd.to_datetime(d['shipping date (DateOrders)'],errors='coerce')
add('Data do pedido inválida','não converte para data',d['dt_pedido'].isna().sum(),'')
add('Data de envio inválida','não converte para data',d['dt_envio'].isna().sum(),'')
add('Envio antes do pedido','envio < pedido',(d['dt_envio']<d['dt_pedido']).sum(),'')
add('Dias reais negativos','Days for shipping (real) < 0',(d['Days for shipping (real)']<0).sum(),'')
add('Prazo previsto zero ou negativo','Days for shipment (scheduled) <= 0',(d['Days for shipment (scheduled)']<=0).sum(),'')
add('Quantidade <= 0','Order Item Quantity <= 0',(d['Order Item Quantity']<=0).sum(),'')
add('Preço <= 0','Order Item Product Price <= 0',(d['Order Item Product Price']<=0).sum(),'')
add('Vendas negativas','Sales < 0',(d['Sales']<0).sum(),'')
add('Lucro por pedido negativo','Order Profit Per Order < 0 (prejuízo real, não erro)',(d['Order Profit Per Order']<0).sum(),'manter')
# consistência do indicador
real=d['Days for shipping (real)'];prev=d['Days for shipment (scheduled)']
st=d['Delivery Status']
add('Atraso pelo status','Delivery Status = Late delivery',(st=='Late delivery').sum(),'indicador')
add('Atraso por dias (real > previsto)','real > previsto',(real>prev).sum(),'indicador alternativo')
add('Status Late mas real <= previsto','contradição',((st=='Late delivery')&(real<=prev)).sum(),'investigar')
add('Status não-Late mas real > previsto','contradição',((st!='Late delivery')&(real>prev)&(st!='Shipping canceled')).sum(),'investigar')
add('Late_delivery_risk=1 sem status Late','flag x status',((d['Late_delivery_risk']==1)&(st!='Late delivery')).sum(),'investigar')
add('Late_delivery_risk=0 com status Late','flag x status',((d['Late_delivery_risk']==0)&(st=='Late delivery')).sum(),'investigar')
add('Entrega cancelada','Delivery Status = Shipping canceled',(st=='Shipping canceled').sum(),'excluir do cálculo de atraso')
add('Pedido cancelado/suspeito','Order Status CANCELED ou SUSPECTED_FRAUD',d['Order Status'].isin(['CANCELED','SUSPECTED_FRAUD']).sum(),'verificar')
# nulos
for c in d.columns:
    n=d[c].isna().sum()
    if n: add('Nulos em '+c,'célula vazia',n,'')
# sensíveis
for c in ['Customer Email','Customer Fname','Customer Lname','Customer Password','Customer Street','Customer Zipcode']:
    add('Coluna pessoal: '+c,'dado de cliente (privacidade)',d[c].notna().sum(),'NÃO levar para o portfólio')
pd.DataFrame(L).to_csv('resultados/01_auditoria_qualidade.csv',index=False,encoding='utf-8-sig')
pd.set_option('display.width',200,'display.max_colwidth',60,'display.max_rows',200)
print(pd.DataFrame(L)[['checagem','linhas_afetadas','pct']].to_string())
print('periodo',d['dt_pedido'].min(),d['dt_pedido'].max(),'| pedidos',d['Order Id'].nunique(),'| clientes',d['Customer Id'].nunique())
print(st.value_counts().to_dict())
print(d.groupby(d['dt_pedido'].dt.to_period('M')).size().to_string())
print('emails distintos',d['Customer Email'].nunique(), d['Customer Email'].astype(str).str[:12].value_counts().head(3).to_dict(), d['Customer Password'].astype(str).value_counts().head(2).to_dict())
