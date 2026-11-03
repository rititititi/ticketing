"""Export a portable local demo; does not deploy or publish supplier information."""
from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parents[1]

def export_demo():
    html=(ROOT/'templates/explorer.html').read_text()
    css=(ROOT/'static/explorer.css').read_text()
    js=(ROOT/'static/explorer.js').read_text()
    data=(ROOT/'data/catalog.json').read_text().replace('<','\\u003c')
    html=html.replace('<link rel="stylesheet" href="{{ url_for(\'static\',filename=\'explorer.css\') }}">','<style>'+css+'</style>')
    html=html.replace('<script src="{{ url_for(\'static\',filename=\'explorer.js\') }}" defer></script>','')
    html=html.replace('href="/"','href="index.html"')
    js=js.replace("const response=await fetch('/api/catalog');if(!response.ok)throw new Error('Catalog unavailable');catalog=await response.json();", "catalog=JSON.parse(document.getElementById('catalog-data').textContent);")
    js=js.replace('/static/sources/', 'source-images/')
    html=html.replace('</body>', '<script id="catalog-data" type="application/json">'+data+'</script><script>'+js+'</script></body>')
    dest=ROOT/'artifacts';dest.mkdir(exist_ok=True)
    (dest/'index.html').write_text(html)
    with zipfile.ZipFile(dest/'concert-atlas-draft2.zip','w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('concert-atlas/index.html',html)
        z.writestr('concert-atlas/START HERE.txt','Open index.html in your browser. No installation is needed. Keep the source-images folder next to index.html. This is private draft supplier evidence, not confirmed inventory or customer prices.\n')
        for name in ['coverage.csv','coverage.json','ticket-options.csv','provenance.json']:
            z.write(ROOT/'data/draft2'/name,'concert-atlas/reports/'+name)
        z.write(ROOT/'data/draft2/REPORT.md','concert-atlas/reports/REPORT.md')
        for p in sorted((ROOT/'static/sources').glob('*.jpg')):
            z.write(p,'concert-atlas/source-images/'+p.name)
    print('Exported artifacts/concert-atlas-draft2.zip — unzip and open index.html.')

if __name__=='__main__':export_demo()
