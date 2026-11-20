# Grava a demonstracao do dashboard (Playwright -> webm -> mp4)
import os, glob, shutil, subprocess
from playwright.sync_api import sync_playwright
HTML='file://'+os.path.abspath('previa/dashboard_previa.html'); OUT='previa/video'; shutil.rmtree(OUT,ignore_errors=True)
CSS='''
#cur{position:fixed;z-index:99999;width:22px;height:22px;border-radius:50%;background:#fff;border:3px solid #ff3d81;box-shadow:0 0 14px #ff3d81;pointer-events:none;transform:translate(-50%,-50%);left:60px;top:60px;transition:left .02s,top .02s}
#ring{position:fixed;z-index:99998;width:20px;height:20px;border-radius:50%;border:3px solid #ffd23f;pointer-events:none;transform:translate(-50%,-50%) scale(.2);opacity:0}
#cap{position:fixed;z-index:99997;left:50%;bottom:26px;transform:translateX(-50%);max-width:86%;background:#050918ee;border:1px solid #ff3d8199;color:#fff;font:600 24px "Segoe UI",sans-serif;padding:14px 26px;border-radius:14px;text-align:center;box-shadow:0 10px 30px #000a;transition:opacity .4s;opacity:0}
#card{position:fixed;inset:0;z-index:99999;background:radial-gradient(700px 400px at 20% 20%,#ff3d8155,transparent 60%),radial-gradient(700px 500px at 80% 70%,#4f8cff55,transparent 60%),#070b1a;color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:"Segoe UI",sans-serif;text-align:center;transition:opacity .8s;padding:0 80px}
#card h1{font-size:50px;margin:0 0 14px;background:linear-gradient(90deg,#fff,#ffd6e6);-webkit-background-clip:text;color:transparent}#card p{font-size:24px;color:#cfd9f5;margin:6px 0}
'''
with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':1280,'height':720},record_video_dir=OUT,record_video_size={'width':1280,'height':720})
    pg=ctx.new_page();pg.goto(HTML);pg.add_style_tag(content=CSS)
    pg.evaluate("""()=>{const c=document.createElement('div');c.id='cur';document.body.appendChild(c);const r=document.createElement('div');r.id='ring';document.body.appendChild(r);const k=document.createElement('div');k.id='cap';document.body.appendChild(k);
     window.__cap=t=>{k.style.opacity=t?1:0;if(t)k.textContent=t};
     document.addEventListener('mousemove',e=>{c.style.left=e.clientX+'px';c.style.top=e.clientY+'px'});
     window.__click=(x,y)=>{r.style.left=x+'px';r.style.top=y+'px';r.animate([{transform:'translate(-50%,-50%) scale(.2)',opacity:1},{transform:'translate(-50%,-50%) scale(2.4)',opacity:0}],{duration:600})};
     const d=document.createElement('div');d.id='card';d.innerHTML='<h1>Causas dos desvios nos indicadores de logística</h1><p>De onde vêm os atrasos? O que fazer?</p><p style="font-size:18px;color:#9fb0d9">Dashboard interativo · Dados públicos DataCo</p>';document.body.appendChild(d);window.__card=d}""")
    W=lambda s:pg.wait_for_timeout(int(s*1000))
    def cap(t,s):pg.evaluate("t=>window.__cap(t)",t);W(s)
    def go(sel,off=110):pg.evaluate("([s,o])=>{const e=document.querySelector(s);window.scrollTo({top:e.getBoundingClientRect().top+scrollY-o,behavior:'smooth'})}",[sel,off])
    def move(x,y):pg.mouse.move(x,y,steps=28)
    def click(sel):
        bx=pg.locator(sel).first.bounding_box();x=bx['x']+bx['width']/2;y=bx['y']+bx['height']/2;move(x,y);pg.evaluate("([x,y])=>window.__click(x,y)",[x,y]);W(.2);pg.locator(sel).first.click();W(.3)
    W(4.5);pg.evaluate("document.getElementById('card').style.opacity=0");W(1)
    move(640,300);cap('57,3% dos pedidos atrasam, mas 86% atrasam só 1 ou 2 dias',6.5)
    cap('Cada card compara o período com a base toda',4);cap(None,.3)
    go('#s2');W(1.2);cap('First Class promete 1 dia e entrega em 2: 100% de atraso',6);cap(None,.3)
    go('#grav',200);W(1.2);cap('86% dos atrasos são de só 1 ou 2 dias: frequente, mas pequeno',6);cap(None,.3)
    go('#s3');W(1.5);cap('O que NÃO explica: nenhum mês, país ou categoria fora do esperado',7);cap(None,.3)
    pg.evaluate("window.scrollTo({top:0,behavior:'smooth'})");W(1.5)
    pg.select_option('#fa','2016');W(1.8);cap('Filtro de ano: cards, gráficos e simulador recalculam',4.5)
    pg.select_option('#fm','3');W(1.8);cap('Filtro de mês: março de 2016',4);cap(None,.2)
    click('#fl');W(1.5)
    go('#s4',100);W(1.2);cap('Simulador: o que muda se o prazo prometido mudar?',3.5)
    click('text=Só First Class: 2 dias');W(1.2);cap('Só ajustar o First Class: o atraso cai de 57,3% para 42,0%',6)
    click('text=+ Standard: 5 dias');W(1.2);cap('Mas há um custo: o prazo médio prometido sobe. É uma troca.',6);cap(None,.2)
    click('text=Hoje');W(.5)
    go('#s4b');W(1.5);cap('Ranking dos modos e países, com analítico em CSV',5);cap(None,.3)
    pg.evaluate("window.scrollTo({top:0,behavior:'smooth'})");W(1.8);cap('Conferido contra SQL: 241 verificações, 0 divergências',5.5);cap(None,.3)
    pg.evaluate("""()=>{const d=window.__card;d.innerHTML='<h1>Decisão: rever o prazo prometido por modo</h1><p>Começando pelo First Class</p><p style="font-size:20px;color:#a7f3d0;margin-top:18px">241 conferências contra SQL · 0 divergências</p><p style="font-size:16px;color:#9fb0d9;margin-top:22px">Base pública DataCo (CC BY 4.0). O autor não informa se os dados são reais ou simulados.</p>';d.style.opacity=1}""");W(5.5)
    ctx.close();b.close()
v=glob.glob(OUT+'/*.webm')[0]
subprocess.run(['ffmpeg','-y','-i',v,'-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-movflags','+faststart','previa/demo_dashboard.mp4'],check=True,capture_output=True)
print('ok')
