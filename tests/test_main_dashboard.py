from pathlib import Path

from fastapi.responses import FileResponse, RedirectResponse

from app.main import DASHBOARD_PAGE, dashboard, root


def test_root_redirects_to_dashboard() -> None:
    response = root()

    assert isinstance(response, RedirectResponse)
    assert response.status_code == 307
    assert response.headers["location"] == "/dashboard"


def test_dashboard_serves_marketplace_file() -> None:
    response = dashboard()

    assert isinstance(response, FileResponse)
    assert Path(response.path) == DASHBOARD_PAGE
    assert Path(response.path).exists()
