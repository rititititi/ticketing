"""Build the standalone bilingual uu scout site and ZIP for local use or GitHub Pages."""
from pathlib import Path
import zipfile
import os,json
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]

def export_demo():
    html=(ROOT/'templates/explorer.html').read_text()
    css=(ROOT/'static/explorer.css').read_text()
    js=(ROOT/'static/explorer.js').read_text()
    translations=(ROOT/'static/i18n.js').read_text()
    data=(ROOT/'data/catalog.json').read_text().replace('<','\\u003c')
    html=html.replace('<link rel="stylesheet" href="{{ url_for(\'static\',filename=\'explorer.css\') }}">','<style>'+css+'</style>')
    html=html.replace('<script src="{{ url_for(\'static\',filename=\'explorer.js\') }}" defer></script>','')
    html=html.replace('<script src="{{ url_for(\'static\',filename=\'i18n.js\') }}" defer></script>','')
    html=html.replace('href="/"','href="index.html"').replace('href="/uploads/"','href="uploads/"')
    js=js.replace("const response=await fetch('/api/catalog');if(!response.ok)throw new Error('Catalog unavailable');catalog=await response.json();", "catalog=JSON.parse(document.getElementById('catalog-data').textContent);")
    js=js.replace('/static/sources/', 'source-images/')
    html=html.replace('href="/static/nov4-coverage.csv"','href="reports/nov4-coverage.csv"')
    html=html.replace('</body>', '<script id="catalog-data" type="application/json">'+data+'</script><script>'+translations+'</script><script>'+js+'</script></body>')
    dest=ROOT/'artifacts';dest.mkdir(exist_ok=True)
    (dest/'index.html').write_text(html)
    with zipfile.ZipFile(dest/'uu-scout.zip','w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('uu-scout/index.html',html)
        admin_url=os.environ.get('UU_SCOUT_ADMIN_URL','').strip()
        if admin_url and (urlparse(admin_url).scheme!='https' or not urlparse(admin_url).netloc):raise ValueError('UU_SCOUT_ADMIN_URL must be an HTTPS URL')
        portal=(ROOT/'templates/upload-admin.html').read_text().replace('__ADMIN_URL__',json.dumps(admin_url).replace('<','\\u003c')).replace('href="/"','href="../index.html"')
        z.writestr('uu-scout/uploads/index.html',portal)
        z.writestr('uu-scout/START HERE.txt','uu scout — NCT WISH Gocheok. Open index.html in your browser and choose English or 简体中文. Keep source-images next to index.html. Source quotes and availability require confirmation.\n打开 index.html，选择 English 或简体中文。请将 source-images 文件夹保留在 index.html 旁边。票源报价及有票状态需另行确认。\n')
        for name in ['coverage.csv','coverage.json','ticket-options.csv','provenance.json']:
            z.write(ROOT/'data/draft2'/name,'uu-scout/reports/'+name)
        z.write(ROOT/'static/nov4-coverage.csv','uu-scout/reports/nov4-coverage.csv')
        z.write(ROOT/'data/nov4/REPORT.md','uu-scout/reports/NOV4-REPORT.md')
        z.write(ROOT/'data/draft2/REPORT.md','uu-scout/reports/REPORT.md')
        for p in sorted((ROOT/'static/sources').iterdir()):
            if p.suffix.lower() not in ['.jpg','.jpeg','.png']:continue
            z.write(p,'uu-scout/source-images/'+p.name)
    print('Exported artifacts/uu-scout.zip — unzip and open index.html.')

if __name__=='__main__':export_demo()
