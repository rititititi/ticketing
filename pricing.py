"""Comparable-ticket matching for a future opt-in alert service; no notifications are sent."""
import re
import math
from datetime import date

def seat_mask(value):
    text=re.sub(r'\s+','',str(value)).upper()
    match=re.fullmatch(r'([0-9]?X)(?:[（(][^()（）]*[）)]|#|号|番)?',text)
    return match[1] if match else None

def comparable(left,right):
    if left.get('id')==right.get('id'):return False
    for item in [left,right]:
        if item.get('sold') or item.get('superseded_by') or item.get('availability') in ['paid_in_source','locked_in_source']:return False
        try:date.fromisoformat(item.get('performance_date') or '')
        except ValueError:return False
        if not re.fullmatch(r'\d{1,2}',str(item.get('row',''))):return False
        if not isinstance(item.get('price'),(int,float)) or isinstance(item['price'],bool) or not math.isfinite(item['price']) or item['price']<=0:return False
        if item.get('section') in [None,'','UNRESOLVED']:return False
    if any(left.get(key)!=right.get(key) for key in ['performance_date','section','currency']):return False
    if (left.get('event_id') or left.get('concert'))!=(right.get('event_id') or right.get('concert')):return False
    mask=seat_mask(left.get('seat_as_printed'))
    return bool(mask and mask==seat_mask(right.get('seat_as_printed')) and abs(int(left['row'])-int(right['row']))<=3)
