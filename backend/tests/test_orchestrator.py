"""Otonom orkestratör testleri."""
import asyncio
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from autonomous_orchestrator import ModuleStatus, check_ephemeris_files, run_module_check  # noqa: E402


def test_module_status_to_dict():
    d = ModuleStatus("test_module", True, latency_ms=12.5).to_dict()
    assert d == {"module": "test_module", "healthy": True, "error": None, "latency_ms": 12.5}


def test_run_module_check_returns_bool():
    assert isinstance(run_module_check("Bilinmeyen Modül"), bool)


def test_check_ephemeris_files():
    result = asyncio.run(check_ephemeris_files())
    assert isinstance(result, ModuleStatus)
    assert result.module == "ephemeris"
    assert result.healthy is True  # dosyalar repoda mevcut


def test_frontend_check_fails_when_port_closed():
    # Port 3000 kapalıysa False dönmeli (eskiden her zaman True dönüyordu)
    import socket
    try:
        socket.create_connection(("localhost", 3000), timeout=1).close()
        return
    except OSError:
        pass
    assert run_module_check("Faz 4: Next.js UI/UX") is False
