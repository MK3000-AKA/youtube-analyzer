# Configuration

## Required

Set one YouTube Data API variable:

```bash
export YOUTUBE_API_KEY="..."
```

`GOOGLE_YOUTUBE_API_KEY` is also accepted.

## Optional cookies

Set a Netscape-format cookie export when subtitles require a logged-in session:

```bash
export YOUTUBE_COOKIE_FILE="/private/path/youtube_cookies.txt"
```

The collector checks these fallback locations:

```text
~/Documents/Codex/.private/credentials/youtube_cookies.txt
~/.youtube_cookies.txt
```

## Optional private environment file

Set:

```bash
export CODEX_TOOL_APIS_FILE="/private/path/tool-apis.env"
```

The file may contain:

```text
YOUTUBE_API_KEY=...
HUGGINGFACE_TOKEN=...
TAVILY_API_KEY=...
```

The collector also checks:

```text
~/Documents/Codex/.private/tool-apis.env
~/.config/youtube-analyzer/env
~/.youtube-analyzer.env
```

Never commit any of these files.
