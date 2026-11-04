'use strict';
const $ = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const money = n => n == null ? 'No numeric quote' : '¥' + new Intl.NumberFormat('en',{maximumFractionDigits:0}).format(n);
let catalog, selected = '', visible = [], zoom = 1;
const ns = 'http://www.w3.org/2000/svg';
function svg(tag, attrs={}, parent=$('seat-map')) { const el=document.createElementNS(ns,tag); Object.entries(attrs).forEach(([k,v])=>el.setAttribute(k,v));parent.append(el);return el; }
function label(text,x,y,attrs={},parent) { const el=svg('text',{x,y,'text-anchor':'middle','dominant-baseline':'middle',...attrs},parent);el.textContent=text;return el; }
function addSection(name,d,x,y) {
 const g=svg('g',{'class':'section-group','data-section':name});
 const path=svg('path',{d,'class':'seat-section',tabindex:0,role:'button','data-name':name},g);
 svg('title',{},path).textContent=name;
 label(name,x,y,{'class':'section-label'},g);
 path.addEventListener('click',()=>choose(name));
 path.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose(name);}});
}
function ellipse(rx,ry,t) {const a=t*Math.PI/180;return [340+rx*Math.cos(a),345+ry*Math.sin(a)];}
function wedge(name,rx,ry,width,height,a,b) {
 const points=[ellipse(rx,ry,a),ellipse(rx,ry,b),ellipse(rx-width,ry-height,b),ellipse(rx-width,ry-height,a)];
 const d=`M${points[0]} A${rx},${ry} 0 0 1 ${points[1]} L${points[2]} A${rx-width},${ry-height} 0 0 0 ${points[3]}Z`;
 const mid=ellipse(rx-width/2,ry-height/2,(a+b)/2);addSection(name,d,...mid);
}
function buildMap() {
 svg('path',{d:'M263 85 H417 V126 L495 143 L491 159 L416 145 Q410 160 352 166 V239 H522 V258 H367 A29 29 0 0 1 313 258 H158 V239 H328 V166 Q270 160 264 145 L184 159 L180 143 L263 126Z','class':'stage-shape'});
 label('STAGE',340,119,{'class':'stage-label'});
 label('FLOOR',125,185,{'class':'floor-label'});label('FLOOR',549,185,{'class':'floor-label'});
 const floor=[
 ['F1','M150 182 H182 V235 H150Z',166,209],['F2','M187 182 L226 176 V235 H187Z',206,207],['F3','M232 176 H271 V235 H232Z',251,205],['F4','M278 180 L316 193 V225 L301 235 H278Z',293,208],
 ['F5','M364 193 L402 180 V235 H379 L364 225Z',387,208],['F6','M409 176 H448 V235 H409Z',428,205],['F7','M454 176 L493 182 V235 H454Z',474,207],['F8','M499 182 H531 V235 H499Z',515,209],
 ['F9','M180 278 H227 V339Z',211,303],['F10','M233 278 H273 V339 H233Z',253,309],['F11','M279 278 H307 L320 301 V339 H279Z',298,314],['F12','M325 302 H355 V339 H325Z',340,321],['F13','M361 301 L374 278 H402 V339 H361Z',381,314],['F14','M408 278 H448 V339 H408Z',428,309],['F15','M454 278 H501 L454 339Z',470,303],
 ['F16','M234 345 H273 V399 L260 384Z',260,361],['F17','M279 345 H319 V359 H286 V399 H279Z',299,352],['F18','M325 345 H355 V359 H325Z',340,352],['F19','M361 345 H402 V399 H395 V359 H361Z',382,352],['F20','M408 345 H447 L421 384 L408 399Z',422,361]
 ];
 floor.forEach(args=>addSection(...args));
 svg('rect',{x:291,y:365,width:98,height:34,rx:3,'class':'console-shape'});label('CONSOLE',340,382,{'class':'floor-label'});
 // Lower bowl: the source uses T01–T07 and T11–T17, with no T08–T10.
 const terrace=['T01','T02','T03','T04','T05','T06','T07'];
 terrace.forEach((name,i)=>wedge(name,211,232,29,25,43+i*13.4,43+(i+1)*13.4-1.5));
 // T11–T14 sit in the outer lower-bowl strip on the right in the supplied chart.
 ['T11','T12','T13'].forEach((name,i)=>wedge(name,244,261,27,24,43+i*13.4,43+(i+1)*13.4-1.5));
 ['T15','T16','T17'].forEach((name,i)=>wedge(name,244,261,27,24,96.6+i*13.4,96.6+(i+1)*13.4-1.5));
 [['D01',47],['D02',63],['D06',104],['D07',120]].forEach(([name,a])=>wedge(name,178,202,25,20,a,a+12));
 [101,102,103,104,105,106,107].forEach((n,i)=>wedge(String(n),244,194,29,31,-12+i*8.1,-12+(i+1)*8.1-1.2));
 [108,109,110,111,112,113,114].forEach((n,i)=>wedge(String(n),244,194,29,31,135+i*8.1,135+(i+1)*8.1-1.2));
 [201,202,203,204,205].forEach((n,i)=>wedge(String(n),277,239,28,34,5+i*8,5+(i+1)*8-1.1));
 [206,207,208,209,210].forEach((n,i)=>wedge(String(n),277,239,28,34,135+i*8,135+(i+1)*8-1.1));
 Array.from({length:22},(_,i)=>301+i).forEach((n,i)=>wedge(String(n),294,341,23,26,17+i*6.63,17+(i+1)*6.63-0.8));
 Array.from({length:24},(_,i)=>401+i).forEach((n,i)=>wedge(String(n),327,393,28,46,15+i*6.25,15+(i+1)*6.25-0.8));
 const names=[...document.querySelectorAll('.section-group')].map(g=>g.dataset.section);
 catalog.tickets.forEach(t=>{if(t.section&&!names.includes(t.section))names.push(t.section);});
 names.sort((a,b)=>a.localeCompare(b,undefined,{numeric:true})).forEach(name=>{const o=document.createElement('option');o.value=name;o.textContent=name;$('section-select').append(o);});
}
// On-site comparison only. No subscriber data or notifications are collected here.
const comparisonCache = new Map(), comparisonGroups = new Map();
function comparisonKey(t) {return [t.event_id||t.concert,t.performance_date,t.section,t.currency,maskForComparison(t.seat_as_printed)].join("|");}
function indexComparisons() {
 comparisonCache.clear();comparisonGroups.clear();
 catalog.tickets.filter(priceEligible).forEach(t=>{const key=comparisonKey(t);if(!comparisonGroups.has(key))comparisonGroups.set(key,[]);comparisonGroups.get(key).push(t);});
}
function maskForComparison(value) {
 const match=String(value??'').replace(/\s+/g,'').toUpperCase().match(/^([0-9]?X)(?:[（(][^()（）]*[）)]|#|号|番)?$/);
 return match ? match[1] : null;
}
function priceEligible(t) {
 return !t.sold&&!t.superseded_by&&!['paid_in_source','locked_in_source'].includes(t.availability)&&/^\d{4}-\d{2}-\d{2}$/.test(t.performance_date||'')&&/^\d{1,2}$/.test(String(t.row))&&typeof t.price==='number'&&Number.isFinite(t.price)&&t.price>0&&t.section&&t.section!=='UNRESOLVED'&&maskForComparison(t.seat_as_printed);
}
function comparableTickets(a,b) {
 return a.id!==b.id&&priceEligible(a)&&priceEligible(b)&&['performance_date','section','currency'].every(k=>a[k]===b[k])&&(a.event_id||a.concert)===(b.event_id||b.concert)&&maskForComparison(a.seat_as_printed)===maskForComparison(b.seat_as_printed)&&Math.abs(Number(a.row)-Number(b.row))<=3;
}
function priceComparison(t) {
 if(comparisonCache.has(t.id))return comparisonCache.get(t.id);
 const distinct=new Map();
 if(priceEligible(t))(comparisonGroups.get(comparisonKey(t))||[]).filter(peer=>comparableTickets(t,peer)).forEach(peer=>{
  // Repeated identical row/mask/quote observations do not multiply the benchmark.
  if(peer.row===t.row&&peer.price===t.price)return;
  const key=[peer.row,maskForComparison(peer.seat_as_printed),peer.price].join('|');if(!distinct.has(key))distinct.set(key,peer);
 });
 const peers=[...distinct.values()].sort((a,b)=>a.price-b.price),prices=peers.map(x=>x.price),mid=Math.floor(prices.length/2);
 const median=prices.length?(prices.length%2?prices[mid]:(prices[mid-1]+prices[mid])/2):null;
 const value={peers,median,below:prices.length>=2&&t.price<median,percent:median?Math.round((1-t.price/median)*100):0};comparisonCache.set(t.id,value);return value;
}
function comparisonDetails(t) {
 const c=priceComparison(t),cheaper=c.peers.filter(p=>p.price<t.price).slice(0,5);
 let result='<p>No eligible comparable quotes. A resolved date, numeric row and clear seat mask are required.</p>';
 if(c.median!==null) {
  result=`<p><strong>${money(c.median)}</strong> <span>comparable median</span> · ${c.peers.length} <span>distinct quotes</span>`;
  if(c.below)result+=` · <strong>${c.percent}% <span>below median</span></strong>`;
  result+='</p>';
  result+=cheaper.length?'<p>Lower comparable quotes:</p>'+cheaper.map(p=>`<button class="quiet compare-ticket" data-compare="${esc(p.id)}">${money(p.price)} · <span>Row ${esc(p.row)}</span> · <span>Source ${p.source_index}</span></button>`).join(''):'<p>No cheaper comparable quote in the current catalog.</p>';
 }
 return `<section class="price-comparison"><h3>Compare similar tickets</h3><p>Same performance, section and seat prefix; numeric rows within ±3. Repeated identical quotes count once. OCR quotes and grouped prices need confirmation.</p>${result}<p class="detail-warning">This is a comparison across offers, not a confirmed price drop for the same ticket. Automatic notifications are not enabled.</p></section>`;
}
function baseTickets() {
 const date=$('date').value, sold=$('include-sold').checked, review=$('review-filter').value;
 return catalog.tickets.filter(t=>(date==='all'||t.date_key===date)&&(sold||!t.sold)&&($('include-history').checked||!t.superseded_by)&&(review==='all'||(review==='checked'?['visually_transcribed_draft1','admin_reviewed'].includes(t.extraction_status):!['visually_transcribed_draft1','admin_reviewed'].includes(t.extraction_status))));
}
function range(items) {const prices=items.filter(t=>!t.sold&&t.price!=null).map(t=>t.price);return prices.length?`${money(Math.min(...prices))}${Math.min(...prices)!==Math.max(...prices)?' – '+money(Math.max(...prices)):''}`:'No active quoted options';}
function choose(section) {selected=section;$('section-select').value=section;render();}
function render() {
 const base=baseTickets().filter(t=>!$('below-median').checked||priceComparison(t).below), term=$('search').value.trim().toLowerCase();
 visible=base.filter(t=>(!selected||t.section===selected)&&(!term||[t.section,t.row,t.seat_as_printed,t.seating_notes,t.source_file,t.date_as_printed,t.raw_ocr,t.legacy_ocr,t.review_flags].join(' ').toLowerCase().includes(term)));
 const sort=$('sort').value;
 visible.sort((a,b)=>sort==='row'?String(a.row).localeCompare(String(b.row),undefined,{numeric:true}):sort==='price-desc'?(b.price??-Infinity)-(a.price??-Infinity):(a.price??Infinity)-(b.price??Infinity));
 $('tickets-title').textContent=selected?`Section ${selected}`:'All sections';
 $('section-summary').textContent=`${visible.length} source records · ${range(visible)}`;
 document.querySelectorAll('.section-group').forEach(g=>{
  const name=g.dataset.section, items=base.filter(t=>t.section===name),active=items.some(t=>!t.sold);
  g.classList.toggle('has-options',active);g.classList.toggle('is-selected',selected===name);
  const title=`Section ${name}. ${items.length} matching source records. ${range(items)}. Select to browse.`;
  g.querySelector('path').setAttribute('aria-label',title);g.querySelector('path').setAttribute('aria-pressed',String(selected===name));g.querySelector('title').textContent=title;
 });
 $('tickets').innerHTML=visible.length?visible.map(t=>`<button class="ticket-card ${t.sold?'sold':''}" data-ticket="${esc(t.id)}"><span class="card-top"><span class="section-badge">${esc(t.section)}</span><span class="status ${t.sold?'status-sold':''}">${t.sold?'Sold in source':t.superseded_by?'Older screenshot version':t.extraction_status==='admin_reviewed'?'Admin reviewed':t.extraction_status==='visually_transcribed_draft1'?'Visually transcribed':'OCR · review required'}</span></span><span class="card-title">Row ${esc(t.row||'needs review')} <span>·</span> Seat ${esc(t.seat_as_printed||'not captured')}</span><span class="card-note">${esc(t.seating_notes||t.delivery||'Individual ticket record')}</span><span class="card-bottom"><span><strong>${t.sold?'Sold':money(t.price)}</strong><small>${t.sold?'Historical source record':'RMB · source quote; grouping needs review'}</small></span><span class="card-arrow">↗</span></span><span class="source-ref">Source ${t.source_index} / row ${esc(t.source_row)} · ${esc(t.date_as_printed)}</span></button>`).join(''):`<div class="empty-state"><span>✳</span><h3>No matching records here.</h3><p>Try another section or date, clear your search, or include sold-out records.</p><button id="empty-clear" class="quiet">Clear section and search ↗</button></div>`;
 document.querySelectorAll('[data-ticket]').forEach(b=>b.addEventListener('click',()=>detail(b.dataset.ticket)));
 if($('empty-clear'))$('empty-clear').onclick=()=>{$('search').value='';choose('');};
}
function dateLabel(t) {return t.performance_date||`${t.date_as_printed} · year/date unresolved`;}
function detail(id) {
 const t=catalog.tickets.find(t=>t.id===id);if(!t)return;
 const source=catalog.sources.find(s=>s.source_index===t.source_index);
 const siblings=catalog.tickets.filter(x=>x.id!==t.id&&x.section===t.section&&x.row===t.row&&x.seat_as_printed&&t.seat_as_printed&&x.seat_as_printed.toLowerCase()===t.seat_as_printed.toLowerCase());
 const fields=[['Extraction',t.extraction_status==='admin_reviewed'?'Admin reviewed':t.extraction_status==='visually_transcribed_draft1'?'Visually transcribed in draft 1':'OCR candidate · fields need checking'],['Row / seat / stock review',t.catalog_review?'Manually reviewed · '+t.catalog_review.availability:'Not manually reviewed'],['Admin review note',t.catalog_review?.note||'None stated'],['Physical row',t.physical_row],['Performance',dateLabel(t)],['Section / row',`${t.section} / ${t.row}`],['Masked seat',t.seat_as_printed],['Quantity',t.quantity_basis],['Seating notes',t.seating_notes||'None stated'],['Delivery',t.delivery||'Not stated'],['Supplier', 'Unknown · not identified by screenshot'],['Source',`${t.source_file} · row ${t.source_row}`],['Verification',t.verification]];
 $('detail-content').innerHTML=`<h2>${esc(t.section)} <span>/ Row ${esc(t.row)}</span></h2><p class="detail-price">${t.sold?'Sold in this source':money(t.price)} <small>${t.sold?'':'RMB · supplier quote'}</small></p><p class="detail-warning">${esc(t.review_flags)}</p><dl>${fields.map(([k,v])=>`<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join('')}</dl>${siblings.length?`<div class="overlap-note">${siblings.length} other source record(s) share these masked section / row / seat attributes. They may be separate tickets or versions and have not been merged.</div>`:''}${comparisonDetails(t)}${rowEvidence(t)}<h3>Row text · OCR may be wrong</h3><pre>${esc(t.raw_ocr||t.legacy_ocr||'No readable OCR; inspect original row')}</pre><button class="primary" id="view-original">View original screenshot ↗</button><p class="detail-footer">Customer selling price not set. Confirm availability with the supplier before requesting payment.</p>`;
 document.querySelectorAll('[data-compare]').forEach(b=>b.onclick=()=>detail(b.dataset.compare));$('view-original').onclick=()=>showSource(source.source_index,t.physical_row);if(!$('ticket-dialog').open)$('ticket-dialog').showModal();
}
function rowEvidence(t) {
 if(!t.source_bbox)return '';
 const source=catalog.sources.find(s=>s.source_index===t.source_index), [x,y,w,bottom]=t.source_bbox;
 return `<figure class="row-evidence"><figcaption>Source ${t.source_index} · physical row ${t.physical_row} · original pixels</figcaption><svg viewBox="0 ${y} ${w} ${bottom-y}" role="img" aria-label="Original screenshot row"><image width="${source.width}" height="${source.height}" href="/static/sources/${encodeURIComponent(t.source_file)}"/></svg></figure>`;
}
function showSource(index, physicalRow) {
 const s=catalog.sources.find(s=>s.source_index===index),lines=catalog.ocr.filter(l=>l.source_index===index), rows=catalog.tickets.filter(t=>t.source_index===index), focus=rows.find(t=>t.physical_row===physicalRow);
 $('source-content').innerHTML=`<h2>Source ${index} <span>/ ${esc(s.visual_family)}</span></h2><p>${esc(s.family_description)}</p><p>${s.physical_option_rows} identified option rows · ${s.visually_transcribed_rows} visually transcribed · ${s.ocr_candidate_rows} OCR candidates · ${s.unreadable_rows} unreadable rows</p>${focus?rowEvidence(focus):''}<p class="detail-warning">Seller and update order unknown. OCR text is unverified and may split or merge rows.</p><a href="/static/sources/${encodeURIComponent(s.source_file)}" target="_blank" rel="noopener">Open full-resolution image ↗</a><img class="source-original" src="/static/sources/${encodeURIComponent(s.source_file)}" alt="Original supplier sheet ${index}"><h3>Every option row in this screenshot</h3><div class="source-rows">${rows.map(t=>`<button class="quiet" data-row-id="${esc(t.id)}">Row ${t.physical_row}: ${esc(t.section)} / ${esc(t.row||'?')} / ${money(t.price)} · ${esc(t.extraction_status)}<br><small>${esc(t.raw_ocr||t.legacy_ocr||'Unreadable — original row retained')}</small></button>`).join('')}</div><h3>Draft 1 OCR · needs review</h3><pre>${esc(lines.map(l=>l.ocr_text).join('\n'))}</pre>`;
 document.querySelectorAll('[data-row-id]').forEach(b=>b.onclick=()=>{$('source-dialog').close();$('ticket-dialog').close();detail(b.dataset.rowId);});$('source-dialog').showModal();
}
function renderSources() {
 const term=$('source-search').value.trim().toLowerCase();
 const sources=catalog.sources.filter(s=>!term||`${s.source_file} ${s.family_description} ${s.visual_family} ${catalog.ocr.filter(l=>l.source_index===s.source_index).map(l=>l.ocr_text).join(' ')}`.toLowerCase().includes(term));
 $('library-count').textContent=`${sources.length} of ${catalog.sources.length} screenshots · visual families are provisional, not seller identities`;
 $('source-grid').innerHTML=sources.map(s=>`<button class="source-card" data-source="${s.source_index}"><div class="source-image"><img loading="lazy" src="/static/sources/${encodeURIComponent(s.source_file)}" alt="Supplier screenshot ${s.source_index}"></div><div><span class="eyebrow">SOURCE ${s.source_index} · ${esc(s.visual_family)}</span><h3>${esc(s.family_description)}</h3><p>${s.extracted_rows} / ${s.physical_option_rows} identified rows represented<br>${s.visually_transcribed_rows} visually transcribed · ${s.ocr_candidate_rows} OCR candidates · ${s.unreadable_rows} unreadable</p><small>${esc(s.source_file)}</small></div></button>`).join('');
 document.querySelectorAll('[data-source]').forEach(b=>b.onclick=()=>showSource(Number(b.dataset.source)));
}
function exportCSV() {
 const fields=['id','physical_row','extraction_status','verification','quantity_basis','raw_ocr','legacy_ocr','source_bbox','source_index','source_file','source_row','date_as_printed','performance_date','section','row','seat_as_printed','quantity','supplier_quote_cny','currency','customer_price_cny','availability','seating_notes','review_flags'];
 const cell=value=>{let s=String(value??'');if(/^[=+\-@]/.test(s))s="'"+s;return '"'+s.replace(/"/g,'""')+'"';};
 const text='\uFEFF'+[fields,...visible.map(t=>fields.map(k=>t[k]))].map(r=>r.map(cell).join(',')).join('\r\n');
 const url=URL.createObjectURL(new Blob([text],{type:'text/csv;charset=utf-8;'}));const a=document.createElement('a');a.href=url;a.download='uu-scout-ticket-options.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function setZoom(n){zoom=Math.max(1,Math.min(2,n));$('seat-map').style.width=`${zoom*100}%`;$('seat-map').style.maxWidth=zoom===1?'680px':'none';}

let updatesFeed={events:[]},updatesLimit=12;
const readUpdateIds=new Set();
try{const saved=JSON.parse(localStorage.getItem('uu-scout-read-updates')||'[]');if(Array.isArray(saved))saved.filter(id=>typeof id==='string'&&/^[a-f0-9]{24}$/.test(id)).forEach(id=>readUpdateIds.add(id));}catch(_){}
function saveReadUpdates(){try{localStorage.setItem('uu-scout-read-updates',JSON.stringify([...readUpdateIds].slice(-3000)));}catch(_){} }
function updateDate(value){if(!value)return '';if(value.length===10)return value;try{return new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Hong_Kong',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(value));}catch(_){return '';}}
function renderUpdates(){
 const events=updatesFeed.events||[],unread=events.filter(e=>!readUpdateIds.has(e.id)).length;
 $('update-count').textContent=unread;$('updates-read-all').disabled=!events.length;$('updates-summary').textContent=`${events.length} updates · ${unread} unread`;
 const type=$('updates-type').value,filtered=events.filter(e=>(type==='all'||e.kind===type)&&(!$('updates-unread').checked||!readUpdateIds.has(e.id)));
 $('updates-list').innerHTML=filtered.slice(0,updatesLimit).map(e=>`<article class="update-card ${readUpdateIds.has(e.id)?'update-read':'update-unread'}"><div class="card-top"><span class="status">${e.kind==='listing_drop'?'Price drop in updated listing':'Lower comparable offer'}</span><small>${esc(updateDate(e.published_at))}</small></div><h3>${esc(e.section)} · <span>Row ${esc(e.row)}</span> · ${esc(e.seat_mask)}</h3><p>${esc(e.performance_date)}</p><p class="update-price">${e.kind==='listing_drop'?`<s>${money(e.previous_price)}</s> → <strong>${money(e.price)}</strong>`:`<strong>${money(e.price)}</strong> <span>vs comparable median</span> ${money(e.median)}`} · ${e.percent}% <span>lower</span></p><p>${e.provisional?'OCR quote · check original before relying on this alert':'Supplier quote · confirm availability'}</p><p class="source-ref">Source ${e.source_index} / row physical-${e.physical_row}</p><button class="quiet" data-update-open="${esc(e.id)}">View ticket and evidence ↗</button>${e.kind==='listing_drop'?`<button class="quiet" data-update-before="${esc(e.id)}">View previous quote ↗</button>`:''}<button class="quiet" data-update-read="${esc(e.id)}">${readUpdateIds.has(e.id)?'Mark unread':'Mark read'}</button></article>`).join('')||'<p>No matching updates. New publications may add more alerts.</p>';
 $('updates-more').hidden=filtered.length<=updatesLimit;
 document.querySelectorAll('[data-update-open],[data-update-before]').forEach(b=>b.onclick=()=>{const id=b.dataset.updateOpen||b.dataset.updateBefore,e=events.find(e=>e.id===id);if(!e)return;readUpdateIds.add(id);saveReadUpdates();renderUpdates();detail(b.dataset.updateBefore?e.previous_ticket_id:e.ticket_id);});
 document.querySelectorAll('[data-update-read]').forEach(b=>b.onclick=()=>{const id=b.dataset.updateRead;if(readUpdateIds.has(id))readUpdateIds.delete(id);else readUpdateIds.add(id);saveReadUpdates();renderUpdates();});
}
async function loadUpdates(){
 try{const feedResponse=await fetch('/api/updates');if(!feedResponse.ok)throw new Error('Updates unavailable');updatesFeed=await feedResponse.json();renderUpdates();}
 catch(_){$('updates-summary').textContent='Updates are temporarily unavailable. Please refresh the page.';}
}
async function init() {
 try {const response=await fetch('/api/catalog');if(!response.ok)throw new Error('Catalog unavailable');catalog=await response.json();indexComparisons();buildMap();render();loadUpdates();renderSources();$('source-count').textContent=catalog.sources.length;
 const stats=catalog.extraction_summary;
 $('draft-summary').textContent=`Draft 2: ${stats.total_option_rows.toLocaleString()} identified option rows across all ${stats.total_source_images} screenshots. ${stats.visually_transcribed_rows} visually transcribed in draft 1; ${stats.ocr_candidate_rows.toLocaleString()} OCR candidates and ${stats.unreadable_rows} unreadable rows need review. Row coverage does not establish field accuracy. Dates, versions and grouped offers remain separate.`;
 $('admin-review-summary').textContent=stats.admin_reviewed_rows?`${stats.admin_reviewed_rows} admin-reviewed uploaded rows.`:'';
 $('coverage-body').innerHTML=catalog.coverage.map(c=>`<tr><td>${c.source_index}</td><td>${esc(c.source_file)}</td><td>${c.physical_option_rows}</td><td>${c.extracted_rows}</td><td>${c.visually_transcribed_rows}</td><td>${c.admin_reviewed_rows||0}</td><td>${c.ocr_candidate_rows}</td><td>${c.unreadable_rows}</td></tr>`).join('');
 $('download-coverage').onclick=()=>{const keys=['source_index','source_file','physical_option_rows','extracted_rows','visually_transcribed_rows','admin_reviewed_rows','ocr_candidate_rows','unreadable_rows','unresolved_section_rows','unresolved_row_rows','unresolved_seat_rows','unresolved_date_rows','unresolved_quote_rows','coverage_status'];const csv=[keys,...catalog.coverage.map(c=>keys.map(k=>c[k]))].map(row=>row.map(v=>'"'+String(v??'').replace(/"/g,'""')+'"').join(',')).join('\r\n');const url=URL.createObjectURL(new Blob(['\uFEFF'+csv],{type:'text/csv;charset=utf-8;'}));const a=document.createElement('a');a.href=url;a.download='uu-scout-coverage.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
 ['date','include-sold','include-history','below-median','sort','review-filter'].forEach(id=>$(id).addEventListener('change',render));$('search').addEventListener('input',render);$('section-select').onchange=e=>choose(e.target.value);$('clear-section').onclick=()=>choose('');$('source-search').addEventListener('input',renderSources);$('download').onclick=exportCSV;

 $('updates-read-all').onclick=()=>{updatesFeed.events.forEach(e=>readUpdateIds.add(e.id));saveReadUpdates();renderUpdates();};
 ['updates-type','updates-unread'].forEach(id=>$(id).onchange=()=>{updatesLimit=12;renderUpdates();});$('updates-more').onclick=()=>{updatesLimit+=12;renderUpdates();};
 $('zoom-in').onclick=()=>setZoom(zoom+.25);$('zoom-out').onclick=()=>setZoom(zoom-.25);$('zoom-reset').onclick=()=>setZoom(1);
 }catch(error){$('tickets').textContent='Could not load the supplier collection. Please restart the app and try again.';console.error(error);}
}
document.querySelectorAll('dialog').forEach(d=>{d.querySelector('.close').onclick=()=>d.close();d.addEventListener('click',e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close();}});});
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>{for(const view of ['sources','explorer','updates'])$(view+'-view').hidden=b.dataset.view!==view;document.querySelectorAll('[data-view]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',String(x===b));});});
init();
