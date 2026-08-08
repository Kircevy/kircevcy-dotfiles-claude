#!/usr/bin/env python3
"""Anthropic Messages API -> OpenAI chat/completions translation proxy.

Bridges Claude Code (Anthropic-native protocol) to OpenCode Go's
OpenAI-compatible endpoint, so any Go-plan model (e.g. deepseek-v4-pro)
can be used inside Claude Code. Zero Python dependencies (stdlib only;
uses curl as the upstream HTTP client because Cloudflare fingerprint-blocks
python-urllib).

Usage: deepseek-go-proxy.py [port]   (default port 18085)
API key is read from $OPENCODE_GO_API_KEY, falling back to
~/.local/share/opencode/auth.json (provider "opencode") like the zen proxy.
"""

import json
import os
import select
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

UPSTREAM = "https://opencode.ai/zen/go/v1/chat/completions"
DEFAULT_PORT = 18085
MODEL = os.environ.get("MODEL", "deepseek-v4-flash")


def zen_key():
    key = os.environ.get("OPENCODE_GO_API_KEY", "").strip()
    if key:
        return key
    auth = json.loads(
        (Path.home() / ".local/share/opencode/auth.json").read_text()
    )
    return auth["opencode"]["key"]


def curl_upstream(payload_bytes, first_byte_timeout=45):
    """POST to upstream via curl. Waits for the HTTP status line with a
    first-byte deadline so a stalled upstream fails fast instead of leaving
    the client spinning (curl --max-time alone would wait minutes)."""
    key = zen_key()
    cmd = [
        "curl", "-sS", "-N", "-D", "-", "-o", "-",
        "-X", "POST", UPSTREAM,
        "-H", f"Authorization: Bearer {key}",
        "-H", "Content-Type: application/json",
        "-H", "User-Agent: curl/8.5.0",
        "--max-time", "590",
        "--data-binary", "@-",
    ]
    proc = subprocess.Popen(
        cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, bufsize=0,
    )
    proc.stdin.write(payload_bytes)
    proc.stdin.close()
    status = None
    deadline = time.monotonic() + first_byte_timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            proc.kill()
            proc.wait()
            raise RuntimeError(f"upstream timeout: no response in {first_byte_timeout}s")
        r, _, _ = select.select([proc.stdout], [], [], min(remaining, 5))
        if not r:
            continue
        line = proc.stdout.readline()
        if not line:
            break
        if line in (b"\r\n", b"\n"):
            break
        if line.startswith(b"HTTP/"):
            status = int(line.split()[1])
    if status is None:
        raise RuntimeError("upstream returned no HTTP status")
    return status, proc


def anthropic_to_openai(body):
    """Convert an Anthropic /v1/messages request to OpenAI chat/completions."""
    model = body.get("model", MODEL)
    out = {"model": model, "stream": bool(body.get("stream"))}

    # The go endpoint makes every model "think" first by default (the whole
    # output budget can go to hidden reasoning, which this proxy drops) —
    # so Claude Code appears to freeze for tens of seconds. Disable thinking
    # for flash (fast chat model); keep it for the pro/plan models that exist
    # for deep planning. Opt out per-run with THINK=1.
    if not os.environ.get("THINK") and model in ("deepseek-v4-flash", "deepseek-v4-flash-free"):
        out["thinking"] = {"type": "disabled"}

    messages = []
    system_parts = []
    if body.get("system"):
        sys_content = body["system"]
        if isinstance(sys_content, str):
            system_parts.append(sys_content)
        else:
            system_parts.extend(b.get("text", "") for b in sys_content if b.get("type") == "text")

    for msg in body.get("messages", []):
        role = msg["role"]
        content = msg.get("content")
        if role == "system":
            if isinstance(content, str):
                system_parts.append(content)
            else:
                system_parts.extend(b.get("text", "") for b in content if b.get("type") == "text")
            continue
        if isinstance(content, str):
            messages.append({"role": role, "content": content})
            continue
        if role == "user":
            user_parts = []
            for block in content:
                if block.get("type") == "text":
                    user_parts.append({"type": "text", "text": block.get("text", "")})
                elif block.get("type") == "tool_result":
                    tool_text = block.get("content", "")
                    if isinstance(tool_text, list):
                        tool_text = "".join(
                            b.get("text", "") for b in tool_text if b.get("type") == "text"
                        )
                    tool_msg = {
                        "role": "tool",
                        "tool_call_id": block.get("tool_use_id", ""),
                        "content": tool_text,
                    }
                    if block.get("is_error"):
                        tool_msg["content"] = "[tool error]\n" + tool_text
                    messages.append(tool_msg)
                elif block.get("type") == "image":
                    src = block.get("source", {})
                    if src.get("type") == "base64":
                        user_parts.append(
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{src.get('media_type', 'image/png')};base64,{src.get('data', '')}"
                                },
                            }
                        )
            if user_parts:
                messages.append({"role": "user", "content": user_parts})
        elif role == "assistant":
            parts = []
            tool_calls = []
            for block in content:
                if block.get("type") == "text" and block.get("text"):
                    parts.append({"type": "text", "text": block["text"]})
                elif block.get("type") == "tool_use":
                    tool_calls.append(
                        {
                            "id": block.get("id", f"call_{len(tool_calls)}"),
                            "type": "function",
                            "function": {
                                "name": block.get("name", ""),
                                "arguments": json.dumps(block.get("input", {})),
                            },
                        }
                    )
            m = {"role": "assistant", "content": parts or ""}
            if tool_calls:
                m["tool_calls"] = tool_calls
            messages.append(m)

    # thinking handled above so it can't be clobbered by body passthrough below
    body_thinking = body.get("thinking")
    if body_thinking is not None:
        out["thinking"] = body_thinking

    if system_parts:
        out["system"] = "\n\n".join(system_parts)
    if messages:
        out["messages"] = messages

    if body.get("max_tokens"):
        out["max_tokens"] = body["max_tokens"]
    if body.get("temperature") is not None:
        out["temperature"] = body["temperature"]
    if body.get("top_p") is not None:
        out["top_p"] = body["top_p"]
    if body.get("stop_sequences"):
        out["stop"] = body["stop_sequences"]

    tools = []
    for t in body.get("tools", []):
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": t.get("name", ""),
                    "description": t.get("description", ""),
                    "parameters": t.get("input_schema", {"type": "object", "properties": {}}),
                },
            }
        )
    if tools:
        out["tools"] = tools
        tc = body.get("tool_choice")
        if tc:
            if isinstance(tc, dict) and tc.get("type") == "auto":
                out["tool_choice"] = "auto"
            elif isinstance(tc, dict) and tc.get("type") == "tool":
                out["tool_choice"] = {"type": "function", "function": {"name": tc.get("name", "")}}
            elif isinstance(tc, dict) and tc.get("type") == "any":
                out["tool_choice"] = "required"
            elif isinstance(tc, str) and tc in ("auto", "any", "none", "required"):
                out["tool_choice"] = tc
    return out


def stop_reason_from_openai(finish):
    return {
        "stop": "end_turn",
        "length": "max_tokens",
        "tool_calls": "tool_use",
        "function_call": "tool_use",
        "content_filter": "end_turn",
    }.get(finish, "end_turn")


def openai_to_anthropic(data):
    """Convert a non-streaming OpenAI chat/completions response to Anthropic."""
    choice = data.get("choices", [{}])[0]
    message = choice.get("message", {})
    content = []
    if message.get("content"):
        content.append({"type": "text", "text": message["content"]})
    for tc in (message.get("tool_calls") or []):
        fn = tc.get("function", {})
        try:
            inp = json.loads(fn.get("arguments", "{}"))
        except json.JSONDecodeError:
            inp = {}
        content.append(
            {
                "type": "tool_use",
                "id": tc.get("id", "toolu_1"),
                "name": fn.get("name", ""),
                "input": inp,
            }
        )
    usage = data.get("usage", {})
    return {
        "id": data.get("id", "msg_1"),
        "type": "message",
        "role": "assistant",
        "content": content,
        "model": data.get("model", MODEL),
        "stop_reason": stop_reason_from_openai(choice.get("finish_reason")),
        "stop_sequence": None,
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
        },
    }


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        # REQ access log is silent by default; set PROXY_VERBOSE=1 to enable.
        if os.environ.get("PROXY_VERBOSE"):
            sys.stderr.write("REQ %s %s\n" % (self.command, self.path))

    def _route(self):
        return urlparse(self.path).path

    def _send(self, code, obj):
        payload = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(payload)
        self.close_connection = True

    def do_GET(self):
        path = self._route()
        if path in ("/health", "/healthz"):
            self._send(200, {"ok": True})
        elif path == "/v1/models":
            self._send(200, {
                "data": [
                    {
                        "id": MODEL,
                        "object": "model",
                        "owned_by": "opencode",
                        "created": 1767225600,
                    }
                ],
                "object": "list",
            })
        else:
            self._send(404, {"error": {"message": "not found", "type": "not_found"}})

    def do_HEAD(self):
        path = self._route()
        if path == "/api/hello":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", "0")
            self.end_headers()
        else:
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.end_headers()

    def do_POST(self):
        path = self._route()
        if path == "/v1/messages":
            self.handle_messages()
        elif path == "/v1/messages/count_tokens":
            body = self._read_json()
            n = sum(len(m.get("content", "")) // 4 for m in body.get("messages", [])) if body else 0
            self._send(200, {"input_tokens": n})
        else:
            self._send(404, {"error": {"message": "not found", "type": "not_found"}})

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw or b"{}")

    def handle_messages(self):
        try:
            body = self._read_json()
            stream = bool(body.get("stream"))
            oai_body = anthropic_to_openai(body)
            payload = json.dumps(oai_body).encode()
            status, proc = curl_upstream(payload)
            if status >= 300:
                err = proc.stdout.read().decode(errors="replace")[:500]
                self._send(502, {"error": {"message": f"upstream {status}: {err}", "type": "upstream_error"}})
                return
            if not stream:
                data = json.loads(proc.stdout.read())
                proc.wait()
                self._send(200, openai_to_anthropic(data))
                return
            self._stream(proc)
        except Exception as e:  # noqa: BLE001 - boundary: must not crash the server
            self._send(500, {"error": {"message": str(e), "type": "internal_error"}})

    def _stream(self, proc):
        """Read OpenAI SSE from curl, translate each chunk to Anthropic SSE."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()

        def sse(event=None, data=None):
            if data is None:
                data = {}
            chunk = (f"event: {event}\n" if event else "") + "data: " + json.dumps(data) + "\n\n"
            self.wfile.write(chunk.encode())
            self.wfile.flush()

        message_id = "msg_proxy_1"
        input_tokens = 0
        tool_blocks = {}
        text_idx = None
        think_idx = None
        next_idx = 0
        emitted_start = False
        finish_reason = None

        def alloc_index():
            nonlocal next_idx
            i = next_idx
            next_idx += 1
            return i

        def close_text():
            nonlocal text_idx
            if text_idx is not None:
                sse("content_block_stop", {"type": "content_block_stop", "index": text_idx})
                text_idx = None

        def close_thinking():
            nonlocal think_idx
            if think_idx is not None:
                sse("content_block_stop", {"type": "content_block_stop", "index": think_idx})
                think_idx = None

        def close_tools():
            for i in sorted(tool_blocks):
                sse("content_block_stop", {"type": "content_block_stop", "index": tool_blocks[i]["idx"]})
            tool_blocks.clear()

        try:
            for raw in proc.stdout:
                if not raw:
                    continue
                line = raw.decode(errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if payload == "[DONE]":
                    break
                chunk = json.loads(payload)
                if chunk.get("usage"):
                    input_tokens = chunk["usage"].get("prompt_tokens", input_tokens)
                if not emitted_start:
                    sse("message_start", {
                        "type": "message_start",
                        "message": {
                            "id": message_id,
                            "type": "message",
                            "role": "assistant",
                            "content": [],
                            "model": chunk.get("model", MODEL),
                            "stop_reason": None,
                            "stop_sequence": None,
                            "usage": {"input_tokens": input_tokens, "output_tokens": 0},
                        },
                    })
                    emitted_start = True
                for choice in chunk.get("choices", []):
                    delta = choice.get("delta", {})
                    finish_reason = choice.get("finish_reason") or finish_reason
                    thinking = delta.get("reasoning_content")
                    if thinking:
                        if think_idx is None:
                            think_idx = alloc_index()
                            sse("content_block_start", {
                                "type": "content_block_start",
                                "index": think_idx,
                                "content_block": {"type": "thinking", "thinking": ""},
                            })
                        sse("content_block_delta", {
                            "type": "content_block_delta",
                            "index": think_idx,
                            "delta": {"type": "thinking_delta", "thinking": thinking},
                        })
                    if delta.get("content"):
                        if text_idx is None:
                            text_idx = alloc_index()
                            sse("content_block_start", {
                                "type": "content_block_start",
                                "index": text_idx,
                                "content_block": {"type": "text", "text": ""},
                            })
                        sse("content_block_delta", {
                            "type": "content_block_delta",
                            "index": text_idx,
                            "delta": {"type": "text_delta", "text": delta["content"]},
                        })
                    for tc in (delta.get("tool_calls") or []):
                        src = tc.get("index", 0)
                        if src not in tool_blocks:
                            idx = alloc_index()
                            tool_blocks[src] = {
                                "idx": idx,
                                "id": tc.get("id", f"toolu_{idx}"),
                                "name": tc.get("function", {}).get("name", ""),
                            }
                            sse("content_block_start", {
                                "type": "content_block_start",
                                "index": idx,
                                "content_block": {
                                    "type": "tool_use",
                                    "id": tool_blocks[src]["id"],
                                    "name": tool_blocks[src]["name"],
                                    "input": {},
                                },
                            })
                        args = tc.get("function", {}).get("arguments", "")
                        if args:
                            sse("content_block_delta", {
                                "type": "content_block_delta",
                                "index": tool_blocks[src]["idx"],
                                "delta": {"type": "input_json_delta", "partial_json": args},
                            })
                    if finish_reason:
                        close_thinking()
                        close_text()
                        close_tools()
                        sse("message_delta", {
                            "type": "message_delta",
                            "delta": {"stop_reason": stop_reason_from_openai(finish_reason)},
                            "usage": {"output_tokens": 0},
                        })
                        sse("message_stop", {"type": "message_stop"})
            if not finish_reason and emitted_start:
                close_thinking()
                close_text()
                close_tools()
                sse("message_delta", {
                    "type": "message_delta",
                    "delta": {"stop_reason": "end_turn"},
                    "usage": {"output_tokens": 0},
                })
                sse("message_stop", {"type": "message_stop"})
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            self.close_connection = True
            try:
                proc.stdout.close()
            except Exception:  # noqa: BLE001
                pass
            proc.wait()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
