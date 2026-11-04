import assert from 'node:assert/strict';
import fs from 'node:fs';
import {DatabaseSync} from 'node:sqlite';
import worker,{runNotifications} from '../notifications-worker/worker.mjs';
import {validatePreferences,matches} from '../notifications-worker/preferences.mjs';
class D1 {
 constructor(){this.db=new DatabaseSync(':memory:');for(const file of fs.readdirSync('notifications-worker/migrations').filter(f=>f.endsWith('.sql')).sort())this.db.exec(fs.readFileSync('notifications-worker/migrations/'+file,'utf8'));}
 prepare(sql){const db=this.db;let values=[];const statement={bind(...v){values=v;return statement;},_run(){const r=db.prepare(sql).run(...values);return {success:true,meta:{changes:Number(r.changes)}};},async run(){return statement._run();},async first(){return db.prepare(sql).get(...values)||null;},async all(){return {results:db.prepare(sql).all(...values)};}};return statement;}
 async batch(statements){this.db.exec('BEGIN');try{const results=statements.map(s=>s._run());this.db.exec('COMMIT');return results;}catch(e){this.db.exec('ROLLBACK');throw e;}}
}
let clock=Date.parse('2026-11-04T12:00:00Z');Date.now=()=>clock;
const preferences={scope:'watchlist',cadence:'updates',performance_date:'2027-01-15',section:'F4',row:12,seat_mask:'1X',min_percent:10,kinds:['listing_drop','below_median']};
const event=(id,extra={})=>({id:id.repeat(24),kind:'below_median',performance_date:'2027-01-15',section:'F4',row:'12',seat_mask:'1X',price:3000,currency:'CNY',median:4000,percent:25,source_index:81,physical_row:1,...extra});
let feed={events:[event('a')]},sent=[],providerStatus=201,providerNetworkError=false;
globalThis.fetch=async(url,options={})=>{
 if(url==='https://feed.test/updates.json')return new Response(JSON.stringify(feed));
 if(url==='https://api.brevo.com/v3/smtp/email'){
  assert.equal(options.headers['api-key'],'fake-provider-key');const payload=JSON.parse(options.body);assert.deepEqual(payload.sender,{name:'uu scout',email:'verified@example.com'});sent.push(payload);if(providerNetworkError)throw new Error('Simulated provider timeout');return new Response('{}',{status:providerStatus});
 }
 throw new Error('Unexpected external request '+url);
};
const env={DB:new D1(),EMAIL_ENABLED:'true',EMAIL_PROVIDER:'brevo',BREVO_API_KEY:'fake-provider-key',TOKEN_SECRET:'fake-token-secret-with-more-than-32-characters',PUBLISH_SECRET:'fake-publish-secret-with-more-than-32-characters',FROM_EMAIL:'verified@example.com',PUBLIC_URL:'https://alerts.test',SITE_URL:'https://rititititi.github.io/ticketing/',FEED_URL:'https://feed.test/updates.json',DAILY_EMAIL_LIMIT:'250',MAX_SUBSCRIBERS:'100',ASSETS:{fetch:async()=>new Response('Confirmation page')}};
const pending=[];const ctx={waitUntil:p=>pending.push(p)};
const request=(path,body,options={})=>new Request('https://alerts.test'+path,{method:body?'POST':'GET',headers:{Origin:'https://rititititi.github.io','Content-Type':'application/json',...options},...(body?{body:JSON.stringify(body)}:{})});
const call=(path,body,options)=>worker.fetch(request(path,body,options),env,ctx);
let response=await call('/api/config');assert.equal((await response.json()).ready,true);
response=await call('/api/subscribe',{email:'fan@example.com',preferences,consent:false});assert.equal(response.status,400);assert.equal(sent.length,0);
response=await call('/api/subscribe',{email:'fan@example.com',preferences,consent:true},{Origin:'https://evil.test'});assert.equal(response.status,403);
response=await call('/api/subscribe',{email:'fan@example.com',preferences,consent:true});assert.equal(response.status,200);assert.equal(sent.length,1);assert.equal((await env.DB.prepare('SELECT COUNT(*) AS n FROM subscribers').first()).n,0);
const token=sent[0].textContent.match(/confirm\?t=([a-f0-9]{64})/)[1];
response=await call('/confirm?t='+token);assert.equal(response.status,200);assert.equal((await env.DB.prepare('SELECT COUNT(*) AS n FROM subscribers').first()).n,0);
response=await call('/api/confirm',{token,confirmed:false});assert.equal(response.status,400);
response=await call('/api/confirm',{token,confirmed:true});assert.equal(response.status,200);assert.equal((await env.DB.prepare('SELECT COUNT(*) AS n FROM subscribers').first()).n,1);
clock+=100;const beforeWrites=env.DB.db.prepare('SELECT total_changes() AS n').get().n;await runNotifications(env);assert.ok(env.DB.db.prepare('SELECT total_changes() AS n').get().n-beforeWrites<5,'Unchanged checks must not rewrite every feed event or subscriber');assert.equal(sent.length,1,'Existing feed is not delivered as a new alert');
feed.events.push(event('b',{row:'16'}));clock+=100;await runNotifications(env);assert.equal(sent.length,1,'Row outside ±3 must not match');
feed.events.push(event('c',{row:'15',kind:'listing_drop',percent:12,previous_price:3500}));clock+=100;
response=await call('/api/internal/publish',{}, {Authorization:'Bearer wrong'});assert.equal(response.status,401);
response=await call('/api/internal/publish',{}, {Authorization:'Bearer '+env.PUBLISH_SECRET});assert.equal(response.status,202);await Promise.all(pending.splice(0));assert.equal(sent.length,2);
assert.match(sent[1].textContent,/Price drop in updated listing/);assert.match(sent[1].textContent,/Source 81/);const unsubscribe=sent[1].textContent.match(/unsubscribe\?t=([a-f0-9]{32}\.[a-f0-9]{64})/)[1];
await Promise.all([runNotifications(env),runNotifications(env)]);assert.equal(sent.length,2,'Retries and concurrent requests must not resend the same event');
response=await call('/unsubscribe?t='+unsubscribe);assert.equal(response.status,200);assert.equal((await env.DB.prepare('SELECT COUNT(*) AS n FROM subscribers').first()).n,1,'GET/email scanners cannot unsubscribe');
response=await call('/api/unsubscribe',{token:unsubscribe.slice(0,-1)+(unsubscribe.endsWith('a')?'b':'a')});assert.equal(response.status,400);
env.EMAIL_ENABLED='false';response=await call('/api/config');assert.equal((await response.json()).ready,false);
response=await call('/api/unsubscribe',{token:unsubscribe});assert.equal(response.status,200,'Unsubscribe still works while sending is paused');assert.equal((await env.DB.prepare('SELECT COUNT(*) AS n FROM subscribers').first()).n,0);assert.equal((await env.DB.prepare('SELECT COUNT(*) AS n FROM mail_outbox').first()).n,0);
assert.equal((await env.DB.prepare('SELECT COUNT(*) AS n FROM deliveries').first()).n,0);env.EMAIL_ENABLED='true';
// Replacement preferences are activated only after another email confirmation.
clock+=100;response=await call('/api/subscribe',{email:'second@example.com',preferences,consent:true},{'CF-Connecting-IP':'another-ip'});assert.equal(response.status,200);const token2=sent.at(-1).textContent.match(/confirm\?t=([a-f0-9]{64})/)[1];response=await call('/api/confirm',{token:token2,confirmed:true});assert.equal(response.status,200);
feed.events.push(event('d',{row:'12',percent:20}));clock+=100;providerStatus=503;await runNotifications(env);let outbox=await env.DB.prepare("SELECT * FROM mail_outbox WHERE status='pending'").first();assert.ok(outbox);const attemptKey=sent.at(-1).headers.idempotencyKey;
providerStatus=201;clock+=11*60000;await runNotifications(env);assert.equal(sent.at(-1).headers.idempotencyKey,attemptKey);assert.equal((await env.DB.prepare('SELECT status FROM mail_outbox WHERE id=?').bind(outbox.id).first()).status,'sent');
feed.events.push(event('e',{row:'12',percent:20}));clock+=100;providerNetworkError=true;await runNotifications(env);const attemptCount=sent.length;outbox=await env.DB.prepare("SELECT * FROM mail_outbox WHERE status='pending'").first();assert.equal(outbox.ambiguous,1);providerNetworkError=false;clock+=16*60000;await runNotifications(env);assert.equal(sent.length,attemptCount,'Uncertain delivery must not be retried after provider idempotency expires');assert.equal((await env.DB.prepare('SELECT status FROM mail_outbox WHERE id=?').bind(outbox.id).first()).status,'uncertain');
assert.throws(()=>validatePreferences({...preferences,row:0}));assert.throws(()=>validatePreferences({...preferences,scope:'all'}));assert.throws(()=>validatePreferences({...preferences,section:'F99'}));assert.equal(matches(preferences,event('e',{seat_mask:'2X'})),false);assert.equal(matches(preferences,event('e',{percent:5})),false);
const bad=new Request('https://alerts.test/api/subscribe',{method:'POST',headers:{Origin:'https://alerts.test','Content-Type':'application/json'},body:'x'.repeat(9000)});response=await worker.fetch(bad,env,ctx);assert.equal(response.status,413);
console.log('Email Worker passed: private SQLite/D1 storage, consent, email confirmation, scanner-safe activation/unsubscribe, matching, old-alert baseline, concurrency/deduplication, provider retry/idempotency, pause-safe deletion, origin checks and bounded requests.');
