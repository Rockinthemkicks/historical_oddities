#!/usr/bin/env bash
# Vice City 60-second production test (editorial review 5).
# Run from the repo folder on YOUR computer (where .env has your API keys):
#     bash episodes/gaming/vice-city-60s-test/run_test.sh
# It shows the estimate first and spends nothing until you type RUN.
# Hard limits for this test: $2.00 per run and $2.00 for the test episode.
set -euo pipefail
cd "$(dirname "$0")/../../.."
T=episodes/gaming/vice-city-60s-test
P="python3 main.py --mode gaming-lore --production $T/production.json"
CAPS="--max-run-cost 2 --episode-budget 2"

[ -f .env ] || { echo "No .env here. Run this from your project folder (unplayedhistory, formerly historical_oddities: the one with your keys)."; exit 1; }
command -v ffmpeg >/dev/null || { echo "ffmpeg is missing (brew install ffmpeg)."; exit 1; }
python3 -c "import PIL, requests" 2>/dev/null || python3 -m pip install -q -r requirements.txt

echo "== Building the test production (free) =="
python3 episodes/gaming/vice-city-dark-history/draft/make_test.py
$P storyboard
$P estimate $CAPS | tail -25

echo
echo "This will generate 7 images (OpenAI) and about 57 seconds of narration (ElevenLabs)."
read -r -p "Type RUN to approve the test and spend up to \$2.00 (anything else cancels): " ok
[ "$ok" = "RUN" ] || { echo "Cancelled. Nothing was spent."; exit 0; }

for stage in research outline script storyboard budget; do
  $P approve "$stage" --note "60-second test, owner authorized a \$2 cap (review 5)"
done

echo "== Producing (paid) =="
$P produce $CAPS

THUMB_BG=$(python3 -c "import json;a={x['id']:x for x in json.load(open('$T/assets/provenance.json'))['assets']};print(a['thumbnail_bg']['path'])")
python3 episodes/gaming/vice-city-dark-history/draft/make_thumbnail.py "$T/$THUMB_BG" "$T/out/thumbnail_mockup.png"

# Results to send back for review: video, images (incl. reference sheet), thumbnail, reports. No keys.
ZIP="$HOME/Desktop/vice_city_60s_test_results.zip"
rm -f "$ZIP"
( cd "$T" && zip -qr "$ZIP" out/documentary.mp4 out/thumbnail_mockup.png out/images out/qc_report.json estimate.json script.json )
echo
echo "Done. Spent this run: $(python3 -c "import json;print('\$%.2f' % json.load(open('$T/out/qc_report.json'))['spent_this_run_usd'])")"
echo "Results zipped to: $ZIP  (upload it in the chat)"
