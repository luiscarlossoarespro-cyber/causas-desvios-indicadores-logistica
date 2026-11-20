import pandas as pd, numpy as np, json
d=pd.read_csv('raw/DataCoSupplyChainDataset.csv',encoding='latin-1');d.columns=[c.strip() for c in d.columns]
R='Days for shipping (real)';P='Days for shipment (scheduled)'
t=pd.DataFrame({
'id_pedido':d['Order Id'],'id_item':d['Order Item Id'],
'data_pedido':pd.to_datetime(d['order date (DateOrders)']),'data_envio':pd.to_datetime(d['shipping date (DateOrders)']),
'modo_envio':d['Shipping Mode'],'prazo_previsto_dias':d[P],'prazo_real_dias':d[R],
'status_entrega':d['Delivery Status'],'status_pedido':d['Order Status'],'tipo_pagamento':d['Type'],
'mercado':d['Market'],'regiao_destino':d['Order Region'],'pais_destino':d['Order Country'],'cidade_destino':d['Order City'],
'departamento':d['Department Name'],'categoria':d['Category Name'],'produto':d['Product Name'],'segmento_cliente':d['Customer Segment'],
'quantidade':d['Order Item Quantity'],'preco_unitario':d['Order Item Product Price'],'desconto':d['Order Item Discount'],
'venda_item':d['Sales'],'lucro_pedido':d['Order Profit Per Order']})
t['diferenca_dias']=t['prazo_real_dias']-t['prazo_previsto_dias']
t['cancelado']=(t['status_entrega']=='Shipping canceled').astype(int)
t['atrasou']=np.where(t['cancelado']==1,np.nan,(t['status_entrega']=='Late delivery').astype(float))
t['ano_mes']=t['data_pedido'].dt.strftime('%Y-%m')
t['cobertura_completa']=(t['data_pedido']<'2017-10-01').astype(int)
# confere definição
nc=t[t.cancelado==0]
assert ((nc['diferenca_dias']>0)==(nc['atrasou']==1)).all()
t.to_csv('resultados/base_tratada_itens.csv',index=False,encoding='utf-8-sig')
t.sample(300,random_state=1).sort_values('id_item').to_csv('resultados/amostra_300.csv',index=False,encoding='utf-8-sig')
# nível pedido (entrega é do pedido)
o=t.groupby('id_pedido').agg(data_pedido=('data_pedido','first'),modo_envio=('modo_envio','first'),prev=('prazo_previsto_dias','first'),real=('prazo_real_dias','first'),
 status=('status_entrega','first'),mercado=('mercado','first'),segmento=('segmento_cliente','first'),ano=('data_pedido',lambda s:s.dt.year.iloc[0]),itens=('id_item','size'),cancelado=('cancelado','first'),atrasou=('atrasou','first')).reset_index()
o.to_csv('resultados/base_pedidos.csv',index=False)
v=o[o.cancelado==0]
def tab(col):
    g=v.groupby(col).agg(pedidos=('atrasou','size'),atrasados=('atrasou','sum')).reset_index();g['pct_atraso']=(g.atrasados/g.pedidos).round(4);return g
T={}
T['modo']=v.groupby('modo_envio').agg(pedidos=('atrasou','size'),atrasados=('atrasou','sum'),prazo_previsto=('prev','first'),real_min=('real','min'),real_max=('real','max'),real_medio=('real','mean')).reset_index()
T['modo']['pct_atraso']=(T['modo'].atrasados/T['modo'].pedidos).round(4);T['modo']['real_medio']=T['modo'].real_medio.round(2)
T['mercado']=tab('mercado');T['segmento']=tab('segmento');T['ano']=tab('ano')
tot=dict(pedidos_total=int(len(o)),pedidos_cancelados=int(o.cancelado.sum()),pedidos_validos=int(len(v)),atrasados=int(v.atrasou.sum()),pct=round(v.atrasou.mean(),4),itens=int(len(t)))
T['cobertura']=t.groupby('ano_mes').agg(itens=('id_item','size'),pedidos=('id_pedido','nunique')).reset_index()
# distribuição real por modo (pedidos válidos)
T['dist']=pd.crosstab(v['modo_envio'],v['real']).reset_index()
for k,x in T.items(): x.to_csv(f'resultados/tab_{k}.csv',index=False)
json.dump(tot,open('resultados/totais.json','w'))
print(tot)
for k in ['modo','mercado','segmento','ano','dist']: print(T[k].to_string(index=False))
print(len(t.columns),list(t.columns))
