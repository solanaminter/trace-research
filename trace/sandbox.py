"""Token Factory Sandbox code execution (pluggable backends).

Backends:
  * "local"        — restricted local subprocess (dev, tests, evals). Network
                     disabled at the job level; only an allowlisted stdlib
                     surface is importable; wall-clock timeout enforced.
  * "tokenfactory" — Nebius Token Factory Sandboxes: isolated cloud microVMs
                     via the account's sandbox execution endpoint
                     (NEBIUS_SANDBOX_URL, confirm exact path in dev.nebius.com).

The pipeline talks only to `Sandbox.execute(job)`; the backend is an env var,
so a run can move from local dev to Token Factory sandboxes with zero code
change — and the audit log records which backend ran every job.
"""
from __future__ import annotations

import ast
import subprocess
import sys
import tempfile
import textwrap
import time
from dataclasses import dataclass, field

import requests

from . import config

# Stdlib modules a generated analysis job may import. Everything else is
# rejected before execution (both backends; Token Factory enforces its own
# isolation on top).
ALLOWED_IMPORTS = {
    "math", "statistics", "datetime", "json", "collections", "itertools",
    "functools", "re", "decimal", "fractions", "csv", "random", "string",
    "typing", "dataclasses", "enum", "heapq", "bisect", "textwrap", "time",
}

FORBIDDEN_NAMES = {"open", "exec", "eval", "__import__", "compile", "input",
                   "exit", "quit", "help", "globals", "locals", "vars",
                   "dir", "getattr", "setattr", "delattr", "hasattr",
                   "memoryview", "breakpoint"}


def check_safety(code: str) -> None:
    """Static safety gate: allowlisted imports only, no dangerous builtins."""
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name.split(".")[0] for a in node.names]
            bad = [n for n in names if n not in ALLOWED_IMPORTS]
            if bad:
                raise ValueError(f"import not allowed in sandbox: {bad}")
        elif isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            raise ValueError(f"name not allowed in sandbox: {node.id}")
        elif isinstance(node, ast.Attribute) and node.attr in ("__class__", "__subclasses__", "__dict__", "__bases__"):
            raise ValueError(f"dunder access not allowed in sandbox: {node.attr}")


@dataclass
class SandboxJob:
    id: str
    code: str
    description: str = ""


@dataclass
class SandboxResult:
    job_id: str
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int
    backend: str
    timed_out: bool = False


@dataclass
class Sandbox:
    settings: config.Settings = field(default_factory=config.Settings)

    @property
    def backend(self) -> str:
        return self.settings.sandbox_backend

    def execute(self, job: SandboxJob) -> SandboxResult:
        check_safety(job.code)
        if self.backend == "tokenfactory":
            return self._execute_tokenfactory(job)
        return self._execute_local(job)

    # -- local mock backend -------------------------------------------------
    def _execute_local(self, job: SandboxJob) -> SandboxResult:
        check_safety(job.code)
        src = textwrap.dedent(job.code)
        t0 = time.time()
        try:
            with tempfile.NamedTemporaryFile("w", suffix=".py", delete=True) as f:
                f.write(src)
                f.flush()
                p = subprocess.run(
                    [sys.executable, "-I", "-E", f.name],  # isolated, no env, no site
                    capture_output=True, text=True,
                    timeout=self.settings.sandbox_timeout_s,
                )
            return SandboxResult(
                job_id=job.id, stdout=p.stdout[-4000:], stderr=p.stderr[-1000:],
                exit_code=p.returncode, duration_ms=int((time.time() - t0) * 1000),
                backend="local",
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(job_id=job.id, stdout="", stderr="timeout",
                                 exit_code=124, duration_ms=self.settings.sandbox_timeout_s * 1000,
                                 backend="local", timed_out=True)

    # -- Nebius Token Factory Sandboxes backend ------------------------------
    def _execute_tokenfactory(self, job: SandboxJob) -> SandboxResult:
        if not self.settings.sandbox_api_url:
            raise RuntimeError(
                "NEBIUS_SANDBOX_URL is not set. Confirm your sandbox execution "
                "endpoint in the dev.nebius.com console (see NEBIUS_SETUP.md), "
                "or use TRACE_SANDBOX_BACKEND=local."
            )
        t0 = time.time()
        r = requests.post(
            self.settings.sandbox_api_url.rstrip("/") + "/execute",
            headers={"Authorization": f"Bearer {self.settings.nebius_api_key}",
                     "Content-Type": "application/json"},
            json={"language": "python", "code": textwrap.dedent(job.code),
                  "timeout_s": self.settings.sandbox_timeout_s},
            timeout=self.settings.sandbox_timeout_s + 15,
        )
        r.raise_for_status()
        body = r.json()
        return SandboxResult(
            job_id=job.id,
            stdout=str(body.get("stdout", ""))[-4000:],
            stderr=str(body.get("stderr", ""))[-1000:],
            exit_code=int(body.get("exit_code", 0)),
            duration_ms=int((time.time() - t0) * 1000),
            backend="tokenfactory",
        )
