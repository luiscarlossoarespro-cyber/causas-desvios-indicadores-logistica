import json, pandas as pd
A=json.load(open('resultados/an_respostas.json')); B=json.load(open('resultados/an6_respostas.json'))
t=pd.read_csv('resultados/base_tratada_itens.csv',parse_dates=['data_pedido'])
o=pd.read_csv('resultados/base_pedidos.csv',parse_dates=['data_pedido'])
v=o[o.cancelado==0].copy()
it=t[t.cancelado==0].groupby('id_pedido').agg(venda=('venda_item','sum'),lucro=('lucro_pedido','sum')).reset_index()
pais=t.drop_duplicates('id_pedido')[['id_pedido','pais_destino']]
v=v.merge(it,on='id_pedido').merge(pais,on='id_pedido')
v['ano']=v.data_pedido.dt.year; v['mes']=v.data_pedido.dt.month
modos=['First Class','Same Day','Second Class','Standard Class']; mi={m:i for i,m in enumerate(modos)}
v['mi']=v.modo_envio.map(mi)
cA=v.groupby(['ano','mes','mi','prev','real']).agg(n=('id_pedido','size'),venda=('venda','sum'),lucro=('lucro','sum')).reset_index()
cubeA=[[int(r.ano),int(r.mes),int(r.mi),int(r.prev),int(r.real),int(r.n),round(float(r.venda),6),round(float(r.lucro),6)] for r in cA.itertuples()]
big=v.groupby('pais_destino').size(); paises=sorted(big[big>=300].index); pidx={p:i for i,p in enumerate(paises)}
vp=v[v.pais_destino.isin(paises)].copy(); vp['pi']=vp.pais_destino.map(pidx)
cB=vp.groupby(['pi','ano','mes','mi']).agg(n=('id_pedido','size'),late=('atrasou','sum')).reset_index()
cubeB=[[int(r.pi),int(r.ano),int(r.mes),int(r.mi),int(r.n),int(r.late)] for r in cB.itertuples()]
D=dict(modos=modos,cubeA=cubeA,paises=paises,cubeB=cubeB,B={k:x for k,x in B.items() if k not in('cenarios',)},
 sens=pd.read_csv('resultados/an6_sensibilidade.csv').to_dict('records'),
 plano=pd.read_csv('resultados/an6_plano_acao.csv').to_dict('records'),kpi=pd.read_csv('resultados/an6_dicionario_indicadores.csv').to_dict('records'),
 cancel=pd.read_csv('resultados/an6_cancelamento_por_modo.csv').to_dict('records'))
html=open('src/previa_template.html',encoding='utf-8').read().replace('__DATA__',json.dumps(D,ensure_ascii=False)).replace('__NCHK__',str(len(pd.read_csv('resultados/09_conferencia_dashboard.csv'))))
open('previa/dashboard_previa.html','w',encoding='utf-8').write(html);print(len(html),len(cubeA),len(cubeB))
