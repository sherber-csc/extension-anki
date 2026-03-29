# PROJECT_HANDOFF.md

## 1. Project identity

Project name: `anki-web-tool`

Goal: build a tool for **web word capture -> local backend processing -> queue management -> formal Anki card generation**.

Primary environment:
- Windows local development
- Chrome extension
- Local Python backend
- Anki + AnkiConnect

Current working project path in the new Codex session:
- `D:\Codex\Project\web-anki`

---

## 2. Source-of-truth priority

Use these files as the primary authority, in this exact order:

1. `SPEC.md`
2. `FIELD_EXAMPLES.md`
3. `ARCHITECTURE.md`

This file `PROJECT_HANDOFF.md` is a migration handoff and execution guide.  
It provides current status, preserved decisions, and next-step priorities.  
It must **not override** the three files above.

If any discussion history conflicts with:
- `SPEC.md`
- `FIELD_EXAMPLES.md`
- `ARCHITECTURE.md`

then those three files win.

---

## 3. Core product boundary

### Extension responsibilities
The browser extension must remain lightweight.

It is responsible for:
- capturing selected word text
- collecting best-effort page context
- showing lightweight notifications
- showing queue state in popup
- triggering backend endpoints

It must **not** become the place for:
- normalization
- lemma resolution
- queue deduplication
- Anki logic
- LLM orchestration
- formal note generation
- field mapping business logic

### Backend responsibilities
The local backend is the heavy logic layer.

It is responsible for:
- normalization
- lemma resolution
- `word_key` generation
- queue management
- deduplication
- preflight checks
- formal generation orchestration
- Anki integration
- LLM integration
- audio generation
- field mapping
- status transitions

---

## 4. Critical business rules that must not drift

### 4.1 `word_key` vs `record_id`
These are different and must never be mixed.

- `record_id` = queue record primary key
- `word_key` = business key derived from normalized lemma

`record_id` must not replace `word_key`.  
`word_key` must not be treated as queue row id.

### 4.2 `forms`
`forms` is a **weak-display field**.

Rules:
- produced by backend
- not produced by extension
- weak display only
- positioned between Meaning and Pair
- current scope: only generate when appropriate under backend rules
- do not let UI or popup invent `forms`

### 4.3 `source_sentence`
`source_sentence` is not an independently displayed final card field.

It is an intermediate input used to build:
- `examples[0]`

### 4.4 queue status semantics
Queue statuses must stay truthful.

- `pending` = captured and waiting for formal generation
- `success` = formal generation genuinely succeeded and note was written successfully
- `failed` = formal generation genuinely ran and failed with a real failure reason

Never use:
- placeholder behavior
- unfinished implementation
- stub generation
to turn `pending` into `failed`.

### 4.5 extension generation boundary
Popup may trigger generation, but popup does not own generation logic.

Popup may:
- call backend endpoint
- display summary
- refresh queue display

Popup must not:
- generate cards itself
- infer detailed generation outcome on its own
- own note mapping rules
- own Anki logic

---

## 5. Current implemented state

The following parts are already built and at least partially validated.

### 5.1 Extension capture flow
Implemented:
- extension loads in Chrome
- content capture works on normal webpages
- word capture can reach backend
- notifications work
- queue insertion works
- deduplication works

Observed working behavior:
- first capture of a word -> added to queue
- repeated capture of same word -> already in queue

Known caveat:
- after extension reload, current page may need refresh
- otherwise capture can hit:
  - `Could not establish connection. Receiving end does not exist.`

This is **not fully root-fixed yet**.
Current workaround:
- reload extension
- refresh current webpage

Future improvement still pending:
- background-side automatic reinjection of `content.js` and one retry

### 5.2 Backend server
Implemented and validated:
- backend can listen on `127.0.0.1:8766`
- startup now prints:
  - `Backend listening on http://127.0.0.1:8766`

### 5.3 Queue inspection endpoint
Implemented:
- `GET /queue`

Current behavior:
- returns recent queue items
- newest first
- current minimal fields include:
  - `record_id`
  - `surface_form`
  - `lemma`
  - `word_key`
  - `status`
  - `captured_at`

This endpoint is confirmed working.

### 5.4 Popup
Implemented:
- minimal popup opens from extension action
- popup can load queue
- popup shows pending item count
- popup shows pending list
- popup has Refresh button
- popup shows more specific error messages
- popup keeps `captured_at` raw
- popup does not hardcode backend URL
- popup uses shared backend URL resolution / protocol

Popup is **not** a full management panel yet.

Current popup includes:
- queue title
- pending count
- pending list
- refresh
- Generate pending cards button

Not implemented in popup:
- delete
- selection
- batch item management
- complex styling
- side panel

### 5.5 Generate pending entry
Implemented:
- `POST /generate-pending` exists
- popup can trigger it
- popup can refresh queue afterward

Important current meaning:
- entry chain exists
- but full formal card generation is **not finished yet**

Placeholder generation semantics were already corrected:
- unfinished formal generation must not convert `pending` into `failed`

Current placeholder-safe behavior:
- returns summary
- leaves pending unchanged if real formal generation is not executed

### 5.6 Generation preflight
Implemented:
- `GET /generation-preflight`

Current purpose:
- read-only availability check
- no queue status changes
- no note write
- no formal generation side effects

Checks included:
- `anki`
- `llm`
- `audio`

Current response shape includes:
- `status`
- `summary`
- `checks`

Examples:
- `ready`
- `not_ready`

---

## 6. Verified current working behaviors

These are the behaviors that were already verified during the prior build session.

### Verified
- extension can capture selected word from normal webpage
- queue dedup works
- backend can listen on `127.0.0.1:8766`
- `GET /queue` returns real queue data
- popup can display pending queue entries
- generate entry can be triggered from popup
- placeholder generation no longer corrupts queue semantics
- `generation-preflight` exists and returns structured readiness information

### Verified queue examples that appeared in real queue
Examples previously observed in queue include:
- `grammar`
- `simple`
- `tenses`
- `explain`
- `interactive`
- `practising`
- `organised`

These are examples of already captured pending items, not guaranteed permanent fixtures.

---

## 7. Important known unfinished items

These are intentionally unfinished and should not be misrepresented as complete.

### 7.1 Single-item real formal generation
Not completed yet.

Target next step:
- process exactly one earliest pending record
- perform real formal generation chain
- only true success -> `success`
- only true failure -> `failed`
- `error_message` must contain real reason

### 7.2 Batch formal generation
Not completed yet.

Must only come **after** single-item real formal generation is stable.

### 7.3 Queue deletion
Not implemented.
Not current priority.

If later added, preferred minimal scope:
- only delete `pending`
- by `record_id`
- single item
- refresh after delete
- no restore
- no batch delete first

### 7.4 Auto reinjection of content script
Not completed.
Still pending as future fix for the content-script reconnect issue.

---

## 8. Next priority: the only correct next step

The next priority is:

# Single pending real formal generation

Not:
- delete queue item
- complex popup management
- side panel
- multi-select generation
- batch orchestration
- popup beautification

### Required order for next implementation
1. choose exactly one earliest pending record
2. run real formal generation chain
3. if truly successful, write card and mark `success`
4. if truly failed, mark `failed` and write real `error_message`

### Formal chain order
The real chain should follow this order:

1. queue layer selects one earliest pending item
2. generation orchestration begins
3. `anki_service` checks readiness / may try to start Anki if required by current design
4. `llm_client` produces structured fields
5. `audio_service` produces audio
6. `example_builder` produces final `examples`
7. `forms_builder` produces final `forms`
8. `note_mapper` produces final note fields
9. `anki_service` writes note
10. queue status updates based on real outcome

### Hard rule
Before writing to Anki:
- perform duplicate check by `word_key`

### Hard failure rule
`error_message` must be real and explainable, such as:
- anki unavailable
- llm config missing
- llm response invalid
- audio generation failed
- anki write failed

Never write:
- generic fake placeholder failure
- meaningless `generation failed`

---

## 9. Current interface inventory

### Existing backend endpoints
Confirmed or intentionally present:
- `GET /queue`
- `POST /generate-pending`
- `GET /generation-preflight`

### Existing popup behaviors
- view pending queue
- refresh queue
- trigger generate entry

### Existing protocols
Backend contracts and extension protocol mirror are already in place and should remain synchronized.

---

## 10. Migration constraints for the new Codex session

The new Codex session must not assume hidden context from the old session.

It must reconstruct context from:
- `SPEC.md`
- `FIELD_EXAMPLES.md`
- `ARCHITECTURE.md`
- this file

The new Codex session must not:
- invent a different architecture
- silently rename fields
- change queue status semantics
- move heavy generation logic into popup
- treat popup as a full management console
- treat placeholder generation as real failure

---

## 11. Recreate these subagent roles

These roles existed in the prior session and must be recreated in the new session.

### `spec_guardian`
Responsibility:
- review compliance against
  - `SPEC.md`
  - `FIELD_EXAMPLES.md`
  - `ARCHITECTURE.md`

Focus:
- field naming
- queue status semantics
- `record_id` vs `word_key`
- `forms`
- `examples`
- extension/backend boundary

### `architecture_reviewer`
Responsibility:
- review module boundaries and dependency direction

Focus:
- popup remains lightweight
- generation logic remains backend-owned
- orchestration does not collapse into UI
- services do not become tangled

### `flow_verifier`
Responsibility:
- verify end-to-end user flow behavior

Focus:
- capture flow
- queue refresh flow
- popup behavior
- generation trigger behavior
- status transitions
- no regression in previously working paths

### `module_implementer`
Responsibility:
- implement only narrowly assigned modules
- no architecture drift
- no protocol drift
- no speculative refactors

---

## 12. Required subagent workflow

The new Codex session must not silently skip subagent usage when asked.

For meaningful steps, preferred order is:

1. `spec_guardian` review
2. `architecture_reviewer` review
3. `module_implementer` implementation of the narrowly scoped task
4. `flow_verifier` post-implementation behavior review

Each meaningful step should explicitly report:
- which subagents were actually called
- which were not called
- what each one did
- what each one concluded

---

## 13. What the new Codex should do first

Before coding anything in the new session, it should:

1. read:
   - `SPEC.md`
   - `FIELD_EXAMPLES.md`
   - `ARCHITECTURE.md`
   - `PROJECT_HANDOFF.md`

2. summarize:
   - current completed state
   - current next priority
   - preserved architecture boundaries

3. recreate and declare:
   - `spec_guardian`
   - `architecture_reviewer`
   - `flow_verifier`
   - `module_implementer`

4. confirm that the next priority is:
   - single pending real formal generation

---

## 14. Explicit “do not drift” list

Do not silently change:
- endpoint meanings
- queue status meanings
- popup role
- generation ownership
- `record_id` meaning
- `word_key` meaning
- `forms` position and meaning
- `source_sentence` usage
- placeholder generation semantics

Do not jump ahead to:
- batch orchestration
- delete UI
- side panel
- queue management expansion
- popup becoming a full dashboard

until single-item real formal generation is truly working.

---

## 15. Handoff summary in one sentence

The project has already completed:
- capture
- dedup
- queue inspection
- popup viewing
- generation entry
- preflight

and the **next and only priority** is:

**make one earliest pending record go through real formal generation and become a real Anki card, with truthful success/failed semantics.**