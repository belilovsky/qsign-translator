#!/usr/bin/env python3
"""Validate QSign's local Platform contracts and an optional Platform mirror."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ID = "qsign-translator"
QAZSTACK_CONTRACT_URL = "https://qsign.qdev.run/.well-known/qazstack-consumer.json"
AVDS_CONTRACT_URL = "https://qsign.qdev.run/.well-known/avds-ui-contract.json"


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def resource_by_id(document: dict[str, Any], resource_id: str) -> dict[str, Any] | None:
    resources = document.get("resources")
    if not isinstance(resources, list):
        return None
    for resource in resources:
        if isinstance(resource, dict) and resource.get("id") == resource_id:
            return resource
    return None


def validate_local_contracts(root: Path) -> list[str]:
    errors: list[str] = []
    manifest = load_json(root / "qdev-project.json")
    consumer = load_json(root / "qazstack-consumer.json")
    avds = load_json(root / "avds-ui-contract.json")
    context = load_json(root / "public" / "public-context.json")
    ai_index = load_json(root / "public" / "ai-index.json")
    discovery = load_json(root / "public" / ".well-known" / "qdev-public-data-agent.json")

    capabilities = manifest.get("capabilities")
    qazstack = capabilities.get("qazstack") if isinstance(capabilities, dict) else None
    avds_capability = capabilities.get("avds") if isinstance(capabilities, dict) else None
    if not isinstance(qazstack, dict) or qazstack.get("mode") != "optional":
        errors.append("manifest must declare QazStack as an optional capability")
    elif qazstack.get("contracts") != ["qazstack-consumer.json"]:
        errors.append("manifest QazStack contract path must be qazstack-consumer.json")
    if not isinstance(avds_capability, dict) or avds_capability.get("mode") != "optional":
        errors.append("manifest must declare AVDS as an optional capability")
    elif "avds-ui-contract.json" not in avds_capability.get("contracts", []):
        errors.append("manifest AVDS contracts must include avds-ui-contract.json")

    if consumer.get("project_id") != manifest.get("project_id") or consumer.get("project_id") != PROJECT_ID:
        errors.append("manifest and QazStack contract must share the QSign project id")
    if consumer.get("integration_mode") != "documented-only":
        errors.append("QSign must not claim a QazStack package or runtime adoption")
    primitives = consumer.get("primitives")
    if primitives != ["governance-and-audit", "observability-and-ui"]:
        errors.append("QSign must declare the approved QazStack primitive pair")
    if QAZSTACK_CONTRACT_URL not in consumer.get("evidence", {}).get("runtime_urls", []):
        errors.append("QazStack contract must declare its projection URL")

    if avds.get("schema_version") != "avds-ui-contract-v1":
        errors.append("AVDS contract must use avds-ui-contract-v1")
    if avds.get("qazstack_behavior_sources") != primitives:
        errors.append("AVDS behavior sources must mirror the approved QazStack primitives")

    machine_readable = context.get("machine_readable")
    if not isinstance(machine_readable, dict):
        errors.append("public context must have machine-readable links")
    else:
        if machine_readable.get("qazstack_consumer") != QAZSTACK_CONTRACT_URL:
            errors.append("public context must link the QazStack contract")
        if machine_readable.get("avds_ui_contract") != AVDS_CONTRACT_URL:
            errors.append("public context must link the AVDS contract")

    expected_resources = {
        "qazstack-consumer-contract": (QAZSTACK_CONTRACT_URL, ["schema_version", "project_id"]),
        "avds-ui-contract": (AVDS_CONTRACT_URL, ["schema_version", "contract_id"]),
    }
    for label, document in (("AI index", ai_index), ("discovery", discovery)):
        for resource_id, (url, stable_fields) in expected_resources.items():
            resource = resource_by_id(document, resource_id)
            if resource is None:
                errors.append(f"{label} must expose {resource_id}")
                continue
            if resource.get("url") != url:
                errors.append(f"{label} has an incorrect URL for {resource_id}")
            if document is ai_index and resource.get("stable_id_fields") != stable_fields:
                errors.append(f"AI index has incorrect stable fields for {resource_id}")
    return errors


def validate_platform_mirror(platform_root: Path) -> list[str]:
    errors: list[str] = []
    registry = load_json(platform_root / "qazstack" / "primitives-registry.json")
    contracts = registry.get("consumer_contracts")
    contract = contracts.get(PROJECT_ID) if isinstance(contracts, dict) else None
    expected_contract = {
        "repository": "https://github.com/belilovsky/qsign-translator",
        "path": "qazstack-consumer.json",
        "integration_mode": "documented-only",
        "qazstack_version": "contract-only",
        "visibility": "source-contract-local-only",
    }
    if contract != expected_contract:
        errors.append("Platform consumer-contract mirror does not match the QSign source contract")

    primitives = registry.get("primitives")
    if not isinstance(primitives, list):
        return errors + ["Platform primitives registry is malformed"]
    for primitive_id in ("governance-and-audit", "observability-and-ui"):
        primitive = next(
            (item for item in primitives if isinstance(item, dict) and item.get("id") == primitive_id),
            None,
        )
        if not isinstance(primitive, dict) or PROJECT_ID not in primitive.get("consumer_ids", []):
            errors.append(f"Platform primitive {primitive_id} must include QSign as a consumer")

    consumer = next(
        (item for item in registry.get("consumers", []) if isinstance(item, dict) and item.get("id") == PROJECT_ID),
        None,
    )
    if not isinstance(consumer, dict) or consumer.get("primitive_ids") != [
        "governance-and-audit",
        "observability-and-ui",
    ]:
        errors.append("Platform consumer record must mirror QSign's primitive pair")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--platform-root",
        type=Path,
        help="optional Platform Portal checkout for the bilateral mirror check",
    )
    args = parser.parse_args()

    errors = validate_local_contracts(ROOT)
    if args.platform_root is not None:
        errors.extend(validate_platform_mirror(args.platform_root.resolve()))
    if errors:
        for error in errors:
            print(f"platform-contract: {error}", file=sys.stderr)
        return 1
    scope = "bilateral" if args.platform_root is not None else "local"
    print(f"platform-contract: {scope} check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
