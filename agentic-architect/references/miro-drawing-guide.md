# Miro drawing guide

How to put the architecture on a Miro board with **Miro's official MCP server** (`https://mcp.miro.com`), and what to do when it is not connected. Tool names below are Miro's current canvas tools (the older `diagram_*`, `layout_*`, `context_*` and `doc_*` tools were removed on 14 September 2026; do not call them).

## 1. Is Miro connected?

Look for Miro MCP tools in your tool list. In Claude Code they appear with an MCP prefix, for example `mcp__miro__canvas_create_from_svg` when the server was added under the name `miro`, or a plugin-prefixed name when installed as a plugin. The ones this skill uses:

| Tool | Used for |
|---|---|
| `canvas_get_canvas_composer_skill` | Required first. Call with no step, then `step="design"`, then `step="dsl"`. Returns Miro's style guide and the SVG board format. Once per session. |
| `canvas_load_format_skill` | Optional extra guidance, e.g. `format_name="diagramming", notation="free_form"` or `"flowchart"`. |
| `board_create` | New board (confirm with the user first). Returns `miro_url`. |
| `canvas_search` | `result_mode="overview"` to find free space on a non-empty board. |
| `canvas_create_from_svg` | Draw the board SVG. |
| `canvas_update_from_svg` | Fix layout or apply review changes, matched on `data-miro-id`. |
| `canvas_read_as_svg` | Read back an area or specific widgets. |
| `board_show` | Call once at the end to publish the result. |

If none are present, go to section 2, then continue with section 6 (fallback).

## 2. Setup instructions to give the user

Tell the user exactly this:

> **Connect Miro to Claude Code (one time, about 2 minutes)**
>
> Option A, Miro's official plugin (recommended by Miro):
> ```
> claude plugin install miro@claude-plugins-official
> ```
>
> Option B, add the MCP server directly (available in all your projects with `--scope user`):
> ```
> claude mcp add --transport http --scope user miro https://mcp.miro.com
> ```
>
> Then authenticate: start Claude Code, run `/mcp`, select **miro**, choose **Authenticate**. Your browser opens Miro's OAuth page: sign in, **pick the Miro team** whose boards Claude may use, and approve. Back in Claude Code, `/mcp` should show miro as connected. Restart the session if the tools do not appear.
>
> Notes: works on all Miro plans, including free. On Enterprise plans an admin must enable MCP first (Admin settings, Apps & Integrations, MCP). Claude only sees boards in the team you picked; to switch teams, re-authenticate. To disconnect: `claude mcp remove miro`.

Sources: Miro developer docs ("Miro's MCP Server", "Miro MCP for Claude Code" marketplace page).

## 3. Drawing workflow

1. **Load Miro's format once**: `canvas_get_canvas_composer_skill` (no step), then `step="design"`, then `step="dsl"`. Follow its rules where they differ from this guide.
2. **Pick the board.** Ask: new board or an existing one? For a new board, propose the name "<Project> architecture" and call `board_create` after the user agrees. For an existing board, call `canvas_search` with `result_mode="overview"` and choose an empty area; never overwrite or delete existing content without explicit permission.
3. **Generate the SVG** from the validated spec:
   ```
   python3 <skill-dir>/scripts/spec_to_miro.py architecture.json --svg board.svg --origin 0,0
   ```
   Use `--origin X,Y` to place it in empty space on an existing board.
4. **Draw**: read `board.svg` and pass its full text as the `svg` argument of `canvas_create_from_svg` with the board URL.
5. **Check the result**: `failed_items` must be empty. If the message lists widgets whose dimensions changed, compare `data-rendered-bounds` with neighbours; if anything overlaps, move it with `canvas_update_from_svg` using the `data-miro-id` values from `result_svg` (send minimal stubs, e.g. `<rect data-miro-id="..." x="..." y="..." width="..." height="..." />`).
6. **Publish**: call `board_show` once with the board URL. Give the user the link and a short summary. (Its built-in preview can leave out perfectly straight connectors; they are on the board. Do not "fix" them.)
7. **After review**: edit `architecture.json`, regenerate, and either patch the changed widgets with `canvas_update_from_svg` or draw the new version beside the old one at a new `--origin` and label it v2. Deleting widgets needs the user's confirmation first.

If Python is not available, hand-author the same SVG following section 4 and Miro's format rules.

## 4. Layout conventions (what the script produces)

- **One main frame** titled with the system name. Inside it: title (56 px bold), one-line summary (keep under 220 characters), then **horizontal lanes**, one per layer, top = outside world, bottom = infrastructure.
- Lane label on the left (layer name in bold, trust level underneath). Lanes alternate faint grey (#f7f7f7) and white.
- **Trust boundaries**: a red dashed divider (#ff6464) between lanes with the label "TRUST BOUNDARY: <what is checked>".
- **Nodes**: 300 x 120, one per component, label in bold plus a short note (labels at most 34 characters; notes about 30, shorter for guardrails because hexagons have less room).
- Grid: 300 px columns with 80 px gaps; pin `"col"` so connected nodes sit in the same column or adjacent lanes. The validator warns when a connector would pass through another node.
- **Connectors**: elbowed, 3 px, arrow at the end, every one labelled with what flows (at most 40 characters). Vertical links go bottom to top side, same-lane links right to left side.
- **Legend frame** to the right: only the node kinds and line kinds actually used, plus the trust-boundary line.
- **Key-decision stickies** (light yellow, up to 6) under the main frame, each ending with its chapter.
- **Design-rationale doc** under the legend: autonomy level, pattern decisions with chapters, trust boundaries and checkers, failure handling, HITL points, evals, risks with owners, non-goals.
- Up to about 24 nodes per frame. Bigger systems: an overview frame plus one detail frame per subsystem, placed left to right 160 px apart.

## 5. Colour and shape key

Miro's diagram (Fluoro) palette; each fill has a matching border and ink colour.

| kind | Meaning | Fill | Border | Ink | Shape |
|---|---|---|---|---|---|
| actor | user, customer, channel | #B3E65F | #6E9A24 | #2F440B | rounded rectangle |
| interface | API, UI, report, edge | #B3E65F | #6E9A24 | #2F440B | rectangle |
| orchestrator | code that routes and calls (workflow, graph, coordinator, retriever) | #9CE6FF | #2C97BB | #1C4657 | rectangle |
| agent | model-driven step (LLM call, worker agent): proposes only | #B8ACFB | #8A7BE0 | #231266 | rounded rectangle |
| guardrail | policy gate, validator, budget guard: denies by default | #FFB575 | #CC7830 | #542700 | hexagon |
| human | approval, review, escalation | #FD9AE7 | #D756BA | #511341 | rounded rectangle |
| tool | tool or MCP server | #FFE86D | #A28E26 | #574900 | rectangle |
| data | database, index, memory, checkpoint, ledger | #81E7DE | #259D92 | #0E4343 | cylinder |
| external | third-party system or untrusted source | #DDDDD8 | #8A8A7E | #434339 | cloud |
| observability | tracing, audit, evals | #BDD1B9 | #81917D | #2C3C29 | rectangle |

| edge kind | Meaning | Style |
|---|---|---|
| data | request or data flow | solid #313131 |
| control | code routes or calls | solid #2C97BB |
| approval | human decision path | dashed #D756BA |
| untrusted | content that must be treated as data | dotted #8A8A7E |
| telemetry | spans, audit events | dotted #81917D |

## 6. Fallback when Miro is not connected

1. Give the setup instructions in section 2.
2. Produce a Mermaid diagram and a local picture from the same spec:
   ```
   python3 <skill-dir>/scripts/spec_to_miro.py architecture.json --mermaid architecture.mmd --preview architecture-preview.svg
   ```
3. Paste the Mermaid into `ARCHITECTURE.md` in a ```mermaid block (GitHub renders it). Tell the user `architecture-preview.svg` opens in any browser.
4. When Miro is connected later, draw the same spec with section 3; nothing else needs to change.

A Mermaid diagram widget can also be put on a Miro board (`<foreignObject data-type="diagram">` in the SVG), but for architectures with many layers the native shapes above read much better; use Mermaid on Miro only if the user asks.

## 7. Gotchas seen in testing

- Escape `&`, `<` and `>` in every label (the script does this). One raw `&` makes the whole call fail.
- Keep the SVG under 200,000 characters (a 25-node diagram is about 25,000).
- Do not wrap everything in a super-frame, and do not nest frames.
- The rationale doc is fixed at 784 px wide and grows downward; leave space below the legend.
- `board_create`, `canvas_update_from_svg` with `data-deleted`, and sharing tools change the user's workspace: confirm first.
- Usage limits apply to Miro MCP; batch the whole diagram into one `canvas_create_from_svg` call.
