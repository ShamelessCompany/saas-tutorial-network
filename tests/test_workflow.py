"""Lightweight self-check and unit tests for SaaS Tutorial Network pipeline."""
import sys
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_workflow
from src.mock_saas import MockSaaSServer
from src.voiceover import generate_voiceover

def test_workflow_config():
    config_file = PROJECT_ROOT / "config" / "default_workflow.yaml"
    assert config_file.exists(), "Config file must exist"
    data = load_workflow(config_file)
    assert "title" in data
    assert "steps" in data
    assert len(data["steps"]) > 0
    assert "narration" in data
    print("[OK] test_workflow_config passed")

def test_mock_saas_server():
    mock_dir = PROJECT_ROOT / "demo_assets" / "mock_saas"
    with MockSaaSServer(mock_dir, port=9876) as base_url:
        req = urllib.request.urlopen(f"{base_url}/index.html", timeout=3)
        assert req.status == 200
        content = req.read().decode("utf-8")
        assert "NexusFlow AI" in content
    print("[OK] test_mock_saas_server passed")

def test_voiceover_fallback(tmp_path: Path = None):
    target = PROJECT_ROOT / "temp" / "test_voice.wav"
    out = generate_voiceover(
        {"hook": "Hola mundo", "solution": "Probando sintetizador"},
        target
    )
    assert out.exists()
    assert out.stat().st_size > 100
    print("[OK] test_voiceover_fallback passed")

if __name__ == "__main__":
    print("Running pipeline self-check tests...")
    test_workflow_config()
    test_mock_saas_server()
    test_voiceover_fallback()
    print("All unit tests passed successfully!")
