"""
Approval stages for gaming-lore documentaries.

  0 topic       - topic proposal and duplicate check
  1 research    - research dossier and source verification   (research.json)
  2 outline     - chapter outline                            (outline.json)
  3 script      - full documentary script                    (script.json)
  4 storyboard  - visual storyboard and asset-rights review  (storyboard.json + assets/provenance.json)
  5 budget      - cost estimate and production approval      (estimate.json)
  6 generation  - narration and visual generation            (paid; needs 1-5)
  7 assembly    - assembly and quality control               (out/qc)
  8 publishing  - publishing package                         (publish/; needs 7)

An approval records a hash of the artifact as approved. If the file changes
afterwards, the approval no longer counts and the stage must be approved
again, so nothing paid or published runs on a version nobody saw.
"""
import hashlib
import json
import os
from datetime import datetime, timezone

STAGES = ["topic", "research", "outline", "script", "storyboard", "budget", "generation",
          "assembly", "publishing"]
ARTIFACTS = {
    "topic": ["production.json"],
    "research": ["research.json"],
    "outline": ["outline.json"],
    "script": ["script.json"],
    "storyboard": ["storyboard.json", "assets/provenance.json"],
    "budget": ["estimate.json"],
    "assembly": ["out/qc_report.json"],
    "publishing": ["publish/description.txt"],
}
REQUIRED_FOR_PAID = ["research", "outline", "script", "storyboard", "budget"]


class NotApproved(RuntimeError):
    pass


def _path(prod_dir):
    return os.path.join(prod_dir, "approvals.json")


def _hash(prod_dir, stage):
    h = hashlib.sha256()
    for rel in ARTIFACTS.get(stage, []):
        p = os.path.join(prod_dir, rel)
        h.update(rel.encode())
        if os.path.exists(p):
            with open(p, "rb") as f:
                h.update(f.read())
        else:
            h.update(b"<missing>")
    return h.hexdigest()


def load(prod_dir):
    p = _path(prod_dir)
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return {}


def approve(prod_dir, stage, by="owner", note=""):
    if stage not in STAGES:
        raise ValueError(f"unknown stage {stage!r}; stages: {STAGES}")
    missing = [rel for rel in ARTIFACTS.get(stage, []) if not os.path.exists(os.path.join(prod_dir, rel))]
    if missing:
        raise NotApproved(f"can't approve {stage}: missing {missing}")
    data = load(prod_dir)
    data[stage] = {"by": by, "note": note, "hash": _hash(prod_dir, stage),
                   "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    with open(_path(prod_dir), "w") as f:
        json.dump(data, f, indent=2)
    return data[stage]


def is_approved(prod_dir, stage):
    entry = load(prod_dir).get(stage)
    return bool(entry) and entry.get("hash") == _hash(prod_dir, stage)


def status(prod_dir):
    data = load(prod_dir)
    out = []
    for i, st in enumerate(STAGES):
        e = data.get(st)
        state = "approved" if is_approved(prod_dir, st) else ("changed since approval" if e else "pending")
        out.append({"stage": i, "name": st, "state": state})
    return out


def require(prod_dir, stages, purpose):
    missing = [s for s in stages if not is_approved(prod_dir, s)]
    if missing:
        raise NotApproved(f"{purpose} needs owner approval of: {', '.join(missing)} "
                          f"(approve with: python3 main.py --mode gaming-lore --production ... approve <stage>)")
