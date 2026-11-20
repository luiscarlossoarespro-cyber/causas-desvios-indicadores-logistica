import duckdb, json
R=json.load(open('resultados/an_respostas.json'))
con=duckdb.connect()
con.execute("""create view b as select * from read_csv('raw/dataco_utf8.csv',header=true,ignore_errors=true,sample_size=-1)""")
con.execute("""create view p as select "Order Id" id, any_value("Shipping Mode") modo, any_value("Days for shipment (scheduled)") prev, any_value("Days for shipping (real)") real,
 any_value("Delivery Status") st, count(*) itens from b group by 1""")
r=lambda q:con.execute(q).fetchall()
chk=[]
def ok(nome,sql_v,py_v,tol=1e-9):
    good=abs(float(sql_v)-float(py_v))<=tol;chk.append((nome,float(sql_v),float(py_v),good));return good
n=r("select count(*) from p where st<>'Shipping canceled'")[0][0];k=r("select count(*) from p where st='Late delivery'")[0][0]
ok('pedidos válidos',n,R['q1']['pedidos']);ok('pedidos atrasados',k,R['q1']['atrasados']);ok('% atraso',k/n,R['q1']['pct'])
ok('pedidos totais',r("select count(*) from p")[0][0],65752);ok('itens',r("select count(*) from b")[0][0],180519)
ok('cancelados',r("select count(*) from p where st='Shipping canceled'")[0][0],R['q7']['pedidos'])
for x in R['q2']:
    a,b=r(f"select count(*), sum(case when st='Late delivery' then 1 else 0 end) from p where st<>'Shipping canceled' and modo='{x['modo']}'")[0]
    ok('pedidos '+x['modo'],a,x['pedidos']);ok('atrasados '+x['modo'],b,x['atrasados']);ok('% '+x['modo'],b/a,x['pct_atraso'],1e-4)
# real>prev == late
ok('contradições real>prev vs status',r("select count(*) from p where st<>'Shipping canceled' and ((real>prev) <> (st='Late delivery'))")[0][0],0)
# excesso médio
ok('excesso médio dias',r("select avg(real-prev) from p where st='Late delivery'")[0][0],R['q1']['dias_excesso_medio'],1e-9)
# venda
vt=r("select sum(\"Sales\") from b where \"Delivery Status\"<>'Shipping canceled'")[0][0];va=r("select sum(\"Sales\") from b where \"Delivery Status\"='Late delivery'")[0][0]
ok('venda total',vt,R['q6']['venda_total'],1e-3);ok('venda em atrasados',va,R['q6']['venda_em_atrasados'],1e-3)
# cenário First Class real>2
fc=r("select count(*) from p where st<>'Shipping canceled' and modo='First Class' and real>2")[0][0];rest=r("select count(*) from p where st='Late delivery' and modo<>'First Class'")[0][0]
ok('cenário só First Class',(fc+rest)/n,R['q5_so_first'])
bad=[c for c in chk if not c[3]]
import csv
with open('resultados/05_conferencia_sql.csv','w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['numero','calculado_em_SQL_no_arquivo_original','calculado_em_Python_na_base_tratada','bate']);[w.writerow([a,round(b,6),round(c,6),'sim' if d else 'NÃO']) for a,b,c,d in chk]
print(len(chk),'conferências;',len(bad),'divergências');[print(x) for x in bad]
