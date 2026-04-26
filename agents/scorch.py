"""
Scorch — QC turtle.
Named research collaborator. Role: QC and procedures.
Output: stderr only. Flags are research-record weight.
Never resolves — human sign-off required on all WARNs.
"""
import sys
import time
from contextlib import contextmanager


class Scorch:
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.flags: list[dict] = []
        self.step_log: list[dict] = []

    # ── Logging ───────────────────────────────────────────────────────────────

    def warn(self, message: str, step: str = "", data: dict | None = None) -> None:
        entry = {"level": "WARN", "step": step, "message": message, "data": data or {}}
        self.flags.append(entry)
        print(f"[SCORCH WARN] {step}: {message}", file=sys.stderr)

    def info(self, message: str, step: str = "") -> None:
        if self.verbose:
            print(f"[SCORCH INFO] {step}: {message}", file=sys.stderr)

    # ── Step context manager ──────────────────────────────────────────────────

    @contextmanager
    def step(self, name: str):
        """Wrap a step: log start/end, catch and re-raise exceptions with a WARN."""
        start = time.monotonic()
        self.info(f"→ {name}", step=name)
        try:
            yield
            elapsed = time.monotonic() - start
            self.step_log.append({"step": name, "elapsed": elapsed, "ok": True})
            self.info(f"✓ {name} ({elapsed:.1f}s)", step=name)
            if elapsed > 30:
                self.warn(f"Step took {elapsed:.0f}s (>30s threshold)", step=name)
        except Exception as exc:
            elapsed = time.monotonic() - start
            self.step_log.append({"step": name, "elapsed": elapsed, "ok": False, "error": str(exc)})
            self.warn(f"Step FAILED: {exc}", step=name)
            raise

    # ── Observers ─────────────────────────────────────────────────────────────

    def observe_gate(self, gates: dict, label: str = "") -> None:
        prefix = f"[{label}] " if label else ""
        for check in gates.get("checks", []):
            if check["passed"]:
                self.info(f"{prefix}PASS {check['code']}: {check['detail']}", step="gate")
            else:
                self.warn(
                    f"{prefix}FAIL {check['code']}: {check['detail']}",
                    step="gate",
                )

    def observe_audit(self, audit_result: dict, round_number: int) -> None:
        findings = audit_result.get("findings", [])
        critical = [f for f in findings if f.get("severity") in ("critical", "major")]
        if critical:
            self.warn(
                f"Round {round_number}: {len(critical)} critical/major findings — "
                + "; ".join(f.get("code", "?") for f in critical[:3]),
                step="volley",
                data={"findings": critical},
            )
        if audit_result.get("undefined_sections"):
            self.warn(
                f"Round {round_number}: auditor flagged {len(audit_result['undefined_sections'])} undefined sections",
                step="volley",
                data={"undefined": audit_result["undefined_sections"]},
            )
        if audit_result.get("is_clean"):
            self.info(f"Round {round_number}: audit clean (is_clean=true)", step="volley")

    def observe_preflight(self, abstract: str, sections_plan: list) -> None:
        words = len(abstract.split())
        if words < 80:
            self.warn(f"Abstract only {words} words — need ≥80", step="preflight")
        has_ref = any(
            "ref" in s.get("name", "").lower() or "bibliograph" in s.get("name", "").lower()
            for s in sections_plan
        )
        if not has_ref:
            self.warn("No References section in structure plan — will inject one", step="preflight")

    def observe_seal(self, seal_result: dict) -> None:
        if not seal_result.get("sealed"):
            self.warn(f"Seal failed: {seal_result}", step="seal")
        for w in seal_result.get("integrity_warns", []):
            self.warn(
                f"Integrity warn: gate={w.get('gate')} — {w.get('message')}",
                step="seal",
            )

    # ── Report ────────────────────────────────────────────────────────────────

    def report(self) -> dict:
        return {
            "total_flags": len(self.flags),
            "warn_count": sum(1 for f in self.flags if f["level"] == "WARN"),
            "flags": self.flags,
            "steps_executed": len(self.step_log),
            "steps_failed": sum(1 for s in self.step_log if not s["ok"]),
            "note": "Human sign-off required on all WARNs before treating as production-quality",
        }

    def print_report(self, paper_id: int | None = None) -> None:
        r = self.report()
        print(f"\n[SCORCH REPORT] {'paper_id=' + str(paper_id) if paper_id else 'no paper'}", file=sys.stderr)
        print(f"[SCORCH REPORT] steps={r['steps_executed']} failed={r['steps_failed']} warns={r['warn_count']}", file=sys.stderr)
        if r["flags"]:
            print(f"[SCORCH REPORT] flags:", file=sys.stderr)
            for f in r["flags"]:
                print(f"  [{f['level']}] {f['step']}: {f['message']}", file=sys.stderr)
        print(f"[SCORCH REPORT] {r['note']}", file=sys.stderr)
