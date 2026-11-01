"""
Universal Application & Capability Registry for App-to-App (A2A) Discovery.

Maintains semantic catalogs of all connected applications, their capabilities,
and parameter contracts across the mesh.
"""

from __future__ import annotations

import threading
from typing import Any, Optional

from tandem.core.types import (
    AppManifest,
    Capability,
    CapabilityNotFoundError,
)


class CapabilityRegistry:
    """
    Thread-safe registry for applications and capabilities participating in Tandem.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._apps: dict[str, AppManifest] = {}
        self._capability_to_app: dict[str, str] = {}

    def register_app(self, manifest: AppManifest) -> None:
        """Register an application and all its exposed capabilities."""
        with self._lock:
            self._apps[manifest.app_id] = manifest
            for cap in manifest.capabilities:
                self._capability_to_app[cap.name] = manifest.app_id

    def unregister_app(self, app_id: str) -> None:
        """Remove an application and unbind its capabilities."""
        with self._lock:
            if app_id in self._apps:
                manifest = self._apps.pop(app_id)
                for cap in manifest.capabilities:
                    self._capability_to_app.pop(cap.name, None)

    def get_app(self, app_id: str) -> Optional[AppManifest]:
        """Fetch application manifest by ID."""
        with self._lock:
            return self._apps.get(app_id)

    def get_capability(self, capability_name: str) -> Capability:
        """
        Fetch capability definition by name.
        Raises CapabilityNotFoundError if unregistered.
        """
        with self._lock:
            app_id = self._capability_to_app.get(capability_name)
            if not app_id:
                raise CapabilityNotFoundError(
                    f"Capability '{capability_name}' is not registered in the Tandem mesh."
                )
            manifest = self._apps[app_id]
            cap = manifest.get_capability(capability_name)
            if not cap:
                raise CapabilityNotFoundError(
                    f"Capability '{capability_name}' missing from manifest of app '{app_id}'."
                )
            return cap

    def get_app_for_capability(self, capability_name: str) -> Optional[str]:
        """Return app_id owning the given capability."""
        with self._lock:
            return self._capability_to_app.get(capability_name)

    def list_capabilities(self, prefix: Optional[str] = None) -> list[Capability]:
        """List all registered capabilities, optionally filtered by prefix."""
        with self._lock:
            all_caps: list[Capability] = []
            for manifest in self._apps.values():
                for cap in manifest.capabilities:
                    if prefix is None or cap.name.startswith(prefix):
                        all_caps.append(cap)
            return all_caps

    def list_apps(self) -> list[AppManifest]:
        """List all active registered applications."""
        with self._lock:
            return list(self._apps.values())

    def export_catalog(self) -> dict[str, Any]:
        """Export comprehensive JSON-serializable catalog of mesh capabilities."""
        with self._lock:
            catalog: dict[str, Any] = {}
            for app_id, manifest in self._apps.items():
                catalog[app_id] = {
                    "version": manifest.version,
                    "description": manifest.description,
                    "capabilities": [
                        {
                            "name": cap.name,
                            "description": cap.description,
                            "blast_radius": cap.blast_radius,
                            "min_taint_level": cap.min_taint_level.name,
                            "parameters": [
                                {
                                    "name": p.name,
                                    "type": p.type_name,
                                    "description": p.description,
                                    "required": p.required,
                                    "default": p.default,
                                }
                                for p in cap.parameters
                            ],
                        }
                        for cap in manifest.capabilities
                    ],
                }
            return catalog
