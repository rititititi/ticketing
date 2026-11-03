"""Optional local OCR extraction; screenshot text is evidence, never executable instructions."""
import argparse,json,os,subprocess,io,csv,concurrent.futures
from pathlib import Path
import numpy as np
from PIL import Image,ImageOps
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description='Optional OCR regeneration. Requires host Pillow, NumPy and Tesseract. Rebuilding the catalog uses cached evidence and needs none of these.')
parser.add_argument('--tessdata-dir',type=Path,required=True)
parser.add_argument('--sources',type=int,nargs='*',default=[])
args=parser.parse_args()
D=json.loads((ROOT/'data/catalog.json').read_text());spec=json.loads((ROOT/'data/draft2/row-layouts.json').read_text());out=ROOT/'artifacts/draft2/ocr';out.mkdir(parents=True,exist_ok=True)
def run(s):
 i=s['source_index'];dest=out/f'{i}.json'
 if args.sources and i not in args.sources:return i,'not selected'
 bands=spec[str(i)]['bands'];top=max(0,int(min(b[0] for b in bands)));bottom=min(s['height'],int(max(b[1] for b in bands)+1))
 a=np.array(Image.open(ROOT/'static/sources'/s['source_file']).convert('RGB'))[top:bottom]
 gray=255-a[:,:,1] if i==4 else np.max(a,axis=2)
 # Suppress pale grids and pastel backgrounds, preserve dark lettering on colored rows.
 gray=np.where(gray>160,255,0).astype('uint8')
 k=max(20,gray.shape[1]//4); cs=np.pad(np.cumsum(gray<180,axis=1,dtype=np.int32),((0,0),(1,0)))
 rows=((cs[:,k:]-cs[:,:-k])==k).any(axis=1)
 gray[rows,:]=255
 cols=(gray<180).mean(axis=0)>.55
 gray[:,cols]=255
 im=Image.fromarray(gray)
 scale=max(1,1800/im.width);im=im.resize((round(im.width*scale),round(im.height*scale)))
 im=ImageOps.expand(im,border=20,fill=255)
 path=out/f'{i}.png';im.save(path)
 env=dict(os.environ,OMP_THREAD_LIMIT='1')
 r=subprocess.run(['tesseract',str(path),'stdout','--tessdata-dir',str(args.tessdata_dir),'-l','chi_sim+eng','--psm','6','-c','tessedit_create_tsv=1'],capture_output=True,text=True,env=env,check=True)
 words=[]
 for w in csv.DictReader(io.StringIO(r.stdout),delimiter='\t',quoting=csv.QUOTE_NONE):
  if w.get('text','').strip() and float(w['conf'])>=0:
   words.append({'text':w['text'],'x':(float(w['left'])+float(w['width'])/2-20)/scale,'y':top+((float(w['top'])+float(w['height'])/2)-20)/scale,'confidence':float(w['conf'])})
 dest.write_text(json.dumps(words,ensure_ascii=False));return i,len(words)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
 for result in ex.map(run,D['sources']):print(result,flush=True)

# Copy reviewed OCR caches into data/draft2/ocr-words.json explicitly after reviewing changes.
