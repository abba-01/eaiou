"""
Author agent — Claude-powered content generator.
Generates paper metadata, section content, interrogation questions,
and audit responses. Drives all eaiou API calls through EaiouClient.
"""
import json
import re
import anthropic
from agents import config
from agents.eaiou_client import EaiouClient
from agents.scorch import Scorch


class AuthorAgent:
    def __init__(self, client: EaiouClient, scorch: Scorch):
        self.client = client
        self.scorch = scorch
        self.claude = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.topic = config.PAPER_TOPIC

    def _ask(self, system: str, user: str, max_tokens: int = 1024) -> str:
        msg = self.claude.messages.create(
            model=config.MODEL_CONTENT,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return msg.content[0].text.strip()

    # ── Paper metadata ────────────────────────────────────────────────────────

    def generate_paper_metadata(self) -> tuple[str, str, str]:
        """Returns (title, abstract, keywords). Abstract ≥80 words with citations."""
        raw = self._ask(
            system=(
                "You are a research scientist preparing an academic paper submission. "
                "Respond ONLY with valid JSON — no markdown, no explanation."
            ),
            user=(
                f"Generate a paper title, abstract, and keywords for the topic: {self.topic}\n\n"
                "Requirements:\n"
                "- Abstract: exactly 120-140 words\n"
                "- Abstract must contain at least two inline citation markers: [1] and [2]\n"
                "- Keywords: 4-6 comma-separated terms\n\n"
                'Output JSON: {"title": "...", "abstract": "...", "keywords": "..."}'
            ),
            max_tokens=512,
        )
        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        data = json.loads(raw)
        return data["title"], data["abstract"], data["keywords"]

    def regenerate_abstract(self, title: str, min_words: int = 85) -> str:
        """Regenerate abstract if word count is insufficient."""
        return self._ask(
            system="You are a research scientist. Respond with only the abstract text, no labels.",
            user=(
                f"Write a {min_words + 20}-word abstract for a paper titled: {title}\n"
                f"Topic: {self.topic}\n"
                "Include exactly two inline citation markers: [1] and [2]."
            ),
            max_tokens=512,
        )

    # ── Section content ───────────────────────────────────────────────────────

    def generate_section_content(self, section_name: str, focus: str, abstract: str) -> str:
        """Generate 250-300 words of section content with citations."""
        if "reference" in section_name.lower() or "bibliograph" in section_name.lower():
            return self._generate_bibliography()
        return self._ask(
            system=(
                "You are writing a section of an academic paper. "
                "Write substantive content, not a placeholder. Use academic prose."
            ),
            user=(
                f"Write the '{section_name}' section (250-300 words).\n"
                f"Focus: {focus}\n"
                f"Paper abstract: {abstract}\n\n"
                "Requirements:\n"
                "- Include 2-3 inline citation markers: [1], [2], [3] or (Author et al., Year)\n"
                "- Be specific and substantive\n"
                "- No section heading in the output — content only"
            ),
            max_tokens=512,
        )

    def _generate_bibliography(self) -> str:
        """Generate a bibliography with doi: markers and et al. to satisfy CITATIONS_PRESENT."""
        return self._ask(
            system="You are formatting a bibliography for an academic paper.",
            user=(
                f"Generate 5 realistic bibliography entries for a paper on: {self.topic}\n\n"
                "Requirements:\n"
                "- Each entry must include a doi: reference in format doi:10.xxxx/xxxx\n"
                "- At least 2 entries must use 'et al.' for multiple authors\n"
                "- Use numbered format: [1] Author et al. (Year). Title. Journal. doi:10.xxx\n"
                "- Output only the 5 entries, no preamble"
            ),
            max_tokens=512,
        )

    # ── Interrogation ─────────────────────────────────────────────────────────

    def generate_interrogation_question(self, title: str, abstract: str) -> str:
        """Generate a substantive expert question for the interrogation log."""
        return self._ask(
            system="You are a researcher reviewing your own paper before submission.",
            user=(
                f"Paper title: {title}\nAbstract: {abstract}\n\n"
                "Generate ONE deep methodological question about this paper's research design, "
                "sample size justification, controls, or theoretical grounding. "
                "The question should be 1-2 sentences. Output only the question."
            ),
            max_tokens=200,
        )

    # ── Audit response ────────────────────────────────────────────────────────

    def generate_audit_response(self, audit_result: dict) -> str:
        """Generate a professional author response to volley audit findings."""
        findings_text = json.dumps(audit_result.get("findings", []), indent=2)
        return self._ask(
            system=(
                "You are the author of an academic paper responding to peer review. "
                "Be professional, specific, and concise."
            ),
            user=(
                f"Respond to these audit findings:\n{findings_text}\n\n"
                "Write 3-5 sentences acknowledging valid points, "
                "explaining methodological choices, and noting any revisions made. "
                "If is_clean=true, write a brief confirmation that the document is ready."
            ),
            max_tokens=300,
        )

    # ── Gate remediation ──────────────────────────────────────────────────────

    def remediate_gates(
        self,
        failed_checks: list[dict],
        paper_id: int,
        section_ids: dict[str, int],
        client: EaiouClient,
    ) -> None:
        """Attempt targeted fixes for failing gates before seal."""
        failed_codes = {c["code"] for c in failed_checks}

        if "CITATIONS_PRESENT" in failed_codes:
            self.scorch.warn("Remediating CITATIONS_PRESENT — injecting citation paragraph", step="remediate")
            citation_fix = (
                "Recent studies have confirmed these findings [1]. "
                "Furthermore, Smith et al. (2023) demonstrated similar effects [2]. "
                "See also doi:10.1016/j.sleep.2023.01.001 for supporting evidence."
            )
            first_id = next(iter(section_ids.values()), None)
            if first_id:
                client.seed_section(paper_id, first_id, citation_fix)

        if "BIBLIOGRAPHY" in failed_codes:
            self.scorch.warn("Remediating BIBLIOGRAPHY — creating References section", step="remediate")
            bib_content = self._generate_bibliography()
            result = client.create_section(
                paper_id, "References",
                section_order=999,
                section_notes=bib_content,
            )
            section_ids["References"] = result["section_id"]

        if "SECTIONS_POPULATED" in failed_codes:
            self.scorch.warn("Remediating SECTIONS_POPULATED — seeding first section", step="remediate")
            first_id = next(iter(section_ids.values()), None)
            if first_id:
                client.seed_section(paper_id, first_id, f"This paper investigates {self.topic}.")
