from __future__ import annotations

from fastapi import APIRouter, WebSocket

from app.persistence.store import store

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "components": {"db": "ok", "redis": "stub-ok"}}


@router.get("/metrics")
def metrics() -> dict:
    return {
        "agents": len(store.agents),
        "wallets": len(store.wallets),
        "transactions": len(store.transactions),
        "proofs": len(store.proofs),
    }


@router.get("/top_agents")
def top_agents() -> dict:
    ranked = sorted(store.agents.values(), key=lambda a: a.get("reputation", 0), reverse=True)[:10]
    return {"items": ranked}


@router.get("/world_map")
def world_map() -> dict:
    features = []
    for name, region in store.regions.items():
        features.append(
            {
                "type": "Feature",
                "properties": {"region": name, "core_energy": region.get("core_energy", 0), "gdp_level": region.get("gdp_level")},
                "geometry": {"type": "Point", "coordinates": region.get("coordinates", [0, 0])},
            }
        )
    return {"type": "FeatureCollection", "features": features}


@router.get("/logs")
def logs(page: int = 1, page_size: int = 50) -> dict:
    start = (page - 1) * page_size
    end = start + page_size
    return {"items": store.logs[start:end], "total": len(store.logs)}


@router.websocket("/events")
async def events(websocket: WebSocket) -> None:
    await websocket.accept()
    await websocket.send_json({"type": "hello", "logs": len(store.logs)})
    for event in store.logs[-20:]:
        await websocket.send_json({"type": "log", "data": event})
    await websocket.close()
