"""Secure Python execution sandbox using E2B Code Interpreter."""

from __future__ import annotations

import structlog

logger = structlog.get_logger()

DEFAULT_TIMEOUT = 60


class SandboxResult:
    def __init__(
        self,
        stdout: str = "",
        stderr: str = "",
        charts: list[dict[str, str]] | None = None,
        error: str | None = None,
    ):
        self.stdout = stdout
        self.stderr = stderr
        self.charts = charts or []
        self.error = error

    @property
    def success(self) -> bool:
        return self.error is None


class PythonSandbox:
    """Execute generated Python code in an E2B sandbox with timeout and output capture."""

    async def execute(
        self,
        code: str,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> SandboxResult:
        try:
            from e2b_code_interpreter import AsyncSandbox
        except ImportError:
            logger.warning("e2b_code_interpreter not available, using local fallback")
            return await self._execute_local(code, timeout)

        try:
            sandbox = await AsyncSandbox.create(timeout=timeout)
            try:
                execution = await sandbox.run_code(code)

                stdout = ""
                stderr = ""
                charts: list[dict[str, str]] = []

                for log in execution.logs.stdout:
                    stdout += log + "\n"
                for log in execution.logs.stderr:
                    stderr += log + "\n"

                # Capture any generated charts/images
                for result in execution.results:
                    if hasattr(result, "png") and result.png:
                        charts.append(
                            {
                                "format": "png",
                                "data": result.png,  # base64 encoded
                            }
                        )
                    if hasattr(result, "svg") and result.svg:
                        charts.append(
                            {
                                "format": "svg",
                                "data": result.svg,
                            }
                        )

                error = None
                if execution.error:
                    error = f"{execution.error.name}: {execution.error.value}"

                logger.info(
                    "sandbox_execution_complete",
                    stdout_len=len(stdout),
                    stderr_len=len(stderr),
                    charts_count=len(charts),
                    success=error is None,
                )

                return SandboxResult(
                    stdout=stdout.strip(),
                    stderr=stderr.strip(),
                    charts=charts,
                    error=error,
                )
            finally:
                await sandbox.kill()

        except Exception as e:
            logger.error("sandbox_execution_failed", error=str(e))
            return SandboxResult(error=str(e))

    async def _execute_local(
        self,
        code: str,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> SandboxResult:
        """Fallback: execute in a subprocess with restricted timeout. NOT production-safe."""
        import asyncio
        import subprocess
        import sys

        proc = None
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                "-c",
                code,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout,
            )

            return SandboxResult(
                stdout=stdout_bytes.decode().strip(),
                stderr=stderr_bytes.decode().strip(),
                error=None if proc.returncode == 0 else f"Exit code {proc.returncode}",
            )
        except TimeoutError:
            if proc:
                proc.kill()
                await proc.wait()
            return SandboxResult(error=f"Execution timed out after {timeout}s")
        except Exception as e:
            return SandboxResult(error=str(e))


python_sandbox = PythonSandbox()
