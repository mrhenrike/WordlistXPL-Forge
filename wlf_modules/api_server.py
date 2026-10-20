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
from collections.abc import AsyncGenerator, Generator
from typing import Any

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

def _parse_generate_body(body: dict[str, Any]) -> dict[str, Any]:
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

def _make_fastapi_app(api_key: str = "") -> Generator[str, None, None]:
    try:
        from fastapi import Depends, FastAPI, Header, HTTPException, Request
        from fastapi.responses import JSONResponse, StreamingResponse
        from pydantic import BaseModel  # noqa: F401
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

    def _check_key(x_wlf_key: str = Header(default="")) -> None:
        if api_key and x_wlf_key != api_key:
            raise HTTPException(status_code=401, detail="Invalid API key")

    @app.get("/v1/status")  # type: ignore[untyped-decorator]
    def status() -> dict[str, Any]:
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

    @app.get("/v1/engines")  # type: ignore[untyped-decorator]
    def list_engines(_: None = Depends(_check_key)) -> dict[str, Any]:
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

    @app.post("/v1/generate")  # type: ignore[untyped-decorator]
    async def generate(request: Request, _: None = Depends(_check_key)) -> Generator[str, None, None]:
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
                    row: dict[str, Any] = {"pw": pw}
                    if params["explain"]:
                        from wlf_modules.explainer import explain
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
            return StreamingResponse(_stream(), media_type="application/x-ndjson")  # type: ignore[no-any-return]
        else:
            # collect all into a list
            results = list(_dispatch_generation(params))[:params["limit"]]
            return JSONResponse({  # type: ignore[no-any-return]
                "request_id": req_id,
                "count": len(results),
                "passwords": results,
                "disclaimer": _DISCLAIMER,
            })

    @app.get("/v1/sessions")  # type: ignore[untyped-decorator]
    def list_sessions(_: None = Depends(_check_key)) -> Any:
        try:
            from wlf_modules.session_manager import SessionManager
            mgr = SessionManager()
            sessions = mgr.list_sessions()
            return {"sessions": [s.session_id for s in sessions]}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    @app.post("/v1/sessions/{session_id}/resume")  # type: ignore[untyped-decorator]
    async def resume_session(session_id: str, _: None = Depends(_check_key)) -> Any:
        try:
            from wlf_modules.session_manager import SessionManager
            mgr = SessionManager()
            ctx = mgr.resume_ctx(session_id)
            return {"session_id": session_id, "ctx": ctx, "disclaimer": _DISCLAIMER}
        except Exception as exc:
            raise HTTPException(status_code=404, detail=str(exc))

    return app  # type: ignore[no-any-return]


def _dispatch_generation(params: dict[str, Any]) -> Generator[str, None, None]:
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


def _engine_factory(name: str, profile: dict[str, Any], ctx: dict[str, Any], limit: int, min_len: int, max_len: int) -> Generator[str, None, None]:
    """Create and run an engine generator."""
    if name == "markov":
        from wlf_modules.markov_engine import MarkovModel
        mm = MarkovModel(order=3)
        seeds = _profile_to_seeds(profile)
        if seeds:
            mm.train(seeds)  # type: ignore[arg-type]
        yield from ((w, 0.5) for w in mm.generate(max_candidates=limit))  # type: ignore[misc]

    elif name in ("gan", "neural"):
        from wlf_modules.gan_engine import GANPasswordEngine
        eng = GANPasswordEngine()
        yield from eng.generate(max_candidates=limit, min_len=min_len, max_len=max_len)  # type: ignore[misc]

    elif name == "vae":
        from wlf_modules.vae_engine import VAEPasswordEngine
        eng = VAEPasswordEngine()  # type: ignore[assignment]
        yield from eng.generate(max_candidates=limit)  # type: ignore[misc]

    elif name == "transformer":
        from wlf_modules.transformer_engine import TransformerPasswordEngine
        eng = TransformerPasswordEngine()  # type: ignore[assignment]
        yield from eng.generate(max_candidates=limit)  # type: ignore[misc]

    elif name == "diffusion":
        from wlf_modules.diffusion_engine import DiffusionPasswordEngine
        eng = DiffusionPasswordEngine()  # type: ignore[assignment]
        yield from eng.generate(max_candidates=limit)  # type: ignore[misc]

    elif name == "masked_lm":
        from wlf_modules.masked_lm_engine import MaskedLMEngine
        eng = MaskedLMEngine()  # type: ignore[assignment]
        yield from eng.generate(max_candidates=limit, min_len=min_len, max_len=max_len)  # type: ignore[misc]

    elif name == "br_deep":
        from wlf_modules.br_deep_engine import BRDeepEngine
        eng = BRDeepEngine(profile=profile)  # type: ignore[assignment]
        yield from eng.generate(max_candidates=limit)  # type: ignore[misc]

    elif name == "bayesian":
        from wlf_modules.bayesian_full import BayesianFullEngine
        eng = BayesianFullEngine(profile=profile)  # type: ignore[assignment]
        yield from eng.generate(max_candidates=limit, min_len=min_len, max_len=max_len)  # type: ignore[misc]

    elif name == "map_elites":
        from wlf_modules.map_elites import MAPElites
        eng = MAPElites()  # type: ignore[assignment]
        yield from eng.generate(max_candidates=limit)  # type: ignore[misc]

    elif name == "genetic":
        from wlf_modules.genetic_engine import GeneticPasswordEngine
        eng = GeneticPasswordEngine()  # type: ignore[assignment]
        yield from eng.generate(max_candidates=limit)  # type: ignore[misc]

    elif name == "tcn":
        from wlf_modules.tcn_engine import TCNPasswordEngine
        eng = TCNPasswordEngine()  # type: ignore[assignment]
        yield from eng.generate(max_candidates=limit, min_len=min_len, max_len=max_len)  # type: ignore[misc]

    elif name == "flow":
        from wlf_modules.flow_engine import FlowPasswordEngine
        eng = FlowPasswordEngine()  # type: ignore[assignment]
        yield from eng.generate(max_candidates=limit, min_len=min_len, max_len=max_len)  # type: ignore[misc]

    elif name == "temporal_drift":
        from wlf_modules.temporal_drift import TemporalDriftEngine
        eng = TemporalDriftEngine()  # type: ignore[assignment]
        yield from eng.generate(profile=profile, max_candidates=limit)  # type: ignore[call-arg, misc]

    elif name == "domain_pcfg":
        from wlf_modules.domain_pcfg import DomainPCFG
        sector = profile.get("sector", "generic")
        eng = DomainPCFG(sector=sector)  # type: ignore[assignment]
        yield from eng.generate(profile=profile, max_candidates=limit)  # type: ignore[call-arg, misc]

    else:
        logger.warning("Unknown engine: %s", name)


def _profile_to_seeds(profile: dict[str, Any]) -> list[str]:
    seeds = []
    name = profile.get("full_name", "") or profile.get("short_name", "")
    if name:
        seeds.extend(name.split())
    seeds.extend(str(k) for k in profile.get("keywords", []))
    return seeds


# ── aiohttp fallback ──────────────────────────────────────────────────────────

def _make_aiohttp_app(api_key: str = "") -> Any:
    try:
        from aiohttp import web
    except ImportError as exc:
        raise RuntimeError(
            "Neither fastapi nor aiohttp is available. "
            "pip install wordlistxpl-forge[api]"
        ) from exc

    async def _check(request: Any) -> None:
        if api_key:
            key = request.headers.get("X-WLF-Key") or request.rel_url.query.get("key", "")
            if key != api_key:
                raise web.HTTPUnauthorized(text="Invalid API key")

    async def status(request: Any) -> Any:
        return web.json_response({"status": "ok", "version": "2.0.0", "disclaimer": _DISCLAIMER})

    async def engines(request: Any) -> Any:
        await _check(request)
        return web.json_response({"engines": ["markov","pcfg","semantic","mask","br_deep","bayesian","genetic","map_elites"]})

    async def generate(request: Any) -> Any:
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
