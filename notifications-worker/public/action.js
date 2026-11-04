'use strict';
const unsubscribe=location.pathname==='/unsubscribe',token=new URLSearchParams(location.search).get('t'),button=document.getElementById('confirm'),status=document.getElementById('status');
document.getElementById('title').textContent=unsubscribe?'Unsubscribe / 退订':'Confirm email alerts / 确认邮件提醒';
document.getElementById('description').textContent=unsubscribe?'Press below to stop alerts and remove your email and preferences. / 点击下方按钮停止提醒，并删除邮箱及偏好。':'Press below to confirm your email and activate matching ticket alerts. Existing offers will not be sent as new alerts. / 点击下方按钮确认邮箱，启用匹配票源提醒。已有报价不会作为新提醒发送。';
button.textContent=unsubscribe?'Unsubscribe / 确认退订':'Confirm email alerts / 确认订阅';
if(!token){button.disabled=true;status.textContent='This link is incomplete. Return to the site to sign up again. / 链接不完整，请返回网站重新申请。';}
button.onclick=async()=>{button.disabled=true;status.textContent='Working… / 正在处理…';try{const response=await fetch('/api/'+(unsubscribe?'unsubscribe':'confirm'),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token,confirmed:true})}),data=await response.json();if(!response.ok)throw new Error(data.error||'Please try again / 请重试');status.textContent=data.message;button.hidden=true;history.replaceState(null,'',location.pathname);}catch(error){status.textContent=error.message;button.disabled=false;}};
