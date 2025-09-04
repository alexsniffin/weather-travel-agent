#!/usr/bin/env python3
"""
Gradio UI with Google Maps embeddings for Weather Travel Agent w/ A2A
"""
from __future__ import annotations

import os
import uuid
import urllib.parse
from typing import Dict, List, Optional, Tuple

import gradio as gr
import httpx
from dotenv import load_dotenv

load_dotenv()

A2A_URL = os.getenv("A2A_URL", "http://127.0.0.1:8000/a2a/")
MAPS_EMBED_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
UI_PORT = int(os.getenv("UI_PORT", "7860"))

def _pick_icon_code(summary: str) -> str:
    s = (summary or "").lower()
    if "thunder" in s or "storm" in s:
        return "11d"
    if "drizzle" in s:
        return "09d"
    if "rain" in s or "shower" in s:
        return "10d"
    if "snow" in s or "sleet" in s or "flurries" in s:
        return "13d"
    if any(x in s for x in ["mist", "fog", "haze", "smoke"]):
        return "50d"
    if "clear" in s:
        return "01d"
    if "cloud" in s:
        return "03d"
    return "03d"

def _build_map_iframe_html(origin: str, destination: str, stops: List[Dict]) -> str:
    """Builds a Google Maps iframe with waypoints. Defaults to NYC if no inputs."""
    if not MAPS_EMBED_API_KEY:
        return (
            "<div style='padding:12px;border:1px solid #444;border-radius:12px;color:#ddd;'>"
            "<b>Map unavailable:</b> set <code>GOOGLE_MAPS_EMBED_API_KEY</code> or <code>GOOGLE_API_KEY</code>."
            "</div>"
        )

    if not origin and not destination:
        # Default to NYC
        base = "https://www.google.com/maps/embed/v1/place"
        params = f"key={MAPS_EMBED_API_KEY}&q=New+York+City,NY"
        return (
            f"<iframe width='100%' height='420' style='border:0;border-radius:12px;' "
            f"loading='lazy' allowfullscreen referrerpolicy='no-referrer-when-downgrade' "
            f"src='{base}?{params}'></iframe>"
        )

    wpts = []
    for s in (stops or [])[:20]:
        lat, lon = s.get("lat"), s.get("lon")
        if lat is None or lon is None:
            continue
        wpts.append(f"{lat:.5f},{lon:.5f}")

    origin_q = urllib.parse.quote_plus(origin or "")
    dest_q = urllib.parse.quote_plus(destination or "")
    waypoints_q = urllib.parse.quote_plus("|".join(wpts)) if wpts else ""
    base = "https://www.google.com/maps/embed/v1/directions"
    params = f"key={MAPS_EMBED_API_KEY}&mode=driving&origin={origin_q}&destination={dest_q}"
    if waypoints_q:
        params += f"&waypoints={waypoints_q}"

    return (
        f"<iframe width='100%' height='420' style='border:0;border-radius:12px;' "
        f"loading='lazy' allowfullscreen referrerpolicy='no-referrer-when-downgrade' "
        f"src='{base}?{params}'></iframe>"
    )

def _build_forecasts_html(forecasts: List[Dict]) -> str:
    """Render weather forecast cards in a dark theme style."""
    if not forecasts:
        return ""
    cards = []
    for f in forecasts:
        name = f.get("name", "")
        summary = f.get("summary", "")
        code = _pick_icon_code(summary)
        icon_url = f"https://openweathermap.org/img/wn/{code}@2x.png"
        cards.append(
            f"""
            <div class="wx-card">
              <div class="wx-card-top">
                <img src="{icon_url}" alt="{summary}" width="36" height="36" />
                <div class="wx-name">{name}</div>
              </div>
              <div class="wx-summary">{summary}</div>
            </div>
            """
        )
    styles = """
    <style>
      .wx-wrap { display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr));
                 gap:12px; margin-top:12px; }
      .wx-card { border:1px solid #333; border-radius:8px; padding:10px; background:#1f2937;
                 box-shadow:0 1px 2px rgba(0,0,0,.5); color:#f3f4f6; }
      .wx-card-top { display:flex; align-items:center; gap:8px; margin-bottom:6px; }
      .wx-name { font-weight:600; font-size:14px; }
      .wx-summary { font-size:13px; color:#d1d5db; line-height:1.3; }
    </style>"""
    return styles + f"<div class='wx-wrap'>{''.join(cards)}</div>"

def _extract_context_id(result: Dict) -> Optional[str]:
    return result.get("contextId") or result.get("context_id")

async def _call_a2a(message: str, context_id: Optional[str]) -> Tuple[str, Optional[Dict], Optional[str]]:
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/send",
        "params": {
            "message": {
                "message_id": f"msg_{uuid.uuid4().hex[:8]}",
                "role": "user",
                "parts": [{"kind": "text", "text": message}],
            }
        },
    }
    if context_id:
        payload["params"]["context_id"] = context_id

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(A2A_URL, json=payload)
        r.raise_for_status()
        resp = r.json()

    result = resp.get("result", {})
    parts = result.get("parts", [])
    reply_text, data_part = "", None
    for p in parts:
        if p.get("kind") == "text" and not reply_text:
            reply_text = p.get("text", "")
        elif p.get("kind") == "data" and data_part is None:
            data_part = p.get("data")
    new_ctx = _extract_context_id(result) or context_id
    return reply_text, data_part, new_ctx

with gr.Blocks(title="Travel Itinerary + Weather (Agent Demo w/ A2A)", theme="base") as demo:
    gr.Markdown(f"# Travel Itinerary + Weather (Agent Demo w/ A2A)\nBackend: `{A2A_URL}`")

    ctx_state = gr.State(value=None)

    with gr.Row():
        # Left column: chat
        with gr.Column(scale=1):
            chatbot = gr.Chatbot(height=600, label="Conversation")
            msg = gr.Textbox(
                placeholder="e.g., I'd like to travel from Chicago to Nashville",
                lines=2,
                label="Your message",
            )
            with gr.Row():
                send_btn = gr.Button("Send", variant="primary")
                clear_btn = gr.Button("Clear")

        # Right column: map above forecasts
        with gr.Column(scale=1):
            map_html = gr.HTML(value=_build_map_iframe_html("", "", []), label="Route Map")
            forecasts_html = gr.HTML(label="Forecasts")

    async def on_send(user_message: str, history: List[Tuple[str, str]], context_id: Optional[str]):
        try:
            reply, data, new_ctx = await _call_a2a(user_message, context_id)
            new_hist = (history or []) + [(user_message, reply or "(no reply)")]

            map_snippet = _build_map_iframe_html("", "", [])
            fc_snippet = ""
            if isinstance(data, dict):
                map_snippet = _build_map_iframe_html(
                    data.get("origin") or "", data.get("destination") or "", data.get("stops") or []
                )
                fc_snippet = _build_forecasts_html(data.get("forecasts") or [])

            return new_hist, "", map_snippet, fc_snippet, new_ctx
        except Exception as e:
            new_hist = (history or []) + [(user_message, f"Error calling A2A: {e}")]
            return new_hist, "", "", "", context_id

    send_btn.click(
        on_send,
        inputs=[msg, chatbot, ctx_state],
        outputs=[chatbot, msg, map_html, forecasts_html, ctx_state],
    )
    msg.submit(
        on_send,
        inputs=[msg, chatbot, ctx_state],
        outputs=[chatbot, msg, map_html, forecasts_html, ctx_state],
    )

    def on_clear():
        return [], "", _build_map_iframe_html("", "", []), "", None

    clear_btn.click(on_clear, outputs=[chatbot, msg, map_html, forecasts_html, ctx_state])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=UI_PORT)
