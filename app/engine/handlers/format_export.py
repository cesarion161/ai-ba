from __future__ import annotations

import io
import zipfile
from typing import Any

import structlog

from app.engine.handlers.base import register_handler
from app.models.workflow_node import NodeType

logger = structlog.get_logger()


@register_handler(NodeType.FORMAT_EXPORT)
class FormatExportHandler:
    async def execute(
        self,
        node_config: dict | None,
        input_data: dict[str, Any],
        user_feedback: str | None = None,
    ) -> dict[str, Any]:
        # Collect all documents
        documents: dict[str, str] = {}
        densified_content: str = ""
        claude_md: str = ""

        for key, data in input_data.items():
            if isinstance(data, dict):
                if "document" in data:
                    title = data.get("title", key)
                    filename = title.lower().replace(" ", "_") + ".md"
                    documents[f"docs/{filename}"] = data["document"]
                if "densified" in data:
                    role = data.get("target_role", "developer")
                    if role == "developer":
                        claude_md = data["densified"]
                    else:
                        documents[f".cursorrules"] = data["densified"]
                    densified_content = data["densified"]

        # Create in-memory zip
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for path, content in documents.items():
                zf.writestr(path, content)
            if claude_md:
                zf.writestr("CLAUDE.md", claude_md)
            if densified_content and ".cursorrules" not in documents:
                zf.writestr(".cursorrules", densified_content)

        archive_bytes = buffer.getvalue()

        # In production, upload to S3 and return presigned URL
        # For now, return metadata
        return {
            "archive_size_bytes": len(archive_bytes),
            "files": list(documents.keys()) + (["CLAUDE.md"] if claude_md else []),
            "format": "zip",
            "archive_url": None,  # Would be S3 presigned URL
        }
