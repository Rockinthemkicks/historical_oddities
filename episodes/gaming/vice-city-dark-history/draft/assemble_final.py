"""Assembles the candidate final script (the corrected expansion) into the pilot production:
script.json + outline.json. Offline; production still needs the owner's stage approvals."""
import json, os, sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_expansion as be
from build_draft import REFERENCE_PROMPT, PILOT
from modules.gaming.script_engine import assemble_script

prod, dossier, rep, outline, chapters, results, orep, deps = be.build()
assert orep["passed"] and all(r["passed"] for r in results) and not any(d["omit"] for d in deps)
pr = json.load(open(os.path.join(PILOT, "production.json")))
pr["reference_prompt"] = REFERENCE_PROMPT
pr["extra_visuals"] = json.load(open(os.path.join(os.path.dirname(PILOT), "vice-city-60s-test", "production.json")))["extra_visuals"]
json.dump(pr, open(os.path.join(PILOT, "production.json"), "w"), indent=2, ensure_ascii=False)
script = assemble_script(pr, {"chapters": outline["chapters"]}, chapters)
script["status"] = "CANDIDATE FINAL (review 8) - production not approved"
json.dump(script, open(os.path.join(PILOT, "script.json"), "w"), indent=2, ensure_ascii=False)
json.dump({"status": "CANDIDATE FINAL (review 8)", "chapters": outline["chapters"]},
          open(os.path.join(PILOT, "outline.json"), "w"), indent=2, ensure_ascii=False)
print(len(script["scenes"]), "scenes,", sum(len(s["narration"].split()) for s in script["scenes"]), "words")
