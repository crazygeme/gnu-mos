"""Validate GPU decoding and frame downloads across Chromium decoder sessions."""

import argparse
import base64
import hashlib
import json
import os
import socket
import struct
import subprocess
import urllib.request
import urllib.parse
class CDP:
    def __init__(self, url, port):
        self.s = socket.create_connection(('127.0.0.1', port), 10)
        self.s.settimeout(30)
        self.buffer = b''
        self.sequence = 0
        self.events = []
        key = base64.b64encode(os.urandom(16)).decode()
        path = urllib.parse.urlsplit(url).path
        self.s.sendall((f'GET {path} HTTP/1.1\r\nHost: localhost:{port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n').encode())
        while b'\r\n\r\n' not in self.buffer:
            self.buffer += self.s.recv(4096)
        header, self.buffer = self.buffer.split(b'\r\n\r\n', 1)
        assert header.split(b'\r\n', 1)[0].split()[1] == b'101', header
        expected = base64.b64encode(hashlib.sha1((key+'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest())
        assert expected in header
    def read(self, size):
        while len(self.buffer) < size:
            part = self.s.recv(max(4096, size-len(self.buffer)))
            if not part: raise EOFError('DevTools connection closed')
            self.buffer += part
        result, self.buffer = self.buffer[:size], self.buffer[size:]
        return result
    def send(self, data, opcode=1):
        mask = os.urandom(4)
        size = len(data)
        header = bytes([0x80|opcode, 0x80|(size if size < 126 else 126 if size < 65536 else 127)])
        if size >= 126: header += struct.pack('!H' if size < 65536 else '!Q',size)
        self.s.sendall(header+mask+bytes(v^mask[i%4] for i,v in enumerate(data)))
    def receive(self):
        output=b''
        while True:
            a,b=self.read(2); size=b&127
            if size==126:size=struct.unpack('!H',self.read(2))[0]
            if size==127:size=struct.unpack('!Q',self.read(8))[0]
            mask=self.read(4) if b&128 else None
            data=self.read(size)
            if mask:data=bytes(v^mask[i%4] for i,v in enumerate(data))
            if a&15==9:self.send(data,10);continue
            if a&15==8:raise EOFError('DevTools closed')
            output+=data
            if a&128:return json.loads(output)
    def call(self, method, params=None):
        self.sequence+=1
        self.send(json.dumps({'id':self.sequence,'method':method,'params':params or {}}).encode())
        while True:
            result=self.receive()
            if result.get('id')==self.sequence:
                if 'error' in result:raise RuntimeError(result['error'])
                return result.get('result',{})
            self.events.append(result)
def get(port,path):
    return json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}{path}',timeout=10))


def decode_hex_dump(data):
    return bytes.fromhex("".join(
        line.split(": ", 1)[1].split("  ", 1)[0].replace(" ", "")
        for line in data.strip().splitlines()
    ))


def main():
    parser = argparse.ArgumentParser(description="Validate repeated H.264 hardware decoding through Chromium DevTools.")
    parser.add_argument("input", help="H.264 MP4 validation fixture")
    parser.add_argument("--port", type=int, default=9222, help="Local DevTools port")
    parser.add_argument("--loops", type=int, default=3, help="Decoder sessions to validate")
    parser.add_argument("--frames", type=int, default=10, help="Frames per decoder session")
    args = parser.parse_args()
    if args.loops < 1 or args.frames < 1:
        parser.error("Loop and frame counts must be positive")
    fixture = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0", "-show_packets",
        "-show_streams", "-show_data", "-of", "json", args.input,
    ]))
    stream = fixture["streams"][0]
    assert stream["codec_name"] == "h264"
    description = decode_hex_dump(stream["extradata"])
    codec = "avc1." + description[1:4].hex()
    packets = fixture["packets"][:args.frames]
    assert len(packets) == args.frames
    chunks = [{
        "type": "key" if "K" in packet["flags"] else "delta",
        "timestamp": round(float(packet["pts_time"]) * 1000000),
        "data": base64.b64encode(decode_hex_dump(packet["data"])).decode(),
    } for packet in packets]
    config = {
        "codec": codec, "codedWidth": stream["width"], "codedHeight": stream["height"],
        "hardwareAcceleration": "prefer-hardware",
        "description": base64.b64encode(description).decode(),
    }
    reference = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", args.input, "-frames:v", str(args.frames),
        "-pix_fmt", "rgba", "-f", "rawvideo", "-",
    ])
    width, height = stream["width"], stream["height"]
    frame_size = width * height * 4
    assert len(reference) == frame_size * args.frames
    points = [(width * x // 14, height * y // 10)
              for y in range(1, 10) for x in range(1, 14)]
    expected = [[reference[frame * frame_size + (y * width + x) * 4 + channel]
                 for x, y in points for channel in range(3)]
                for frame in range(args.frames)]
    target = next(item for item in get(args.port, "/json/list") if item["type"] == "page")
    connection = CDP(target["webSocketDebuggerUrl"], args.port)
    try:
        connection.call("Media.enable")
        expression = """(async()=>{
            let decoded=0,downloaded=0;const samples=[],points=POINTS;
            const errors=[],work=[],config=CONFIG;
            config.description=Uint8Array.from(atob(config.description),x=>x.charCodeAt(0));
            const supported=await VideoDecoder.isConfigSupported(config);
            if(!supported.supported)throw new Error('Hardware H.264 configuration is unsupported');
            const decoder=new VideoDecoder({output:f=>{
                decoded++;
                const canvas=new OffscreenCanvas(f.displayWidth,f.displayHeight);
                const context=canvas.getContext('2d');context.drawImage(f,0,0);
                const drawn=context.getImageData(0,0,canvas.width,canvas.height).data;
                const sample=(data,stride)=>points.flatMap(([x,y])=>Array.from(data.subarray(y*stride+x*4,y*stride+x*4+3)));
                const rendered=sample(drawn,canvas.width*4);
                const options={format:'RGBA'},data=new Uint8Array(f.allocationSize(options));
                work.push(f.copyTo(data,options).then(layout=>{
                    downloaded++;samples.push({timestamp:f.timestamp,rendered,
                        copied:sample(data.subarray(layout[0].offset),layout[0].stride)});
                }).finally(()=>f.close()));
            },error:e=>errors.push(String(e))});
            decoder.configure(config);
            for(const c of CHUNKS){c.data=Uint8Array.from(atob(c.data),x=>x.charCodeAt(0));decoder.decode(new EncodedVideoChunk(c))}
            try{await decoder.flush();await Promise.all(work)}catch(e){errors.push(String(e))}
            if(decoder.state!=='closed')decoder.close();
            return {decoded,downloaded,errors,samples};
        })()""".replace("CONFIG", json.dumps(config)).replace("CHUNKS", json.dumps(chunks)).replace("POINTS", json.dumps(points))
        results = []
        for _ in range(args.loops):
            connection.events.clear()
            response = connection.call("Runtime.evaluate", {
                "expression": expression, "returnByValue": True, "awaitPromise": True,
            })
            assert "exceptionDetails" not in response, response
            result = response["result"]["value"]
            assert result["decoded"] == result["downloaded"] == args.frames, result
            assert not result["errors"], result
            comparisons = []
            for sample, software in zip(sorted(result.pop("samples"), key=lambda item: item["timestamp"]), expected):
                comparison = {"timestamp": sample["timestamp"]}
                for operation in ("rendered", "copied"):
                    actual = sample[operation]
                    assert len(actual) == len(software)
                    error = sum(abs(a - b) for a, b in zip(actual, software)) / len(software)
                    comparison[operation + "MeanError"] = round(error, 4)
                    assert error <= 8, comparison
                comparisons.append(comparison)
            result["pixelComparisons"] = comparisons
            properties = [prop for event in connection.events
                          if event["method"] == "Media.playerPropertiesChanged"
                          for prop in event["params"]["properties"]]
            assert {"name": "kVideoDecoderName", "value": "VaapiVideoDecoder"} in properties, properties
            assert {"name": "kIsPlatformVideoDecoder", "value": "true"} in properties, properties
            results.append(result)
        print(json.dumps({"decoder": "VaapiVideoDecoder", "sessions": results}, indent=2))
    finally:
        connection.s.close()


if __name__ == "__main__":
    main()
