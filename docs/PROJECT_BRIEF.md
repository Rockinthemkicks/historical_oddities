HISTORICAL ODDITIES 2.0

Master Project Brief for Claude Code

Project: Fully Automated Animated Educational Video Business
GitHub Owner: Rockinthemkicks
Repository: "historical-oddities-automation"
Development Environment: macOS, Python, FFmpeg
AI Development Partners: Claude Code (implementation) + ChatGPT (architecture, strategy, review)

---

1. PROJECT OVERVIEW

We are building a highly automated, AI-assisted content production business that generates original animated educational videos for YouTube and automatically repurposes them into Shorts, Facebook Reels, TikTok videos, and Instagram Reels.

This project is an expansion of an existing Python video-production pipeline called Historical Oddities.

Important: Do not rebuild the existing system from scratch. First inspect, document, test, and preserve its working functionality.

The long-term objective is to create a reliable content-production engine that can operate with minimal human intervention while producing entertaining, original, monetizable educational videos.

The owner is willing to perform some original creative work, particularly where it materially improves content quality or profitability, but wants to minimize repetitive production tasks.

The business must be designed around profitability rather than maximizing content volume.

Primary objectives

1. Generate original, high-quality educational videos.
2. Automate topic discovery, research, scripting, illustration generation, narration, editing, and rendering.
3. Produce both long-form and short-form content from a shared production workflow.
4. Maintain a consistent, recognizable visual identity.
5. Minimize ongoing human involvement.
6. Keep API and production costs low.
7. Support automated scheduling and publishing through authorized platform integrations.
8. Track performance, production costs, and revenue.
9. Support expansion to additional original content channels if the first channel proves profitable.

Financial objectives

Target: $5,000–$10,000 in monthly operating profit.

This is an aspirational business goal, not a revenue forecast.

The initial system should be inexpensive to test and operate. The owner has previously indicated an initial experimental budget of approximately $250–$500, with willingness to invest more after positive validation.

Prioritize measurable profitability, production efficiency, and return on invested time.

---

2. BUSINESS STRATEGY

Primary content format

The chosen format is illustrated motion graphics rather than fully animated character cartoons.

This decision was made because illustrated motion graphics are easier to automate, less computationally expensive, and more reliable to produce consistently.

Videos should use:

- AI-generated 2D illustrations.
- Camera pans and zooms.
- Layered visual movement where practical.
- Animated diagrams.
- Simple character movements when useful.
- Text overlays and captions.
- Transitions.
- Professional narration.
- Background music and sound effects where licensed and appropriate.

Avoid making fully animated, lip-synchronized characters a requirement for the initial system.

Primary platforms

YouTube long-form: Primary monetization target.

YouTube Shorts: Audience discovery and additional monetization.

Facebook Reels: Additional distribution and potential monetization.

TikTok: Audience discovery and potential monetization.

Instagram Reels: Additional audience discovery.

Publishing integrations must respect platform permissions, API limitations, and monetization policies.

Monetization

The system should eventually support:

- YouTube advertising revenue.
- Facebook monetization where eligible.
- Sponsorship integrations.
- Affiliate marketing.
- Digital products where appropriate.
- Future expansion into owned products.

Do not assume platform monetization approval or guaranteed advertising revenue.

The business should track revenue against production expenses.

---

3. CONTENT STRATEGY

Channel identity

The existing channel concept is Historical Oddities.

Its established focus is strange, surprising, forgotten, and sometimes absurd historical events.

We are considering broadening the editorial strategy to include:

- Strange scientific phenomena.
- Engineering failures.
- Unusual disasters.
- Bizarre historical events.
- Fascinating real-world mysteries.
- Science-based what-if scenarios.
- Unusual inventions.
- Forgotten experiments.

Important editorial decision: Do not automatically change the established Historical Oddities brand into a general science channel. Treat this as a proposed expansion requiring owner approval.

The initial goal is to find topics that are interesting, evergreen, factual, and capable of supporting compelling visual storytelling.

Example future topics

- What would happen if GPS stopped working worldwide?
- Why can lakes suddenly release deadly gases?
- What happens when an entire city loses power?
- Why can bridges begin moving uncontrollably?
- What would happen if all satellites disappeared?

Clearly distinguish real historical events, scientific explanations, and hypothetical scenarios.

Do not present speculative scenarios as established facts.

Topic-selection requirements

The automated research engine should:

1. Generate candidate topics.
2. Check against previously published or used topics.
3. Identify strong curiosity-driven hooks.
4. Assess historical or scientific accuracy.
5. Evaluate available source material.
6. Estimate visual storytelling potential.
7. Assess suitability for long-form and short-form adaptations.
8. Rank topics for owner approval.

Do not treat AI-generated estimates of virality as reliable predictions.

---

4. EXISTING HISTORICAL ODDITIES PIPELINE

The owner has already developed a Python-based automated video-production system.

The existing project includes or has previously used:

- "main.py"
- "pipeline_prompt.md"
- "video_pipeline_workflow.md"
- A structured JSON scene format.
- AI-generated illustration prompts.
- ElevenLabs narration.
- Caption generation.
- FFmpeg video assembly.
- Vertical video output.

The current system is oriented toward approximately 90-second educational videos.

The new project must extend this system to support longer episodes and automatic Shorts.

Existing production stages

Stage 0 — Topic proposals

Generate approximately 3–5 candidate topics.

Check against previously used topics to avoid duplication.

Stage 1 — Script

Generate a narration script.

The existing workflow requires the owner to reply "APPROVE" before continuing.

Stage 2 — Storyboard

Create a scene-by-scene storyboard.

The owner reviews and approves it.

Stage 3 — Master Visual Reference

Generate one consistent visual reference for the episode.

This establishes the illustration style and recurring character appearances.

Stage 4 — Scene image prompts

Generate scene-specific image prompts.

Existing batch format:

- One physical line per scene.
- One blank line between scene prompts.
- No extra headers.
- Image filenames follow "scene01.png", "scene02.png", etc.
- Scene illustrations are 16:9 landscape.

Stage 5 — Video assembly

The existing pipeline:

- Uses ElevenLabs for narration.
- Associates narration with scenes.
- Generates captions.
- Uses FFmpeg to assemble the final video.
- Produces a vertical video.
- Places a title in the upper black letterbox area.

These behaviors should be preserved unless deliberately superseded.

Existing JSON format

{
  "title": "Example Episode",
  "scenes": [
    {
      "scene_number": 1,
      "narration": "Example narration.",
      "image_prompt": ""
    }
  ]
}

Historically, "image_prompt" may be intentionally empty in the JSON, with image prompts delivered separately.

Do not change this schema without providing backward compatibility or a documented migration.

Existing command example

python3 main.py \
  --project out/emu_war_test \
  --skip-script \
  --skip-images \
  --script-file my_script.json \
  --images-dir my_images/

The exact current CLI behavior must be confirmed by inspecting the repository.

Previous technical issues

The earlier pipeline encountered and resolved problems involving:

- ElevenLabs permissions.
- Missing image files.
- FFmpeg caption and overlay filters.
- Invalid MP4 output involving missing "moov" atoms.
- Inconsistent voice selection.

Regression tests should be added where practical.

---

5. LOCKED VISUAL IDENTITY

The existing preferred style is called:

Vintage Notebook-Cartoon

This is a core project requirement.

Visual characteristics

Backgrounds

- Warm cream or off-white textured paper.
- Subtle aged-paper appearance.
- Clean, readable compositions.

Linework

- Imperfect charcoal-brown or black ink.
- Hand-drawn appearance.
- Restrained cross-hatching.
- Subtle pencil shading.

Characters

- Simple cartoon proportions.
- Oversized round or oval heads.
- Compact bodies.
- Slim limbs.
- Minimal eyes, eyebrows, and mouths.
- Consistent appearances between scenes.

Color palette

- Sepia.
- Brown.
- Olive.
- Dusty blue.
- Brick red.
- Muted yellow.
- Gray-blue.

Composition

- Clear foreground, middle ground, and background.
- Generous negative space.
- Limited clutter.
- Readable educational diagrams.

Prohibited visual characteristics

- Photorealism.
- 3D rendering.
- Graphic gore.
- Excessive visual clutter.
- Inconsistent character designs.
- Modern objects in historical scenes unless historically appropriate.

The system should use persistent style references and character descriptions to maintain consistency.

---

6. TARGET AUTOMATION ARCHITECTURE

The desired system is a modular Python application.

Suggested components:

historical-oddities-automation/
│
├── main.py
│
├── pipeline/
│   ├── topic_research.py
│   ├── topic_scoring.py
│   ├── script_generator.py
│   ├── fact_checker.py
│   ├── storyboard.py
│   ├── visual_reference.py
│   ├── image_generator.py
│   ├── narration.py
│   ├── motion_graphics.py
│   ├── video_builder.py
│   ├── shorts_generator.py
│   ├── thumbnail_generator.py
│   ├── metadata_generator.py
│   ├── quality_control.py
│   ├── publisher.py
│   └── analytics.py
│
├── config/
│   └── settings.yaml
│
├── prompts/
│
├── assets/
│
├── tests/
│
├── .github/
│   └── workflows/
│
├── CLAUDE.md
├── README.md
├── requirements.txt
└── .env.example

This structure is a proposal, not a requirement to reorganize working code immediately.

Claude should inspect the existing project before recommending structural changes.

Automation requirements

The system should eventually support:

Topic discovery

- Scheduled topic generation.
- Duplicate detection.
- Source collection.
- Topic ranking.

Research and scripting

- Evidence-backed research.
- Source references.
- Script generation.
- Factual validation.
- Human review of uncertain claims.

Visual production

- Consistent illustrated scenes.
- Reusable characters and visual elements.
- Controlled image-generation costs.
- Automated retries when necessary.

Audio production

- ElevenLabs narration.
- Stable voice configuration.
- Scene-level timing.
- Optional licensed music and effects.

Motion graphics

- Automated pans.
- Zooms.
- Transitions.
- Layered movement where feasible.
- Animated diagrams.
- Caption timing.

Video exports

- 16:9 long-form YouTube episodes.
- 9:16 Shorts and Reels.
- Configurable resolutions and quality.
- Proper audio and video encoding.

Publishing

- Generated titles.
- Descriptions.
- Thumbnails.
- Tags.
- Scheduling.
- Platform-specific formatting.

Analytics

- Views.
- Watch time.
- Audience retention.
- Click-through rate where available.
- Subscriber growth.
- Revenue where available.
- Production cost.
- Revenue per production hour.

---

7. LONG-FORM VIDEO GENERATOR

Target format

Initial production target:

- Duration: 6–9 minutes.
- Aspect ratio: 16:9.
- Primary platform: YouTube.
- Narrated educational storytelling.
- Consistent illustrated motion graphics.

The system should not create unnecessary scenes solely to increase scene count.

Scene duration and illustration density should be determined by pacing, narration, and visual clarity.

Narrative structure

Suggested structure:

1. Strong opening hook.
2. Establish the mystery or problem.
3. Provide historical or scientific context.
4. Explain the underlying mechanism.
5. Explore surprising developments or consequences.
6. Deliver a satisfying conclusion.

The script should prioritize accuracy and audience engagement rather than artificial suspense.

Visual production

The first version should use:

- Static illustrations.
- Automated camera movement.
- Captions.
- Simple transitions.
- Narration.

More advanced animation can be added after this system works reliably.

---

8. AUTOMATIC SHORTS GENERATOR

Every long-form episode should support generating approximately three short-form videos.

Target format

- 9:16 vertical.
- Approximately 30–60 seconds initially.
- Designed for YouTube Shorts, Facebook Reels, TikTok, and Instagram Reels.
- Standalone storytelling.
- Strong opening hook.
- Readable mobile captions.

Critical requirement

Do not simply crop the long-form video into a vertical rectangle.

The system should adapt scenes to vertical framing.

Possible techniques include:

- Intelligent reframing.
- Repositioning illustrated elements.
- Enlarging diagrams.
- Reorganizing text.
- Generating vertical-specific illustrations when needed.

Short selection

The system should identify segments with:

- Strong curiosity hooks.
- Clear narrative payoff.
- Interesting scientific or historical revelations.
- Minimal dependency on missing context.

Where necessary, generate new narration to make each Short understandable independently.

Deliverables per episode

episode/
├── long_form.mp4
├── short_01.mp4
├── short_02.mp4
├── short_03.mp4
├── thumbnail.png
├── metadata.json
├── script.json
├── sources.json
└── production_report.json

---

9. QUALITY CONTROL

Quality control is essential because this system is intended to operate with minimal supervision.

Technical validation

Automatically verify:

- Required scene files exist.
- Image dimensions are valid.
- Narration files are readable.
- Audio is present when required.
- MP4 files are playable.
- Output durations are within tolerance.
- Aspect ratios are correct.
- Captions are present when expected.
- No rendering process failed silently.

Use FFprobe or equivalent tools for media validation.

Content validation

Check for:

- Duplicate topics.
- Unsupported factual claims.
- Contradictory narration.
- Inconsistent names and dates.
- Missing context.
- Repetitive scripts.
- Copyright concerns.
- Platform-policy risks.

AI-based fact checking must not be treated as conclusive verification.

High-risk or uncertain content should require human review.

Approval system

The existing workflow uses explicit "APPROVE" stages.

The new system should support configurable approval modes:

Manual

- Approve each production stage.

Semi-automated

- Approve topic and final video.

Highly automated

- Produce complete drafts automatically.
- Send only flagged items for additional review.
- Require final publishing authorization until the system has demonstrated reliability.

Do not remove the owner's control over publishing without explicit authorization.

---

10. COST MANAGEMENT

Profitability is a central engineering requirement.

Track expenses associated with:

- Language-model API calls.
- Image generation.
- Narration.
- Rendering.
- Storage.
- Publishing services.
- Other paid integrations.

Required safeguards

- Per-video cost estimates.
- Configurable spending limits.
- API retry limits.
- Caching.
- Reusable visual assets.
- Detection of duplicate work.
- Logging of failed jobs.
- Prevention of runaway generation loops.

The system should be capable of estimating the cost of a proposed production run before starting expensive operations.

The initial experimental budget is approximately $250–$500.

Do not assume previously discussed cost estimates are verified API prices. Confirm current provider pricing before selecting production settings.

---

11. GITHUB AND DEVELOPMENT WORKFLOW

Repository:

"Rockinthemkicks/historical-oddities-automation"

The repository should be private.

Claude Code responsibilities

Claude is the primary implementation agent.

Responsibilities include:

- Inspecting existing code.
- Documenting architecture.
- Proposing improvements.
- Implementing approved features.
- Running tests.
- Debugging.
- Maintaining documentation.
- Creating focused pull requests.
- Explaining technical tradeoffs.

ChatGPT responsibilities

ChatGPT acts as:

- Product strategist.
- Technical architecture collaborator.
- Requirements writer.
- Code reviewer.
- Testing and validation partner.
- Business-model analyst.

Both assistants should coordinate through GitHub issues, pull requests, documentation, and explicit user decisions.

Neither assistant should claim to have reviewed or tested code without actually doing so.

Development rules

1. Preserve working features.
2. Prefer small, testable changes.
3. Use feature branches.
4. Submit pull requests for review.
5. Add automated tests.
6. Document new dependencies.
7. Keep credentials out of source control.
8. Avoid unnecessary paid services.
9. Maintain backward compatibility where practical.
10. Do not merge major changes without approval.

Secrets and credentials

Use environment variables, local secret management, or GitHub Actions secrets as appropriate.

Never commit:

- ElevenLabs API keys.
- AI-provider API keys.
- OAuth tokens.
- Publishing credentials.
- Personal access tokens.

Include ".env.example" with placeholder variable names only.

---

12. DEVELOPMENT ROADMAP

Milestone 1 — Existing pipeline audit

Priority: Immediate

Claude should:

1. Inspect the repository.
2. Identify the current entry points.
3. Review the JSON schema.
4. Examine ElevenLabs integration.
5. Review image-generation workflow.
6. Inspect FFmpeg rendering.
7. Document dependencies.
8. Identify existing tests.
9. Identify technical risks.
10. Propose the smallest safe upgrade path.

Deliverable: Architecture assessment and implementation plan.

Do not modify production behavior during this milestone.

Milestone 2 — Dual-format rendering prototype

Build a small test that generates:

- One 16:9 landscape video.
- One 9:16 vertical video.

Use three scenes.

Verify both outputs with automated media checks.

Preserve the existing narration and caption workflow.

Milestone 3 — Long-form production

Extend the script, scene, audio, and rendering systems to support 6–9 minute videos.

Add basic automated motion graphics.

Keep the production process modular and restartable.

Milestone 4 — Shorts generation

Generate multiple standalone Shorts from a completed long-form episode.

Add vertical composition, adapted narration, and mobile-friendly captions.

Milestone 5 — Automated topic research

Add:

- Topic discovery.
- Duplicate prevention.
- Source collection.
- Research notes.
- Topic scoring.
- Script-generation integration.

Milestone 6 — Production orchestration

Create one command that can:

1. Select an approved topic.
2. Generate the script.
3. Create the storyboard.
4. Produce illustrations.
5. Generate narration.
6. Assemble the long-form video.
7. Produce Shorts.
8. Generate thumbnails and metadata.
9. Run quality checks.
10. Save all outputs and reports.

Milestone 7 — Publishing and analytics

Integrate supported publishing services.

Implement scheduling, logging, analytics collection, and failure notifications.

Do not assume all social platforms offer unrestricted publishing APIs.

Milestone 8 — Profitability optimization

Measure:

- Average cost per video.
- Production reliability.
- Views per video.
- Revenue per 1,000 views.
- Revenue per production hour.
- Cost per published minute.
- Profit by platform and content format.

Use real results to determine whe