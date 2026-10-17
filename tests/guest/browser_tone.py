"""Generate a browser Web Audio reference tone for physical host capture."""
import argparse
import json
from browser_h264 import CDP, get

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--port", type=int, default=9222)
parser.add_argument("--seconds", type=int, default=15)
args = parser.parse_args()
if not 1 <= args.seconds <= 20:
    parser.error("Duration must be between one and twenty seconds")
target = next(t for t in get(args.port, "/json/list") if t["type"] == "page")
connection = CDP(target["webSocketDebuggerUrl"], args.port)
expression = """(async()=>{
    for(const video of document.querySelectorAll('video'))video.pause();
    const ctx=new AudioContext(),oscillator=ctx.createOscillator(),gain=ctx.createGain();
    oscillator.frequency.value=660;gain.gain.value=0;
    oscillator.connect(gain).connect(ctx.destination);await ctx.resume();
    const start=ctx.currentTime;
    gain.gain.setValueAtTime(0,start);
    gain.gain.linearRampToValueAtTime(.25,start+.01);
    gain.gain.setValueAtTime(.25,start+SECONDS-.01);
    gain.gain.linearRampToValueAtTime(0,start+SECONDS);
    oscillator.start(start);oscillator.stop(start+SECONDS);
    await new Promise(resolve=>setTimeout(resolve,SECONDS*1000+100));
    const result={sampleRate:ctx.sampleRate,frequency:660,seconds:SECONDS,
                  elapsed:ctx.currentTime-start,state:ctx.state};
    await ctx.close();return result;
})()""".replace("SECONDS", str(args.seconds))
result = connection.call("Runtime.evaluate", {
    "expression": expression, "returnByValue": True,
    "awaitPromise": True, "userGesture": True,
})
if "exceptionDetails" in result:
    raise RuntimeError(result["exceptionDetails"])
print("BROWSER_TONE_OK " + json.dumps(result["result"]["value"]))
