"""
eaiou HTTP client.
Handles: nginx basic auth (on every request) + session cookie (post-login).
All methods return parsed dicts. Raises on non-2xx responses.
"""
import httpx
from agents import config


class EaiouClient:
    def __init__(self):
        self._http = httpx.Client(
            base_url=config.BASE_URL,
            auth=(config.NGINX_USER, config.NGINX_PASS),
            follow_redirects=True,
            timeout=60.0,
        )

    # ── Auth ──────────────────────────────────────────────────────────────────

    def login(self) -> None:
        resp = self._http.post(
            "/auth/login",
            data={"username": config.ADMIN_USER, "password": config.ADMIN_PASS},
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Login failed: HTTP {resp.status_code}")

    # ── Paper lifecycle ───────────────────────────────────────────────────────

    def submit_paper(
        self,
        title: str,
        abstract: str,
        author_name: str,
        orcid: str,
        keywords: str,
        ai_disclosure_level: str = "collaborative",
        ai_disclosure_notes: str = "",
    ) -> int:
        """Submit a new paper. Returns paper_id extracted from redirect URL."""
        data = {
            "title": title,
            "abstract": abstract,
            "author_name": author_name,
            "orcid": orcid,
            "keywords": keywords,
            "ai_disclosure_level": ai_disclosure_level,
            "ai_disclosure_notes": ai_disclosure_notes,
            "attest_conceived": "on",
            "attest_methodology": "on",
            "attest_interpreted": "on",
            "attest_responsibility": "on",
        }
        resp = self._http.post("/author/submit", data=data)
        if resp.status_code not in (200, 303):
            raise RuntimeError(f"submit_paper failed: HTTP {resp.status_code} — {resp.text[:200]}")
        # After follow_redirects, resp.url = .../author/workspace/{paper_id}
        paper_id = int(str(resp.url).rstrip("/").split("/")[-1])
        return paper_id

    def generate_structure(self, title: str, hypothesis: str, keywords: str = "", gap_declaration: str = "") -> dict:
        resp = self._http.post("/author/api/structure", json={
            "title": title,
            "hypothesis": hypothesis,
            "keywords": keywords,
            "gap_declaration": gap_declaration,
        })
        resp.raise_for_status()
        return resp.json()

    def create_section(
        self,
        paper_id: int,
        section_name: str,
        section_order: int = 0,
        section_content: str = "",
        section_notes: str = "",
    ) -> dict:
        resp = self._http.post(
            f"/author/api/sections/{paper_id}",
            json={
                "section_name": section_name,
                "section_order": section_order,
                "section_content": section_content,
                "section_notes": section_notes,
            },
        )
        resp.raise_for_status()
        return resp.json()

    def seed_section(self, paper_id: int, section_id: int, content: str, seeded_from: str = "interrogation") -> dict:
        resp = self._http.post(
            f"/author/api/sections/{paper_id}/{section_id}/seed",
            json={"content": content, "seeded_from": seeded_from},
        )
        resp.raise_for_status()
        return resp.json()

    def interrogate(self, paper_id: int, question: str, expert_domain: str = "") -> dict:
        resp = self._http.post("/author/api/interrogate", json={
            "paper_id": paper_id,
            "question": question,
            "expert_domain": expert_domain,
        })
        resp.raise_for_status()
        return resp.json()

    def add_module(self, paper_id: int, role: str, display_label: str, model_id: str) -> dict:
        resp = self._http.post(f"/author/api/modules/{paper_id}", json={
            "role": role,
            "display_label": display_label,
            "provider": "anthropic",
            "model_id": model_id,
        })
        resp.raise_for_status()
        return resp.json()

    def module_read(self, paper_id: int, module_id: int) -> dict:
        resp = self._http.post(f"/author/api/modules/{paper_id}/{module_id}/read")
        resp.raise_for_status()
        return resp.json()

    def module_redteam(self, paper_id: int, module_id: int, focus: str = "") -> dict:
        resp = self._http.post(
            f"/author/api/modules/{paper_id}/{module_id}/redteam",
            json={"focus": focus},
        )
        resp.raise_for_status()
        return resp.json()

    def run_audit(self, paper_id: int) -> dict:
        resp = self._http.post(f"/author/api/audit/{paper_id}")
        resp.raise_for_status()
        return resp.json()

    def respond_to_audit(self, paper_id: int, round_number: int, author_response: str) -> dict:
        resp = self._http.post(
            f"/author/api/audit/{paper_id}/respond",
            json={"round_number": round_number, "author_response": author_response},
        )
        resp.raise_for_status()
        return resp.json()

    def check_gates(self, paper_id: int) -> dict:
        resp = self._http.get(f"/author/workspace/{paper_id}/gate")
        resp.raise_for_status()
        return resp.json()

    def seal_paper(self, paper_id: int) -> dict:
        resp = self._http.post(f"/author/workspace/{paper_id}/seal")
        if resp.status_code == 422:
            return {"sealed": False, "blocked": True, "detail": resp.json()}
        resp.raise_for_status()
        return resp.json()
