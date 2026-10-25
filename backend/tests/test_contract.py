import json
from pathlib import Path
from app.main import app
from app.tasks.engine import generate,public

def test_openapi_snapshot_matches():
    expected=json.loads((Path(__file__).resolve().parents[2]/'docs/openapi.json').read_text())
    assert app.openapi()==expected

def test_public_renderer_contract():
    for f in ['dependencies','logic','ordering','induction','hypothesis']:
        t=public(generate(f,1,987))
        assert set(t)=={'family','difficulty','instructions','render','response_schema'}
        assert isinstance(t['instructions'],str) and t['render']['kind']
        assert t['response_schema']['kind'] in {'boolean_choice','roles','three_way','number','rule_choice'}
