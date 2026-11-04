/* Opt-in only: no email address or subscription data is stored in browser storage. */
'use strict';
(()=>{
 const $=id=>document.getElementById(id);let apiURL='';
 const sections=[...Array.from({length:20},(_,i)=>'F'+(i+1)),...Array.from({length:7},(_,i)=>'T0'+(i+1)),...Array.from({length:7},(_,i)=>'T'+(i+11)),...[[101,114],[201,210],[301,322],[401,424]].flatMap(([a,b])=>Array.from({length:b-a+1},(_,i)=>String(a+i)))];
 $('notify-section').replaceChildren(...sections.map(s=>new Option(s,s)));
 $('notify-mask').replaceChildren(new Option('X','X'),...Array.from({length:10},(_,i)=>new Option(i+'X',i+'X')));$('notify-mask').value='1X';
 async function setup(){
  try{
   const response=await fetch('/api/notification-config');if(!response.ok)throw new Error('Setup unavailable');const config=await response.json();
   if(!config.api_url)return;
   const url=new URL(config.api_url);if(url.protocol!=='https:'||url.username||url.password)throw new Error('Invalid subscription address');apiURL=url.href.replace(/\/$/,'');
   const health=await fetch(apiURL+'/api/config'),state=await health.json();if(!health.ok||!state.ready)return;
   $('notify-fields').disabled=false;$('notify-status').textContent='Choose your tickets below. We will send a confirmation email before activating alerts.';
  }catch(_){$('notify-status').textContent='Email alerts are being set up. Sign-up will open after sender verification.';}
 }
 $('notify-form').onsubmit=async event=>{
  event.preventDefault();if(!$('notify-form').reportValidity()||!apiURL)return;
  const kinds=[...document.querySelectorAll('#notify-form [name="alert-kind"]:checked')].map(input=>input.value);
  if(!kinds.length){$('notify-status').textContent='Choose at least one alert type.';return;}
  const payload={email:$('notify-email').value.trim(),consent:$('notify-consent').checked,website:$('notify-website').value,preferences:{scope:'watchlist',cadence:'updates',performance_date:$('notify-date').value,section:$('notify-section').value,row:Number($('notify-row').value),seat_mask:$('notify-mask').value,min_percent:Number($('notify-discount').value),kinds}};
  $('notify-submit').disabled=true;$('notify-status').textContent='Sending your confirmation email…';
  try{
   const response=await fetch(apiURL+'/api/subscribe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}),data=await response.json();
   if(!response.ok)throw new Error(data.error||'Could not request confirmation. Please try again later.');
   $('notify-email').value='';$('notify-status').textContent='Check your inbox and spam folder, open the email, then confirm. Alerts are not active until you confirm your email.';
  }catch(error){$('notify-status').textContent=error.message;}finally{$('notify-submit').disabled=false;}
 };
 setup();
})();
