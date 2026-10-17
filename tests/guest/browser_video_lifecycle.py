"""Validate repeated HTTPS video playback and tab closure through local CDP."""
import argparse
import json
import time

from browser_h264 import CDP, get

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--port', type=int, default=19222)
parser.add_argument('--loops', type=int, default=30)
parser.add_argument('--seconds', type=float, default=5)
args = parser.parse_args()
if args.loops < 1 or args.seconds <= 0:
    parser.error('Loop count and playback duration must be positive')

browser = CDP(get(args.port, '/json/version')['webSocketDebuggerUrl'], args.port)
home = next(page for page in get(args.port, '/json/list')
            if page['type'] == 'page' and page['url'] == 'https://haokan.baidu.com/')
connection = CDP(home['webSocketDebuggerUrl'], args.port)
urls = connection.call('Runtime.evaluate', {
    'expression': '[...document.querySelectorAll("a[href]")].map(a=>a.href).filter(u=>u.includes("haokan.baidu.com/v?")).slice(0,8)',
    'returnByValue': True,
})['result']['value']
connection.s.close()
assert urls, 'Video links are unavailable'

expression = '''(()=>{
    const video=document.querySelector('video');
    if(!video)return null;
    video.muted=false;video.volume=1;video.play().catch(()=>{});
    return {url:location.href,secure:isSecureContext,time:video.currentTime,
            ready:video.readyState,paused:video.paused,
            muted:video.muted,volume:video.volume,
            audioDecoded:video.webkitAudioDecodedByteCount,
            frames:video.getVideoPlaybackQuality().totalVideoFrames,
            error:video.error&&video.error.message};
})()'''
try:
    for iteration in range(args.loops):
        target = browser.call('Target.createTarget', {'url': urls[iteration % len(urls)]})['targetId']
        connection = None
        try:
            page = next(page for page in get(args.port, '/json/list') if page['id'] == target)
            connection = CDP(page['webSocketDebuggerUrl'], args.port)
            deadline = time.monotonic() + 45
            first = None
            while time.monotonic() < deadline:
                response = connection.call('Runtime.evaluate', {
                    'expression': expression, 'returnByValue': True, 'userGesture': True,
                })
                assert 'exceptionDetails' not in response, response
                state = response['result'].get('value')
                if state:
                    assert state['error'] is None, state
                    if state['time'] > 0 and state['frames'] > 0 and first is None:
                        first = state
                    if first and state['time'] - first['time'] >= args.seconds:
                        assert state['secure'] and not state['paused'], state
                        assert state['frames'] > first['frames'], state
                        assert not state['muted'] and state['volume'] == 1, state
                        assert state['audioDecoded'] > first['audioDecoded'], state
                        print(json.dumps({'iteration': iteration + 1, 'start': first, 'end': state}), flush=True)
                        break
                time.sleep(.5)
            else:
                raise AssertionError(('Video playback did not advance', iteration + 1, state))
        finally:
            if connection:
                connection.s.close()
            assert browser.call('Target.closeTarget', {'targetId': target})['success']
        alive = CDP(home['webSocketDebuggerUrl'], args.port)
        assert alive.call('Runtime.evaluate', {'expression': '6*7', 'returnByValue': True})['result']['value'] == 42
        alive.s.close()
    print(json.dumps({'passed': args.loops, 'playback_seconds_per_loop': args.seconds}), flush=True)
finally:
    browser.s.close()
