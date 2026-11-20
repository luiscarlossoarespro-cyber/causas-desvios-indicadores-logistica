# Confere o dashboard (JavaScript no navegador) contra SQL direto no arquivo original, em varios filtros.
import duckdb, json, os, pandas as pd
from playwright.sync_api import sync_playwright
con=duckdb.connect()
con.execute("""create view b as select * from read_csv('raw/dataco_utf8.csv',header=true,ignore_errors=true,sample_size=-1)""")
con.execute("""create table v as select "Order Id" id, any_value("Shipping Mode") modo, any_value("Days for shipment (scheduled)") prev, any_value("Days for shipping (real)") real,
 any_value("Order Status") os, any_value("Order Country") pais, any_value(strptime("order date (DateOrders)",'%m/%d/%Y %H:%M')) dt, sum("Sales") venda, sum("Benefit per order") lucro
 from b group by 1 having os not in ('CANCELED','SUSPECTED_FRAUD')""")
con.execute("create table w as select *, year(dt) a, month(dt) m, real-prev e from v")
MOD=['First Class','Same Day','Second Class','Standard Class']
def sql(a,m):
    wh=' where 1=1'+(f' and a={a}' if a else '')+(f' and m={m}' if m else '')
    r=lambda q:con.execute(q+wh).fetchall()[0]
    n,late,ven,venL=r("select count(*),sum((e>0)::int),sum(venda),sum(case when e>0 then venda else 0 end) from w")
    g=[int(r(f"select count(*) from w")[0]*0+con.execute(f"select count(*) from w{wh} and e{c}").fetchall()[0][0]) for c in ['=1','=2','=3','>=4']]
    mods={k:con.execute(f"select count(*),sum((e>0)::int),quantile_disc(real,0.5),quantile_disc(real,0.9) from w{wh} and modo='{k}'").fetchall()[0] for k in MOD}
    return dict(n=n,late=late,venda=ven,vendaL=venL,grav=g,mods=mods)
filtros=[(0,0),(2015,0),(2016,0),(2017,0),(2018,0),(0,3),(2016,3),(2017,11),(2015,1),(2018,1)]
res=[];ok_all=True
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page();pg.goto('file://'+os.path.abspath('previa/dashboard_previa.html'));pg.wait_for_timeout(500)
    for a,m in filtros:
        pg.select_option('#fa',str(a));pg.select_option('#fm',str(m));pg.wait_for_timeout(200)
        js=pg.evaluate("({n:S.n,late:S.late,venda:S.vend,vendaL:S.vendL,grav:S.grav,mods:S.mod.map(x=>[x.n,x.late,pct(x.h,x.n,.5),pct(x.h,x.n,.9)])})")
        q=sql(a,m)
        def cmp(nome,x,y,tol=1e-6):
            global ok_all
            good=abs(float(x)-float(y))<=tol;ok_all&=good;res.append(dict(ano=a or 'Todos',mes=m or 'Todos',conferencia=nome,dashboard=float(x),sql=float(y),ok=good))
        cmp('pedidos válidos',js['n'],q['n']);cmp('pedidos atrasados',js['late'],q['late']);cmp('vendas',js['venda'],q['venda'],0.01);cmp('vendas em atrasados',js['vendaL'],q['vendaL'],0.01)
        for i,gv in enumerate(q['grav']):cmp(f'atraso grupo {i+1}',js['grav'][i],gv)
        for i,k in enumerate(MOD):
            if q['mods'][k][0]:
                cmp(f'{k}: pedidos',js['mods'][i][0],q['mods'][k][0]);cmp(f'{k}: atrasados',js['mods'][i][1],q['mods'][k][1]);cmp(f'{k}: mediana real',js['mods'][i][2],q['mods'][k][2]);cmp(f'{k}: P90 real',js['mods'][i][3],q['mods'][k][3])
    # países: total de pedidos nos 41 países do cubo em um filtro
    pg.select_option('#fa','2016');pg.select_option('#fm','0');pg.wait_for_timeout(200)
    js=pg.evaluate("D.cubeB.filter(r=>r[1]==2016).reduce((s,r)=>s+r[4],0)")
    paises=pg.evaluate("D.paises");lst=','.join("'"+x.replace("'","''")+"'" for x in paises)
    sq=con.execute(f"select count(*) from w where a=2016 and pais in ({lst})").fetchall()[0][0]
    res.append(dict(ano=2016,mes='Todos',conferencia='pedidos nos 41 países',dashboard=js,sql=sq,ok=js==sq));ok_all&=(js==sq)
df=pd.DataFrame(res);df.to_csv('resultados/09_conferencia_dashboard.csv',index=False)
print(len(df),'conferências;',int((~df.ok).sum()),'divergências')
print(df[~df.ok].to_string())
