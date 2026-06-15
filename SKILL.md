---
name: youtube-video-analyzer
description: Analyze YouTube videos into an evidence-based 9-module HTML report. Use when a user sends a YouTube URL or video ID and asks to analyze, summarize, review, compare, 解读, 分析, 评测, or generate a report. Collect real metadata, comments, subtitles and chapters, distinguish demonstrations from comprehensive reviews, surface contradictory user evidence, verify important current claims, and clearly label unavailable sources.
---

# YouTube video analyzer

Generate a useful conclusion, not a transcript recap.

## Codex workflow

1. Extract the video ID.
2. Collect metadata, comments and subtitles:

```bash
python3 <skill_dir>/scripts/analyze_youtube.py <VIDEO_URL_OR_ID> \
  --output-dir <workspace>/outputs
```

3. Inspect `work/youtube-analysis/<VIDEO_ID>/`:
   - `video.json`
   - `comments_clean.json`
   - `transcript_<LANG>.txt`
4. Read `references/analysis-standard.md`.
5. Replace every draft placeholder with findings grounded in the collected sources.
6. Save the final report as:

```text
outputs/youtube_analysis_<VIDEO_ID>_<YYYYMMDD>.html
```

7. Validate:

```bash
python3 <skill_dir>/scripts/validate_report_v6.py <HTML_PATH>
```

8. Render at desktop and mobile widths when browser tooling is available. Fix horizontal overflow and broken assets.

Never invent playback statistics, comments, subtitles, timestamps, quotes, sponsorship status or source provenance. Mark unavailable evidence explicitly.

## OpenClaw compatibility

Existing OpenClaw users may continue to run:

```bash
python3 <skill_dir>/ai_youtube_report_v6.py <VIDEO_ID> [OUTPUT_DIR]
```

The legacy v6 pipeline remains available. The `scripts/` workflow is the portable collector-first path used by Codex.

## Credentials

Prefer environment variables:

- `YOUTUBE_API_KEY` or `GOOGLE_YOUTUBE_API_KEY`
- `YOUTUBE_COOKIE_FILE`
- `CODEX_TOOL_APIS_FILE`

The collector also checks common private local paths documented in `references/configuration.md`.

Never print or write API keys and cookies into reports, source bundles, logs or Git.

## Report structure

Keep the V6 nine-module structure:

1. Hero and disclosure
2. Stats grid
3. Engagement analysis
4. Content summary
5. Comment sentiment
6. Comment topics
7. Top comments
8. Keywords
9. Core insights

An optional external-verification section may follow the core insights.

## Output quality

- Lead with the real conclusion.
- Separate creator claims, visible demonstrations, audience feedback and external verification.
- Identify whether the video is an independent review, sponsored review, first look, tutorial or cinematic showcase.
- Prefer specific negative or contradictory comments over generic praise.
- Explain what the video does not test.
- For product videos, state who should buy, who should wait and which risks remain unresolved.
- Do not treat polished footage as proof of default image quality when LUTs, grading, accessories, multiple operators or professional rigs are involved.
