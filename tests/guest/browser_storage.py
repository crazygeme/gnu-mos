"""Validate HTTPS, JavaScript, Canvas, and browser restart through local CDP."""
import argparse
import json
import time

from browser_h264 import CDP, get

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--port', type=int, default=19222)
parser.add_argument('--close', action='store_true')
args = parser.parse_args()
page = next(item for item in get(args.port, '/json/list') if item['type'] == 'page')
connection = CDP(page['webSocketDebuggerUrl'], args.port)
connection.call('Page.enable')
result = connection.call('Page.navigate', {'url': 'https://example.com/'})
assert not result.get('errorText'), result
for _ in range(60):
    result = connection.call('Runtime.evaluate', {
        'expression': 'JSON.stringify({url:location.href,ready:document.readyState,title:document.title,secure:isSecureContext})',
        'returnByValue': True,
    })
    state = json.loads(result['result']['value'])
    if state['url'].startswith('https://example.com/') and state['ready'] == 'complete':
        break
    time.sleep(.5)
assert state['secure'] and 'Example Domain' in state['title'], state
result = connection.call('Runtime.evaluate', {
    'expression': '''(async()=>{
        const canvas=document.createElement('canvas');canvas.width=120;canvas.height=80;
        const ctx=canvas.getContext('2d');ctx.fillStyle='rgb(17,34,51)';ctx.fillRect(0,0,120,80);
        document.body.prepend(canvas);await new Promise(requestAnimationFrame);
        return {javascript:6*7,pixel:Array.from(ctx.getImageData(20,20,1,1).data),png:canvas.toDataURL().startsWith('data:image/png;base64,')};
    })()''',
    'awaitPromise': True, 'returnByValue': True,
})
assert 'exceptionDetails' not in result, result
value = result['result']['value']
assert value == {'javascript': 42, 'pixel': [17, 34, 51, 255], 'png': True}, value
print(json.dumps({'https': state, **value}, ensure_ascii=False))
if args.close:
    try:
        connection.call('Browser.close')
    except EOFError:
        pass
connection.s.close()
