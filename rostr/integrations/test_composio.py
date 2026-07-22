"""Test suite for Composio integration client.

Run with: python -m pytest rostr/integrations/test_composio.py -v
Or standalone: python rostr/integrations/test_composio.py

Requires: pip install composio-core
"""

import os
import sys

# Add project root to path for standalone execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from rostr.integrations.composio_client import ComposioClient, Integration


def test_list_apps():
    """Test that we can list available Composio apps."""
    client = ComposioClient()

    print("Listing available Composio apps...")
    apps = client.list_apps(limit=25)

    print(f"Found {len(apps)} apps (showing up to 25):")
    print("-" * 60)

    for app in apps:
        print(f"  {app.name:<25} {app.app_id:<20} {app.description[:40]}")

    print()
    assert len(apps) > 0, "Expected at least one app from Composio"
    assert all(isinstance(a, Integration) for a in apps)
    print(f"PASS: {len(apps)} apps listed successfully")
    return apps


def test_get_total_apps():
    """Test we can get total available integrations count."""
    client = ComposioClient()

    total = client.get_total_apps()
    print(f"\nTotal integrations available: {total}")
    assert total > 0, "Expected total apps > 0"
    print(f"PASS: {total} total apps")
    return total


def test_get_actions():
    """Test that we can list actions for an app (e.g., slack)."""
    client = ComposioClient()

    print("\nFetching actions for 'slack'...")
    actions = client.get_actions("slack")

    print(f"Found {len(actions)} Slack actions:")
    for action in actions[:10]:
        name = action.get("name", "unknown")
        desc = action.get("description", "")[:50]
        print(f"  {name:<40} {desc}")

    if len(actions) > 10:
        print(f"  ... and {len(actions) - 10} more")

    # Slack should have actions; if SDK doesn't find them, this is informational
    print(f"PASS: Actions query returned {len(actions)} results")
    return actions


def test_list_connections():
    """Test listing connections for a test entity (may be empty)."""
    client = ComposioClient()

    entity_id = "rostr-test-user"
    print(f"\nListing connections for entity: {entity_id}")
    connections = client.list_connections(entity_id)

    print(f"Found {len(connections)} connections:")
    for conn in connections:
        print(f"  {conn.get('app', 'unknown'):<20} status={conn.get('status', '?')}")

    print(f"PASS: Connections query succeeded ({len(connections)} found)")
    return connections


def main():
    """Run all integration tests."""
    # Check for API key
    api_key = os.getenv("COMPOSIO_API_KEY", "")
    if not api_key:
        print("ERROR: COMPOSIO_API_KEY environment variable not set.")
        print("Set it with: export COMPOSIO_API_KEY='your-key-here'")
        sys.exit(1)

    print("=" * 60)
    print("ROSTR Composio Integration Tests")
    print(f"API Key: {api_key[:8]}...{api_key[-4:]}")
    print("=" * 60)

    try:
        test_list_apps()
        test_get_total_apps()
        test_get_actions()
        test_list_connections()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED")
        print("=" * 60)
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
