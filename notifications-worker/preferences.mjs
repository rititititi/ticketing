// Price-alert preferences only; no screenshot text or user input becomes executable code.
export const SECTIONS=new Set([...Array.from({length:20},(_,i)=>'F'+(i+1)),...Array.from({length:7},(_,i)=>'T0'+(i+1)),...Array.from({length:7},(_,i)=>'T'+(i+11)),...[[101,114],[201,210],[301,322],[401,424]].flatMap(([a,b])=>Array.from({length:b-a+1},(_,i)=>String(a+i)))]);
export function validatePreferences(input){
 if(!input||typeof input!=='object')throw new Error('Choose your ticket preferences / 请选择票源偏好');
 const scope=input.scope||'watchlist';if(scope!=='watchlist')throw new Error('Invalid alert scope');
 const cadence=input.cadence||'updates';if(!['daily','updates'].includes(cadence))throw new Error('Choose daily or new-update alerts');
 const min_percent=input.min_percent??10;if(!Number.isInteger(min_percent)||min_percent<0||min_percent>90)throw new Error('Choose a discount between 0 and 90%');
 const kinds=input.kinds??['listing_drop','below_median'];if(!Array.isArray(kinds)||!kinds.length||kinds.some(k=>!['listing_drop','below_median'].includes(k)))throw new Error('Choose at least one supported alert type');
 const result={scope,cadence,min_percent,kinds:[...new Set(kinds)]};
 if(scope==='watchlist'){
  if(!['2027-01-15','2027-01-16'].includes(input.performance_date))throw new Error('Choose the performance date');
  const section=String(input.section||'').toUpperCase();if(!SECTIONS.has(section))throw new Error('Choose a valid section');
  const row=Number(input.row);if(!Number.isInteger(row)||row<1||row>99)throw new Error('Use a numeric row from 1 to 99');
  if(typeof input.seat_mask!=='string'||!/^[0-9]?X$/.test(input.seat_mask))throw new Error('Choose the printed seat prefix');
  Object.assign(result,{performance_date:input.performance_date,section,row,seat_mask:input.seat_mask});
 }
 return result;
}
export function matches(preferences,event){
 if(!preferences.kinds.includes(event.kind)||!Number.isFinite(event.percent)||event.percent<preferences.min_percent)return false;
 if(preferences.scope==='all')return true;
 return event.performance_date===preferences.performance_date&&event.section===preferences.section&&event.seat_mask===preferences.seat_mask&&/^\d{1,2}$/.test(String(event.row))&&Math.abs(Number(event.row)-preferences.row)<=3;
}
export function isDue(subscriber,now){const p=JSON.parse(subscriber.preferences);return p.cadence==='updates'||now-subscriber.last_sent_at>=24*60*60*1000;}
