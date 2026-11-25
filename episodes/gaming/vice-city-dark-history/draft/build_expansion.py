"""Proposed 10-12 minute expansion (review 7). Builds an EXPANDED copy of the approved draft; the approved
draft (build_draft.py) is not modified. Run from the repo root. No paid calls."""
import copy, json, os, sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_draft as bd
from modules.gaming.config import load_production
from modules.gaming.research import validate_dossier
from modules.gaming.script_engine import validate_chapter, validate_outline, outline_dependencies, word_budget

ill, reuse, card = bd.ill, bd.reuse, bd.card

NEW_CHAPTER = ("ch03b", "The Reluctant Empire", "Even the man who wanted out builds an empire.", 140, [
  ("Vic's way out of the Army leads straight into the rackets.", ["C53", "C11"],
   [bd.CARD, reuse("img_corporal_dock", "zoom_to:0.4,0.4,0.4")]),
  ("He goes to work for Marty Jay Williams, the leader of a street gang called the Trailer Park Mafia.", ["C53"],
   [ill("Tense, non-graphic. A run-down trailer park at dusk, string lights, a battered pickup truck, a cheap office trailer with its door ajar.", id="img_trailer")]),
  ("When Marty is killed, Louise suggests that Vic take over Marty's businesses. He does, and the gang becomes the Vance Crime Family.", ["C53", "C50"],
   [reuse("img_trailer", "zoom_in")]),
  ("Its businesses read like a map of the city's underground economy: protection, loan sharking, prostitution, drugs, smuggling and robbery.", ["C54"],
   [dict(card("rows", "THE VANCE EMPIRE, 1984", rows=[["PROTECTION", "", "protection"], ["LOANS", "", "loan"],
        ["VICE", "prostitution and drugs", "prostitution"], ["SMUGGLING", "", "smuggling"], ["ROBBERY", "", "robbery"]], motion="none"), reveal=True)]),
  ("So the reluctant soldier closes out 1984 as the head of a crime family, side by side with his brother. "
   "In this city, even the exit seems to run through the rackets.", ["C55", "C53"],
   [reuse("img_clockwork", "pan_right")]),
])

INSERT_CH06 = [
  ("The first person Tommy meets in Vice City isn't a gangster. It's a lawyer.", ["C56"],
   [ill("Calm, non-graphic. A nervous man in a rumpled 1980s suit waiting beside a boxy sedan outside an airport terminal at midday, palm trees, heat haze.", id="img_lawyer")]),
  ("Ken Rosenberg, the Forelli family's lawyer, picks Tommy up at the airport and drives him straight to the deal.", ["C56"],
   [reuse("img_lawyer", "zoom_in")]),
]

INSERT_CH06_GOLD = [
  ("In the opening scene, he says it plainly: Vice City is twenty-four carat gold these days.",
   ["C63"], [card("stamp", "\u201c24-CARAT GOLD\u201d", ["SONNY FORELLI, ON VICE CITY"])]),
]

INSERT_CH08_BANK = [
  ("Then there's the bank. From his new nightclub, the Malibu, Tommy plans a robbery of El Banco Corrupto Grande, a name that translates as the big corrupt bank.",
   ["C58"], [ill("Tense, non-graphic. A grand 1980s bank facade in a Cuban neighborhood at night, marble columns, a blank sign above the doors, an empty getaway van at the curb.", id="img_bank")]),
  ("Introducing his crew, Tommy jokes that Ken, the lawyer, washes the money for them.", ["C57"],
   [card("stamp", "“HE WASHES THE MONEY FOR US.”", ["TOMMY, ON HIS LAWYER"])]),
  ("Even the bank wears its corruption on its sign. It's the game's own satire, and it's hard to miss.", ["C61"], [reuse("img_bank", "zoom_to:0.5,0.25,0.5")]),
]

INSERT_CH08_APPRENTICE = [
  ("Taking notes through all of this is Avery's young protégé, Donald Love, who writes down the gang-war tactic in Two Bit Hit.", ["C59"],
   [ill("Calm, non-graphic. A young man in an oversized suit scribbling in a small notepad behind an older developer's shoulder, an architect's model on the desk between them.", id="img_protege")]),
  ("Years later, in Grand Theft Auto III, Love is a real-estate developer who owns a media company. Avery's playbook didn't stay in Vice City.", ["C60", "C62"],
   [reuse("img_protege", "zoom_in")]),
]

INSERT_CH10 = [
  ("Vic built an empire because the city left him little else. Rosenberg washed Tommy's money. Avery's protégé carried the playbook to another city.",
   ["C55", "C57", "C62"], [reuse("img_clockwork", "zoom_out")]),
]


SPEECH_WPS = 179 / 60          # measured in the revised 60-second test
MAX_HOLD = 7.5                  # seconds on one shot before it should move on (house pacing rule)
# Production approval (2026-11-25): fewer repeated push-ins. Reframes alternate a push-in to a detail
# with a slow lateral move or a pull-back, so consecutive shots don't all zoom.
REFRAMES = ["zoom_to:0.3,0.4,0.5", "pan_left", "zoom_to:0.7,0.55,0.5", "zoom_out", "zoom_to:0.5,0.3,0.45", "pan_right"]


def engagement_pass(chs):
    """Free visual variety for long lines: a second, reframed shot of the line's own image, or a
    row-by-row reveal for list cards. Never adds a paid image."""
    k = 0
    for cid, _, _, _, segs in chs:
        for i, sg in enumerate(segs):
            visuals = sg[2]
            secs = len(sg[0].split()) / SPEECH_WPS + (sg[3].get("pause_after", 0.45) if len(sg) > 3 else 0.45)
            if secs / max(len(visuals), 1) <= MAX_HOLD:
                continue
            for v in visuals:
                if v.get("kind") == "text_card" and v.get("rows") and not v.get("reveal"):
                    v["reveal"], v["motion"] = True, "none"
            src = next((v for v in reversed(visuals) if v.get("kind") in ("illustration", "reuse")), None)
            if src is None:
                continue
            if src.get("kind") == "illustration" and not src.get("id"):
                src["id"] = f"img_{cid}_{i}"
            of = src["of"] if src.get("kind") == "reuse" else src["id"]
            visuals.append(reuse(of, REFRAMES[k % len(REFRAMES)]))
            k += 1


def business_of_vice_visuals(chs):
    """Production approval (2026-11-25) asked for Chapter 9's visual pacing: it was a run of illustrations
    and push-ins. This swaps repeated zooms for an evidence board that builds mission by mission, a
    then-and-now card, the bank's name as typography and a closing board revealed on the narrator's words.
    Narration is unchanged; every visual is local (no paid images added)."""
    segs = next(c for c in chs if c[1] == "The Business of Vice")[4]

    def vis(start):
        return segs[find(segs, start)][2]

    def board(rows):
        return dict(card("rows", "AVERY'S JOBS", rows=rows, motion="none"), bg_of="img_model")

    jobs = [["FOUR IRON", "a rival developer killed"], ["DEMOLITION MAN", "a rival site destroyed"],
            ["TWO BIT HIT", "a gang war started"]]
    v = vis("Avery Carrington is a real-estate developer")
    v[0]["motion"] = "pan_right"
    vis("In Four Iron")[:] = [vis("In Four Iron")[0], board(jobs[:1])]
    vis("In Demolition Man")[:] = [vis("In Demolition Man")[0], board(jobs[:2])]
    plan = next(x for x in vis("In Two Bit Hit") if x.get("kind") == "text_card")
    vis("In Two Bit Hit")[:] = [dict(board(jobs), motion="zoom_in")]
    # the step-by-step plan now illustrates the line that describes the plan, revealed step by step
    vis("In Avery's plan")[:] = [dict(plan, motion="none", reveal=True, bg_of="img_model")]
    v = vis("Taking notes through all of this")
    v[:] = [v[0]]
    vis("Years later, in Grand Theft Auto III")[:] = [
        reuse("img_protege", "pan_left"),
        dict(card("rows", "THE APPRENTICE", rows=[["VICE CITY", "takes notes for Avery"],
                                                   ["GTA III", "developer, owns a media company"]], motion="none"),
             bg_of="img_protege")]
    v = vis("Tommy's own businesses")
    v[1:] = [reuse("img_printworks", "pan_left")]
    vis("Even the bank wears")[:] = [
        dict(card("title", "EL BANCO CORRUPTO GRANDE", ["“the big corrupt bank”"], motion="none"), bg_of="img_bank")]
    vis("A developer who uses murder")[:] = [
        dict(card("rows", "THE SYSTEM, 1986", rows=[["THE DEVELOPER", "murder wins the land", "developer"],
                                                     ["THE BUSINESS", "prints its own money", "business"],
                                                     ["THE CONGRESSMAN", "kept in line with photographs", "congressman"]],
                  motion="none"), reveal=True, bg_of="img_printworks")]


def find(segs, start):
    for i, sg in enumerate(segs):
        if sg[0].startswith(start):
            return i
    raise KeyError(start)


def expanded_chapters():
    chs = copy.deepcopy(bd.CHAPTERS)
    by = {c[0]: c for c in chs}
    # ch03b after ch03
    chs.insert([c[0] for c in chs].index("ch03") + 1, NEW_CHAPTER)
    s6 = by["ch06"][4]
    i = find(s6, "According to Tommy's lawyer")
    s6[find(s6, "On the other side"):find(s6, "On the other side") + 1] = [
        s6[find(s6, "On the other side")], INSERT_CH06_GOLD[0]]
    i = find(s6, "According to Tommy's lawyer")
    s6[i] = (s6[i][0].replace("According to Tommy's lawyer, Ken Rosenberg,", "According to Rosenberg,"),) + tuple(s6[i][1:])
    s6[i:i] = INSERT_CH06
    s8 = by["ch08"][4]
    s8[find(s8, "And when Congressman"):find(s8, "And when Congressman")] = INSERT_CH08_BANK
    s8[find(s8, "Tommy's own businesses"):find(s8, "Tommy's own businesses")] = INSERT_CH08_APPRENTICE
    s10 = by["ch10"][4]
    s10[find(s10, "The sergeant, the agent"):find(s10, "The sergeant, the agent")] = INSERT_CH10
    engagement_pass(chs)
    business_of_vice_visuals(chs)
    # renumber so chapter ids stay sequential (ch01..ch11)
    return [(f"ch{i + 1:02d}",) + tuple(c[1:]) for i, c in enumerate(chs)]


def build():
    orig = bd.CHAPTERS
    bd.CHAPTERS = expanded_chapters()
    try:
        out = bd.build()
    finally:
        bd.CHAPTERS = orig
    return out


if __name__ == "__main__":
    prod, dossier, rep, outline, chapters, results, orep, deps = build()
    here = os.path.dirname(os.path.abspath(__file__))
    json.dump({"status": "PROPOSED EXPANSION (review 7) - not approved; the approved draft is draft_chapters.json",
               "chapters": chapters}, open(os.path.join(here, "expanded_chapters.json"), "w"), indent=2, ensure_ascii=False)
    json.dump({"outline": outline, "outline_check": orep, "chapter_checks": results, "dependencies": deps},
              open(os.path.join(here, "expanded_checks.json"), "w"), indent=2, ensure_ascii=False)
    words = sum(r["words"] for r in results)
    print("outline:", orep["passed"], orep["errors"][:2])
    for r in results:
        print(r["chapter"], r["words"], "OK" if r["passed"] else r["errors"], r["warnings"][:2])
    print("total words", words, "~speech min at 158 wpm", round(words / 158, 1))
    print("omit:", [o for d in deps for o in d["omit"]])
