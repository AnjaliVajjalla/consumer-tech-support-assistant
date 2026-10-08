# Real-Time Voice AI Assistant

A web app that lets you have a spoken, hands-free conversation with an
AI assistant: ask a question out loud, hear a spoken answer, ask a
follow-up, all in the browser. Every stage of the pipeline (speech-in,
model, speech-out) is visible and measurable, audio streams to the
server live as you talk, and the assistant can use one small tool
(real-time weather) when it actually needs to.

## Why this project exists

Built for hands-on practice with the full realtime voice pipeline: speech
recognition, LLM reasoning, tool/function calling, WebSocket streaming,
text-to-speech, latency measurement, evaluation, and resilient AI
application design. See `PROJECT_BRIEF.md` for the original scope and
boundaries.

## Architecture

```
 BROWSER                                    SERVER (Flask + WebSocket)
 ───────                                    ──────────────────────────
 mic audio (getUserMedia)
     │
     ▼
 MediaRecorder + silence detection
 (Web Audio AnalyserNode)
     │
     │  small audio chunks, sent live
     │  over the WebSocket as you talk
     ▼
 ──────────────────────────────────────►   accumulate chunks until
                                            browser signals "done"
                                                    │
                                                    ▼
                                            transcribe (Whisper STT)
                                                    │
                                                    ▼
                                            LLM call (Claude, streamed)
                                                    │
                                       ┌────────────┴─────────────┐
                                       │                          │
                                no tool needed              needs a tool
                                       │                          │
                                       │            validate arguments,
                                       │            run get_weather(),
                                       │            send result back,
                                       │            get final answer
                                       │                          │
                                       └────────────┬─────────────┘
                                                    ▼
                                            speak (TTS)
                                                    │
 ◄──────────────────────────────────────────────────
 live progress events pushed the instant each        │
 stage happens (recording/transcribing/thinking/      ▼
 speaking), then a final transcript + reply    play audio, save turn
```

One WebSocket connection = one full turn. Conversation memory persists
across turns within a chat (the LLM itself is stateless; the server
resends growing history each call). Each chat gets a random fun name
(e.g. "Silly Raccoon"), is saved to disk, and is browsable/deletable
from the Past Chats list. A CLI version also exists (`src/pipeline.py`,
run via `python3 -m src.pipeline`) using the same core pipeline logic,
with server-side mic capture (`sounddevice`) instead of the browser.

Each stage is its own module in `src/`: `capture.py` (CLI-only mic
capture, voice-activity detection), `transcribe.py` (Whisper, plus a
bytes-based path for browser audio), `respond.py` (Claude, streaming +
tool calling), `tools.py` (the weather tool + argument validation),
`speak.py` (TTS + playback), `trace.py` (per-stage latency),
`pipeline.py` (orchestrates all of it, states + fallbacks + the
conversation loop). `app.py` is the Flask web server: it serves the
page and handles the `/ws/turn` WebSocket connection that does
everything above.

States exposed at every stage: `[recording]` → `[processing]` →
`[success]` / `[failure]` / `[fallback]`, shown live in the browser as
the turn progresses, not just at the end.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file with your API keys:
```
ANTHROPIC_API_KEY=sk-...
OPENAI_API_KEY=sk-...
```

## Running it

```bash
python3 app.py
```

Then open `http://127.0.0.1:5050`. Click **Start turn**, your browser
will ask for microphone permission the first time, then just speak.
Recording stops automatically when you pause, or click **Stop
Recording** to end it early. Ask a follow-up, ask about the weather
somewhere, ask anything else, it's a real back-and-forth conversation
with memory, not one question and reset. Click **New Chat** to start a
fresh conversation (with a new random name), and browse or delete past
chats from the list below.

There's also a terminal-only CLI version, useful for quick testing
without a browser:
```bash
python3 -m src.pipeline
```
Say "goodbye" (or "stop listening," "exit," "quit") to end it, or press
Ctrl+C to stop immediately.

## Testing vs. evaluation

- `pytest tests/`: 12 unit tests, free, no real API calls (API-calling
  functions are tested with mocks). Checks the *code* behaves correctly:
  does WAV conversion produce valid audio, does latency tracking record
  correctly even when a stage fails, does the pipeline's fallback logic
  actually trigger when a stage errors out, does tool-argument
  validation correctly reject bad input (missing/empty/oversized).
- `pytest evals/`: 9 real-API evals against meaningful scenarios. Checks
  the *system* behaves well: does a weather question correctly trigger
  the tool, does a nonexistent location get handled gracefully instead of
  hallucinated, does a non-weather question correctly skip the tool, is a
  broad/open-ended question still kept short enough to be spoken
  naturally, does an unsupported request (e.g. "send an email for me")
  get declined honestly instead of falsely claiming it happened, and does
  transcription hold up for clear speech, spoken numbers, a proper noun,
  and a longer question (via a TTS-to-Whisper round trip, see caveat
  below). Costs a small amount to run (real Claude + Whisper + TTS
  calls).

## Evaluation results

All 4 original response evals pass. One real finding along the way: the
first run of `test_reply_is_short_and_voice_appropriate` failed, "Tell me
about the history of the Roman Empire" got a 93-word answer, too long to
be spoken naturally, even though the system prompt already asked for
short replies. The prompt held up fine for narrow questions but not
broad, open-ended ones. Fixed by explicitly telling the model to stay
short "even for broad or open-ended questions" and to pick the single
most important point rather than being comprehensive. Re-ran the eval:
same question, 49 words instead of 93, still a real, informative answer.
Confirms evals catch quality drift that unit tests can't, the code never
crashed, it just wasn't behaving the way the system was supposed to.

Transcription evals (added later) test Whisper accuracy via a TTS
round trip: generate audio from known text, transcribe it, check the
words match. All 4 pass, including a spoken phone number, which Whisper
correctly ran together into "5551234567" digit by digit. Honest
caveat: this tests clear, synthetic TTS speech, not real human speech
with accents or background noise, that's still untested (see Known
limitations).

A separate real bug the eval suite itself caught: `evals/` silently
broke when `get_response()`'s return type changed to a tuple (added for
conversation memory) and the evals weren't updated to match, they still
unpacked it as a plain string. Fixed by re-running the eval suite and
updating the unpacking, a reminder that evals need maintenance just like
code.

## Latency

Measured live, stage-by-stage, on the original terminal-only CLI
version (not yet re-measured on the current web/streaming
architecture, numbers below predate that, see Known limitations):

| stage | typical range | notes |
|---|---|---|
| record | 4-6s | voice-activity-detected: matches how long you actually talk, not a fixed timer |
| transcribe | 0.75-2.8s | Whisper API |
| respond (no tool) | ~1-2s | one Claude API call |
| respond (tool call) | ~3.2-4.8s | two Claude API calls (ask → tool requested → run it → final answer), roughly 2-3x slower than a direct answer |
| speak | 4-13s | OpenAI TTS + playback; scales with reply length |
| **total per turn** | **~14-22s** | end to end, one full question-to-spoken-answer cycle |

The clearest tradeoff: tool calling roughly doubles `respond` latency
(two API round trips instead of one), a real cost worth knowing when
deciding whether a feature needs a tool or can be answered directly.

## Known limitations

- Latency numbers above are from the original CLI pipeline, not yet
  re-measured on the current browser/WebSocket architecture. The
  `transcribe`/`respond`/`speak` stages should be the same, but audio
  now streams to the server live instead of recording fully first,
  worth re-measuring rather than assuming it's identical.
- Tested only on one machine/microphone; `SILENCE_THRESHOLD` (used both
  server-side in `src/capture.py` for the CLI, and mirrored client-side
  in the browser's silence detection) is a starting guess and may need
  tuning for different mics or noisy rooms.
- Streaming applies to the *audio transport* (chunks sent live as you
  talk) and the *text* response (visible incrementally as Claude
  generates it); transcription itself is not incremental, Whisper's API
  only accepts a complete audio file and returns one final transcript,
  there's no partial live transcript with this API. Audio playback also
  still waits for the full reply before speaking; true sentence-by-
  sentence audio streaming would need sentence-boundary detection and
  an audio queue, not yet built.
- One tool (weather, via the free Open-Meteo API). No broader multi-tool
  agent, by design, per the project brief's scope.
- No automatic WebSocket reconnection, a deliberate choice: this app
  opens one connection per turn, so there's no in-progress state worth
  silently resuming if a connection drops. Instead, failures are surfaced
  clearly ("Connection lost, click Start turn to try again.") rather than
  faking a recovery that wouldn't actually do anything meaningful.
- Transcription evals use synthetic TTS-generated speech, not real
  human voices, so noisy/accented speech and interruptions are still
  untested. Numbers and proper nouns in transcription are now covered
  (see Evaluation results), just not against messy real-world audio.
- Chat history is saved locally (`data/chats/`, gitignored), single-user,
  no accounts, per this project's scope.
- `evals/` costs real money to run (small, but non-zero), so it's run
  deliberately, not on every save, unlike the free `tests/` suite.

## Tech stack

Python, Flask + `flask-sock` (WebSocket web server), OpenAI Whisper API
(STT), Anthropic Claude API (LLM, streaming + tool calling), OpenAI TTS
API (speech), browser `getUserMedia`/`MediaRecorder`/Web Audio API
(client-side mic capture, silence detection, live audio streaming),
`sounddevice` + `soundfile` (CLI-only mic capture and audio playback),
`requests` (the weather tool, via the free Open-Meteo API), `pytest`
(unit tests + evals).
