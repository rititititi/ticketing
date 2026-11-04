'use strict';
const $=id=>document.getElementById(id);let csrf='',jobId='',rawRows=[],timer;
const message=text=>$('message').textContent=text;
async function api(path,options={}){const response=await fetch('/api/'+path,{...options,headers:{...(csrf?{'X-CSRF-Token':csrf}:{}),...options.headers}});const data=await response.json();if(!response.ok)throw new Error(data.error||'Request failed');return data;}
function busy(form,state){form.querySelectorAll('button').forEach(b=>b.disabled=state);}
async function signIn(){const data=await api('session');csrf=data.csrf;$('login').hidden=true;$('workspace').hidden=false;$('logout').hidden=false;const sources=await api('sources');$('base-source').replaceChildren(new Option('New independent sheet / 新的独立表格',''),...sources.map(s=>new Option(`${s.index}: ${s.name}`,s.index)));}
$('login-form').onsubmit=async event=>{event.preventDefault();busy(event.target,true);try{await api('login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password:$('password').value})});$('password').value='';await signIn();message('Signed in / 已登录');}catch(e){message(e.message);}finally{busy(event.target,false);}};
$('logout').onclick=async()=>{try{await api('logout',{method:'POST'});location.reload();}catch(e){message(e.message);}};
function addRow(row={}){const tr=document.createElement('tr');tr.dataset.raw=row.raw_ocr||'';for(const key of ['section','row','seat_as_printed','price','sold','performance_date','notes']){const td=document.createElement('td');const input=document.createElement(key==='notes'?'textarea':'input');input.dataset.key=key;if(key==='sold'){input.type='checkbox';input.checked=!!row.sold;}else{if(key!=='notes')input.type=key==='price'?'number':key==='performance_date'?'date':'text';input.value=row[key]??'';if(key==='price'){input.min='0';input.max='1000000';input.step='0.01';}if(key==='section')input.maxLength=20;else if(key==='notes')input.maxLength=500;else input.maxLength=80;}td.append(input);tr.append(td);}const td=document.createElement('td'),remove=document.createElement('button');remove.textContent='×';remove.type='button';remove.onclick=()=>tr.remove();td.append(remove);tr.append(td);$('rows').append(tr);}
$('add-row').onclick=()=>addRow();
function edit(data){$('review').hidden=false;$('rows').replaceChildren();rawRows=data.rows;rawRows.forEach(addRow);$('confirmed').checked=false;$('original').src=`/api/jobs/${jobId}/image`;$('original-link').href=$('original').src;message(data.error||'OCR complete. Check every row before publishing. / 识别完成，请逐行核对后发布。');}
async function poll(){clearTimeout(timer);try{const data=await api(`jobs/${jobId}`);$('retry').hidden=false;if(data.status==='review'){edit(data);return;}if(data.status==='published'){message('Published to the repository. GitHub Pages deployment is starting. / 已写入仓库，网站正在重新部署。');$('review').hidden=true;$('retry').hidden=true;return;}if(data.status==='failed'){message(data.error||'OCR failed. Retry the job or upload a clearer image. / 识别失败，请重试或换用更清晰的图片。');return;}message('Processing in GitHub Actions; this can take a few minutes. Keep the job ID to resume later. / 正在 GitHub Actions 中处理，可能需要几分钟，请保留任务编号。');timer=setTimeout(poll,10000);}catch(e){message(e.message);}}
function openJob(id){if(!/^[a-f0-9]{32}$/.test(id)){message('Invalid job ID / 任务编号格式错误');return;}jobId=id;$('job-ref').textContent=`Job ID / 任务编号: ${id}`;try{sessionStorage.setItem('uu-scout-job',id);}catch(_){}$('review').hidden=true;poll();}
$('resume-form').onsubmit=event=>{event.preventDefault();openJob($('resume-id').value.trim());};
$('upload-form').onsubmit=async event=>{event.preventDefault();busy(event.target,true);try{const form=new FormData();form.set('image',$('image').files[0]);form.set('base_source',$('base-source').value);const data=await api('upload',{method:'POST',body:form});openJob(data.id);}catch(e){message(e.message);}finally{busy(event.target,false);}};
$('retry').onclick=async()=>{try{await api(`jobs/${jobId}/retry`,{method:'POST'});poll();}catch(e){message(e.message);}};
$('publish').onclick=async()=>{if(!$('confirmed').checked){message('First confirm that every row matches the original. / 请先确认已核对全部原始行。');return;}$('publish').disabled=true;try{const rows=[...$('rows').children].map(tr=>{const row={raw_ocr:tr.dataset.raw};for(const input of tr.querySelectorAll('[data-key]'))row[input.dataset.key]=input.dataset.key==='sold'?input.checked:input.dataset.key==='price'?(input.value===''?null:Number(input.value)):input.value;return row;});await api(`jobs/${jobId}/publish`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({rows,reviewed_all_rows:true})});$('review').hidden=true;poll();}catch(e){message(e.message);}finally{$('publish').disabled=false;}};
signIn().then(()=>{try{const id=sessionStorage.getItem('uu-scout-job');if(id)openJob(id);const reviewId=sessionStorage.getItem('uu-scout-review-job');if(/^[a-f0-9]{32}$/.test(reviewId||'')){queueJob=reviewId;queuePublishing=true;$('upload-workspace').hidden=true;$('catalog-review').hidden=false;$('queue-retry').hidden=false;$('queue-job').textContent='Review job / 核对任务: '+queueJob;pollReviewJob();}}catch(_){}}).catch(e=>{if(!e.message.includes('sign in'))message(e.message);});

// Existing-catalog review uses the same password session and CSRF token as uploads.
let queueData=null,queueSource=0,queuePage=0,queueJob='',queueTimer,queuePublishing=false,queueFilter='pending';
const availabilityLabels={unknown:'Unknown / 未知',available:'Available / 确认有票',sold:'Sold out / 已售出',paid:'Paid / 已付款',locked:'Locked / 已锁定'};
const reasonLabels={row_missing:'Row missing / 排号缺失',row_needs_confirmation:'Confirm printed row / 排号待核实',seat_missing:'Seat missing / 座位缺失',seat_needs_confirmation:'Confirm seat / 座位待核实',availability_unknown:'Availability unknown / 有票状态未知'};
$('show-upload').onclick=()=>{$('catalog-review').hidden=true;$('upload-workspace').hidden=false;};
$('show-catalog-review').onclick=async()=>{$('upload-workspace').hidden=true;$('catalog-review').hidden=false;try{if(!queueData)await loadReviewQueue();}catch(e){message(e.message);}};
async function loadReviewQueue(){
 const index=await api('review/queue');$('queue-summary').textContent=`${index.total_pending} current records need field or availability confirmation / 条当前记录需核实字段或状态`;
 const previous=queueSource;$('queue-source').replaceChildren(...index.sources.map(s=>new Option(`${s.source_index}: ${s.pending_rows}/${s.total_rows} pending / 待核实 · ${s.source_file}`,s.source_index)));
 queueSource=index.sources.some(s=>s.source_index===previous)?previous:(index.sources.find(s=>s.pending_rows)?.source_index||index.sources[0]?.source_index||0);$('queue-source').value=String(queueSource);queuePage=0;
 if(queueSource)await loadReviewPage();else{$('queue-rows').replaceChildren();$('queue-page').textContent='No current records / 暂无记录';}
}
async function loadReviewPage(){queueData=await api(`review/sources/${queueSource}?page=${queuePage}`);renderReviewRows();}
function selectedReviewRows(){return [...$('queue-rows').children].filter(tr=>tr.querySelector('[data-select]')?.checked);}
function renderReviewRows(){
 $('queue-rows').replaceChildren();$('queue-select-all').checked=false;$('queue-confirmed').checked=false;
 $('queue-page').textContent=`Page / 页 ${queuePage+1} / ${queueData.source.pages} · ${queueData.source.total_rows} records / 条记录`;
 $('queue-prev').disabled=queuePage===0||queuePublishing;$('queue-next').disabled=queuePage+1>=queueData.source.pages||queuePublishing;
 const records=queueData.rows.filter(r=>queueFilter==='all'||(queueFilter==='fields'?r.reasons.some(reason=>reason.startsWith('row_')||reason.startsWith('seat_')):queueFilter==='stock'?r.reasons.includes('availability_unknown'):r.reasons.length));
 for(const record of records){
  const tr=document.createElement('tr');tr.dataset.id=record.id;tr.dataset.revision=record.revision;
  let td=document.createElement('td'),selected=document.createElement('input');selected.type='checkbox';selected.dataset.select='1';selected.onchange=()=>{$('queue-confirmed').checked=false;};selected.setAttribute('aria-label',`Approve record ${record.physical_row} / 批准第 ${record.physical_row} 行`);td.append(selected);tr.append(td);
  td=document.createElement('td');const title=document.createElement('strong');title.textContent=`${record.section} · #${record.physical_row}`;const reasons=document.createElement('p');reasons.className='queue-reasons';reasons.textContent=record.reasons.map(r=>reasonLabels[r]||r).join('\n')||'Reviewed / 已核对';td.append(title,reasons);tr.append(td);
  for(const key of ['row','seat_as_printed','availability','note']){
   td=document.createElement('td');const input=document.createElement(key==='availability'?'select':key==='note'?'textarea':'input');input.dataset.field=key;
   if(key==='availability')input.replaceChildren(...Object.entries(availabilityLabels).map(([value,label])=>new Option(label,value)));
   else input.maxLength=key==='note'?500:80;
   input.setAttribute('aria-label',`${key} · ${record.physical_row}`);input.value=key==='note'?(record.catalog_review?.note||''):record[key]??'';input.addEventListener('input',()=>{selected.checked=true;$('queue-confirmed').checked=false;});td.append(input);tr.append(td);
  }
  td=document.createElement('td');const evidence=document.createElement('button');evidence.textContent='View row / 查看原行';evidence.onclick=()=>showReviewEvidence(record);td.append(evidence);tr.append(td);$('queue-rows').append(tr);
 }
 if(!records.length){const tr=document.createElement('tr'),td=document.createElement('td');td.colSpan=7;td.textContent='No pending rows on this page. Choose All records or the next page. / 本页暂无待核实记录，可选择全部记录或下一页。';tr.append(td);$('queue-rows').append(tr);}
 $('queue-save').disabled=queuePublishing;
}
function showReviewEvidence(record){
 const area=$('queue-evidence');area.replaceChildren();const heading=document.createElement('p');heading.textContent=`Source / 来源 ${queueSource} · row / 原行 ${record.physical_row} · ${record.section}`;area.append(heading);
 const href=`/api/review/sources/${queueSource}/image`,box=record.source_bbox;
 if(Array.isArray(box)&&box.length===4&&box.every(Number.isFinite)&&box[3]>box[1]){
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox',`0 ${box[1]} ${queueData.source.width} ${box[3]-box[1]}`);svg.setAttribute('role','img');svg.setAttribute('aria-label','Original screenshot row / 原图行');const image=document.createElementNS(svg.namespaceURI,'image');image.setAttribute('width',queueData.source.width);image.setAttribute('height',queueData.source.height);image.setAttribute('href',href);svg.append(image);area.append(svg);
 }else{const image=document.createElement('img');image.src=href;image.alt='Original screenshot / 原始截图';area.append(image);}
 const link=document.createElement('a');link.href=href;link.target='_blank';link.rel='noopener';link.textContent='Open full screenshot / 打开完整原图';const raw=document.createElement('pre');raw.className='queue-raw';raw.textContent=record.raw_ocr;area.append(link,raw);
}
function canNavigateReview(){if(selectedReviewRows().length){message('Approve or unselect the selected records before changing pages / 请先批准或取消选中记录，再切换页面');return false;}return !queuePublishing;}
$('queue-source').onchange=async()=>{if(!canNavigateReview()){$('queue-source').value=String(queueSource);return;}queueSource=Number($('queue-source').value);queuePage=0;try{await loadReviewPage();}catch(e){message(e.message);}};
$('queue-filter').onchange=()=>{if(canNavigateReview()){queueFilter=$('queue-filter').value;renderReviewRows();}else $('queue-filter').value=queueFilter;};
$('queue-select-all').onchange=()=>{document.querySelectorAll('#queue-rows [data-select]').forEach(c=>c.checked=$('queue-select-all').checked);$('queue-confirmed').checked=false;};
for(const [id,step] of [['queue-prev',-1],['queue-next',1]])$(id).onclick=async()=>{if(!canNavigateReview())return;queuePage+=step;try{await loadReviewPage();}catch(e){queuePage-=step;message(e.message);}};
$('queue-refresh').onclick=async()=>{if(queuePublishing){message('Wait for publication to finish / 请等待发布完成');return;}try{await loadReviewQueue();}catch(e){message(e.message);}};
$('queue-save').onclick=async()=>{
 if(!$('queue-confirmed').checked){message('Confirm the selected rows against the original screenshot first / 请先确认已核对选中原始行');return;}
 const changes=selectedReviewRows().map(tr=>{const row={id:tr.dataset.id,revision:tr.dataset.revision};tr.querySelectorAll('[data-field]').forEach(input=>row[input.dataset.field]=input.value);return row;});
 if(!changes.length){message('Select records to approve / 请选择要批准的记录');return;}
 $('queue-save').disabled=true;
 try{const data=await api('review/approve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source_index:queueSource,changes,confirmed:true})});queueJob=data.id;try{sessionStorage.setItem('uu-scout-review-job',queueJob);}catch(_){}queuePublishing=true;$('queue-job').textContent=`Review job / 核对任务: ${queueJob}`;$('queue-retry').hidden=false;if(data.status==='dispatch_failed'){message(data.error);queuePublishing=false;$('queue-save').disabled=false;return;}pollReviewJob();}
 catch(e){message(e.message);$('queue-save').disabled=false;}
};
async function pollReviewJob(){clearTimeout(queueTimer);try{
 const data=await api(`review/jobs/${queueJob}`);
 if(data.status==='published'){queuePublishing=false;try{sessionStorage.removeItem('uu-scout-review-job');}catch(_){}$('queue-retry').hidden=true;message('Corrections saved. Website updates are deploying / 核对结果已保存，网站正在更新');await loadReviewQueue();return;}
 if(data.status==='failed'){queuePublishing=false;$('queue-save').disabled=false;message(data.error+' / 请重新加载核对列表后重试');return;}
 message('Publishing selected corrections in GitHub Actions / 正在 GitHub Actions 中发布选中的核对结果');queueTimer=setTimeout(pollReviewJob,10000);
 }catch(e){queuePublishing=false;message(e.message);$('queue-save').disabled=false;}}
$('queue-retry').onclick=async()=>{try{await api(`review/jobs/${queueJob}/retry`,{method:'POST'});queuePublishing=true;pollReviewJob();}catch(e){message(e.message);}};
