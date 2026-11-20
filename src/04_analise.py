import pandas as pd, numpy as np, json
from scipy import stats
from sklearn.linear_model import LogisticRegression
t=pd.read_csv('resultados/base_tratada_itens.csv',parse_dates=['data_pedido','data_envio'])
o=pd.read_csv('resultados/base_pedidos.csv',parse_dates=['data_pedido'])
v=o[o.cancelado==0].copy(); v['atrasou']=v.atrasou.astype(int); v['dif']=v.real-v.prev
R={}
def wilson(k,n,z=1.96):
    p=k/n;d=1+z*z/n;c=p+z*z/(2*n);m=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n));return (c-m)/d,(c+m)/d
# Q1 geral
n=len(v);k=int(v.atrasou.sum());lo,hi=wilson(k,n)
late=v[v.atrasou==1]
R['q1']=dict(pedidos=n,atrasados=k,pct=k/n,ic_lo=lo,ic_hi=hi,dias_excesso_medio=float(late.dif.mean()),dias_excesso_mediana=float(late.dif.median()),dias_excesso_p90=float(late.dif.quantile(.9)),
 real_medio=float(v.real.mean()),real_mediana=float(v.real.median()),real_p90=float(v.real.quantile(.9)),prev_medio=float(v.prev.mean()))
# Q2 modo
rows=[]
for m,s in v.groupby('modo_envio'):
    a=int(s.atrasou.sum());l,h=wilson(a,len(s));ls=s[s.atrasou==1]
    rows.append(dict(modo=m,pedidos=len(s),pct_pedidos=len(s)/n,prazo_prometido=int(s.prev.iloc[0]),real_mediana=float(s.real.median()),real_p90=float(s.real.quantile(.9)),atrasados=a,pct_atraso=a/len(s),ic_lo=l,ic_hi=h,excesso_medio=float(ls.dif.mean()) if len(ls) else 0,
      participacao_nos_atrasos=a/k))
Q2=pd.DataFrame(rows);R['q2']=Q2.round(4).to_dict('records')
# Q3 recorrência (meses com cobertura completa)
vm=v[v.data_pedido<'2017-10-01'].copy();vm['mes']=vm.data_pedido.dt.strftime('%Y-%m')
M=vm.groupby('mes').agg(pedidos=('atrasou','size'),atrasados=('atrasou','sum')).reset_index();M['pct']=M.atrasados/M.pedidos
pbar=M.atrasados.sum()/M.pedidos.sum();M['lcl']=pbar-3*np.sqrt(pbar*(1-pbar)/M.pedidos);M['ucl']=pbar+3*np.sqrt(pbar*(1-pbar)/M.pedidos);M['fora']=((M.pct<M.lcl)|(M.pct>M.ucl)).astype(int)
R['q3']=dict(meses=len(M),pct_min=float(M.pct.min()),pct_max=float(M.pct.max()),media=float(pbar),meses_fora_controle=int(M.fora.sum()))
vm['dow']=vm.data_pedido.dt.dayofweek;dw=vm.groupby('dow').atrasou.mean();R['q3']['dow_min']=float(dw.min());R['q3']['dow_max']=float(dw.max())
M.to_csv('resultados/an_mensal.csv',index=False)
# Q4 causa: o que explica o atraso? teste de independência do prazo real
def chi(col,tab=v):
    ct=pd.crosstab(tab[col],tab['real']);c,p,dof,_=stats.chi2_contingency(ct);n_=ct.values.sum();V=np.sqrt(c/(n_*(min(ct.shape)-1)));return dict(fator=col,qui2=float(c),p=float(p),cramer_v=float(V))
# dentro de cada modo (remove o efeito do prazo prometido)
cat=t[t.cancelado==0].drop_duplicates('id_pedido')[['id_pedido','categoria','departamento','pais_destino','regiao_destino']]
w=v.merge(cat,on='id_pedido');w['mes']=w.data_pedido.dt.strftime('%Y-%m')
Q4=[]
for f in ['mercado','segmento','ano','categoria','regiao_destino']:
    for m in ['Standard Class','Second Class']:
        s=w[w.modo_envio==m];r=chi(f,s);r['modo']=m;Q4.append(r)
Q4=pd.DataFrame(Q4);Q4.to_csv('resultados/an_independencia.csv',index=False);R['q4_max_cramer']=float(Q4.cramer_v.max());R['q4_min_p']=float(Q4.p.min())
# modelo: logística com modo + controles (vs só modo)
X=pd.get_dummies(w[['modo_envio','mercado','segmento','ano']].astype(str),drop_first=True).astype(float)
y=w.atrasou.values
from sklearn.metrics import roc_auc_score
Xm=pd.get_dummies(w[['modo_envio']],drop_first=True).astype(float)
lm=LogisticRegression(max_iter=500,C=1e6).fit(Xm,y);lf=LogisticRegression(max_iter=500,C=1e6).fit(X,y)
R['q4_auc_modo']=float(roc_auc_score(y,lm.predict_proba(Xm)[:,1]));R['q4_auc_completo']=float(roc_auc_score(y,lf.predict_proba(X)[:,1]))
# Q5 simulação de prazo prometido (SLA)
sim=[]
for m,s in v.groupby('modo_envio'):
    for p in range(0,7):
        sim.append(dict(modo=m,prazo_simulado=p,pct_atraso=float((s.real>p).mean())))
S=pd.DataFrame(sim);S.to_csv('resultados/an_simulacao_prazo.csv',index=False)
# cenário: prazo = menor valor com atraso <=10% por modo
alvo=[]
for m,s in v.groupby('modo_envio'):
    for p in range(0,8):
        if (s.real>p).mean()<=0.10: alvo.append((m,p,float((s.real>p).mean()),int(s.prev.iloc[0])));break
R['q5_alvo10']=alvo
tot_new=sum(((v.modo_envio==m)&(v.real>p)).sum() for m,p,_,_ in alvo);R['q5_pct_novo']=float(tot_new/n)
# cenário 2: só corrigir First Class para 2 dias
fc=((v.modo_envio=='First Class')&(v.real>2)).sum();rest=((v.modo_envio!='First Class')&(v.atrasou==1)).sum();R['q5_so_first']=float((fc+rest)/n)
# Q6 impacto financeiro (itens de pedidos válidos)
ti=t[t.cancelado==0].copy();ti['atr']=ti.atrasou.astype(int)
R['q6']=dict(venda_total=float(ti.venda_item.sum()),venda_em_atrasados=float(ti[ti.atr==1].venda_item.sum()),pct=float(ti[ti.atr==1].venda_item.sum()/ti.venda_item.sum()),
 lucro_medio_atrasado=float(ti[ti.atr==1].lucro_pedido.mean()),lucro_medio_prazo=float(ti[ti.atr==0].lucro_pedido.mean()),
 mw_p=float(stats.mannwhitneyu(ti[ti.atr==1].lucro_pedido,ti[ti.atr==0].lucro_pedido).pvalue),lucro_neg_atr=float((ti[ti.atr==1].lucro_pedido<0).mean()),lucro_neg_prazo=float((ti[ti.atr==0].lucro_pedido<0).mean()))
# Q7 cancelamentos
c=t[t.cancelado==1].drop_duplicates('id_pedido');R['q7']=dict(pedidos=len(c),por_status=c.status_pedido.value_counts().to_dict())
# Q8 concentração (Pareto) de pedidos atrasados por país/categoria
P=w[w.atrasou==1].groupby('pais_destino').size().sort_values(ascending=False);cum=P.cumsum()/P.sum();R['q8']=dict(paises=int(len(P)),paises_para_80=int((cum<=0.8).sum()+1))
V=w.groupby('pais_destino').atrasou.agg(['size','mean']);V=V[V['size']>=300];R['q8']['pct_atraso_pais_min']=float(V['mean'].min());R['q8']['pct_atraso_pais_max']=float(V['mean'].max());R['q8']['paises_300+']=int(len(V))
Cc=w.groupby('categoria').atrasou.agg(['size','mean']);Cc=Cc[Cc['size']>=500];R['q8']['cat_min']=float(Cc['mean'].min());R['q8']['cat_max']=float(Cc['mean'].max());R['q8']['categorias_500+']=int(len(Cc))
json.dump(R,open('resultados/an_respostas.json','w'),indent=1,default=float)
print(json.dumps(R,indent=1,default=float)[:6000])
print(M.pct.round(3).describe().to_dict())
print(Q4.round(4).to_string())
