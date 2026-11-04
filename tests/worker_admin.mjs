import assert from 'node:assert/strict';
import worker,{validateRows} from '../admin-worker/worker.mjs';
const env={ADMIN_PASSWORD:'test-only-long-password',SESSION_SECRET:'test-only-session-key-with-32-characters',GITHUB_TOKEN:'fake-test-token',GITHUB_OWNER:'owner',GITHUB_REPO:'repo',GITHUB_BRANCH:'main',SITE_URL:'https://site.test/',ASSETS:{fetch:async()=>new Response('Admin UI')}};
const host='https://admin.test';let calls=[];const files=new Map([['data/draft2/coverage.json',{data:[{source_index:1,source_file:'old.jpg',sha256:'old-sha'}],sha:'old'}]]);
globalThis.fetch=async(url,options={})=>{
 calls.push({url:String(url),options});assert.match(options.headers.Authorization,/^Bearer fake-test-token$/);
 const path=new URL(url).pathname.split('/contents/')[1];
 if(path&&options.method==='PUT'){const payload=JSON.parse(options.body);files.set(decodeURIComponent(path),{data:JSON.parse(Buffer.from(payload.content,'base64').toString('utf8').startsWith('{')?Buffer.from(payload.content,'base64').toString('utf8'):'null'),sha:'new-sha'});return new Response('{}',{status:201});}
 if(path){const file=files.get(decodeURIComponent(path));return file?new Response(JSON.stringify({content:Buffer.from(JSON.stringify(file.data)).toString('base64'),sha:file.sha})):new Response('{}',{status:404});}
 if(String(url).endsWith('/dispatches'))return new Response(null,{status:204});
 throw new Error('Unexpected GitHub request '+url);
};
const request=(path,options={})=>new Request(host+path,options);
let response=await worker.fetch(request('/api/sources'),env);assert.equal(response.status,401);assert.equal(calls.length,0);
response=await worker.fetch(request('/api/login',{method:'POST',headers:{Origin:'https://evil.test','Content-Type':'application/json'},body:JSON.stringify({password:env.ADMIN_PASSWORD})}),env);assert.equal(response.status,403);
response=await worker.fetch(request('/api/login',{method:'POST',headers:{Origin:host,'Content-Type':'application/json'},body:JSON.stringify({password:env.ADMIN_PASSWORD})}),env);assert.equal(response.status,200);
const cookie=response.headers.get('set-cookie');assert.match(cookie,/HttpOnly/);assert.match(cookie,/Secure/);assert.match(cookie,/SameSite=Strict/);
const cookieHeader=cookie.split(';')[0];response=await worker.fetch(request('/api/session',{headers:{Cookie:cookieHeader}}),env);const {csrf}=await response.json();assert.ok(csrf);
response=await worker.fetch(request('/api/upload',{method:'POST',headers:{Origin:host,Cookie:cookieHeader},body:'invalid'}),env);assert.equal(response.status,403);
response=await worker.fetch(request('/api/session',{headers:{Cookie:'uu_session=forged.value'}}),env);assert.equal(response.status,401);
response=await worker.fetch(request('/api/sources',{headers:{Cookie:cookieHeader}}),env);assert.equal(response.status,200);assert.equal((await response.json())[0].index,1);
const form=new FormData();form.set('image',new File([new Uint8Array([137,80,78,71,13,10,26,10,0,1])],'sheet.png',{type:'image/png'}));form.set('base_source','1');
response=await worker.fetch(request('/api/upload',{method:'POST',headers:{Origin:host,Cookie:cookieHeader,'X-CSRF-Token':csrf},body:form}),env);assert.equal(response.status,202);const {id}=await response.json();assert.match(id,/^[a-f0-9]{32}$/);
assert.equal(files.get(`data/upload-jobs/${id}/request.json`).data.base_source_index,1);
files.set(`data/upload-jobs/${id}/review.json`,{sha:'old-review',data:{status:'review',rows:[],width:500,height:800}});
const row={section:'F4',row:'12',seat_as_printed:'1X',performance_date:'2027-01-15',notes:'',raw_ocr:'F4区12排1X',price:3500,sold:false};
response=await worker.fetch(request(`/api/jobs/${id}/publish`,{method:'POST',headers:{Origin:host,Cookie:cookieHeader,'X-CSRF-Token':csrf,'Content-Type':'application/json'},body:JSON.stringify({rows:[row],reviewed_all_rows:false})}),env);assert.equal(response.status,400);
response=await worker.fetch(request(`/api/jobs/${id}/publish`,{method:'POST',headers:{Origin:host,Cookie:cookieHeader,'X-CSRF-Token':csrf,'Content-Type':'application/json'},body:JSON.stringify({rows:[row],reviewed_all_rows:true})}),env);assert.equal(response.status,202);
assert.equal(files.get(`data/upload-jobs/${id}/review.json`).data.status,'approved');
assert.throws(()=>validateRows([{...row,price:NaN}]));assert.throws(()=>validateRows([{...row,sold:'yes'}]));
const bad=new FormData();bad.set('image',new File(['<script>'],'fake.png',{type:'image/png'}));response=await worker.fetch(request('/api/upload',{method:'POST',headers:{Origin:host,Cookie:cookieHeader,'X-CSRF-Token':csrf},body:bad}),env);assert.equal(response.status,400);
for(let i=0;i<11;i++)response=await worker.fetch(request('/api/login',{method:'POST',headers:{Origin:host,'CF-Connecting-IP':'test-rate','Content-Type':'application/json'},body:JSON.stringify({password:'bad'})}),env);
assert.equal(response.status,429);
console.log('Worker checks passed: password sessions, HttpOnly/Secure cookies, origin and CSRF protection, upload validation, explicit review, GitHub dispatch, forged sessions, and login throttling.');
