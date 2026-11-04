"""Generate evidence-backed website alerts. No external messages or subscriber data."""
import hashlib,json,re
from collections import defaultdict
from statistics import median
from pricing import comparable,seat_mask

def key(ticket):return (ticket.get('event_id') or ticket.get('concert'),ticket.get('performance_date'),ticket.get('section'),ticket.get('currency'),seat_mask(ticket.get('seat_as_printed')))
def eligible(t):
    # Reuse the matcher, including its strict date, row, stock and mask requirements.
    return comparable(t,{**t,'id':'eligibility-probe:'+t['id']})
def identifier(t):
    printed=str(t.get('printed_identifier') or '').strip()
    if not printed:
        # Earlier drafts omitted the ID cell but retained its explicit leading OCR column.
        match=re.match(r'^\s*([A-Za-z0-9_-]+)\s*\|\s*(?:202[67]\d{4}|202[67][/.]\d{1,2}[/.]\d{1,2})(?!\d)',t.get('raw_ocr',''))
        if match:printed=match[1]
    return re.sub(r'\s+','',printed).lower().removeprefix('序号')
def event_id(parts):return hashlib.sha256(json.dumps(parts,ensure_ascii=False,sort_keys=True).encode()).hexdigest()[:24]

def build_feed(catalog):
    current=[t for t in catalog['tickets'] if eligible(t)];groups=defaultdict(list);by_source=defaultdict(list);sources={s['source_index']:s for s in catalog['sources']}
    for t in current:groups[key(t)].append(t)
    for t in catalog['tickets']:by_source[t['source_index']].append(t)
    previous=defaultdict(list)
    for source in catalog['sources']:
        if source.get('superseded_by'):previous[source['superseded_by']].append(source['source_index'])
    events=[];seen_comparables=set()
    # Prefer recently imported evidence when several screenshots repeat an observation.
    for ticket in sorted(current,key=lambda t:(t.get('batch_id',''),t['source_index'],t['id']),reverse=True):
        quote_key=(*key(ticket),int(ticket['row']),ticket['price']);older=[]
        listing=identifier(ticket)
        if listing:
            for source_index in previous[ticket['source_index']]:
                matches=[old for old in by_source[source_index] if identifier(old)==listing]
                if len(matches)!=1:continue
                old=matches[0]
                # Same explicit listing ID, same attributes and reviewed version relationship.
                if old.get('sold') or not isinstance(old.get('price'),(int,float)) or isinstance(old['price'],bool) or old['price']<=0:continue
                if key(old)==key(ticket) and str(old.get('row'))==str(ticket['row']):older.append(old)
        date=ticket.get('catalog_review',{}).get('reviewed_at') or ticket.get('batch_id') or sources[ticket['source_index']].get('published_at') or ''
        common=dict(ticket_id=ticket['id'],source_index=ticket['source_index'],physical_row=ticket['physical_row'],section=ticket['section'],row=ticket['row'],seat_mask=seat_mask(ticket['seat_as_printed']),performance_date=ticket['performance_date'],price=ticket['price'],currency=ticket['currency'],published_at=date,provisional=ticket.get('extraction_status')=='ocr_candidate')
        if older:
            old=min(older,key=lambda t:t['price'])
            if ticket['price']<old['price']:
                events.append(common|dict(id=event_id(['listing_drop',ticket['id'],old['id'],ticket['price'],old['price']]),kind='listing_drop',previous_price=old['price'],previous_ticket_id=old['id'],previous_source_index=old['source_index'],percent=round((1-ticket['price']/old['price'])*100),basis='Explicit listing ID and linked spreadsheet version; physical ticket identity still needs supplier confirmation'))
                seen_comparables.add(quote_key);continue
        if quote_key in seen_comparables:continue
        observations={}
        for peer in groups[key(ticket)]:
            if not comparable(ticket,peer) or (int(peer['row'])==int(ticket['row']) and peer['price']==ticket['price']):continue
            observations.setdefault((int(peer['row']),peer['price']),peer)
        peers=list(observations.values())
        if len(peers)<2:continue
        benchmark=median(p['price'] for p in peers)
        if ticket['price']>=benchmark:continue
        seen_comparables.add(quote_key)
        events.append(common|dict(id=event_id(['below_median',quote_key,ticket['price'],benchmark]),kind='below_median',median=benchmark,peer_count=len(peers),peer_ids=[p['id'] for p in sorted(peers,key=lambda p:p['price'])],percent=round((1-ticket['price']/benchmark)*100),basis='Same performance, section and seat mask, numeric rows within ±3; repeated identical row/price observations counted once'))
    events.sort(key=lambda e:(e['published_at'][:10],e['kind']=='listing_drop',e['percent'],e['id']),reverse=True)
    return dict(schema_version=1,events=events,counts={kind:sum(e['kind']==kind for e in events) for kind in ['listing_drop','below_median']},note='Supplier quotes and OCR evidence require confirmation. Comparable offers do not establish a historical drop for the same physical ticket.')

def write_derived(catalog,root):
    from pathlib import Path
    from ticket_reviews import write_review_index
    write_review_index(catalog,root)
    folder=Path(root)/'data';(folder/'site-updates.json').write_text(json.dumps(build_feed(catalog),ensure_ascii=False,separators=(',',':')))
