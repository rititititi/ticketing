const encoder=new TextEncoder();
const JOB=/^[a-f0-9]{32}$/;
const MAX_IMAGE=3*1024*1024;
const loginAttempts=new Map();
const json=(value,status=200,headers={})=>new Response(JSON.stringify(value),{status,headers:{'Content-Type':'application/json','Cache-Control':'no-store','X-Content-Type-Options':'nosniff',...headers}});
const base64=bytes=>{let text='';for(let i=0;i<bytes.length;i+=16384)text+=String.fromCharCode(...bytes.subarray(i,i+16384));return btoa(text);};
const decode=s=>Uint8Array.from(atob(s),c=>c.charCodeAt(0));
async function boundedBytes(request,limit){
 const chunks=[];let total=0;const reader=request.body?.getReader();if(!reader)return new Uint8Array();
 while(true){const {value,done}=await reader.read();if(done)break;total+=value.length;if(total>limit){await reader.cancel();const error=new Error('Request too large / 请求内容过大');error.status=413;throw error;}chunks.push(value);}
 const result=new Uint8Array(total);let offset=0;for(const chunk of chunks){result.set(chunk,offset);offset+=chunk.length;}return result;
}
async function readJSON(request,limit){try{return JSON.parse(new TextDecoder().decode(await boundedBytes(request,limit)));}catch(error){if(error.status)throw error;const invalid=new Error('Invalid JSON request');invalid.status=400;throw invalid;}}
async function hmac(secret,text){const key=await crypto.subtle.importKey('raw',encoder.encode(secret),{name:'HMAC',hash:'SHA-256'},false,['sign']);return base64(new Uint8Array(await crypto.subtle.sign('HMAC',key,encoder.encode(text))));}
async function equal(a,b){const left=new Uint8Array(await crypto.subtle.digest('SHA-256',encoder.encode(a))),right=new Uint8Array(await crypto.subtle.digest('SHA-256',encoder.encode(b)));let difference=0;for(let i=0;i<left.length;i++)difference|=left[i]^right[i];return difference===0;}
async function session(request,env){
 const token=(request.headers.get('Cookie')||'').match(/(?:^|; )uu_session=([^;]+)/)?.[1];if(!token)return null;
 try{const [payload,signature]=decodeURIComponent(token).split('.');if(!await equal(signature,await hmac(env.SESSION_SECRET,payload)))return null;const data=JSON.parse(new TextDecoder().decode(decode(payload)));if(data.exp<=Date.now())return null;return {token:payload,csrf:await hmac(env.SESSION_SECRET,'csrf:'+payload)};}catch{return null;}
}
async function github(env,path,options={}){
 const response=await fetch(`https://api.github.com/repos/${encodeURIComponent(env.GITHUB_OWNER)}/${encodeURIComponent(env.GITHUB_REPO)}/${path}`,{...options,headers:{'Authorization':`Bearer ${env.GITHUB_TOKEN}`,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'uu-scout-admin','Content-Type':'application/json',...options.headers}});
 if(!response.ok){const error=new Error(`GitHub request failed (${response.status}). Check the Worker GitHub token and repository permissions.`);error.status=response.status;throw error;}return response;
}
const pathFor=path=>path.split('/').map(encodeURIComponent).join('/');
async function getFile(env,path){const response=await github(env,`contents/${pathFor(path)}?ref=${encodeURIComponent(env.GITHUB_BRANCH)}`);const file=await response.json();if(!file.content)throw new Error('Repository file is too large or unavailable.');return {sha:file.sha,data:JSON.parse(new TextDecoder().decode(decode(file.content.replace(/\s/g,''))))};}
async function putFile(env,path,bytes,message,sha){return github(env,`contents/${pathFor(path)}`,{method:'PUT',body:JSON.stringify({message,content:base64(bytes),branch:env.GITHUB_BRANCH,...(sha?{sha}:{})})});}
async function putJSON(env,path,data,message,sha){return putFile(env,path,encoder.encode(JSON.stringify(data,null,2)),message,sha);}
async function dispatch(env,id,phase){await github(env,'actions/workflows/upload-screenshot.yml/dispatches',{method:'POST',body:JSON.stringify({ref:env.GITHUB_BRANCH,inputs:{job_id:id,phase}})});}
export function validateRows(rows){
 if(!Array.isArray(rows)||!rows.length||rows.length>1000)throw new Error('Review between 1 and 1000 option rows.');
 return rows.map((row,index)=>{
  if(!row||typeof row!=='object')throw new Error(`Invalid row ${index+1}.`);
  const result={};for(const [key,limit] of [['section',20],['row',80],['seat_as_printed',80],['performance_date',10],['notes',500],['raw_ocr',3000]]){if(typeof(row[key]??'')!=='string'||(row[key]??'').length>limit)throw new Error(`Invalid ${key} in row ${index+1}.`);result[key]=(row[key]??'').trim();}
  if(result.performance_date&&!/^\d{4}-\d{2}-\d{2}$/.test(result.performance_date))throw new Error(`Invalid date in row ${index+1}.`);
  if(typeof row.sold!=='boolean')throw new Error(`Choose the sold status for row ${index+1}.`);
  if(row.price!==null&&(typeof row.price!=='number'||!Number.isFinite(row.price)||row.price<0||row.price>1000000))throw new Error(`Invalid price in row ${index+1}.`);
  return {...result,price:row.price,sold:row.sold};
 });
}
export default {async fetch(request,env){
 const url=new URL(request.url);
 if(!url.pathname.startsWith('/api/'))return env.ASSETS.fetch(request);
 if(!env.ADMIN_PASSWORD||env.ADMIN_PASSWORD.length<16||!env.SESSION_SECRET||env.SESSION_SECRET.length<32||!env.GITHUB_TOKEN)return json({error:'Finish setup: add the Worker secrets ADMIN_PASSWORD (16+ characters), SESSION_SECRET (32+ random characters), and GITHUB_TOKEN.'},503);
 if(!['GET','POST'].includes(request.method))return json({error:'Method not allowed'},405);
 if(request.method==='POST'&&request.headers.get('Origin')!==url.origin)return json({error:'Cross-origin requests are not allowed.'},403);
 try{
  if(url.pathname==='/api/login'&&request.method==='POST'){
   const ip=request.headers.get('CF-Connecting-IP')||'unknown',now=Date.now(),attempt=loginAttempts.get(ip)||{count:0,start:now};if(now-attempt.start>600000){attempt.count=0;attempt.start=now;}if(attempt.count>=10)return json({error:'Too many attempts. Try again in 10 minutes / 尝试次数过多，请稍后重试'},429);attempt.count++;loginAttempts.set(ip,attempt);
   const body=await readJSON(request,2048);if(typeof body.password!=='string'||body.password.length>256||!await equal(body.password,env.ADMIN_PASSWORD))return json({error:'Incorrect password / 密码错误'},401);
   loginAttempts.delete(ip);
   const payload=base64(encoder.encode(JSON.stringify({exp:Date.now()+12*60*60*1000,nonce:crypto.randomUUID()}))),signed=payload+'.'+await hmac(env.SESSION_SECRET,payload);
   return json({ok:true},200,{'Set-Cookie':`uu_session=${encodeURIComponent(signed)}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=43200`});
  }
  const auth=await session(request,env);if(!auth)return json({error:'Please sign in / 请先登录'},401);
  if(request.method==='POST'&&!await equal(request.headers.get('X-CSRF-Token')||'',auth.csrf))return json({error:'Refresh this page before trying again / 请刷新页面'},403);
  if(url.pathname==='/api/session'&&request.method==='GET')return json({csrf:auth.csrf,site:env.SITE_URL});
  if(url.pathname==='/api/logout'&&request.method==='POST')return json({ok:true},200,{'Set-Cookie':'uu_session=; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=0'});
  if(url.pathname==='/api/sources'&&request.method==='GET'){const file=await getFile(env,'data/draft2/coverage.json');return json(file.data.filter(s=>!s.superseded_by).map(s=>({index:s.source_index,name:s.source_file,sha256:s.sha256})));}
  if(url.pathname==='/api/upload'&&request.method==='POST'){
   const size=Number(request.headers.get('Content-Length'));if(size>MAX_IMAGE+16384)return json({error:'Use a JPG or PNG smaller than 3 MB / 请使用小于 3 MB 的 JPG 或 PNG'},413);
   const bounded=await boundedBytes(request,MAX_IMAGE+16384),form=await new Request(request.url,{method:'POST',headers:{'Content-Type':request.headers.get('Content-Type')||''},body:bounded}).formData(),file=form.get('image');if(!file||typeof file.arrayBuffer!=='function'||file.size>MAX_IMAGE||file.size===0)return json({error:'Select a JPG or PNG under 3 MB'},400);
   const bytes=new Uint8Array(await file.arrayBuffer()),png=bytes.slice(0,8).every((b,i)=>b===[137,80,78,71,13,10,26,10][i]),jpg=bytes[0]===255&&bytes[1]===216&&bytes[2]===255;
   if(!png&&!jpg)return json({error:'Only actual JPG and PNG images are accepted.'},400);
   const base=form.get('base_source')||'',sources=(await getFile(env,'data/draft2/coverage.json')).data,previous=base?sources.find(s=>String(s.source_index)===base):null;
   if(base&&!previous)return json({error:'Select an existing screenshot to update.'},400);
   const id=crypto.randomUUID().replace(/-/g,''),extension=png?'png':'jpg',hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');
   if(sources.some(s=>s.sha256===hash))return json({error:'This exact image is already published. Upload the changed screenshot / 此图片已发布，请上传更新后的截图'},409);
   const path=`data/upload-jobs/${id}/input.${extension}`;
   await putFile(env,path,bytes,`Stage screenshot ${id}`);
   await putJSON(env,`data/upload-jobs/${id}/request.json`,{id,input_path:path,extension,sha256:hash,original_filename:String(file.name||'upload').slice(0,150),base_source_index:previous?.source_index??null,base_source_sha256:previous?.sha256??null,created_at:new Date().toISOString()},`Request OCR ${id}`);
   await dispatch(env,id,'extract');return json({id},202);
  }
  const match=url.pathname.match(/^\/api\/jobs\/([a-f0-9]{32})(\/publish|\/image|\/retry)?$/);
  if(match){const id=match[1],suffix=match[2]||'';
   if(suffix==='/image'&&request.method==='GET'){const req=(await getFile(env,`data/upload-jobs/${id}/request.json`)).data;if(!['png','jpg'].includes(req.extension)||req.input_path!==`data/upload-jobs/${id}/input.${req.extension}`)return json({error:'Invalid image reference'},400);const response=await github(env,`contents/${pathFor(req.input_path)}?ref=${encodeURIComponent(env.GITHUB_BRANCH)}`,{headers:{Accept:'application/vnd.github.raw+json'}});return new Response(response.body,{headers:{'Content-Type':req.extension==='png'?'image/png':'image/jpeg','Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'}});}
   if(suffix==='/retry'&&request.method==='POST'){await getFile(env,`data/upload-jobs/${id}/request.json`);let phase='extract';try{const current=(await getFile(env,`data/upload-jobs/${id}/review.json`)).data;if(current.status==='published')return json({error:'Already published'},409);if(current.status==='approved')phase='publish';}catch(error){if(error.status!==404)throw error;}await dispatch(env,id,phase);return json({ok:true},202);}
   if(suffix===''&&request.method==='GET'){try{return json((await getFile(env,`data/upload-jobs/${id}/review.json`)).data);}catch(error){if(error.status===404)return json({status:'processing'});throw error;}}
   if(suffix==='/publish'&&request.method==='POST'){
    const body=await readJSON(request,850000);if(body.reviewed_all_rows!==true)return json({error:'Check the original screenshot and confirm every option row before publishing.'},400);
    const file=await getFile(env,`data/upload-jobs/${id}/review.json`);if(file.data.status!=='review')return json({error:'This job is not awaiting review.'},409);
    const rows=validateRows(body.rows);await putJSON(env,`data/upload-jobs/${id}/review.json`,{...file.data,rows,status:'approved',reviewed_all_rows:true,approved_at:new Date().toISOString()},`Approve screenshot ${id}`,file.sha);
    await dispatch(env,id,'publish');return json({ok:true},202);
   }
  }
  return json({error:'Not found'},404);
 }catch(error){return json({error:error.message||'Request failed; please retry.'},[400,409,413].includes(error.status)?error.status:502);}
}};
