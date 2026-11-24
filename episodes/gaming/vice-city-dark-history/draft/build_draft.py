"""Draft narration for review 4, written by Claude from the dossier (no paid API call).
Each segment lists the claims it rests on. Run from the repo root to rebuild draft files and checks."""
import json, os, sys
sys.path.insert(0, os.getcwd())
from modules.gaming.config import load_production
from modules.gaming.research import validate_dossier
from modules.gaming.script_engine import validate_chapter, outline_dependencies, validate_outline, word_budget

HERE = os.path.dirname(os.path.abspath(__file__))
PILOT = os.path.dirname(HERE)

def ill(p): return {"kind": "illustration", "prompt": p}
CARD = {"kind": "chapter_card"}

CHAPTERS = [
 ("ch01", "The Man at the Docks", "Hook: the dealer who wanted out; thesis.", 170, [
  ("Vice City, 1986. A boat cuts across a bay lined with pastel hotels and new money. On board is a man just out of fifteen years in prison, "
   "sent south by his old crime family to oversee a drug deal.", ["C18", "C19"],
   [CARD, ill("dusk over a pastel art-deco waterfront, a lone speedboat wake, neon signs flickering on")]),
  ("Waiting at the exchange is a dealer named Victor Vance. Two years earlier, Vic had tried to walk away from all of it. "
   "He told his brother he wanted to stay away from drugs. After a war that cost him nearly everything, the brothers decided to leave town and lay low.",
   ["C47", "C16", "C32"], [ill("a tired young man in a plain shirt at a dock table, a closed briefcase in front of him, harbor lights behind")]),
  ("Now he's back at a deal table, and the deal is ambushed. Vic and two of the newcomer's men are killed. The money and the cocaine are gone. Vic's brother Lance escapes.",
   ["C20"], [ill("an empty dock at night, an open briefcase on the boards, a helicopter's lights pulling away over the water")]),
  ("The newcomer is Tommy Vercetti, and the usual story says Vice City's crime begins with him. It doesn't. "
   "An Army sergeant, an undercover agent, a cartel and a property developer were already running the machine. Tommy walked into it, and took it over.",
   ["C48", "C42", "C46", "C43"], [ill("a vast clockwork mechanism built from city blocks, palm trees and neon, one empty seat at its center")]),
 ]),
 ("ch02", "Before GTA 6, Another Vice City", "Continuity: this is the 3D-era city, not GTA VI's backstory.", 190, [
  ("First, which Vice City is this? Grand Theft Auto VI came out on November 19, 2026. It's set in the state of Leonida, "
   "and Rockstar describes its Vice City as the darkest side of the sunniest place in America.", ["C01", "C05", "C06"],
   [{"kind": "timeline", "prompt": "Vice City across the series: 1997, 2002, 2006, 2026"}]),
  ("That launch was enormous. Take-Two says the game made 3.79 billion dollars in day-one retail sales, its own figure, "
   "while the analytics firm Sensor Tower estimated about 1.84 billion by release day. Either way, millions of people are now walking Vice City's streets.",
   ["C02"], [{"kind": "timeline", "prompt": "Two bars: company-reported day-one figure vs third-party estimate, labelled by source"}]),
  ("This video is not about that city's backstory. The name goes back to the first Grand Theft Auto in 1997, a top-down game "
   "in its own separate continuity, where Vice City was one of three cities and a stand-in for Miami.", ["C03", "C04"],
   [ill("a hand-drawn top-down street map of a coastal city on a drafting table, coffee ring, pencil")]),
  ("Our story belongs to the 3D era: Vice City Stories, set in 1984, and Vice City, set two years later in 1986. "
   "Different games, different continuities, the same name on the map. We'll keep them apart.", ["C08", "C03"],
   [{"kind": "timeline", "prompt": "Three continuities side by side: 2D (1997), 3D (1984-1986), HD (GTA VI)"}]),
  ("GTA VI has its own Vice City and its own leads, Jason and Lucia. Nothing in this video is that game's official history, and none of it spoils that story.",
   ["C07", "C05"], [ill("a modern neon skyline at night reflected in wet asphalt, deliberately different in era from the 1980s scenes")]),
 ]),
 ("ch03", "The Sergeant", "Institution 1: an Army sergeant inside the cartel trade.", 210, [
  ("In 1984, Victor Vance is an Army corporal at Fort Baxter, the base on the edge of the city. He needs money for his brother Pete's asthma medication, "
   "and that need is the lever his sergeant pulls.", ["C10", "C31"],
   [CARD, ill("a military airbase at dawn behind a chain-link fence, palm trees, a young corporal walking alone")]),
  ("Sergeant Jerry Martinez runs a secret drug business and uses Vic to do his jobs. When Vic stops being useful, Martinez sets him up. "
   "Drugs are found, there's a sex worker in Vic's car, and Vic is thrown out of the Army with a dishonorable discharge.", ["C11"],
   [ill("a sergeant's silhouette in a doorway, a duffel bag of contraband on a barracks floor, harsh overhead light")]),
  ("Here is the detail that matters. After Vic and Lance take a shipment of cocaine from Martinez, they find out whose it really was. "
   "It belonged to the Mendez brothers, the most powerful drug family in the city. Martinez wasn't a lone dealer in uniform. "
   "An Army sergeant was working as a courier for a cartel.", ["C12", "C13"],
   [{"kind": "evidence_board", "prompt": "Sergeant -> shipment -> cartel tower, red string"}]),
  ("And Vic? Again and again he says he wants out of the drug game but has no choice. When Lance offers him twenty kilos of cocaine to get started, he turns it down. "
   "Hold on to that. This is the story of a man who wanted out of the system, and another who wanted to own it.", ["C47", "C48"],
   [ill("two brothers in a cramped apartment, one holding out a heavy package, the other turning away toward a window")]),
 ]),
 ("ch04", "The Agent", "Institution 2: an undercover agent selling information.", 180, [
  ("Vic's next contact is Bryan Forbes, an undercover agent who sells the Vance brothers information about drug deals. "
   "The sources we could check disagree about which agency he works for, so we won't name one.", ["C39"],
   [CARD, ill("a man in sunglasses and a cheap suit in a diner booth sliding a folded note across the table")]),
  ("His ID becomes a weapon. In a mission called The Mugshot Longshot, Lance pastes the sergeant's photo onto Forbes's ID, "
   "to convince the Mendez brothers that Martinez himself is working for the law.", ["C41"],
   [ill("close-up of a laminated ID card on a desk, a photo being replaced with scissors and glue, no readable text")]),
  ("Think about what that trick depends on. It only works in a city where everyone assumes the law is just another buyer at the table. "
   "In our reading, the badge isn't a threat to the drug trade here. It's a currency inside it.", ["C41", "C42"],
   [ill("a badge-shaped poker chip on a green felt table among stacks of cash, cigar smoke, hands at the edges of the frame")]),
  ("By 1984, then, a sergeant is moving cartel cocaine and an undercover agent is selling information to dealers. "
   "That doesn't prove the whole Army or the whole police force was corrupt, and the games never claim it. "
   "What they show is narrower and maybe more unsettling: the individuals trusted to stand between the city and its drug trade were already inside it.",
   ["C42"], [{"kind": "evidence_board", "prompt": "Two figures with official roles linked to the drug trade; caption 'individuals, not institutions'"}]),
 ]),
 ("ch05", "The Cartel's Tower", "The Mendez war, Diaz's maneuvering, and 'Last Stand'.", 250, [
  ("The Mendez brothers, Armando and Diego, rule the 1984 drug trade from a downtown tower known as the Mendez Foundation building. "
   "A foundation's name on a cartel headquarters is a small detail. Our reading: it fits a city where crime liked to look respectable.",
   ["C13"], [CARD, ill("a gleaming downtown skyscraper at night with a blank brass plaque at its entrance, limousines at the curb")]),
  ("They use the Vance brothers for a few jobs, then betray them, and Vic goes to war. It costs him dearly. "
   "Louise, one of the people closest to him, dies after the Mendez brothers kidnap her, and Armando is killed at the Mendez mansion.",
   ["C15", "C16"], [ill("an empty hospital corridor at night, a single chair, rain on the window")]),
  ("Vic's last ally is a rival drug baron, Ricardo Diaz, who gives him work against the Mendez operation. "
   "Diaz is already maneuvering. That same year he blackmails Gonzalez, the right-hand man of a retired colonel named Cortez, "
   "for information on the colonel's drug shipments, as part of his plan to become the city's drug baron.", ["C14", "C49"],
   [{"kind": "evidence_board", "prompt": "Diaz -> Gonzalez (blackmail) -> Colonel's shipments"}]),
  ("The final mission, Last Stand, is a job for Diaz. Vic attacks the Mendez building from the air and kills Diego Mendez and Sergeant Martinez on the roof. "
   "Then he and Lance decide to leave town and lay low. Vic had escaped. For now.", ["C38", "C32"],
   [ill("a skyscraper rooftop at sunrise after a storm, a helicopter silhouette departing, scattered papers in the wind")]),
  ("Step back and look at who gave the order. Vic did the fighting, but Last Stand was Diaz's job, aimed at Diaz's biggest rivals. "
   "Our inference is that Diaz is the one who stands to gain most from that rooftop. The games don't show how he spends the next two years, so we won't fill that gap.",
   ["C14", "C38"], [{"kind": "evidence_board", "prompt": "Rooftop photo pinned at center; strings to 'who fought' and 'who ordered'"}]),
 ]),
 ("ch06", "The Exchange", "1986: the colonel, the leak, the ambush.", 160, [
  ("Two years later, Vic is back at a deal table, and the games never show how he got back in. "
   "According to Tommy's lawyer, Ken Rosenberg, the retired colonel Juan Garcia Cortez helped set the exchange up. "
   "Two years after a sergeant ran cocaine through Fort Baxter, a retired colonel is helping arrange a cocaine deal. Military rank, again, sitting inside the trade.", ["C32", "C33", "C11"],
   [CARD, ill("a luxury yacht moored at a marina at golden hour, an older man in a white dress uniform jacket on deck, seen from far away")]),
  ("Sonny Forelli sent Tommy to profit from the city's growing drug trade. We've seen how that ended: an ambush, two dead Forelli men, a dead dealer, and the money gone.",
   ["C19", "C20"], [ill("a newspaper on a café table, coffee steaming, the headline area left blank, palm shadows")]),
  ("Cortez later tells Tommy who talked: his own right-hand man, Gonzalez, gave away information about the deal. "
   "Tommy kills him in a mission called Treacherous Swine. Notice the shape of that betrayal. The leak didn't come from the street. "
   "It came from inside a colonel's own circle.", ["C34", "C33"],
   [ill("a penthouse balcony at night, curtains blowing, a figure running for the stairs")]),
  ("Who received that information, the game never says outright. It's implied to be Diaz, and the 1984 blackmail suggests the line ran through Gonzalez long before Tommy arrived. "
   "That connection is our inference, not something the games state.", ["C34", "C49"],
   [{"kind": "evidence_board", "prompt": "1984 blackmail and 1986 leak, dotted line marked 'implied'"}]),
 ]),
 ("ch07", "The Heir", "Tommy inherits Diaz's empire.", 160, [
  ("Tommy goes to work for Diaz. It's Lance, working alongside him, who learns that Diaz's gang carried out the ambush. "
   "The two of them storm Diaz's mansion on Starfish Island, kill him, and Tommy moves in and takes over the operation.", ["C21", "C22"],
   [CARD, ill("a grand island mansion at night, marble staircase, shattered chandelier light across the floor")]),
  ("This is usually told as Tommy's rise, and he does rise, to become the city's major criminal power. "
   "But look at what he actually acquires: a mansion, a drug empire and a set of relationships that Diaz had already built.", ["C48", "C43"],
   [ill("a man in a ivory linen suit standing alone in a huge mansion office, his back to us, looking out over a bay")]),
  ("From the mansion, Tommy spreads into businesses across the city. Lance stays at his side, but the story shows Lance starting to feel underappreciated, "
   "pushed to the edge of a rise he helped start. That resentment will matter at the end.", ["C22", "C25"],
   [{"kind": "map", "prompt": "Stylised original city map: business icons lighting up one by one around the mansion"}]),
  ("Our interpretation: Tommy didn't corrupt Vice City. He inherited its corruption, sat down at its center, and ran it harder. "
   "And the most revealing part of that system wasn't the drug trade at all.", ["C43"],
   [{"kind": "map", "prompt": "Stylised original map of the city: Starfish Island mansion lit, routes radiating outward"}]),
 ]),
 ("ch08", "The Business of Vice", "Economic corruption: Avery, the Print Works, Congressman Shrub.", 330, [
  ("It was property. Avery Carrington is a Texan real-estate developer, and his missions are optional side stories you can skip. "
   "They're also the clearest picture of how business works in this city.", ["C46"],
   [CARD, ill("an architect's scale model of a waterfront district under a desk lamp, a gold pen and a land deed beside it, no readable text")]),
  ("In the first, a rival developer won't sell Avery some land, so Avery sends Tommy to persuade him at a golf course. The developer ends up dead. "
   "In the second, a competing construction site down the street is in Avery's way, so Tommy blows it up, and they talk about it as saving the rejuvenation of the area.",
   ["C46"], [ill("a half-built tower wrapped in scaffolding at dusk, a small toy-like helicopter hovering near an upper floor")]),
  ("In the third, Avery spells out his strategy. A gang war, he says, brings property prices down. "
   "Tommy dresses as a member of one gang and attacks a funeral held by another, so the two go to war.", ["C35", "C36"],
   [ill("a funeral parlor exterior in the rain, black umbrellas, a lone figure in borrowed colors watching from across the street")]),
  ("The motive comes from Avery's own mouth. What we take from it is our interpretation: in Avery's Vice City, violence is a tool for moving real-estate prices.",
   ["C36"], [{"kind": "timeline", "prompt": "Gang war -> panic -> prices fall -> developer buys; labelled 'Avery's stated plan'"}]),
  ("These missions run beside the main story, and you can finish them even after the final mission. The player can skip them. "
   "The city's property war, though, is there either way.", ["C46"],
   [ill("a sunlit sales office with glossy brochures of condos, a broken window taped over behind the desk")]),
  ("Tommy learns fast. He buys a print shop, the Print Works, and it's the foreman who suggests that printing money is the profitable thing to do. "
   "Tommy turns it into a counterfeiting operation by stealing a courier's printing plates. "
   "He buys a film studio, and when Congressman Alex Shrub moves to ban pornography to win puritan votes, Tommy gets incriminating photos of the congressman to stop him.",
   ["C45", "C44"], [ill("sheets of freshly printed banknotes drying on lines in a dim print shop, no readable text or faces on the notes")]),
  ("Notice how Shrub is handled. He isn't bribed and he isn't threatened with a gun. He's managed with leverage, the way a business manages a problem. "
   "That's our reading of the mission, and it's the same logic Avery used with land.", ["C44", "C36"],
   [ill("an envelope of photographs on a polished desk under a green banker's lamp, a congressional-style lapel pin beside it, no faces visible")]),
  ("A developer using murder to win land. A businessman printing his own money. A congressman kept in line with photographs. "
   "By 1986, Tommy isn't outside the system. He's fluent in it.", ["C46", "C45", "C44"],
   [{"kind": "evidence_board", "prompt": "Developer, print shop, congressman, all pinned around one empty center"}]),
 ]),
 ("ch09", "This Is Business", "The finale: what is said vs implied.", 170, [
  ("The fake money has one destination. Sonny Forelli comes south to collect what he considers his. "
   "In the final confrontation, Sonny calls Tommy the Harwood Butcher and says the fifteen years Tommy spent in prison were Sonny's to spend.",
   ["C23", "C18", "C24"], [CARD, ill("a mansion foyer at night, men in dark coats on a staircase, one older man in front, faces in shadow")]),
  ("Sonny talks about Tommy's fifteen years in prison like an investment, and he has come south to cash it in.",
   ["C18", "C24"], [{"kind": "timeline", "prompt": "Fifteen years in prison, release, sent south in 1986"}]),
  ("Tommy says he was sent to kill one man, and they knew he was coming. Sonny doesn't confess. He deflects. "
   "The game implies a setup. It never states one.", ["C24"],
   [ill("two silhouettes facing each other across a long marble floor, a single beam of light between them")]),
  ("This matters because many fan accounts state the setup as fact: Sonny framed Tommy and let him serve his fifteen years. "
   "The game itself is more careful. It gives you Sonny's evasion and lets you draw your own conclusion.", ["C37", "C24"],
   [{"kind": "evidence_board", "prompt": "Two columns: 'What the dialogue says' vs 'What fan accounts claim'"}]),
  ("Lance has already switched sides. He tells Sonny about the fake money, and Tommy kills them both. "
   "Lance had felt underappreciated in Tommy's rise, and his explanation for the betrayal is simple: this is business.", ["C23", "C25"],
   [ill("a rooftop at night above the city lights, a broken pair of aviator sunglasses on the ledge")]),
 ]),
 ("ch10", "Built on Crime", "Conclusion: Vic and Tommy, the thesis restated.", 130, [
  ("Two men, two years apart. Vic Vance kept saying he wanted out, and the city brought him back to a deal table where he died. "
   "Tommy Vercetti wanted the top, and he got it.", ["C47", "C32", "C20", "C48"],
   [CARD, ill("split composition: a dock at night on the left, a mansion balcony at dawn on the right, the same bay between them")]),
  ("The difference between them isn't that one was good. Vic dealt drugs and fought a war. "
   "The difference is that Vic kept looking for the exit, and Tommy went looking for the keys.", ["C47", "C48"],
   [ill("a man's hand dropping a ring of keys onto a mahogany desk, a second hand reaching for a door handle, both in shadow")]),
  ("But the sergeant, the agent, the cartel, the colonel and the developer were all there first. "
   "Our argument is simple. Tommy Vercetti didn't corrupt Vice City. He inherited a city that was already built on crime. "
   "When the series returns to Vice City in GTA VI, it does so in a different continuity, with a different history still to be told.",
   ["C42", "C33", "C46", "C43", "C05"], [ill("the neon coastal skyline at dusk from the opening, now seen from the mansion's balcony, a cracked badge on the railing")]),
 ]),
]


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
              "segments": [{"narration": n, "claim_ids": ids, "visuals": v} for n, ids, v in segs]}
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
