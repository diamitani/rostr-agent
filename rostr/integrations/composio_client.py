"""Composio Integration Client — connects ROSTR to 1000+ services via OAuth.

Uses the official Composio Python SDK (composio-core) which handles API versioning.
Install: pip install composio-core
"""

import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class Integration:
    """Represents a Composio app integration."""
    name: str
    app_id: str
    status: str  # "connected", "available", "error"
    actions: list = field(default_factory=list)
    description: str = ""
    logo: str = ""
    categories: list = field(default_factory=list)


class ComposioClient:
    """ROSTR wrapper around Composio SDK for managing integrations."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("COMPOSIO_API_KEY", "")
        if not self.api_key:
            raise ValueError("COMPOSIO_API_KEY required")

        from composio import Composio
        self._client = Composio(api_key=self.api_key)

    def list_apps(self, limit: int = 50) -> List[Integration]:
        """List available Composio apps/toolkits."""
        response = self._client.toolkits.list()
        apps = []
        for item in response.items[:limit]:
            apps.append(Integration(
                name=getattr(item, 'name', ''),
                app_id=getattr(item, 'key', getattr(item, 'slug', '')),
                status="available",
                description=getattr(item, 'description', ''),
                logo=getattr(item, 'logo', ''),
            ))
        return apps

    def get_total_apps(self) -> int:
        """Get total number of available integrations."""
        response = self._client.toolkits.list()
        return int(response.total_items) if response.total_items else 0

    def list_connections(self, entity_id: str) -> List[Dict[str, Any]]:
        """List connected accounts for a user entity."""
        try:
            accounts = self._client.connected_accounts.list(
                user_uuid=entity_id
            )
            result = []
            for acc in getattr(accounts, 'items', []):
                result.append({
                    "id": getattr(acc, 'id', ''),
                    "app": getattr(acc, 'app_name', getattr(acc, 'appName', '')),
                    "status": getattr(acc, 'status', 'active'),
                    "created_at": str(getattr(acc, 'created_at', '')),
                })
            return result
        except Exception:
            return []

    def initiate_connection(self, entity_id: str, app_name: str, redirect_url: str = "") -> str:
        """Start OAuth flow for an app. Returns the redirect URL for the user."""
        try:
            params = {
                "app_name": app_name,
                "entity_id": entity_id,
            }
            if redirect_url:
                params["redirect_url"] = redirect_url

            result = self._client.connected_accounts.initiate(**params)
            return getattr(result, 'redirect_url', getattr(result, 'redirectUrl', ''))
        except Exception as e:
            raise RuntimeError(f"Failed to initiate connection for {app_name}: {e}")

    def execute_action(self, entity_id: str, action: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a Composio action (e.g., SLACK_SEND_MESSAGE)."""
        try:
            result = self._client.tools.execute(
                action=action,
                entity_id=entity_id,
                params=params or {}
            )
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_actions(self, app_name: str, limit: int = 20) -> List[Dict[str, str]]:
        """Get available actions for a specific app."""
        try:
            actions = self._client.tools.list(toolkit=app_name)
            result = []
            for action in getattr(actions, 'items', [])[:limit]:
                result.append({
                    "name": getattr(action, 'name', ''),
                    "display_name": getattr(action, 'display_name', getattr(action, 'displayName', '')),
                    "description": getattr(action, 'description', ''),
                })
            return result
        except Exception:
            return []
