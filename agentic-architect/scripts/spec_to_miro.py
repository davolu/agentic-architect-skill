#!/usr/bin/env python3
"""Turn an Agentic Architect spec (JSON) into
  1. a Miro canvas-composer SVG (for canvas_create_from_svg on Miro's MCP server), and
  2. a Mermaid flowchart (fallback when Miro is not connected, or to paste anywhere).

Usage:
  python3 spec_to_miro.py architecture.json --svg board.svg --mermaid architecture.mmd --preview preview.svg
  python3 spec_to_miro.py architecture.json --check      # validate only

Standard library only. The spec format is documented in templates/architecture.example.json.
Part of Agentic Architect by David Oluyale, Agentic AI Hub (MIT).
"""
import argparse, json, sys
from xml.sax.saxutils import escape

# ---- visual language (keep in sync with references/miro-drawing-guide.md) ----
# Miro's Fluoro diagram palette: (fill, stroke, ink)
KINDS = {
    "actor":        ("#B3E65F", "#6E9A24", "#2F440B", "round_rectangle", "User / actor / channel"),
    "interface":    ("#B3E65F", "#6E9A24", "#2F440B", "rectangle",       "Interface / API edge"),
    "orchestrator": ("#9CE6FF", "#2C97BB", "#1C4657", "rectangle",       "Orchestrator / workflow (code decides)"),
    "agent":        ("#B8ACFB", "#8A7BE0", "#231266", "round_rectangle", "Model-driven agent / LLM call (proposes)"),
    "guardrail":    ("#FFB575", "#CC7830", "#542700", "hexagon",         "Guardrail / policy gate (deny by default)"),
    "human":        ("#FD9AE7", "#D756BA", "#511341", "round_rectangle", "Human approval / review point"),
    "tool":         ("#FFE86D", "#A28E26", "#574900", "rectangle",       "Tool / MCP server (typed, scoped)"),
    "data":         ("#81E7DE", "#259D92", "#0E4343", "can",             "Data store / index / memory"),
    "external":     ("#DDDDD8", "#8A8A7E", "#434339", "cloud",           "External system / untrusted content"),
    "observability":("#BDD1B9", "#81917D", "#2C3C29", "rectangle",       "Tracing / evals / audit"),
}
EDGES = {  # stroke, dash, legend label
    "data":     ("#313131", None,  "Data / request flow"),
    "control":  ("#2C97BB", None,  "Control (code routes or calls)"),
    "approval": ("#D756BA", "5,5", "Approval / human decision"),
    "untrusted":("#8A8A7E", "2,2", "Untrusted content (treat as data)"),
    "telemetry":("#81917D", "2,2", "Telemetry / audit events"),
}
NODE_W, NODE_H, GAP_X = 300, 120, 80
LANE_H, LANE_LABEL_W, PAD = 230, 300, 64
TITLE_H = 240
LANE_FILLS = ["#f7f7f7", "#ffffff"]


def die(msg):
    print("spec error: " + msg, file=sys.stderr)
    sys.exit(2)


def validate(spec):
    for k in ("title", "layers", "edges"):
        if k not in spec:
            die(f"missing top-level key '{k}'")
    ids = {}
    for li, layer in enumerate(spec["layers"]):
        if not layer.get("nodes"):
            die(f"layer '{layer.get('name')}' has no nodes")
        for n in layer["nodes"]:
            if n["id"] in ids:
                die(f"duplicate node id '{n['id']}'")
            if n.get("kind") not in KINDS:
                die(f"node '{n['id']}' kind must be one of {sorted(KINDS)}")
            ids[n["id"]] = li
    for e in spec["edges"]:
        if e["from"] not in ids or e["to"] not in ids:
            die(f"edge {e['from']} -> {e['to']} references an unknown node")
        if e.get("kind", "data") not in EDGES:
            die(f"edge kind must be one of {sorted(EDGES)}")
        if len(e.get("label", "")) > 40:
            print(f"warning: long edge label '{e['label']}' (keep <= 40 chars)", file=sys.stderr)
    for layer in spec["layers"]:
        for n in layer["nodes"]:
            if len(n["label"]) > 34:
                print(f"warning: long node label '{n['label']}' (keep <= 34 chars, put detail in 'note')", file=sys.stderr)
    return ids


def a(s):
    """escape for XML attribute"""
    return escape(str(s), {'"': "&quot;"})


def layout(spec):
    """Grid layout: one horizontal lane per layer, nodes in columns.
    A node may pin "col" (0-based); otherwise a lane's nodes are centred."""
    pinned = [n.get("col") for l in spec["layers"] for n in l["nodes"] if "col" in n]
    ncols = max([len(l["nodes"]) for l in spec["layers"]] + [c + 1 for c in pinned])
    inner_w = ncols * NODE_W + (ncols - 1) * GAP_X
    frame_w = LANE_LABEL_W + inner_w + 2 * PAD
    pos = {}
    for li, layer in enumerate(spec["layers"]):
        n = len(layer["nodes"])
        y = TITLE_H + li * LANE_H + (LANE_H - NODE_H) / 2
        if any("col" in node for node in layer["nodes"]):
            for node in layer["nodes"]:
                c = node.get("col", 0)
                pos[node["id"]] = (LANE_LABEL_W + PAD + c * (NODE_W + GAP_X), y, li, c)
        else:
            row_w = n * NODE_W + (n - 1) * GAP_X
            x0 = LANE_LABEL_W + PAD + (inner_w - row_w) / 2
            for ni, node in enumerate(layer["nodes"]):
                x = x0 + ni * (NODE_W + GAP_X)
                pos[node["id"]] = (x, y, li, (x - LANE_LABEL_W - PAD) / (NODE_W + GAP_X))
    frame_h = TITLE_H + len(spec["layers"]) * LANE_H + PAD
    return frame_w, frame_h, pos


def crossing_warnings(spec, pos):
    """Warn when an edge's elbowed route would pass through another node:
    vertical runs sit in the source and target columns, so any node in a lane
    strictly between them, in either column, is in the way. Same-lane edges
    are blocked by any node between them in that lane."""
    warns = []
    cells = {(p[2], round(p[3], 2)): nid for nid, p in pos.items()}
    for e in spec["edges"]:
        f, t = pos[e["from"]], pos[e["to"]]
        lo, hi = sorted((f[2], t[2]))
        blockers = []
        if lo == hi:
            a_, b_ = sorted((f[3], t[3]))
            blockers = [nid for (l, c), nid in cells.items() if l == lo and a_ < c < b_]
        else:
            for l in range(lo + 1, hi):
                for c in {round(f[3], 2), round(t[3], 2)}:
                    if (l, c) in cells:
                        blockers.append(cells[(l, c)])
        if blockers:
            warns.append(f"edge {e['from']} -> {e['to']} passes through {', '.join(blockers)}; move a node (\"col\") or connect adjacent lanes")
    return warns


def sides(p_from, p_to):
    (x1, _, l1, _c1), (x2, _, l2, _c2) = p_from, p_to
    if l1 < l2:
        return "bottom", "top"
    if l1 > l2:
        return "top", "bottom"
    return ("right", "left") if x1 < x2 else ("left", "right")


def build_svg(spec, origin=(0, 0)):
    fw, fh, pos = layout(spec)
    ox, oy = origin
    out = ['<svg xmlns="http://www.w3.org/2000/svg">']
    # ---------- main frame ----------
    out.append(f'<g id="arch" transform="translate({ox},{oy})" data-frame="{a(spec["title"])}">')
    out.append(f'<rect data-type="frame" x="0" y="0" width="{fw}" height="{fh}" fill="#ffffff" data-title="{a(spec["title"])}" />')
    out.append(f'<text x="{PAD}" y="{PAD + 56}" font-family="noto_sans" font-size="56" font-weight="bold" fill="#1a1a1a">{escape(spec["title"])}</text>')
    if spec.get("summary"):
        out.append(f'<textArea x="{PAD}" y="{PAD + 80}" width="{fw - 2 * PAD}" font-family="noto_sans" font-size="22" fill="#595959">{escape(spec["summary"])}</textArea>')
    # lanes (created first => behind nodes)
    for li, layer in enumerate(spec["layers"]):
        y = TITLE_H + li * LANE_H
        out.append(f'<rect id="lane{li}" x="{PAD/2}" y="{y + 10}" width="{fw - PAD}" height="{LANE_H - 20}" rx="12" fill="{LANE_FILLS[li % 2]}" stroke="#e7e7e7" stroke-width="2" />')
        trust = layer.get("trust", "")
        label = f'<b>{escape(layer["name"])}</b>' + (f'<br/>{escape(trust)}' if trust else "")
        out.append(f'<textArea x="{PAD}" y="{y + 40}" width="{LANE_LABEL_W - 40}" font-family="noto_sans" font-size="22" fill="#1a1a1a">{label}</textArea>')
    # trust boundaries between lanes
    for li, layer in enumerate(spec["layers"]):
        tb = layer.get("boundary_below")
        if tb and li < len(spec["layers"]) - 1:
            y = TITLE_H + (li + 1) * LANE_H
            out.append(f'<line data-type="divider" x1="{PAD/2}" y1="{y}" x2="{fw - PAD/2}" y2="{y}" stroke="#ff6464" stroke-width="4" data-line-style="dashed" />')
            out.append(f'<text x="{fw - PAD}" y="{y - 8}" text-anchor="end" font-family="noto_sans" font-size="16" font-weight="bold" fill="#bd0a0a">TRUST BOUNDARY: {escape(tb)}</text>')
    # nodes
    for layer in spec["layers"]:
        for n in layer["nodes"]:
            x, y, _, _c = pos[n["id"]]
            fill, stroke, ink, shape, _ = KINDS[n["kind"]]
            content = f'<b>{escape(n["label"])}</b>' + (f'<br/>{escape(n["note"])}' if n.get("note") else "")
            rx = ' rx="16"' if shape == "round_rectangle" else ""
            fsize = 16 if shape in ("hexagon", "cloud") else 18
            shape_attr = "" if shape == "rectangle" else f' data-shape="{shape}"'
            out.append(f'<rect id="{a(n["id"])}" x="{x}" y="{y}" width="{NODE_W}" height="{NODE_H}"{rx}{shape_attr} fill="{fill}" stroke="{stroke}" stroke-width="2" data-text-color="{ink}" data-font-family="noto_sans" data-font-size="{fsize}" data-content="{a(content)}" />')
    # connectors (always after nodes)
    for i, e in enumerate(spec["edges"]):
        p1, p2 = pos[e["from"]], pos[e["to"]]
        s1, s2 = sides(p1, p2)
        stroke, dash, _ = EDGES[e.get("kind", "data")]
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        arrow = "both" if e.get("bidirectional") else "end"
        lbl = f' data-content="{a(e["label"])}"' if e.get("label") else ""
        out.append(f'<line id="e{i}" x1="{p1[0]}" y1="{p1[1]}" x2="{p2[0]}" y2="{p2[1]}" stroke="{stroke}" stroke-width="3"{dash_attr} data-arrow="{arrow}" data-shape="elbowed" data-start="{a(e["from"])}" data-end="{a(e["to"])}" data-start-side="{s1}" data-end-side="{s2}"{lbl} />')
    out.append("</g>")

    # ---------- legend frame (right of main frame) ----------
    lx, lw = ox + fw + 160, 560
    used_kinds = [k for k in KINDS if any(n["kind"] == k for l in spec["layers"] for n in l["nodes"])]
    used_edges = [k for k in EDGES if any(e.get("kind", "data") == k for e in spec["edges"])]
    lh = PAD + 80 + len(used_kinds) * 90 + 60 + len(used_edges) * 60 + PAD + 60
    out.append(f'<g id="legend" transform="translate({lx},{oy})" data-frame="Legend">')
    out.append(f'<rect data-type="frame" x="0" y="0" width="{lw}" height="{lh}" fill="#ffffff" data-title="Legend" />')
    out.append(f'<text x="{PAD/2}" y="{PAD}" font-family="noto_sans" font-size="36" font-weight="bold" fill="#1a1a1a">Legend</text>')
    y = PAD + 40
    for k in used_kinds:
        fill, stroke, ink, shape, desc = KINDS[k]
        shape_attr = "" if shape == "rectangle" else f' data-shape="{shape}"'
        out.append(f'<rect id="lg_{k}" x="{PAD/2}" y="{y}" width="120" height="64"{shape_attr} fill="{fill}" stroke="{stroke}" stroke-width="2" data-text-color="{ink}" data-font-size="14" data-content="{a(k)}" />')
        out.append(f'<textArea x="{PAD/2 + 140}" y="{y + 16}" width="{lw - 200}" font-family="noto_sans" font-size="18" fill="#595959">{escape(desc)}</textArea>')
        y += 90
    y += 20
    for k in used_edges:
        stroke, dash, desc = EDGES[k]
        style = ' data-line-style="dashed"' if dash == "5,5" else (' data-line-style="dotted"' if dash else "")
        out.append(f'<line data-type="divider" x1="{PAD/2}" y1="{y + 14}" x2="{PAD/2 + 120}" y2="{y + 14}" stroke="{stroke}" stroke-width="4"{style} />')
        out.append(f'<textArea x="{PAD/2 + 140}" y="{y}" width="{lw - 200}" font-family="noto_sans" font-size="18" fill="#595959">{escape(desc)}</textArea>')
        y += 60
    out.append(f'<line data-type="divider" x1="{PAD/2}" y1="{y + 14}" x2="{PAD/2 + 120}" y2="{y + 14}" stroke="#ff6464" stroke-width="4" data-line-style="dashed" />')
    out.append(f'<textArea x="{PAD/2 + 140}" y="{y}" width="{lw - 200}" font-family="noto_sans" font-size="18" fill="#595959">Trust boundary (checked in code)</textArea>')
    out.append("</g>")

    # ---------- design rationale doc ----------
    doc = rationale_markdown(spec)
    out.append(f'<foreignObject id="rationale" x="{lx}" y="{oy + lh + 160}" width="784" height="1105" data-type="doc">\n{escape(doc)}\n</foreignObject>')
    # key-decision stickies under the main frame
    for i, d in enumerate(spec.get("key_decisions", [])[:6]):
        sx = ox + i * (350 + 32)
        out.append(f'<rect id="kd{i}" data-type="sticky" x="{sx}" y="{oy + fh + 96}" width="350" height="228" data-color="light_yellow" data-content="{a(d)}" />')
    out.append("</svg>")
    return "\n".join(out)


def rationale_markdown(spec):
    lines = [f"# Design rationale: {spec['title']}", ""]
    if spec.get("summary"):
        lines += [spec["summary"], ""]
    if spec.get("autonomy"):
        lines += ["## Autonomy level", spec["autonomy"], ""]
    for key, head in (("rationale", "Pattern decisions (with course chapter)"),
                      ("trust_boundaries", "Trust boundaries and their checkers"),
                      ("failure_handling", "Failure handling and stop reasons"),
                      ("hitl", "Human approval points"),
                      ("evals", "How success is evaluated"),
                      ("risks", "Open risks and owners"),
                      ("non_goals", "Non-goals")):
        if spec.get(key):
            lines.append(f"## {head}")
            lines += [f"- {x}" for x in spec[key]]
            lines.append("")
    lines.append("Designed with Agentic Architect (David Oluyale, Agentic AI Hub).")
    return "\n".join(lines)



def _wrap(text, width_px, size):
    per = max(6, int(width_px / (size * 0.55)))
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > per and cur:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines


def build_preview(spec):
    """A plain SVG (any browser can open it) that approximates the Miro layout,
    including elbowed connectors and labels. Use it to review the design before
    drawing, or as a picture for a README when Miro is not connected."""
    fw, fh, pos = layout(spec)
    W = fw + 160 + 560 + 40
    stick = spec.get("key_decisions", [])[:6]
    H = fh + (96 + 228 + 40 if stick else 40)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Noto Sans, Arial, sans-serif">',
         '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="context-stroke"/></marker></defs>',
         f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
         f'<rect x="0" y="0" width="{fw}" height="{fh}" fill="#ffffff" stroke="#e7e7e7" stroke-width="2"/>',
         f'<text x="{PAD}" y="{PAD + 56}" font-size="56" font-weight="bold" fill="#1a1a1a">{escape(spec["title"])}</text>']
    if spec.get("summary"):
        for i, ln in enumerate(_wrap(spec["summary"], fw - 2 * PAD, 22)[:2]):
            o.append(f'<text x="{PAD}" y="{PAD + 104 + i * 28}" font-size="22" fill="#595959">{escape(ln)}</text>')
    for li, layer in enumerate(spec["layers"]):
        y = TITLE_H + li * LANE_H
        o.append(f'<rect x="{PAD/2}" y="{y + 10}" width="{fw - PAD}" height="{LANE_H - 20}" rx="12" fill="{LANE_FILLS[li % 2]}" stroke="#e7e7e7" stroke-width="2"/>')
        o.append(f'<text x="{PAD}" y="{y + 64}" font-size="22" font-weight="bold" fill="#1a1a1a">{escape(layer["name"])}</text>')
        if layer.get("trust"):
            for i, ln in enumerate(_wrap(layer["trust"], LANE_LABEL_W - 60, 18)):
                o.append(f'<text x="{PAD}" y="{y + 94 + i * 24}" font-size="18" fill="#595959">{escape(ln)}</text>')
        if layer.get("boundary_below") and li < len(spec["layers"]) - 1:
            yb = TITLE_H + (li + 1) * LANE_H
            o.append(f'<line x1="{PAD/2}" y1="{yb}" x2="{fw - PAD/2}" y2="{yb}" stroke="#ff6464" stroke-width="4" stroke-dasharray="14,8"/>')
            o.append(f'<text x="{fw - PAD}" y="{yb - 8}" text-anchor="end" font-size="16" font-weight="bold" fill="#bd0a0a">TRUST BOUNDARY: {escape(layer["boundary_below"])}</text>')
    # connectors under nodes
    def anchor(p, side):
        x, y = p[0], p[1]
        return {"top": (x + NODE_W / 2, y), "bottom": (x + NODE_W / 2, y + NODE_H),
                "left": (x, y + NODE_H / 2), "right": (x + NODE_W, y + NODE_H / 2)}[side]
    labels = []
    for e in spec["edges"]:
        p1, p2 = pos[e["from"]], pos[e["to"]]
        s1, s2 = sides(p1, p2)
        (x1, y1), (x2, y2) = anchor(p1, s1), anchor(p2, s2)
        if s1 in ("top", "bottom"):
            ym = (y1 + y2) / 2
            pts = [(x1, y1), (x1, ym), (x2, ym), (x2, y2)]
            lx, ly = (x2, ym + (y2 - ym) / 2) if x1 != x2 else (x1, ym)
        else:
            pts = [(x1, y1), (x2, y2)]
            lx, ly = (x1 + x2) / 2, y1
        stroke, dash, _ = EDGES[e.get("kind", "data")]
        d = f' stroke-dasharray="{ "10,6" if dash == "5,5" else "4,4"}"' if dash else ""
        ends = ' marker-start="url(#ah)"' if e.get("bidirectional") else ""
        o.append(f'<polyline points="{" ".join(f"{a_},{b_}" for a_, b_ in pts)}" fill="none" stroke="{stroke}" stroke-width="3"{d} marker-end="url(#ah)"{ends}/>')
        if e.get("label"):
            labels.append((lx, ly, e["label"], stroke))
    for n in [n for l in spec["layers"] for n in l["nodes"]]:
        x, y = pos[n["id"]][0], pos[n["id"]][1]
        fill, stroke, ink, shape, _ = KINDS[n["kind"]]
        if shape == "hexagon":
            k = 28
            o.append(f'<polygon points="{x+k},{y} {x+NODE_W-k},{y} {x+NODE_W},{y+NODE_H/2} {x+NODE_W-k},{y+NODE_H} {x+k},{y+NODE_H} {x},{y+NODE_H/2}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        elif shape == "can":
            o.append(f'<rect x="{x}" y="{y+10}" width="{NODE_W}" height="{NODE_H-20}" fill="{fill}" stroke="{stroke}" stroke-width="2"/><ellipse cx="{x+NODE_W/2}" cy="{y+NODE_H-10}" rx="{NODE_W/2}" ry="10" fill="{fill}" stroke="{stroke}" stroke-width="2"/><rect x="{x+1}" y="{y+12}" width="{NODE_W-2}" height="{NODE_H-24}" fill="{fill}"/><ellipse cx="{x+NODE_W/2}" cy="{y+10}" rx="{NODE_W/2}" ry="10" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        elif shape == "cloud":
            o.append(f'<rect x="{x}" y="{y}" width="{NODE_W}" height="{NODE_H}" rx="60" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        else:
            rx = 16 if shape == "round_rectangle" else 0
            o.append(f'<rect x="{x}" y="{y}" width="{NODE_W}" height="{NODE_H}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        lines = [(ln, True) for ln in _wrap(n["label"], NODE_W - 50, 18)] + [(ln, False) for ln in _wrap(n.get("note", ""), NODE_W - 50, 15)]
        ty = y + NODE_H / 2 - (len(lines) - 1) * 11 + 6
        for i, (ln, b) in enumerate(lines):
            fw_attr = ' font-weight="bold"' if b else ""
            o.append(f'<text x="{x + NODE_W/2}" y="{ty + i*22}" text-anchor="middle" font-size="{18 if b else 15}"{fw_attr} fill="{ink}">{escape(ln)}</text>')
    for lx, ly, t, stroke in labels:
        w = len(t) * 8 + 14
        o.append(f'<rect x="{lx - w/2}" y="{ly - 12}" width="{w}" height="22" rx="4" fill="#ffffff" stroke="{stroke}" stroke-width="1"/><text x="{lx}" y="{ly + 4}" text-anchor="middle" font-size="13" fill="#313131">{escape(t)}</text>')
    # legend
    lx0 = fw + 160
    used_kinds = [k for k in KINDS if any(n["kind"] == k for l in spec["layers"] for n in l["nodes"])]
    used_edges = [k for k in EDGES if any(e.get("kind", "data") == k for e in spec["edges"])]
    o.append(f'<text x="{lx0}" y="{PAD}" font-size="36" font-weight="bold" fill="#1a1a1a">Legend</text>')
    y = PAD + 40
    for k in used_kinds:
        fill, stroke, ink, shape, desc = KINDS[k]
        o.append(f'<rect x="{lx0}" y="{y}" width="120" height="56" rx="{16 if shape != "rectangle" else 0}" fill="{fill}" stroke="{stroke}" stroke-width="2"/><text x="{lx0+60}" y="{y+33}" text-anchor="middle" font-size="14" fill="{ink}">{k}</text><text x="{lx0+140}" y="{y+34}" font-size="17" fill="#595959">{escape(desc)}</text>')
        y += 80
    for k in used_edges + ["boundary"]:
        stroke, dash, desc = EDGES[k] if k != "boundary" else ("#ff6464", "5,5", "Trust boundary (checked in code)")
        d = f' stroke-dasharray="{ "10,6" if dash == "5,5" else "4,4"}"' if dash else ""
        o.append(f'<line x1="{lx0}" y1="{y+14}" x2="{lx0+120}" y2="{y+14}" stroke="{stroke}" stroke-width="4"{d}/><text x="{lx0+140}" y="{y+20}" font-size="17" fill="#595959">{escape(desc)}</text>')
        y += 50
    for i, dtext in enumerate(stick):
        sx, sy = i * (350 + 32), fh + 96
        o.append(f'<rect x="{sx}" y="{sy}" width="350" height="228" fill="#fff6b6" stroke="#ffdc4a"/>')
        for j, ln in enumerate(_wrap(dtext, 310, 22)[:6]):
            o.append(f'<text x="{sx + 175}" y="{sy + 60 + j*30}" text-anchor="middle" font-size="22" fill="#1a1a1a">{escape(ln)}</text>')
    o.append("</svg>")
    return "\n".join(o)


def build_mermaid(spec):
    m = ["flowchart TB"]
    for k, (fill, stroke, ink, *_ ) in KINDS.items():
        m.append(f"    classDef {k} fill:{fill},stroke:{stroke},color:{ink}")
    shapes = {"round_rectangle": ("([", "])"), "rectangle": ("[", "]"), "hexagon": ("{{", "}}"),
              "can": ("[(", ")]"), "cloud": (">", "]")}
    for li, layer in enumerate(spec["layers"]):
        name = layer["name"] + (f" ({layer['trust']})" if layer.get("trust") else "")
        m.append(f'    subgraph L{li}["{name.replace(chr(34), chr(39))}"]')
        for n in layer["nodes"]:
            o, c = shapes[KINDS[n["kind"]][3]]
            label = n["label"] + (f"<br/><small>{n['note']}</small>" if n.get("note") else "")
            m.append(f'        {n["id"]}{o}"{label.replace(chr(34), chr(39))}"{c}:::{n["kind"]}')
        m.append("    end")
    arrows = {"data": "-->", "control": "==>", "approval": "-.->", "untrusted": "-.->", "telemetry": "-.->"}
    for e in spec["edges"]:
        ar = arrows[e.get("kind", "data")]
        lbl = f'|{e["label"]}|' if e.get("label") else ""
        m.append(f"    {e['from']} {ar}{lbl} {e['to']}")
    return "\n".join(m) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--svg")
    ap.add_argument("--mermaid")
    ap.add_argument("--preview", help="write a plain SVG preview (open in any browser)")
    ap.add_argument("--origin", default="0,0", help="top-left x,y on the board (pick an empty area)")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    spec = json.load(open(args.spec))
    ids = validate(spec)
    n_nodes = len(ids)
    if len(spec.get("summary", "")) > 220:
        print("warning: summary over 220 chars may wrap into the first lane; shorten it", file=sys.stderr)
    if n_nodes > 24:
        print(f"warning: {n_nodes} nodes; split into an overview plus detail frames (<= 24 each)", file=sys.stderr)
    for w in crossing_warnings(spec, layout(spec)[2]):
        print("warning: " + w, file=sys.stderr)
    if args.check:
        print(f"ok: {len(spec['layers'])} layers, {n_nodes} nodes, {len(spec['edges'])} edges")
        return
    ox, oy = (int(v) for v in args.origin.split(","))
    if args.svg:
        open(args.svg, "w").write(build_svg(spec, (ox, oy)))
        print("wrote", args.svg)
    if args.preview:
        open(args.preview, "w").write(build_preview(spec))
        print("wrote", args.preview)
    if args.mermaid:
        open(args.mermaid, "w").write(build_mermaid(spec))
        print("wrote", args.mermaid)


if __name__ == "__main__":
    main()
