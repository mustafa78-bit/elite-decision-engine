from api.app import APIApp
from api.main import app, get_app


def test_api_main_exports_app():
    assert app is not None
    assert isinstance(app, APIApp)
    assert get_app() is app
