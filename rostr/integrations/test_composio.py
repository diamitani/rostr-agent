"""Test suite for Composio integration client (v3 API).

Run with: python -m pytest rostr/integrations/test_composio.py -v
Or standalone: python rostr/integrations/test_composio.py

Requires: pip install httpx
"""

import os
import sys

# Add project root to path for standalone execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from rostr.integrations.composio_client import ComposioClient, Integration, COMPOSIO_BASE_URL


def test_list_apps():
    """Test that we can list available Composio toolkits."""
    client = ComposioClient()

    print("Listing available Composio toolkits...")
    apps = client.list_apps(limit=25)

    print(f"Found {len(apps)} toolkits (showing up to 25):")
    print("-" * 70)

    for app in apps:
        cats = ", ".join(app.categories[:2]) if app.categories else ""
        print(f"  {app.name:<22} {app.slug:<18} {cats:<20} {app.description[:30]}")

    print()
    assert len(apps) > 0, "Expected at least one toolkit from Composio"
    assert all(isinstance(a, Integration) for a in apps)
    assert all(a.slug for a in apps), "Every app should have a slug"
    print(f"PASS: {len(apps)} toolkits listed successfully")
    return apps


def test_get_total_apps():
    """Test we can get total available toolkits count."""
    client = ComposioClient()

    total = client.get_total_apps()
    print(f"\nTotal toolkits available: {total}")
    assert total > 100, f"Expected 100+ toolkits, got {total}"
    print(f"PASS: {total} total toolkits")
    return total


def test_get_actions():
    """Test that we can list actions/tools for a toolkit (slack)."""
    client = ComposioClient()

    print("\nFetching actions for 'slack'...")
    actions = client.get_actions("slack", limit=10)

    print(f"Found {len(actions)} Slack actions:")
    for action in actions:
        name = action.get("name", "unknown")
        desc = action.get("description", "")[:55]
        print(f"  {name:<45} {desc}")

    assert len(actions) > 0, "Expected at least one action for Slack"
    print(f"PASS: {len(actions)} Slack actions retrieved")
    return actions


def test_list_connections():
    """Test listing connections for a test entity (may be empty)."""
    client = ComposioClient()

    entity_id = "rostr-test-user"
    print(f"\nListing connections for entity: {entity_id}")
    connections = client.list_connections(entity_id)

    print(f"Found {len(connections)} connections:")
    for conn in connections:
        print(f"  {conn.get('app', 'unknown'):<18} status={conn.get('status', '?'):<10} id={conn.get('id', '?')}")

    print(f"PASS: Connections query succeeded ({len(connections)} found)")
    return connections


def test_get_auth_config():
    """Test fetching auth config for a toolkit."""
    client = ComposioClient()

    print("\nFetching auth config for 'gmail'...")
    config_id = client.get_auth_config("gmail")

    if config_id:
        print(f"  Auth config ID: {config_id}")
        print("PASS: Auth config retrieved")
    else:
        print("  No auth config found (toolkit not configured)")
        print("PASS: Method returned None as expected for unconfigured toolkit")

    return config_id


def main():
    """Run all integration tests."""
    # Check for API key
    api_key = os.getenv("COMPOSIO_API_KEY", "")
    if not api_key:
        print("ERROR: COMPOSIO_API_KEY environment variable not set.")
        print("Set it with: export COMPOSIO_API_KEY='your-key-here'")
        sys.exit(1)

    print("=" * 70)
    print("ROSTR Composio Integration Tests (v3 API)")
    print(f"Endpoint: {COMPOSIO_BASE_URL}")
    print(f"API Key:  {api_key[:8]}...{api_key[-4:]}")
    print("=" * 70)

    try:
        test_list_apps()
        test_get_total_apps()
        test_get_actions()
        test_list_connections()
        test_get_auth_config()

        print("\n" + "=" * 70)
        print("ALL TESTS PASSED")
        print("=" * 70)
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
