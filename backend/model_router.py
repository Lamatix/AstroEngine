"""
Backward compatibility shim.
Gerçek implementasyon: app/services/model_router_service.py
Bu dosya kök dizindeki scriptlerle uyumluluk için tutulmaktadır.
"""
from app.services.model_router_service import AutonomousModelRouter, model_router_instance

__all__ = ["AutonomousModelRouter", "model_router_instance"]
