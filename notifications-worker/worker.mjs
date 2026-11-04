import {validatePreferences,matches,isDue} from './preferences.mjs';
const encoder=new TextEncoder(),DAY=86400000;
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const digest=async text=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',encoder.encode(text))),b=>b.toString(16).padStart(2,'0')).join('');
async function signature(secret,text){const key=await crypto.subtle.importKey('raw',encoder.encode(secret),{name:'HMAC',hash:'SHA-256'},false,['sign']);return Array.from(new Uint8Array(await crypto.subtle.sign('HMAC',key,encoder.encode(text))),b=>b.toString(16).padStart(2,'0')).join('');}
async function equal(a,b){return await digest(a)===await digest(b);}
function problem(message,status=400){return Object.assign(new Error(message),{status});}
function configured(env){return env.EMAIL_ENABLED==='true'&&env.DB&&(env.EMAIL_PROVIDER==='resend'?env.RESEND_API_KEY:env.BREVO_API_KEY)&&typeof env.PUBLIC_URL==='string'&&env.PUBLIC_URL.startsWith('https://')&&env.TOKEN_SECRET?.length>=32&&typeof env.FROM_EMAIL==='string'&&/^[^\s<>@]+@[^\s<>@]+\.[^\s<>@]+$/.test(env.FROM_EMAIL);}
async function ready(env){if(!configured(env))return false;try{await env.DB.prepare('SELECT id FROM subscribers LIMIT 1').first();return true;}catch{return false;}}
function originAllowed(request,env){const origin=request.headers.get('Origin');return origin===new URL(request.url).origin||origin===new URL(env.SITE_URL).origin;}
function response(request,env,data,status=200){const headers={'Content-Type':'application/json','Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Vary':'Origin'};if(originAllowed(request,env))headers['Access-Control-Allow-Origin']=request.headers.get('Origin');return new Response(JSON.stringify(data),{status,headers});}
async function bodyJSON(request){const reader=request.body?.getReader();if(!reader)throw problem('Missing request');let size=0;const chunks=[];while(true){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>8192){await reader.cancel();throw problem('Request too large',413);}chunks.push(value);}const bytes=new Uint8Array(size);let at=0;for(const c of chunks){bytes.set(c,at);at+=c.length;}try{return JSON.parse(new TextDecoder().decode(bytes));}catch{throw problem('Invalid JSON');}}
async function limit(env,key,maximum,period,now){const bucket=Math.floor(now/period);const result=await env.DB.prepare('INSERT INTO rate_limits(key,count,expires_at) VALUES(?,1,?) ON CONFLICT(key) DO UPDATE SET count=count+1 WHERE count<?').bind(key+':'+bucket,now+period,maximum).run();if(!result.meta.changes)throw problem('Too many requests. Please try again later / 请求过多，请稍后重试',429);}
async function reserveMail(env,now){const day=new Date(now).toISOString().slice(0,10),max=Math.max(1,Math.min(10000,Number(env.DAILY_EMAIL_LIMIT)||90));const result=await env.DB.prepare('INSERT INTO mail_budget(day,count) VALUES(?,1) ON CONFLICT(day) DO UPDATE SET count=count+1 WHERE count<?').bind(day,max).run();if(!result.meta.changes)throw problem('Email sending limit reached; please try again tomorrow / 今日发送额度已用完，请明天再试',429);}
async function sendEmail(env,payload,idempotency){
 await reserveMail(env,Date.now());
 const resend=env.EMAIL_PROVIDER==='resend',hash=await digest(idempotency),providerKey=hash.slice(0,8)+'-'+hash.slice(8,12)+'-4'+hash.slice(13,16)+'-a'+hash.slice(17,20)+'-'+hash.slice(20,32);let res;
 try{
  res=await fetch(resend?'https://api.resend.com/emails':'https://api.brevo.com/v3/smtp/email',{method:'POST',headers:resend?{'Authorization':'Bearer '+env.RESEND_API_KEY,'Content-Type':'application/json','Idempotency-Key':idempotency}:{'api-key':env.BREVO_API_KEY,'Content-Type':'application/json',Accept:'application/json'},body:JSON.stringify(resend?{from:'uu scout <'+env.FROM_EMAIL+'>',...payload}:{sender:{name:'uu scout',email:env.FROM_EMAIL},to:payload.to.map(email=>({email})),subject:payload.subject,textContent:payload.text,htmlContent:payload.html,headers:{idempotencyKey:providerKey}}),signal:AbortSignal.timeout(10000)});
 }catch{throw Object.assign(problem('Email delivery could not be confirmed. Please try again later / 暂时无法确认邮件投递状态，请稍后再试',503),{ambiguous:true});}
 if(!res.ok){console.warn('Email provider response',env.EMAIL_PROVIDER||'brevo',res.status);throw problem('Email provider is temporarily unavailable; please retry later / 邮件服务暂时不可用，请稍后重试',503);}
}
async function unsubscribeToken(env,id){return id+'.'+await signature(env.TOKEN_SECRET,'unsubscribe:'+id);}
async function tokenSubscriber(env,token){if(typeof token!=='string'||!/^([a-f0-9]{32})\.([a-f0-9]{64})$/.test(token))throw problem('Invalid unsubscribe link');const [id,sig]=token.split('.');if(!await equal(sig,await signature(env.TOKEN_SECRET,'unsubscribe:'+id)))throw problem('Invalid unsubscribe link');return id;}
export async function syncFeed(env){
 const res=await fetch(env.FEED_URL,{headers:{Accept:'application/json','Cache-Control':'no-cache'},signal:AbortSignal.timeout(15000)});if(!res.ok)throw problem('Ticket updates are temporarily unavailable',503);
 const text=await res.text();if(text.length>2000000)throw problem('Unexpected updates payload',503);const data=JSON.parse(text);if(!Array.isArray(data.events)||data.events.length>3000)throw problem('Invalid updates feed',503);
 const now=Date.now(),events=data.events.filter(e=>/^[a-f0-9]{24}$/.test(e.id)&&['listing_drop','below_median'].includes(e.kind)&&typeof e.price==='number'&&Number.isFinite(e.price)&&e.price>0&&e.currency==='CNY');
 // D1 caps a batch's statements; upserts are chunked while retaining first-seen time.
 await env.DB.prepare('UPDATE alert_events SET active=0').run();
 for(let i=0;i<events.length;i+=80)await env.DB.batch(events.slice(i,i+80).map(e=>env.DB.prepare('INSERT INTO alert_events(id,payload,first_seen_at,last_seen_at,active) VALUES(?,?,?,?,1) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload,last_seen_at=excluded.last_seen_at,active=1').bind(e.id,JSON.stringify(e),now,now)));
 return now;
}
async function subscribe(request,env,base){
 const body=await bodyJSON(request);if(body.website)return {ok:true};if(body.consent!==true)throw problem('Please agree to receive matching alerts / 请先同意接收匹配提醒');
 const email=typeof body.email==='string'?body.email.trim().toLowerCase():'';if(email.length>254||!/^([^\s<>@]+)@([a-z0-9-]+\.)+[a-z]{2,63}$/i.test(email))throw problem('Enter a valid email address / 请填写有效邮箱');
 const preferences=validatePreferences(body.preferences),now=Date.now(),ip=request.headers.get('CF-Connecting-IP')||'unknown',ipKey=await signature(env.TOKEN_SECRET,'ip:'+ip),contactHash=await signature(env.TOKEN_SECRET,'email:'+email);
 await limit(env,'signup-ip:'+ipKey,5,3600000,now);await limit(env,'signup-email:'+contactHash,3,DAY,now);
 const count=await env.DB.prepare('SELECT COUNT(*) AS total FROM subscribers').first();if(count.total>=Math.min(100,Math.max(1,Number(env.MAX_SUBSCRIBERS)||100)))throw problem('The trial subscription list is full. Please contact uu scout / 试用订阅名额已满，请联系 uu scout',503);
 const token=crypto.randomUUID().replace(/-/g,'')+crypto.randomUUID().replace(/-/g,''),hash=await digest(token),url=base+'/confirm?t='+token;
 await env.DB.prepare('INSERT INTO pending_subscriptions(token_hash,contact,contact_hash,preferences,created_at,expires_at) VALUES(?,?,?,?,?,?)').bind(hash,email,contactHash,JSON.stringify(preferences),now,now+DAY).run();
 const text=`Confirm your uu scout ticket alerts / 确认 uu scout 票源提醒\n\n${preferences.performance_date} · ${preferences.section} · row ${preferences.row} ±3 · ${preferences.seat_mask} · minimum ${preferences.min_percent}%\n\nOpen this link and press Confirm / 打开链接并点击确认：\n${url}\n\nThis link expires in 24 hours. No subscription is active until confirmed. If you did not request this, ignore this email. / 链接 24 小时内有效，确认后才会订阅。若非本人申请，请忽略。`;
 try{await sendEmail(env,{to:[email],subject:'Confirm uu scout ticket alerts / 确认票源提醒',text,html:'<div style="font:16px system-ui;line-height:1.7"><h2>uu scout</h2><p>Confirm your matching ticket alerts / 确认订阅匹配票源提醒</p><p>'+esc(preferences.performance_date)+' · '+esc(preferences.section)+' · '+esc(preferences.row)+' ±3 · '+esc(preferences.seat_mask)+'</p><p><a href="'+esc(url)+'">Confirm email alerts / 确认邮件提醒</a></p><p>No subscription is active until you confirm. Ignore this email if you did not request it. / 确认后才会订阅，若非本人申请请忽略。</p></div>'},'confirm-'+hash);}catch(error){if(!error.ambiguous)await env.DB.prepare('DELETE FROM pending_subscriptions WHERE token_hash=?').bind(hash).run();throw error;}
 return {ok:true,message:'Check your email and confirm. Nothing is active until you confirm / 请查收邮件并确认，确认后才会启用提醒'};
}
async function confirm(request,env){
 const body=await bodyJSON(request);if(body.confirmed!==true||typeof body.token!=='string'||!/^([a-f0-9]{64})$/.test(body.token))throw problem('Open the confirmation email and press Confirm');
 const hash=await digest(body.token),pending=await env.DB.prepare('SELECT * FROM pending_subscriptions WHERE token_hash=?').bind(hash).first();if(!pending||pending.expires_at<Date.now())throw problem('This link expired or was already used. Request a new confirmation / 链接已过期或使用，请重新申请');
 // Seed the current feed before activation; existing deals must not flood a new subscriber.
 await syncFeed(env);const now=Date.now()+1,id=crypto.randomUUID().replace(/-/g,'');
 const result=await env.DB.batch([env.DB.prepare('DELETE FROM subscribers WHERE contact=?').bind(pending.contact),env.DB.prepare('INSERT INTO subscribers(id,contact,preferences,confirmed_at,last_sent_at) SELECT ?,?,?,?,0 WHERE (SELECT COUNT(*) FROM subscribers)<?').bind(id,pending.contact,pending.preferences,now,Math.min(100,Math.max(1,Number(env.MAX_SUBSCRIBERS)||100))),env.DB.prepare('DELETE FROM pending_subscriptions WHERE contact_hash=?').bind(pending.contact_hash)]);
 if(!result[1].meta.changes)throw problem('The trial subscription list is full. Request a new confirmation later / 试用订阅名额已满，请稍后重新申请',503);
 return {ok:true,message:'Confirmed. You will receive new matching alerts when published / 已确认，新的匹配提醒发布后将发送到你的邮箱'};
}
function eventText(e){const label=e.kind==='listing_drop'?'Price drop in updated listing / 更新票源降价':'Lower comparable offer / 更低的同类报价',baseline=e.kind==='listing_drop'?e.previous_price:e.median;return `${label}\n${e.performance_date} · ${e.section} · row ${e.row} · ${e.seat_mask}\nCNY ${e.price} (${e.percent}% below CNY ${baseline})\nSource ${e.source_index}, row ${e.physical_row}`;}
async function deliverOutbox(env,outbox){
 if(outbox.status==='sent'||outbox.next_attempt_at>Date.now())return false;
 const window=env.EMAIL_PROVIDER==='resend'?23*3600000:14*60000;
 if(outbox.ambiguous&&Date.now()-outbox.created_at>window){await env.DB.prepare("UPDATE mail_outbox SET status='uncertain' WHERE id=?").bind(outbox.id).run();return false;}
 const subscriber=await env.DB.prepare('SELECT id FROM subscribers WHERE id=?').bind(outbox.subscriber_id).first();if(!subscriber)return false;
 await env.DB.prepare('UPDATE mail_outbox SET ambiguous=1 WHERE id=?').bind(outbox.id).run();
 try{
  await sendEmail(env,JSON.parse(outbox.payload),'alerts-'+outbox.id);
  await env.DB.batch([env.DB.prepare("UPDATE mail_outbox SET status='sent',attempts=attempts+1 WHERE id=?").bind(outbox.id),env.DB.prepare('UPDATE subscribers SET last_sent_at=? WHERE id=?').bind(Date.now(),outbox.subscriber_id)]);return true;
 }catch(error){
  const attempts=outbox.attempts+1,ambiguous=outbox.ambiguous||error.ambiguous?1:0,status=attempts>=6?(ambiguous?'uncertain':'failed'):'pending';await env.DB.prepare('UPDATE mail_outbox SET status=?,attempts=?,ambiguous=?,next_attempt_at=? WHERE id=?').bind(status,attempts,ambiguous,Date.now()+Math.min(DAY,(ambiguous?60000:300000)*2**attempts),outbox.id).run();return false;
 }
}
export async function runNotifications(env){
 const deadline=Date.now()+18000;
 if(!await ready(env))return;
 await syncFeed(env);const now=Date.now(),subscribers=(await env.DB.prepare('SELECT * FROM subscribers ORDER BY last_sent_at,id LIMIT 100').all()).results;
 for(const subscriber of subscribers){
  if(Date.now()>deadline)break;
  const locked=await env.DB.prepare('INSERT INTO subscriber_locks(id,locked_until) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET locked_until=excluded.locked_until WHERE locked_until<?').bind(subscriber.id,Date.now()+90000,Date.now()).run();if(!locked.meta.changes)continue;
  try{
   const pending=await env.DB.prepare("SELECT * FROM mail_outbox WHERE subscriber_id=? AND status='pending' ORDER BY created_at LIMIT 1").bind(subscriber.id).first();if(pending){await deliverOutbox(env,pending);continue;}
   if(!isDue(subscriber,now))continue;
   const events=(await env.DB.prepare('SELECT e.id,e.payload FROM alert_events e WHERE e.active=1 AND e.first_seen_at>? AND NOT EXISTS(SELECT 1 FROM deliveries d WHERE d.subscriber_id=? AND d.event_id=e.id) ORDER BY e.first_seen_at,e.id LIMIT 1000').bind(subscriber.confirmed_at,subscriber.id).all()).results.map(row=>JSON.parse(row.payload)),preferences=JSON.parse(subscriber.preferences),matching=events.filter(e=>matches(preferences,e));if(!matching.length)continue;
   const id=await digest(subscriber.id+':'+matching.map(e=>e.id).sort().join(',')),unsubscribe=env.PUBLIC_URL.replace(/\/$/,'')+'/unsubscribe?t='+await unsubscribeToken(env,subscriber.id),site=env.SITE_URL.replace(/#.*$/,'')+'#updates',items=matching.slice(0,10);
   const text=`uu scout · ${matching.length} matching ticket alert(s) / 条匹配提醒\n\n${items.map(eventText).join('\n\n')}\n\n${matching.length>10?'More matching alerts are on the website / 更多匹配提醒请查看网站\n':''}${site}\n\nOCR quotes and grouped prices need supplier confirmation. Comparable offers are not confirmed drops for the same physical ticket. / OCR 报价和组合票价格须向票源方确认；相近报价不等于同一张票降价。\n\nUnsubscribe / 退订：${unsubscribe}`;
   const payload={to:[subscriber.contact],subject:`uu scout: ${matching.length} matching ticket alert(s) / 匹配票源提醒`,text,html:'<div style="font:15px system-ui;line-height:1.7"><h2>uu scout · '+matching.length+' matching alerts / 条匹配提醒</h2>'+items.map(e=>'<p>'+esc(eventText(e)).replace(/\n/g,'<br>')+'</p>').join('')+'<p><a href="'+esc(site)+'">View updates and screenshot evidence / 查看动态及原图证据</a></p><p>Confirm OCR quotes, grouped prices and availability with the supplier. / 请向票源方确认 OCR 报价、组合票价格及有票状态。</p><p><a href="'+esc(unsubscribe)+'">Unsubscribe / 退订</a></p></div>'};
   await env.DB.batch([env.DB.prepare("INSERT OR IGNORE INTO mail_outbox(id,subscriber_id,payload,created_at,next_attempt_at,status) VALUES(?,?,?,?,?,'pending')").bind(id,subscriber.id,JSON.stringify(payload),now,now),...matching.map(e=>env.DB.prepare('INSERT OR IGNORE INTO deliveries(subscriber_id,event_id,outbox_id) VALUES(?,?,?)').bind(subscriber.id,e.id,id))]);
   await deliverOutbox(env,{id,subscriber_id:subscriber.id,payload:JSON.stringify(payload),status:'pending',attempts:0,next_attempt_at:0,created_at:now,ambiguous:0});
  }finally{await env.DB.prepare('DELETE FROM subscriber_locks WHERE id=?').bind(subscriber.id).run();}
 }
 await env.DB.batch([env.DB.prepare('DELETE FROM pending_subscriptions WHERE expires_at<?').bind(Date.now()),env.DB.prepare('DELETE FROM rate_limits WHERE expires_at<?').bind(Date.now()),env.DB.prepare('DELETE FROM mail_outbox WHERE created_at<? AND status IN (\'sent\',\'failed\')').bind(Date.now()-30*DAY),env.DB.prepare('DELETE FROM mail_budget WHERE day<?').bind(new Date(Date.now()-7*DAY).toISOString().slice(0,10))]);
}
export default {
 async fetch(request,env,ctx){
  const url=new URL(request.url);
  if(request.method==='OPTIONS')return new Response(null,{status:204,headers:originAllowed(request,env)?{'Access-Control-Allow-Origin':request.headers.get('Origin'),'Access-Control-Allow-Methods':'GET,POST,OPTIONS','Access-Control-Allow-Headers':'Content-Type','Vary':'Origin'}:{}});
  if(!url.pathname.startsWith('/api/')){
   if(url.pathname==='/confirm'||url.pathname==='/unsubscribe')return env.ASSETS.fetch(new Request(url.origin+'/action.html',request));
   return env.ASSETS.fetch(request);
  }
  if(url.pathname==='/api/config'&&request.method==='GET')return response(request,env,{ready:!!await ready(env),channel:'email',site:env.SITE_URL});
  if(request.method!=='POST')return response(request,env,{error:'Method not allowed'},405);
  const internal=url.pathname==='/api/internal/publish';
  if(internal){if(!env.PUBLISH_SECRET||env.PUBLISH_SECRET.length<32||!await equal(request.headers.get('Authorization')||'','Bearer '+env.PUBLISH_SECRET))return response(request,env,{error:'Unauthorized'},401);}
  else if(!originAllowed(request,env))return response(request,env,{error:'Cross-origin requests are not allowed'},403);
  try{
   // Unsubscribe must remain available even if outbound email is paused.
   if(url.pathname==='/api/unsubscribe'){
    if(!env.DB||!env.TOKEN_SECRET||env.TOKEN_SECRET.length<32)throw problem('Subscription storage is temporarily unavailable',503);
    const body=await bodyJSON(request),id=await tokenSubscriber(env,body.token),subscriber=await env.DB.prepare('SELECT contact FROM subscribers WHERE id=?').bind(id).first();
    if(subscriber){const contactHash=await signature(env.TOKEN_SECRET,'email:'+subscriber.contact);await env.DB.batch([env.DB.prepare('DELETE FROM pending_subscriptions WHERE contact_hash=?').bind(contactHash),env.DB.prepare('DELETE FROM subscribers WHERE id=?').bind(id),env.DB.prepare('DELETE FROM subscriber_locks WHERE id=?').bind(id)]);}
    return response(request,env,{ok:true,message:'Unsubscribed. Your email and preferences have been removed from the subscription database / 已退订，邮箱及偏好已从订阅数据库删除'});
   }
   if(!await ready(env))return response(request,env,{error:'Email alerts are still being set up. Please check back / 邮件提醒正在设置中，请稍后再来'},503);
   if(internal){ctx.waitUntil(runNotifications(env));return response(request,env,{ok:true,status:'queued'},202);}
   if(url.pathname==='/api/subscribe')return response(request,env,await subscribe(request,env,url.origin));
   if(url.pathname==='/api/confirm')return response(request,env,await confirm(request,env));
   return response(request,env,{error:'Not found'},404);
  }catch(error){return response(request,env,{error:error.status?error.message:'Request failed. Please try again later / 请求失败，请稍后重试'},error.status||500);}
 },
 async scheduled(controller,env,ctx){ctx.waitUntil(runNotifications(env));}
};
