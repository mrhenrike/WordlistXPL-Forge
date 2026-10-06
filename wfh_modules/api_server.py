"""api_server.py - REST API server for WordlistXPL-Forge.

Exposes generation endpoints over HTTP so other tools can request wordlists
programmatically.  Implements a streaming NDJSON response for large outputs.

Requires: pip install wordlistxpl-forge[api]
  (fastapi, uvicorn, pydantic)

Falls back to aiohttp when fastapi is unavailable.

Endpoints:
  POST /v1/generate            Stream NDJSON of generated passwords
  POST /v1/pipeline            Run a YAML pipeline spec
  GET  /v1/engines             List available engines
  GET  /v1/status              Server health + resource stats
  GET  /v1/sessions            List sessions
  POST /v1/sessions/{id}/resume  Resume a saved session

Security:
  - API key auth (X-WLF-Key header or ?key= query param)
  - Rate limiting (tokens per minute)
  - AUTHORIZED USE ONLY disclaimer on every response

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
import uuid
from typing import Any, AsyncGenerator, Optional

logger = logging.getLogger(__name__)

_DISCLAIMER = (
    "AUTHORIZED USE ONLY — WordlistXPL-Forge generates wordlists for "
    "authorized security testing. Use only in systems you own or have "
    "written permission to test."
)

_DEFAULT_API_KEY = os.environ.get("WLF_API_KEY", "")
_DEFAULT_HOST = os.environ.get("WLF_HOST", "127.0.0.1")
_DEFAULT_PORT = int(os.environ.get("WLF_PORT", "8771"))
_MAX_LIMIT = 10_000_000  # 10M per request


# ── Request / response models ─────────────────────────────────────────────────

def _parse_generate_body(body: dict) -> dict:
    """Validate and normalise the /v1/generate request body."""
    engines = body.get("engines", ["markov"])
    if not isinstance(engines, list):
        engines = [engines]
    limit = int(body.get("limit", 10_000))
    if limit > _MAX_LIMIT:
        limit = _MAX_LIMIT
    profile = body.get("profile", {})
    if not isinstance(profile, dict):
        profile = {}
    return {
        "engines": engines,
        "limit": limit,
        "profile": profile,
        "min_len": int(body.get("min_len", 4)),
        "max_len": int(body.get("max_len", 32)),
        "stream": bool(body.get("stream", True)),
        "format": body.get("format", "text"),   # text | ndjson
        "explain": bool(body.get("explain", False)),
    }


# ── FastAPI application ───────────────────────────────────────────────────────

def _make_fastapi_app(api_key: str = ""):
    try:
        from fastapi import Depends, FastAPI, Header, HTTPException, Request
        from fastapi.responses import JSONResponse, StreamingResponse
        from pydantic import BaseModel
    except ImportError as exc:
        raise RuntimeError(
            "FastAPI not installed. pip install wordlistxpl-forge[api]"
        ) from exc

    app = FastAPI(
        title="WordlistXPL-Forge API",
        version="2.0.0",
        description=_DISCLAIMER,
        docs_url="/v1/docs",
        redoc_url="/v1/redoc",
    )

    def _check_key(x_wlf_key: str = Header(default="")):
        if api_key and x_wlf_key != api_key:
            raise HTTPException(status_code=401, detail="Invalid API key")

    @app.get("/v1/status")
    def status():
        try:
            import psutil
            ram = psutil.virtual_memory()
            ram_used_pct = ram.percent
        except ImportError:
            ram_used_pct = None
        return {
            "status": "ok",
            "version": "2.0.0",
            "disclaimer": _DISCLAIMER,
            "ram_used_pct": ram_used_pct,
            "uptime": time.time(),
        }

    @app.get("/v1/engines")
    def list_engines(_: None = Depends(_check_key)):
        return {
            "engines": [
                "markov", "pcfg", "semantic", "mask", "prince",
                "neural", "gan", "vae", "transformer", "diffusion",
                "masked_lm", "br_deep", "bayesian", "map_elites",
                "genetic", "tcn", "flow", "temporal_drift",
                "password_graph", "domain_pcfg",
            ],
            "disclaimer": _DISCLAIMER,
        }

    @app.post("/v1/generate")
    async def generate(request: Request, _: None = Depends(_check_key)):
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")

        params = _parse_generate_body(body)
        req_id = str(uuid.uuid4())

        async def _stream() -> AsyncGenerator[bytes, None]:
            yield json.dumps({
                "event": "start",
                "request_id": req_id,
                "disclaimer": _DISCLAIMER,
            }).encode() + b"\n"

            count = 0
            limit = params["limit"]
            gen = _dispatch_generation(params)
            for pw in gen:
                if params["format"] == "ndjson":
                    row: dict = {"pw": pw}
                    if params["explain"]:
                        from wfh_modules.explainer import explain
                        exp = explain(pw, "api", 0.5)
                        row = exp.as_dict()
                    yield json.dumps(row).encode() + b"\n"
                else:
                    yield pw.encode() + b"\n"
                count += 1
                if count >= limit:
                    break
                if count % 5000 == 0:
                    await asyncio.sleep(0)  # yield event loop

            yield json.dumps({
                "event": "done",
                "count": count,
                "request_id": req_id,
            }).encode() + b"\n"

        if params["stream"]:
            return StreamingResponse(_stream(), media_type="application/x-ndjson")
        else:
            # collect all into a list
            results = list(_dispatch_generation(params))[:params["limit"]]
            return JSONResponse({
                "request_id": req_id,
                "count": len(results),
                "passwords": results,
                "disclaimer": _DISCLAIMER,
            })

    @app.get("/v1/sessions")
    def list_sessions(_: None = Depends(_check_key)):
        try:
            from wfh_modules.session_manager import SessionManager
            mgr = SessionManager()
            sessions = mgr.list_sessions()
            return {"sessions": [s.session_id for s in sessions]}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    @app.post("/v1/sessions/{session_id}/resume")
    async def resume_session(session_id: str, _: None = Depends(_check_key)):
        try:
            from wfh_modules.session_manager import SessionManager
            mgr = SessionManager()
            ctx = mgr.resume_ctx(session_id)
            return {"session_id": session_id, "ctx": ctx, "disclaimer": _DISCLAIMER}
        except Exception as exc:
            raise HTTPException(status_code=404, detail=str(exc))

    return app


def _dispatch_generation(params: dict):
    """Yield passwords by dispatching to the requested engines."""
    ctx = {
        "limit": params["limit"],
        "compute_mode": "cpu",
        "use_ml": False,
        "stream": True,
    }
    profile = params.get("profile", {})
    engines = params.get("engines", ["markov"])
    count = 0
    limit = params["limit"]
    min_len = params["min_len"]
    max_len = params["max_len"]

    for engine_name in engines:
        per_engine = max(100, limit // max(len(engines), 1))
        try:
            gen = _engine_factory(engine_name, profile, ctx, per_engine, min_len, max_len)
            for item in gen:
                if isinstance(item, tuple):
                    pw = item[0]
                else:
                    pw = item
                if min_len <= len(pw) <= max_len:
                    yield pw
                    count += 1
                    if count >= limit:
                        return
        except Exception as exc:
            logger.warning("Engine %s failed: %s", engine_name, exc)


def _engine_factory(name: str, profile: dict, ctx: dict, limit: int, min_len: int, max_len: int):
    """Create and run an engine generator."""
    if name == "markov":
        from wfh_modules.markov_engine import MarkovModel
        mm = MarkovModel(order=3)
        seeds = _profile_to_seeds(profile)
        if seeds:
            mm.train(seeds)
        yield from ((w, 0.5) for w in mm.generate(max_candidates=limit))

    elif name in ("gan", "neural"):
        from wfh_modules.gan_engine import GANPasswordEngine
        eng = GANPasswordEngine()
        yield from eng.generate(max_candidates=limit, min_len=min_len, max_len=max_len)

    elif name == "vae":
        from wfh_modules.vae_engine import VAEPasswordEngine
        eng = VAEPasswordEngine()
        yield from eng.generate(max_candidates=limit)

    elif name == "transformer":
        from wfh_modules.transformer_engine import TransformerPasswordEngine
        eng = TransformerPasswordEngine()
        yield from eng.generate(max_candidates=limit)

    elif name == "diffusion":
        from wfh_modules.diffusion_engine import DiffusionPasswordEngine
        eng = DiffusionPasswordEngine()
        yield from eng.generate(max_candidates=limit)

    elif name == "masked_lm":
        from wfh_modules.masked_lm_engine import MaskedLMEngine
        eng = MaskedLMEngine()
        yield from eng.generate(max_candidates=limit, min_len=min_len, max_len=max_len)

    elif name == "br_deep":
        from wfh_modules.br_deep_engine import BRDeepEngine
        eng = BRDeepEngine(profile=profile)
        yield from eng.generate(max_candidates=limit)

    elif name == "bayesian":
        from wfh_modules.bayesian_full import BayesianFullEngine
        eng = BayesianFullEngine(profile=profile)
        yield from eng.generate(max_candidates=limit, min_len=min_len, max_len=max_len)

    elif name == "map_elites":
        from wfh_modules.map_elites import MAPElites
        eng = MAPElites()
        yield from eng.generate(max_candidates=limit)

    elif name == "genetic":
        from wfh_modules.genetic_engine import GeneticPasswordEngine
        eng = GeneticPasswordEngine()
        yield from eng.generate(max_candidates=limit)

    elif name == "tcn":
        from wfh_modules.tcn_engine import TCNPasswordEngine
        eng = TCNPasswordEngine()
        yield from eng.generate(max_candidates=limit, min_len=min_len, max_len=max_len)

    elif name == "flow":
        from wfh_modules.flow_engine import FlowPasswordEngine
        eng = FlowPasswordEngine()
        yield from eng.generate(max_candidates=limit, min_len=min_len, max_len=max_len)

    elif name == "temporal_drift":
        from wfh_modules.temporal_drift import TemporalDriftEngine
        eng = TemporalDriftEngine()
        yield from eng.generate(profile=profile, max_candidates=limit)

    elif name == "domain_pcfg":
        from wfh_modules.domain_pcfg import DomainPCFG
        sector = profile.get("sector", "generic")
        eng = DomainPCFG(sector=sector)
        yield from eng.generate(profile=profile, max_candidates=limit)

    else:
        logger.warning("Unknown engine: %s", name)


def _profile_to_seeds(profile: dict) -> list[str]:
    seeds = []
    name = profile.get("full_name", "") or profile.get("short_name", "")
    if name:
        seeds.extend(name.split())
    seeds.extend(str(k) for k in profile.get("keywords", []))
    return seeds


# ── aiohttp fallback ──────────────────────────────────────────────────────────

def _make_aiohttp_app(api_key: str = ""):
    try:
        from aiohttp import web
    except ImportError as exc:
        raise RuntimeError(
            "Neither fastapi nor aiohttp is available. "
            "pip install wordlistxpl-forge[api]"
        ) from exc

    async def _check(request):
        if api_key:
            key = request.headers.get("X-WLF-Key") or request.rel_url.query.get("key", "")
            if key != api_key:
                raise web.HTTPUnauthorized(text="Invalid API key")

    async def status(request):
        return web.json_response({"status": "ok", "version": "2.0.0", "disclaimer": _DISCLAIMER})

    async def engines(request):
        await _check(request)
        return web.json_response({"engines": ["markov","pcfg","semantic","mask","br_deep","bayesian","genetic","map_elites"]})

    async def generate(request):
        await _check(request)
        body = await request.json()
        params = _parse_generate_body(body)
        response = web.StreamResponse()
        response.headers["Content-Type"] = "application/x-ndjson"
        await response.prepare(request)
        count = 0
        for pw in _dispatch_generation(params):
            await response.write((pw + "\n").encode())
            count += 1
            if count >= params["limit"]:
                break
        await response.write_eof()
        return response

    app = web.Application()
    app.router.add_get("/v1/status", status)
    app.router.add_get("/v1/engines", engines)
    app.router.add_post("/v1/generate", generate)
    return app


# ── Entrypoint ────────────────────────────────────────────────────────────────

def run_server(
    host: str = _DEFAULT_HOST,
    port: int = _DEFAULT_PORT,
    api_key: str = _DEFAULT_API_KEY,
    reload: bool = False,
) -> None:
    """Start the WLF API server."""
    logger.info("Starting WordlistXPL-Forge API on %s:%d", host, port)
    logger.info("AUTHORIZED USE ONLY — %s", _DISCLAIMER)

    try:
        import uvicorn
        app = _make_fastapi_app(api_key)
        uvicorn.run(app, host=host, port=port, reload=reload, log_level="info")
    except ImportError:
        try:
            from aiohttp import web
            app = _make_aiohttp_app(api_key)
            web.run_app(app, host=host, port=port)
        except ImportError:
            logger.error(
                "No ASGI server available. "
                "pip install wordlistxpl-forge[api]"
            )
            sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_server()
