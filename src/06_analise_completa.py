# Analise completa (nivel senior): gravidade, capacidade x promessa, paises, reincidencia, sensibilidade, impacto, cenarios.
import pandas as pd, numpy as np, json
from scipy import stats
rng=np.random.default_rng(42)
t=pd.read_csv('resultados/base_tratada_itens.csv',parse_dates=['data_pedido'])
o=pd.read_csv('resultados/base_pedidos.csv',parse_dates=['data_pedido'])
v=o[o.cancelado==0].copy(); v['atrasou']=v.atrasou.astype(int); v['exc']=v.real-v.prev
n=len(v); R={}
def wilson(k,n,z=1.96):
    p=k/n;d=1+z*z/n;c=p+z*z/(2*n);m=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n));return (c-m)/d,(c+m)/d
# A) Gravidade do atraso
late=v[v.atrasou==1]
def faixa(x): return '1 dia' if x==1 else '2 dias' if x==2 else '3 dias' if x==3 else '4 dias ou mais'
late=late.assign(faixa=late.exc.map(faixa))
G=late.groupby(['modo_envio','faixa']).size().unstack(fill_value=0)
G['total']=G.sum(axis=1); G.loc['TODOS']=G.sum()
Gp=(G.div(G['total'],axis=0)).round(4)
G.reset_index().to_csv('resultados/an6_gravidade_contagem.csv',index=False)
Gp.reset_index().to_csv('resultados/an6_gravidade_pct.csv',index=False)
R['gravidade']={c:float(Gp.loc['TODOS',c]) for c in Gp.columns if c!='total'}
R['gravidade_1dia_pct']=float((late.exc==1).mean()); R['gravidade_ate2_pct']=float((late.exc<=2).mean())
# B) Promessa x capacidade
rows=[]
for m,s in v.groupby('modo_envio'):
    pr=int(s.prev.iloc[0]); r=dict(modo=m,pedidos=len(s),prazo_prometido=pr,real_min=int(s.real.min()),real_p50=float(s.real.quantile(.5)),real_p90=float(s.real.quantile(.9)),real_max=int(s.real.max()),pct_atraso=float(s.atrasou.mean()))
    for alvo in (0.10,0.05,0.0):
        r[f'prazo_p/atraso<={int(alvo*100)}%']=next(p for p in range(0,10) if (s.real>p).mean()<=alvo)
    rows.append(r)
B=pd.DataFrame(rows).round(4); B.to_csv('resultados/an6_promessa_vs_capacidade.csv',index=False)
# C) Paises: real vs esperado pelo mix de modos, BH-FDR
pm=v.groupby('modo_envio').atrasou.mean()
cat=t[t.cancelado==0].drop_duplicates('id_pedido')[['id_pedido','pais_destino','regiao_destino','categoria','departamento']]
w=v.merge(cat,on='id_pedido'); w['esp']=w.modo_envio.map(pm)
def vs_esperado(col,minimo=300):
    g=w.groupby(col).agg(pedidos=('atrasou','size'),atrasados=('atrasou','sum'),esperado=('esp','sum'),var=('esp',lambda x:(x*(1-x)).sum())).reset_index()
    g=g[g.pedidos>=minimo].copy(); g['z']=(g.atrasados-g.esperado)/np.sqrt(g['var']); g['p']=2*stats.norm.sf(abs(g.z))
    o_=np.argsort(g.p.values); m=len(g); adj=np.empty(m); prev=1
    for rank,i in reversed(list(enumerate(o_,1))): prev=min(prev,g.p.values[i]*m/rank); adj[i]=prev
    g['p_fdr']=adj; g['pct']=g.atrasados/g.pedidos; g['pct_esperado']=g.esperado/g.pedidos; g['desvio_pp']=(g.pct-g.pct_esperado)*100
    return g.drop(columns='var').sort_values('p')
for col,nome in [('pais_destino','paises'),('categoria','categorias'),('regiao_destino','regioes')]:
    g=vs_esperado(col); g.round(4).to_csv(f'resultados/an6_real_vs_esperado_{nome}.csv',index=False)
    R[f'{nome}_testados']=int(len(g)); R[f'{nome}_sinalizados_fdr5']=int((g.p_fdr<0.05).sum()); R[f'{nome}_max_desvio_pp']=float(g.desvio_pp.abs().max())
# D) Reincidencia por cliente (raw tem Customer Id)
raw=pd.read_csv('raw/DataCoSupplyChainDataset.csv',encoding='latin-1',usecols=['Order Id','Customer Id'],low_memory=False).drop_duplicates('Order Id')
c=v.merge(raw.rename(columns={'Order Id':'id_pedido','Customer Id':'cliente'}),on='id_pedido')
cs=c.groupby('cliente').agg(pedidos=('atrasou','size'),atrasados=('atrasou','sum'),esperado=('modo_envio',lambda s:s.map(pm).sum())).reset_index()
cs=cs[cs.pedidos>=3]
sim=[]
P=[c[c.cliente==k].modo_envio.map(pm).values for k in cs.cliente]
obs_var=np.var((cs.atrasados/cs.pedidos).values)
sims=[]
probs=[p for p in P]
for _ in range(200):
    sims.append(np.var([rng.binomial(1,p).mean() for p in probs]))
R['reincid']=dict(clientes_3mais=int(len(cs)),var_observada=float(obs_var),var_simulada_media=float(np.mean(sims)),var_simulada_p95=float(np.quantile(sims,.95)),p_sim=float((np.array(sims)>=obs_var).mean()))
cs['atrasou_todas']=(cs.atrasados==cs.pedidos).astype(int)
R['reincid']['clientes_sempre_atrasados_pct']=float(cs.atrasou_todas.mean()); R['reincid']['esperado_sempre_atrasados_pct']=float(np.mean([np.prod(p) for p in probs]))
# E) Sensibilidade da definicao
sens=[]
def add(nome,s,col='atrasou'): k=int(s[col].sum()); l,h=wilson(k,len(s)); sens.append(dict(cenario=nome,pedidos=len(s),atrasados=k,pct=k/len(s),ic_lo=l,ic_hi=h))
add('Definicao base (real > prometido)',v)
v['atr2']=(v.exc>=2).astype(int); add('So atrasos de 2 dias ou mais',v,'atr2')
add('Sem First Class',v[v.modo_envio!='First Class'])
add('Sem Same Day',v[v.modo_envio!='Same Day'])
add('Somente Standard Class',v[v.modo_envio=='Standard Class'])
vv=v[v.data_pedido<'2017-10-01']; add('So meses completos (ate 09/2017)',vv)
allv=o.copy(); allv['atrasou']=allv.atrasou.fillna(0).astype(int); add('Incluindo cancelados como nao atrasados',allv)
S=pd.DataFrame(sens).round(6); S.to_csv('resultados/an6_sensibilidade.csv',index=False)
# F) Impacto financeiro
it=t[t.cancelado==0].groupby('id_pedido').agg(venda=('venda_item','sum'),lucro=('lucro_pedido','sum'),desc=('desconto','mean'),qtd=('quantidade','sum')).reset_index()
f=v.merge(it,on='id_pedido')
rows=[]
for nome,s in [('No prazo',f[f.atrasou==0]),('Atrasado',f[f.atrasou==1])]:
    rows.append(dict(grupo=nome,pedidos=len(s),venda_total=s.venda.sum(),venda_media=s.venda.mean(),lucro_medio=s.lucro.mean(),lucro_mediana=s.lucro.median(),desconto_medio=s.desc.mean(),pct_lucro_negativo=(s.lucro<0).mean()))
F=pd.DataFrame(rows).round(4); F.to_csv('resultados/an6_impacto_financeiro.csv',index=False)
R['mw_lucro_p']=float(stats.mannwhitneyu(f[f.atrasou==1].lucro,f[f.atrasou==0].lucro).pvalue)
R['mw_venda_p']=float(stats.mannwhitneyu(f[f.atrasou==1].venda,f[f.atrasou==0].venda).pvalue)
fg=f.groupby(f.exc.clip(upper=4)).agg(pedidos=('lucro','size'),lucro_medio=('lucro','mean'),venda_media=('venda','mean')).reset_index().round(2)
fg.to_csv('resultados/an6_lucro_por_dias_excesso.csv',index=False)
R['venda_atrasados']=float(f[f.atrasou==1].venda.sum()); R['venda_total']=float(f.venda.sum())
# G) Cancelamento/fraude por modo (todos os pedidos)
st=t.drop_duplicates('id_pedido').assign(fraude=lambda d:(d.status_pedido=='SUSPECTED_FRAUD').astype(int))
g=st.groupby('modo_envio').agg(pedidos=('id_pedido','size'),cancelados=('cancelado','sum'),fraude=('fraude','sum')).reset_index()
g['pct_cancelado']=g.cancelados/g.pedidos; g['pct_fraude']=g.fraude/g.pedidos; g.round(4).to_csv('resultados/an6_cancelamento_por_modo.csv',index=False)
R['cancel_chi_p']=float(stats.chi2_contingency(pd.crosstab(st.modo_envio,st.cancelado))[1])
# H) Cenarios de SLA
base=v.copy(); cen=[]
def pct(prom): return float((base.real>base.modo_envio.map(prom)).mean())
atual={m:int(s.prev.iloc[0]) for m,s in v.groupby('modo_envio')}
def cena(nome,mudanca):
    p=dict(atual); p.update(mudanca); a=pct(p); cen.append(dict(cenario=nome,prazos=str(p),pct_atraso=a,reducao_pp=(R_atual-a)*100,prazo_medio_prometido=float(base.modo_envio.map(p).mean())))
R_atual=pct(atual)
cena('Hoje',{})
cena('A) First Class: 1 -> 2 dias',{'First Class':2})
cena('B) A + Same Day: 0 -> 1 dia',{'First Class':2,'Same Day':1})
cena('C) B + Second Class: 2 -> 4 dias',{'First Class':2,'Same Day':1,'Second Class':4})
cena('D) C + Standard: 4 -> 5 dias',{'First Class':2,'Same Day':1,'Second Class':4,'Standard Class':5})
cena('E) Prazo = maximo real de cada modo',{'First Class':2,'Same Day':1,'Second Class':6,'Standard Class':6})
C_=pd.DataFrame(cen).round(4); C_.to_csv('resultados/an6_cenarios_sla.csv',index=False)
# I) KPIs
kpi=pd.DataFrame([
 ['Taxa de entrega no prazo (OTD)','Pedidos com dias reais <= prazo prometido / pedidos válidos','Por modo de envio, não só o geral','Logística','Semanal'],
 ['Taxa de atraso','1 - OTD','Meta definida por modo (prazo que entrega com até 10% de atraso)','Logística','Semanal'],
 ['Dias de excesso (P90)','P90 de (dias reais - prazo prometido), só nos atrasados','Acompanhar a gravidade, não só a frequência','Logística','Semanal'],
 ['Aderência da promessa','Prazo prometido / P90 dos dias reais, por modo','Valor 1,0 ou mais indica promessa realista','Comercial + Logística','Mensal'],
 ['Pedidos cancelados / suspeita de fraude','Cancelados / pedidos totais','Separar do indicador de prazo','Risco','Mensal'],
 ['Lucro médio por pedido: atrasado x no prazo','Média do lucro por grupo','Verificar se o atraso custa margem','Financeiro','Mensal']],
 columns=['indicador','formula','como_usar','dono','frequencia'])
kpi.to_csv('resultados/an6_dicionario_indicadores.csv',index=False)
a=C_.set_index('cenario')
fmt=lambda x:('%.1f'%(x*100)).replace('.',',')+'%'
plano=pd.DataFrame([
 ['Ajustar a promessa do First Class (1 -> 2 dias)','Hoje 100% dos pedidos First Class chegam em 2 dias; prometer 1 garante o atraso','Comercial + Logística','Regra de prazo no checkout','Atraso geral de {} para {}'.format(fmt(R_atual),fmt(a.loc['A) First Class: 1 -> 2 dias','pct_atraso'])),'Custo baixo: só a promessa muda'],
 ['Revisar a promessa do Same Day e do Second Class','Same Day atrasa 48% e Second Class 80%: o real passa da promessa','Logística','Revisão de prazos por modo','Com os dois ajustes: {}'.format(fmt(a.loc['C) B + Second Class: 2 -> 4 dias','pct_atraso'])),'Ou aumentar a capacidade'],
 ['Painel por modo (não só o geral)','O indicador geral esconde que o problema está no prazo de cada modo','Analista de dados','Dashboard de indicadores','Visibilidade semanal','Custo baixo'],
 ['Monitorar com gráfico de controle','Nenhum mês saiu do esperado: o atraso é constante','Analista de dados','Gráfico p com limites','Alerta só se sair do limite','Evita reagir a ruído'],
 ['Validar a causa com dados reais da empresa','A base não traz etapas (separação, transporte) nem transportadora','Gestor + TI','Novas colunas de rastreio','Permite achar a causa física','Depende da empresa']],
 columns=['acao','por_que','quem','onde_como','impacto_simulado','observacao'])
plano.to_csv('resultados/an6_plano_acao.csv',index=False)
R['cenarios']=C_.to_dict('records'); R['atual_pct']=R_atual
json.dump(R,open('resultados/an6_respostas.json','w'),indent=1,ensure_ascii=False,default=float)
print(B.to_string()); print(Gp.to_string()); print(S.to_string()); print(F.to_string()); print(C_[['cenario','pct_atraso','reducao_pp','prazo_medio_prometido']].to_string())
print(json.dumps({k:v_ for k,v_ in R.items() if k not in('cenarios','gravidade')},indent=1,default=float,ensure_ascii=False))
