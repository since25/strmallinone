"""Stable identity and de-duplication helpers for transfer resources."""

from ..models.resource import ResourceDto


def _extra_string(resource: ResourceDto, key: str) -> str:
    value = resource.extra.get(key)
    return str(value).strip() if value is not None else ""


def resource_key(resource: ResourceDto) -> str:
    """Return the provider/share/receive identity used for idempotency."""

    share_code = _extra_string(resource, "shareCode")
    receive_code = _extra_string(resource, "receiveCode")
    if share_code and receive_code:
        return f"{resource.provider}:{share_code}:{receive_code}"
    # Manual or future providers may not expose the parsed codes.  The resource
    # id is still deterministic and gives callers a useful, non-empty key.
    return f"{resource.provider}:id:{resource.id}"


def target_folder(resource: ResourceDto, movie_folder: str, tv_folder: str) -> str:
    return tv_folder if resource.mediaType == "tv" else movie_folder


def dedupe_resources(resources: list[ResourceDto]) -> list[ResourceDto]:
    """Keep the first resource and aggregate distinct source labels."""

    result: list[ResourceDto] = []
    positions: dict[str, int] = {}
    for resource in resources:
        key = resource_key(resource)
        source = resource.extra.get("source")
        source_name = str(source).strip() if source is not None else ""
        if key not in positions:
            positions[key] = len(result)
            result.append(resource)
            continue
        existing = result[positions[key]]
        sources: list[str] = []
        for candidate in [*existing.extra.get("sources", []), existing.extra.get("source"), source_name]:
            if isinstance(candidate, str) and candidate and candidate not in sources:
                sources.append(candidate)
        extra = dict(existing.extra)
        if sources:
            extra["sources"] = sources
        result[positions[key]] = existing.model_copy(update={"extra": extra})
    return result
