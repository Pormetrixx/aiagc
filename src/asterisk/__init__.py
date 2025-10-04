"""
Asterisk package initialization
"""

# Modern ARI interface (recommended)
from .ari_interface import AsteriskARI
from .ari_call_handler import ARICallHandler, create_ari_application

# Legacy AGI interface (deprecated but maintained for backward compatibility)
from .agi_interface import AsteriskAGI, AsteriskAMI
from .call_handler import CallHandler

__all__ = [
    # ARI (Modern - Recommended)
    "AsteriskARI",
    "ARICallHandler",
    "create_ari_application",
    # AGI (Legacy - Deprecated)
    "AsteriskAGI",
    "AsteriskAMI",
    "CallHandler"
]
