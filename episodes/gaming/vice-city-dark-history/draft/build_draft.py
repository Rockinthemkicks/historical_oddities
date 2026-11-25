"""Draft narration for review 4, written by Claude from the dossier (no paid API call).
Each segment lists the claims it rests on. Run from the repo root to rebuild draft files and checks."""
import json, os, sys
sys.path.insert(0, os.getcwd())
from modules.gaming.config import load_production
from modules.gaming.research import validate_dossier
from modules.gaming.script_engine import validate_chapter, outline_dependencies, validate_outline, word_budget

HERE = os.path.dirname(os.path.abspath(__file__))
PILOT = os.path.dirname(HERE)

def ill(p, id=None, motion=None):
    v = {"kind": "illustration", "prompt": p}
    if id: v["id"] = id
    if motion: v["motion"] = motion
    return v

def reuse(of, motion): return {"kind": "reuse", "of": of, "motion": motion}
def card(style, heading="", lines=(), rows=(), note=None, motion="zoom_in"):
    v = {"kind": "text_card", "style": style, "heading": heading, "lines": list(lines), "rows": [list(r) for r in rows],
         "motion": motion}
    if note: v["note"] = note
    return v

CARD = {"kind": "chapter_card"}

# Recurring original characters (reference sheets). Prompts never name game characters.
REFERENCE_PROMPT = (
    "Character reference sheet on a plain warm-grey background for an original character, 'the Corporal': "
    "a man in his late twenties with a tired, decent face, short cropped dark hair and light stubble. "
    "Three full-body views side by side (front, three-quarter, profile) wearing a plain olive army field jacket over a white T-shirt, "
    "plus a fourth view of the same man in civilian clothes: a pale blue short-sleeved shirt and dark trousers. "
    "Two small head studies (worried, resolved). Consistent proportions, clean even lighting, no text labels.")

CHAPTERS = [
 ("ch01", "The Man Who Tried to Leave", "Hook: Vic tried to escape; Tommy inherited the system.", 120, [
  ("Two years before Tommy Vercetti took over Vice City, another man was trying to escape it.", ["C08", "C32", "C22"],
   [ill("Calm, atmospheric, non-graphic. Wide establishing view of a fictional 1980s subtropical coastal city at dusk: pastel art-deco hotels "
        "along a beachfront boulevard, palm silhouettes, the first neon signs flickering on in pink and teal, a single speedboat wake "
        "heading out across the calm bay toward open sea. Signs are abstract glowing shapes with no letters.", id="img_waterfront", motion="zoom_in")]),
  ("His name was Victor Vance.", ["C10"],
   [card("stamp", "VICTOR VANCE", ["VICE CITY, 1984"])]),
  ("A soldier turned drug dealer, Vic had survived a corrupt sergeant, a war with a powerful cartel, and the loss of the woman he loved.",
   ["C10", "C11", "C15", "C16", "C50"],
   [ill("Somber, non-graphic. The Corporal from the reference sheet, in his olive army field jacket, standing alone at dawn outside the "
        "chain-link fence of a military airbase, hangars and palm trees behind him, looking back over his shoulder.", id="img_corporal_base", motion="pan_right"),
    ill("Somber, non-graphic. The Corporal from the reference sheet, in civilian clothes, sitting alone on a plastic chair in an empty "
        "hospital corridor at night, elbows on his knees, rain streaking the window beside him. Quiet grief.", id="img_corporal_hospital", motion="zoom_in")]),
  ("By the end of 1984, he was ready to leave it all behind.", ["C32", "C47"],
   [reuse("img_waterfront", "zoom_to:0.55,0.70,0.45")]),
  ("Two years later, he was back, at a drug deal that would end his life and begin Tommy Vercetti's rise to power.",
   ["C32", "C20", "C48"],
   [card("stamp", "1986", ["TWO YEARS LATER"], motion="zoom_out"),
    ill("Tense, non-graphic. The Corporal from the reference sheet, now in his pale blue civilian shirt, two years older, waiting at a "
        "folding table on a dark harbor pier at night, a closed briefcase in front of him, harbor lights and a moored freighter behind.",
        id="img_corporal_dock", motion="zoom_in")]),
  ("Vice City tells the story of Tommy building a criminal empire.", ["C48"],
   [ill("Somber, investigative, non-graphic. Surreal editorial illustration: an enormous brass clockwork mechanism whose gears are built "
        "from miniature city blocks, palm trees, hotel towers and neon tubes, glowing softly at dusk. At its center sits a single empty "
        "leather executive chair under a spotlight. Wide composition, deep perspective.", id="img_clockwork", motion="zoom_out")]),
  ("But the empire was already there.", ["C22", "C43"],
   [reuse("img_clockwork", "zoom_to:0.5,0.55,0.5")]),
  ("Behind the neon and the oceanfront mansions, a corrupt sergeant, rival drug lords and an undercover agent working both sides "
   "had been shaping the city since at least 1984.", ["C11", "C13", "C14", "C39", "C49"],
   [dict(card("rows", "VICE CITY, 1984", rows=[["THE SERGEANT", "running drugs for a cartel", "sergeant"],
                                              ["THE DRUG LORDS", "the Mendez brothers, Ricardo Diaz", "drug"],
                                              ["THE AGENT", "selling deal information", "agent"]], motion="none"),
         reveal=True)]),
  ("Tommy didn't invent the system.", ["C43"], [reuse("img_clockwork", "zoom_to:0.5,0.6,0.9")], {"pause_after": 1.3}),
  ("He inherited it.", ["C43"],
   [card("title", "THE DARK HISTORY OF VICE CITY", ["Before GTA 6", "An Unplayed History documentary"], motion="zoom_in",
         note="Illustrations are original artwork, not game footage.")], {"pause_after": 3.0}),
 ]),
 ("ch02", "Which Vice City?", "Continuity in about 20-30 seconds.", 60, [
  ("First, which Vice City is this?", ["C51", "C52"],
   [card("rows", "THREE VICE CITIES", rows=[["1997", "Grand Theft Auto  ·  2D"], ["1984-86", "Vice City Stories  ·  Vice City  ·  3D"],
                                            ["2026", "GTA VI  ·  HD"]],
         motion="none")]),
  ("Vice City Stories, set in 1984, and Vice City, set in 1986, share one continuity: the series' 3D era.", ["C08", "C51"],
   [reuse("v_continuity", "zoom_to:0.3,0.5,0.25")]),
  ("Grand Theft Auto VI's modern Vice City, in the fictional state of Leonida, belongs to a separate continuity.", ["C05", "C52"],
   [ill("Calm, non-graphic. A modern subtropical city skyline at night reflected in wet asphalt, glass towers and LED billboards with "
        "no readable text, clearly present-day, a strong contrast with 1980s pastel architecture.", id="img_modern", motion="pan_left")]),
  ("This is the story of the older city. It isn't GTA VI's backstory, and it won't spoil GTA VI.", ["C51", "C52"],
   [reuse("img_waterfront", "pan_right")]),
 ]),
 ("ch03", "The Sergeant", "An Army sergeant inside the cartel trade.", 150, [
  ("In 1984, Victor Vance is an Army corporal at Fort Baxter, on the edge of Vice City.", ["C08", "C10"], [CARD, reuse("img_corporal_base", "zoom_in")]),
  ("He needs money for his brother Pete's asthma medication.", ["C31"],
   [ill("Somber, non-graphic. A small inhaler and a stack of unpaid pharmacy bills on a kitchen table in a cramped apartment, late afternoon light.")]),
  ("His sergeant, Jerry Martinez, runs a secret drug business, and Vic is drawn in as a reluctant middleman.", ["C11"],
   [ill("Tense, non-graphic. A sergeant's silhouette in a barracks doorway, a duffel bag on the floor, the Corporal from the reference sheet watching warily.")]),
  ("Then Martinez frames him. Drugs are found, there's a sex worker in Vic's car, and Vic is dishonorably discharged.", ["C11"],
   [card("stamp", "DISHONORABLE DISCHARGE", ["FORT BAXTER, 1984"])]),
  ("Vic later learns whose cocaine Martinez had been moving: the Mendez brothers', the most powerful drug family in the city.", ["C12", "C13"],
   [card("rows", "THE SUPPLY LINE", rows=[["THE SERGEANT", "moves the shipment"], ["THE CARTEL", "owns it"]])]),
  ("An Army sergeant, working as a courier for a cartel.", ["C12"], [reuse("img_corporal_base", "pan_left")]),
  ("Vic, meanwhile, keeps saying he wants out of the drug game. When Lance offers him twenty kilos of cocaine to get started, he turns it down.",
   ["C47"], [ill("Somber, non-graphic. Two brothers in a cramped apartment; one holds out a heavy taped package, the other, the Corporal from the reference sheet, turns away toward the window.")]),
 ]),
 ("ch04", "The Agent", "An undercover agent selling information; individuals, not institutions.", 130, [
  ("Then there's Bryan Forbes, an undercover agent who sells the Vance brothers information about drug deals.", ["C39"],
   [CARD, ill("Tense, non-graphic. A man in sunglasses and a cheap suit in a diner booth sliding a folded note across the table.")]),
  ("Forbes's own ID becomes part of the scheme. In The Mugshot Longshot, Lance pastes Martinez's photo onto it, "
   "to convince the Mendez brothers that their sergeant is working for the law.", ["C41"],
   [ill("Investigative, non-graphic. Close-up of a laminated ID card on a desk, a photo being replaced with scissors and glue, no readable text.")]),
  ("An agent selling tips to dealers. A sergeant running cocaine for a cartel.", ["C39", "C12"],
   [card("rows", "1984", rows=[["THE AGENT", "sells deal information"], ["THE SERGEANT", "moves cartel cocaine"]])]),
  ("Neither proves the whole Army or the whole police force was corrupt, and the games never say so.", ["C42"], [reuse("v_agentcard", "zoom_out")]),
  ("But in these cases, the men trusted to stand between Vice City and its drug trade were already part of it.", ["C42"],
   [reuse("img_clockwork", "pan_right")]),
 ]),
 ("ch05", "The Cartel's Tower", "The Mendez war, Diaz's maneuvering, Last Stand.", 210, [
  ("The Mendez brothers, Armando and Diego, run the 1984 drug trade from a downtown tower also known as the Mendez Foundation building.", ["C13"],
   [CARD, ill("Cold, ominous, non-graphic. Night view of an imposing 1980s downtown skyscraper with a smoked-glass facade and a lit marble lobby; "
              "a blank polished brass plaque beside the revolving door; two black limousines idle at the curb.", id="img_tower")]),
  ("A charitable-sounding name on a cartel's headquarters. A small detail, and a telling one.", ["C13"], [reuse("img_tower", "zoom_to:0.45,0.8,0.6")]),
  ("The brothers use the Vances for a few jobs, then betray them, and Vic goes to war with the cartel.", ["C15"],
   [ill("Tense, non-graphic. A rain-soaked street at night outside a cartel nightclub, the Corporal from the reference sheet stepping out of a car, neon reflections.")]),
  ("It costs him dearly. Louise, the woman he loves, dies after the Mendez brothers kidnap her, and Armando is killed at the Mendez mansion.",
   ["C16", "C50"], [reuse("img_corporal_hospital", "zoom_out")]),
  ("Vic's last backer is a rival drug baron, Ricardo Diaz, who gives him work against the Mendez operation.", ["C14"],
   [ill("Tense, non-graphic. A flamboyant drug baron's office: gold fixtures, a wall of security monitors, a man's silhouette behind a desk, cigar smoke.")]),
  ("Diaz is already maneuvering. That same year he blackmails Gonzalez, the right-hand man of a retired colonel, for information on the colonel's drug shipments, "
   "as part of his plan to become the city's drug baron.", ["C49", "C34"],
   [card("rows", "DIAZ, 1984", rows=[["BLACKMAILS", "the colonel's right-hand man"], ["WANTS", "the shipment routes"], ["GOAL", "the city's drug trade"]])]),
  ("The final mission, Last Stand, is a job for Diaz. Vic attacks the Mendez building from the air and kills Diego Mendez and Martinez on the roof.",
   ["C38", "C14"], [ill("Somber, non-graphic. A skyscraper rooftop at sunrise after a storm, a military helicopter silhouette pulling away, scattered papers in the wind.")]),
  ("Then Vic and Lance decide to leave town and lay low.", ["C32"], [reuse("img_waterfront", "zoom_to:0.55,0.7,0.6")]),
  ("Lance suggests hiding the leftover cocaine and selling it later. Vic's answer is flat: he is not interested.", ["C65"],
   [card("stamp", "\u201cI AM NOT INTERESTED.\u201d", ["VIC VANCE, 1984"])]),
 ]),
 ("ch06", "The Exchange", "1986: the colonel, the leak, the ambush.", 150, [
  ("Two years later, Vic is back at a deal table. The games never show how he returned.", ["C32"], [CARD, reuse("img_corporal_dock", "zoom_out")]),
  ("On the other side of that table is Tommy Vercetti. Sonny Forelli has sent him south to keep him out of Liberty City and to get the family a cut of the drug money.",
   ["C19", "C63"],
   [ill("Somber, non-graphic. A dimly lit northern restaurant back room, a heavy man's silhouette at a table pushing a plane ticket forward.", id="img_backroom")]),
  ("According to Tommy's lawyer, Ken Rosenberg, the deal was set up with help from a retired colonel, Juan Garcia Cortez.", ["C33"],
   [ill("Calm, non-graphic. A luxury yacht moored at a marina at golden hour, an older man in a white jacket on deck seen from far away.", id="img_yacht")]),
  ("The deal is ambushed. Vic and two Forelli men are killed, the money and the cocaine are taken, and Lance escapes.", ["C20"],
   [ill("Somber, non-graphic. An empty dock at night, an open briefcase on the boards, a helicopter's lights pulling away over the water.")]),
  ("Cortez later tells Tommy who talked: his own right-hand man, Gonzalez, gave away information about the deal. Tommy kills him in Treacherous Swine.",
   ["C34"], [reuse("img_yacht", "zoom_in")]),
  ("The game never says who Gonzalez talked to. But two years earlier, Diaz had blackmailed him for information on Cortez's shipments.",
   ["C34", "C49"], [card("rows", "THE LEAK", rows=[["1984", "Diaz blackmails Gonzalez"], ["1986", "Gonzalez leaks the deal"], ["RECIPIENT", "never named"]])]),
 ]),
 ("ch07", "The Heir", "Tommy takes over Diaz's empire.", 110, [
  ("Tommy goes to work for Diaz. Lance, working alongside him, learns that Diaz's gang carried out the ambush.", ["C21"],
   [CARD, reuse("v_diazoffice", "zoom_in")]),
  ("Together they storm Diaz's mansion on Starfish Island and kill him, and Tommy takes the mansion and Diaz's empire.", ["C22"],
   [ill("Somber, non-graphic. A grand island mansion at night, marble staircase, shattered chandelier light across an empty floor.", id="img_mansion")]),
  ("From there, Tommy rises to become Vice City's major criminal power.", ["C48"],
   [ill("Somber, non-graphic. A broad-shouldered man in an ivory linen suit standing alone in a huge mansion office, his back to us, looking out over a bay at dawn.", id="img_newcomer")]),
  ("But the mansion and the drug empire he builds on belonged to Diaz first.", ["C22", "C43"], [reuse("img_mansion", "pan_left")]),
  ("Lance stays at his side, but he starts to feel underappreciated in a rise he helped begin.", ["C25"],
   [ill("Somber, non-graphic. A man in a white suit and aviator sunglasses leaning alone on a balcony rail at a party, the crowd blurred behind him.")]),
 ]),
 ("ch08", "The Business of Vice", "Economic corruption in 1986.", 250, [
  ("Drugs weren't the only business in Tommy's Vice City.", ["C46", "C45"], [CARD, reuse("img_clockwork", "pan_left")]),
  ("Avery Carrington is a real-estate developer who gives Tommy work in a set of optional side missions.", ["C46"],
   [ill("Calm, non-graphic. An architect's scale model of a waterfront district under a desk lamp, a gold pen and a land deed beside it, no readable text.", id="img_model")]),
  ("In Four Iron, a rival developer won't sell Avery some land, and Tommy kills him on a golf course.", ["C46"],
   [ill("Tense, non-graphic. An empty golf course at dawn, a single golf cart abandoned on the fairway, a dropped club in the grass.")]),
  ("In Demolition Man, a competing construction site is in Avery's way, and Tommy blows it up.", ["C46"],
   [ill("Tense, non-graphic. A half-built tower wrapped in scaffolding at dusk, a small remote-control helicopter hovering near an upper floor.")]),
  ("In Two Bit Hit, Avery puts it plainly: nothing brings down real estate prices quicker than a good old-fashioned gang war.", ["C36"],
   [card("rows", "AVERY'S PLAN", rows=[["STEP 1", "start a gang war"], ["STEP 2", "prices fall"], ["STEP 3", "buy cheap"]])]),
  ("Tommy dresses as a Cuban gang member and attacks a Haitian funeral, so the two gangs go to war.", ["C35"],
   [ill("Somber, non-graphic. A funeral parlor exterior in the rain, black umbrellas, a lone figure in borrowed colors watching from across the street.")]),
  ("In Avery's plan, violence is simply a way to move the market.", ["C36"], [reuse("img_model", "zoom_to:0.5,0.5,0.5")]),
  ("Tommy's own businesses run on similar logic. At the Print Works, the foreman suggests printing money, "
   "and Tommy steals a courier's printing plates to start counterfeiting.", ["C45"],
   [ill("Investigative, non-graphic. Sheets of freshly printed banknotes drying on lines in a dim print shop, no readable text or faces on the notes.", id="img_printworks")]),
  ("And when Congressman Alex Shrub moves to ban pornography to win puritan votes, Tommy, who now owns a film studio, "
   "gets incriminating photos of the congressman to stop him.", ["C44"],
   [ill("Investigative, non-graphic. An envelope of photographs on a polished desk under a green banker's lamp, a lapel pin beside it, no faces visible.")]),
  ("A developer who uses murder to win land. A business that prints its own money. A congressman kept in line with photographs.",
   ["C46", "C45", "C44"], [reuse("img_printworks", "pan_right")]),
  ("By 1986, Tommy isn't outside Vice City's system. He's fluent in it.", ["C48", "C43"], [reuse("img_newcomer", "zoom_in")]),
 ]),
 ("ch09", "This Is Business", "The finale: what is said, and what is only implied.", 120, [
  ("The counterfeit money has one destination: Sonny Forelli, who comes south to collect.", ["C23", "C45"],
   [CARD, ill("Tense, non-graphic. A mansion foyer at night, men in dark coats on a staircase, one older man in front, faces in shadow.", id="img_foyer")]),
  ("Sonny arrives joking about Tommy's old nickname: the Harwood Butcher.", ["C18", "C24"],
   [reuse("img_foyer", "zoom_in")]),
  # Corrected 2026-11-25 against two mission transcripts: Sonny's "fifteen years" line answers Tommy's later
  # "you took fifteen years from me", after Lance's betrayal and death, not the "they knew I was coming" line.
  ("Tommy says he was sent to kill one man, and they knew he was coming.",
   ["C24"], [ill("Tense, non-graphic. Two silhouettes facing each other across a long marble floor, a single beam of light between them.", id="img_faceoff")]),
  ("Lance has already switched sides. He tells Sonny about the fake money.", ["C23"], [reuse("img_foyer", "pan_right")]),
  ("Lance's explanation for the betrayal is short: this is business.", ["C23", "C25"], [card("stamp", "\u201cTHIS IS BUSINESS.\u201d", [""])]),
  ("Tommy kills Lance. Then, face to face, he tells Sonny those fifteen years were taken from him. Sonny's answer: they were his to spend.",
   ["C23", "C24"], [ill("Somber, non-graphic. A rooftop at night above the city lights, a broken pair of aviator sunglasses on the ledge."),
                    reuse("img_faceoff", "zoom_to:0.5,0.5,0.4")]),
  ("It lands as a confession.", ["C64"], [reuse("img_faceoff", "zoom_to:0.5,0.5,0.6")], {"pause_after": 1.0}),
  ("Then Tommy kills him too.", ["C23"], [reuse("img_foyer", "zoom_out")]),
 ]),
 ("ch10", "Built on Crime", "Conclusion: the exit and the keys.", 110, [
  ("Two men, two years apart.", ["C08"], [CARD, ill("Somber, non-graphic. Split composition: a dark harbor pier at night on the left, a mansion balcony at dawn on the right, the same bay between them.", id="img_split")]),
  ("Vic Vance said he wanted out, and the city brought him back to a deal table where he died.", ["C47", "C32", "C20"], [reuse("img_corporal_dock", "zoom_out")]),
  ("Tommy Vercetti wanted the top, and he got it.", ["C48"], [reuse("img_newcomer", "zoom_out")]),
  ("The difference is that Vic kept looking for the exit, and Tommy went looking for the keys.", ["C47", "C48"],
   [ill("Somber, non-graphic. A man's hand dropping a ring of keys onto a mahogany desk, a second hand reaching for a door handle, both in shadow.")]),
  ("The sergeant, the agent, the cartel and the colonel were all there before Tommy arrived.", ["C42", "C13", "C49"], [reuse("v_rows1984", "zoom_in")]),
  ("The evidence points one way. Tommy didn't corrupt Vice City. He inherited it.", ["C43"],
   [ill("Somber, dramatic, non-graphic. An old, generic badge with no insignia or lettering lies cracked on a wet seawall railing in the foreground; "
        "behind it, out of focus, the neon-lit 1980s coastal skyline at dusk in magenta and teal.", id="img_badge"),
    dict(card("title", "UNPLAYED HISTORY", ["Sources for every claim are linked in the description."], motion="none"), bg_of="img_badge")],
   {"pause_after": 4.0}),
 ]),
]

# visual ids referenced by reuse that need explicit ids on their source
NAMED = {("ch02", 0, 0): "v_continuity", ("ch04", 2, 0): "v_agentcard", ("ch05", 4, 0): "v_diazoffice", ("ch01", 7, 0): "v_rows1984"}
for cid, _, _, _, segs in CHAPTERS:
    for (key, vid) in NAMED.items():
        if key[0] == cid:
            segs[key[1]][2][key[2]]["id"] = vid


def build():
    prod = load_production(os.path.join(PILOT, "production.json"))
    dossier = json.load(open(os.path.join(PILOT, "research.json")))
    rep = validate_dossier(dossier, prod)
    outline = {"status": "PROPOSED (review 4) - not approved", "title": prod["title"], "chapters": [
        {"id": cid, "title": t, "purpose": p, "target_words": tw,
         "claim_ids": sorted({c for seg in segs for c in seg[1]}, key=lambda x: int(x[1:]))}
        for cid, t, p, tw, segs in CHAPTERS]}
    chapters, results, earlier = [], [], []
    for (cid, t, p, tw, segs), och in zip(CHAPTERS, outline["chapters"]):
        ch = {"chapter_id": cid, "summary": p,
              "segments": [{"narration": sg[0], "claim_ids": sg[1], "visuals": sg[2], **(sg[3] if len(sg) > 3 else {})}
                           for sg in segs]}
        r = validate_chapter(ch, och, dossier, earlier)
        results.append({"chapter": cid, **r})
        earlier.append(ch)
        chapters.append(ch)
    budget = word_budget(prod["target_minutes"])
    orep = validate_outline(outline, dossier, budget)
    deps = outline_dependencies(outline, rep["readiness"])
    return prod, dossier, rep, outline, chapters, results, orep, deps


if __name__ == "__main__":
    prod, dossier, rep, outline, chapters, results, orep, deps = build()
    json.dump(outline, open(os.path.join(PILOT, "outline_proposed.json"), "w"), indent=2)
    json.dump({"status": "DRAFT - not approved", "chapters": chapters}, open(os.path.join(HERE, "draft_chapters.json"), "w"), indent=2)
    json.dump({"outline_check": orep, "chapter_checks": results, "dependencies": deps},
              open(os.path.join(HERE, "draft_checks.json"), "w"), indent=2)
    words = sum(r["words"] for r in results)
    print("outline:", orep["passed"], orep["errors"])
    for r in results:
        print(r["chapter"], r["words"], "OK" if r["passed"] else r["errors"], r["warnings"])
    print("total words", words, "minutes", round(words / 140, 1))
    print("omit:", [o for d in deps for o in d["omit"]])
