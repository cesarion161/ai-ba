import pytest

from app.services.sandbox import PythonSandbox


@pytest.mark.asyncio
async def test_sandbox_simple_execution():
    sandbox = PythonSandbox()
    result = await sandbox._execute_local("print('hello world')")
    assert result.success
    assert result.stdout == "hello world"


@pytest.mark.asyncio
async def test_sandbox_math():
    sandbox = PythonSandbox()
    result = await sandbox._execute_local("print(2 + 2)")
    assert result.success
    assert "4" in result.stdout


@pytest.mark.asyncio
async def test_sandbox_error():
    sandbox = PythonSandbox()
    result = await sandbox._execute_local("raise ValueError('test error')")
    assert not result.success
    assert result.error is not None


@pytest.mark.asyncio
async def test_sandbox_timeout():
    sandbox = PythonSandbox()
    result = await sandbox._execute_local("import time; time.sleep(10)", timeout=1)
    assert not result.success
    assert "timed out" in (result.error or "").lower()


@pytest.mark.asyncio
async def test_sandbox_multiline():
    sandbox = PythonSandbox()
    code = """
tam = 1_000_000_000
sam = tam * 0.1
som = sam * 0.05
print(f"TAM: ${tam:,.0f}")
print(f"SAM: ${sam:,.0f}")
print(f"SOM: ${som:,.0f}")
"""
    result = await sandbox._execute_local(code)
    assert result.success
    assert "TAM: $1,000,000,000" in result.stdout
    assert "SOM: $5,000,000" in result.stdout
