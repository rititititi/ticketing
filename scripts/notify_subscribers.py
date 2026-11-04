"""Notify the private delivery Worker after publication. Never log secrets or subscriber data."""
import os,urllib.request,urllib.error
url=os.environ.get('NOTIFICATIONS_URL','').strip().rstrip('/')
secret=os.environ.get('NOTIFICATIONS_PUBLISH_SECRET','')
if not url or not secret:
    print('Email notifications are not configured; website publication is unaffected.')
else:
    from urllib.parse import urlparse
    parsed=urlparse(url)
    if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password:raise ValueError('Use the HTTPS notifications Worker URL')
    request=urllib.request.Request(url+'/api/internal/publish',data=b'{}',method='POST',headers={'Authorization':'Bearer '+secret,'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(request,timeout=30) as response:print('Subscriber delivery queued. Worker status:',response.status)
    except urllib.error.HTTPError as error:
        print('Subscriber delivery was not queued; HTTP',error.code,'. The Worker retry schedule will check again.')
    except Exception:
        print('Subscriber delivery endpoint unavailable. The Worker retry schedule will check again.')
