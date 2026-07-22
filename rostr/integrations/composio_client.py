"""Composio Integration Client — connects ROSTR to 1000+ services via OAuth.

Uses the Composio REST API v3 (https://backend.composio.dev/api/v3).
No SDK dependency — direct HTTP calls with httpx for reliability.

Install: pip install httpx
"""

import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

import httpx

COMPOSIO_BASE_URL = "https://backend.composio.dev/api/v3"


@dataclass
class Integration:
    """Represents a Composio app integration."""

    name: str
    slug: str
    status: str  # "connected", "available", "error"
    actions: list = field(default_factory=list)
    description: str = ""
    logo: str = ""
    categories: list = field(default_factory=list)
    auth_schemes: list = field(default_factory=list)
    no_auth: bool = False


class ComposioClient:
    """Client for the Composio REST API v3.

    Manages OAuth connections, lists available toolkits/services, and executes
    tools (e.g., GMAIL_SEND_EMAIL, SLACK_SEND_MESSAGE) on behalf of
    ROSTR user entities.

    All methods are synchronous for simplicity.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("COMPOSIO_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "COMPOSIO_API_KEY must be provided or set as an environment variable"
            )
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        self.base_url = COMPOSIO_BASE_URL

    def _request(self, method: str, path: str, **kwargs) -> Any:
        """Make a request to the Composio API."""
        url = f"{self.base_url}{path}"
        response = httpx.request(
            method,
            url,
            headers=self.headers,
            timeout=30.0,
            **kwargs,
        )
        response.raise_for_status()
        return response.json()

    def _parse_items(self, data: Any) -> List[Dict[str, Any]]:
        """Parse a Composio paginated response."""
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("items", [])
        return []

    def list_apps(self, limit: int = 100) -> List[Integration]:
        """List available Composio toolkits (apps).

        Returns:
            List of Integration dataclass instances.
        """
        data = self._request("GET", "/toolkits")
        items = self._parse_items(data)

        apps = []
        for item in items[:limit]:
            meta = item.get("meta", {})
            apps.append(
                Integration(
                    name=item.get("name", item.get("slug", "")),
                    slug=item.get("slug", ""),
                    status="available",
                    description=meta.get("description", ""),
                    logo=meta.get("logo", ""),
                    categories=[
                        c.get("name", c.get("id", ""))
                        for c in meta.get("categories", [])
                    ],
                    auth_schemes=item.get("auth_schemes", []),
                    no_auth=item.get("no_auth", False),
                )
            )
        return apps

    def get_total_apps(self) -> int:
        """Get total number of available toolkits."""
        data = self._request("GET", "/toolkits")
        if isinstance(data, dict):
            return data.get("total_items", len(self._parse_items(data)))
        return len(self._parse_items(data))

    def list_connections(self, entity_id: str) -> List[Dict[str, Any]]:
        """List connected accounts for a user entity.

        Args:
            entity_id: The ROSTR user identifier.

        Returns:
            List of connection dictionaries.
        """
        try:
            data = self._request(
                "GET",
                "/connected_accounts",
                params={"user_uuid": entity_id},
            )
            items = self._parse_items(data)
            result = []
            for acc in items:
                toolkit = acc.get("toolkit", {})
                result.append({
                    "id": acc.get("id", ""),
                    "app": toolkit.get("slug", acc.get("appName", "")),
                    "app_name": toolkit.get("slug", ""),
                    "status": acc.get("status", "ACTIVE"),
                    "created_at": acc.get("createdAt", acc.get("created_at", "")),
                    "auth_scheme": acc.get("authScheme", ""),
                })
            return result
        except httpx.HTTPStatusError:
            return []

    def get_auth_config(self, toolkit_slug: str) -> Optional[str]:
        """Get the default auth config ID for a toolkit (needed for OAuth).

        Args:
            toolkit_slug: The toolkit slug (e.g., "slack", "gmail").

        Returns:
            The auth_config_id string, or None if not found.
        """
        try:
            data = self._request(
                "GET",
                "/auth_configs",
                params={"toolkit_slug": toolkit_slug},
            )
            items = self._parse_items(data)
            # Prefer composio-managed OAuth configs
            for item in items:
                if item.get("is_composio_managed"):
                    return item.get("id")
            # Fallback to first available
            if items:
                return items[0].get("id")
            return None
        except httpx.HTTPStatusError:
            return None

    def initiate_connection(
        self, entity_id: str, app_name: str, redirect_url: str = ""
    ) -> Dict[str, Any]:
        """Start OAuth flow for an app. Returns redirect URL and connection details.

        Uses POST /api/v3/connected_accounts/link for Composio-managed OAuth.

        Args:
            entity_id: The ROSTR user identifier.
            app_name: The toolkit slug (e.g., "slack", "gmail", "hubspot").
            redirect_url: URL to redirect after OAuth completes.

        Returns:
            Dict with redirect_url, link_token, connected_account_id.
        """
        # First get the auth config for this toolkit
        auth_config_id = self.get_auth_config(app_name.lower())
        if not auth_config_id:
            raise RuntimeError(
                f"No auth config found for '{app_name}'. "
                f"Create one at https://app.composio.dev"
            )

        payload: Dict[str, Any] = {
            "auth_config_id": auth_config_id,
            "user_id": entity_id,
        }
        if redirect_url:
            payload["redirect_url"] = redirect_url

        data = self._request("POST", "/connected_accounts/link", json=payload)
        return {
            "redirect_url": data.get("redirect_url", ""),
            "link_token": data.get("link_token", ""),
            "connected_account_id": data.get("connected_account_id", ""),
            "expires_at": data.get("expires_at", ""),
        }

    def execute_action(
        self,
        entity_id: str,
        action: str,
        params: Optional[Dict[str, Any]] = None,
        connected_account_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute a Composio tool/action on behalf of a user.

        Uses POST /api/v3/tools/execute/{ACTION_NAME}

        Args:
            entity_id: The ROSTR user identifier.
            action: Action/tool name (e.g., "GMAIL_SEND_EMAIL", "SLACK_SEND_MESSAGE").
            params: Action-specific input parameters (passed as 'arguments').
            connected_account_id: The specific connected account to use.

        Returns:
            Action execution result dictionary.
        """
        payload: Dict[str, Any] = {
            "entity_id": entity_id,
            "arguments": params or {},
        }
        if connected_account_id:
            payload["connected_account_id"] = connected_account_id

        try:
            data = self._request(
                "POST",
                f"/tools/execute/{action}",
                json=payload,
            )
            return {"success": True, "result": data}
        except httpx.HTTPStatusError as e:
            error_body = ""
            try:
                error_body = e.response.json()
            except Exception:
                error_body = e.response.text
            return {
                "success": False,
                "error": str(e),
                "status": e.response.status_code,
                "detail": error_body,
            }

    def get_actions(self, app_name: str, limit: int = 20) -> List[Dict[str, str]]:
        """Get available tools/actions for a specific toolkit.

        Uses GET /api/v3/tools?toolkit_slug={app}&limit=N

        Args:
            app_name: The toolkit slug (e.g., "slack", "gmail").
            limit: Max number of actions to return.

        Returns:
            List of action dictionaries with name, display_name, description.
        """
        try:
            data = self._request(
                "GET",
                "/tools",
                params={"toolkit_slug": app_name.lower(), "limit": limit},
            )
            items = self._parse_items(data)
            result = []
            for action in items[:limit]:
                result.append({
                    "name": action.get("enum", action.get("name", "")),
                    "display_name": action.get("name", action.get("displayName", "")),
                    "description": action.get("description", ""),
                })
            return result
        except httpx.HTTPStatusError:
            return []

    def get_integrations(self, entity_id: str) -> List[Integration]:
        """High-level: get all apps with connection status for a user.

        Combines list_apps() and list_connections() to return a unified
        view of available and connected integrations.

        Args:
            entity_id: The ROSTR user identifier.

        Returns:
            List of Integration objects with status set.
        """
        apps = self.list_apps(limit=200)
        connections = self.list_connections(entity_id)

        connected_slugs = {
            conn["app"].lower()
            for conn in connections
            if conn.get("status", "").upper() == "ACTIVE"
        }

        for app in apps:
            if app.slug.lower() in connected_slugs:
                app.status = "connected"

        return apps
