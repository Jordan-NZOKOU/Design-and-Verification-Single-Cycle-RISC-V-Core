#!/usr/bin/env python3
# Copyright 2026 Jordan Nzokou and Doeg Tiozang
# Project: Nexvantis
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Generate the complete Nexvantis diagram set as native draw.io sources.

The canonical assets are uncompressed diagrams.net/draw.io XML files.  SVG,
PNG, and PDF release files are rendered from the same geometry so the editable
source and published figures remain synchronized.  When Draw.io Desktop is
available, the generated ``.drawio`` files can also be exported directly with
its command-line interface without changing the diagrams.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence
from xml.sax.saxutils import escape, quoteattr

try:
    from PIL import Image, PngImagePlugin
except Exception:  # pragma: no cover - optional metadata enhancement
    Image = None
    PngImagePlugin = None

try:
    import fitz
except Exception:  # pragma: no cover - optional metadata enhancement
    fitz = None

ROOT = Path(__file__).resolve().parents[1]
DIAGRAM_DIR = ROOT / "13_diagrams"
SOURCE_DIR = DIAGRAM_DIR / "source"
SVG_DIR = DIAGRAM_DIR / "svg"
PNG_DIR = DIAGRAM_DIR / "png"
PDF_DIR = DIAGRAM_DIR / "pdf"
MANIFEST_PATH = DIAGRAM_DIR / "diagram_manifest.json"
COMBINED_DRAWIO = SOURCE_DIR / "Nexvantis_Diagram_Library.drawio"

PROJECT = "Nexvantis"
COPYRIGHT = "Copyright 2026 Jordan Nzokou and Doeg Tiozang"
LICENSE_NAME = "Apache License 2.0"
NOTICE_SHORT = f"{COPYRIGHT} | Project: {PROJECT} | {LICENSE_NAME}"
NOTICE_FULL = """Copyright 2026 Jordan Nzokou and Doeg Tiozang
Project: Nexvantis

Licensed under the Apache License, Version 2.0 (the \"License\");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an \"AS IS\" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License."""

# Restrained engineering palette shared by every diagram.
NAVY = "#0B1F3A"
BLUE = "#146FA8"
TEAL = "#008A93"
PURPLE = "#6554C0"
ORANGE = "#C76300"
GREEN = "#2E7D32"
RED = "#B42318"
INK = "#243447"
MID = "#5E6C84"
GRID = "#D7DEE8"
PALE = "#F5F8FC"
PALE_BLUE = "#EAF3FA"
PALE_TEAL = "#E8F6F5"
PALE_PURPLE = "#F0EDFF"
PALE_ORANGE = "#FFF2E4"
PALE_GREEN = "#EAF5EB"
PALE_RED = "#FDEDED"
WHITE = "#FFFFFF"
BLACK = "#111827"

CANVAS_W = 1800
CANVAS_H = 1000
CONTENT_TOP = 110
CONTENT_BOTTOM = 940


@dataclass
class Element:
    kind: str
    id: str
    x: float = 0
    y: float = 0
    w: float = 0
    h: float = 0
    label: str = ""
    fill: str = WHITE
    stroke: str = INK
    stroke_width: float = 2.0
    font_size: int = 18
    font_color: str = INK
    bold: bool = False
    align: str = "center"
    valign: str = "middle"
    radius: float = 10
    points: list[tuple[float, float]] = field(default_factory=list)
    arrow: bool = False
    dashed: bool = False
    opacity: float = 1.0
    rotation: float = 0.0
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass
class Diagram:
    stem: str
    title: str
    category: str
    description: str
    subtitle: str = ""
    width: int = CANVAS_W
    height: int = CANVAS_H
    elements: list[Element] = field(default_factory=list)
    _counter: int = 0

    def _id(self, prefix: str = "e") -> str:
        self._counter += 1
        return f"{prefix}{self._counter}"

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        label: str = "",
        *,
        fill: str = WHITE,
        stroke: str = INK,
        stroke_width: float = 2,
        font_size: int = 18,
        font_color: str = INK,
        bold: bool = False,
        radius: float = 10,
        kind: str = "rect",
        align: str = "center",
        valign: str = "middle",
        opacity: float = 1.0,
        element_id: str | None = None,
    ) -> str:
        eid = element_id or self._id(kind[0])
        self.elements.append(
            Element(
                kind=kind,
                id=eid,
                x=x,
                y=y,
                w=w,
                h=h,
                label=label,
                fill=fill,
                stroke=stroke,
                stroke_width=stroke_width,
                font_size=font_size,
                font_color=font_color,
                bold=bold,
                radius=radius,
                align=align,
                valign=valign,
                opacity=opacity,
            )
        )
        return eid

    def text(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        label: str,
        *,
        font_size: int = 18,
        font_color: str = INK,
        bold: bool = False,
        align: str = "center",
        valign: str = "middle",
        rotation: float = 0,
        element_id: str | None = None,
    ) -> str:
        eid = element_id or self._id("t")
        self.elements.append(
            Element(
                kind="text",
                id=eid,
                x=x,
                y=y,
                w=w,
                h=h,
                label=label,
                fill="none",
                stroke="none",
                font_size=font_size,
                font_color=font_color,
                bold=bold,
                align=align,
                valign=valign,
                rotation=rotation,
            )
        )
        return eid

    def line(
        self,
        points: Sequence[tuple[float, float]],
        *,
        stroke: str = BLUE,
        stroke_width: float = 3,
        arrow: bool = True,
        dashed: bool = False,
        label: str = "",
        font_size: int = 15,
        font_color: str | None = None,
        element_id: str | None = None,
    ) -> str:
        eid = element_id or self._id("l")
        self.elements.append(
            Element(
                kind="line",
                id=eid,
                points=list(points),
                stroke=stroke,
                stroke_width=stroke_width,
                arrow=arrow,
                dashed=dashed,
                label=label,
                font_size=font_size,
                font_color=font_color or stroke,
            )
        )
        return eid

    def polygon(
        self,
        points: Sequence[tuple[float, float]],
        label: str = "",
        *,
        fill: str = WHITE,
        stroke: str = INK,
        stroke_width: float = 2,
        font_size: int = 18,
        font_color: str = INK,
        bold: bool = False,
        kind: str = "polygon",
        element_id: str | None = None,
    ) -> str:
        eid = element_id or self._id("p")
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        self.elements.append(
            Element(
                kind=kind,
                id=eid,
                x=min(xs),
                y=min(ys),
                w=max(xs) - min(xs),
                h=max(ys) - min(ys),
                points=list(points),
                label=label,
                fill=fill,
                stroke=stroke,
                stroke_width=stroke_width,
                font_size=font_size,
                font_color=font_color,
                bold=bold,
            )
        )
        return eid

    def ellipse(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        label: str = "",
        *,
        fill: str = WHITE,
        stroke: str = INK,
        stroke_width: float = 2,
        font_size: int = 18,
        font_color: str = INK,
        bold: bool = False,
    ) -> str:
        return self.rect(
            x,
            y,
            w,
            h,
            label,
            fill=fill,
            stroke=stroke,
            stroke_width=stroke_width,
            font_size=font_size,
            font_color=font_color,
            bold=bold,
            radius=min(w, h) / 2,
            kind="ellipse",
        )

    def diamond(self, x: float, y: float, w: float, h: float, label: str, **kwargs: object) -> str:
        pts = [(x + w / 2, y), (x + w, y + h / 2), (x + w / 2, y + h), (x, y + h / 2)]
        return self.polygon(pts, label, kind="diamond", **kwargs)

    def mux(self, x: float, y: float, w: float, h: float, label: str = "MUX", **kwargs: object) -> str:
        pts = [(x, y), (x + w * 0.78, y + h * 0.08), (x + w, y + h / 2), (x + w * 0.78, y + h * 0.92), (x, y + h)]
        return self.polygon(pts, label, kind="mux", **kwargs)

    def alu(self, x: float, y: float, w: float, h: float, label: str = "ALU", **kwargs: object) -> str:
        pts = [
            (x, y),
            (x + w * 0.62, y + h * 0.08),
            (x + w, y + h * 0.50),
            (x + w * 0.62, y + h * 0.92),
            (x, y + h),
            (x + w * 0.20, y + h * 0.50),
        ]
        return self.polygon(pts, label, kind="alu", **kwargs)

    def register(self, x: float, y: float, w: float, h: float, label: str, **kwargs: object) -> str:
        eid = self.rect(x, y, w, h, label, kind="register", **kwargs)
        # Draw a small clock wedge as a separate line pair.
        self.line([(x, y + h - 24), (x + 12, y + h - 12), (x, y + h)], stroke=kwargs.get("stroke", INK), stroke_width=2, arrow=False)
        return eid

    def memory(self, x: float, y: float, w: float, h: float, label: str, **kwargs: object) -> str:
        eid = self.rect(x, y, w, h, label, kind="memory", **kwargs)
        stroke = kwargs.get("stroke", INK)
        self.line([(x + 14, y + 10), (x + 14, y + h - 10)], stroke=stroke, stroke_width=1.5, arrow=False)
        self.line([(x + 24, y + 10), (x + 24, y + h - 10)], stroke=stroke, stroke_width=1.0, arrow=False)
        return eid

    def section(self, x: float, y: float, w: float, label: str, color: str = BLUE) -> None:
        self.rect(x, y, w, 36, label.upper(), fill=color, stroke=color, font_color=WHITE, font_size=14, bold=True, radius=5)

    def callout(self, x: float, y: float, w: float, h: float, title: str, body: str, color: str = BLUE) -> None:
        self.rect(x, y, w, h, "", fill=WHITE, stroke=color, stroke_width=2, radius=12)
        self.rect(x, y, w, 36, title, fill=color, stroke=color, font_color=WHITE, font_size=15, bold=True, radius=12)
        # Wrap prose explicitly so SVG/PDF exports and draw.io sources remain
        # readable at repository and report scale without relying on a renderer-
        # specific automatic text-layout algorithm.
        width_chars = max(24, int((w - 28) / 8.2))
        wrapped: list[str] = []
        for paragraph in body.splitlines() or [body]:
            if not paragraph:
                wrapped.append("")
                continue
            wrapped.extend(textwrap.wrap(paragraph, width=width_chars, break_long_words=False) or [""])
        self.text(x + 14, y + 45, w - 28, h - 55, "\n".join(wrapped), font_size=14, font_color=INK, align="left", valign="top")

    def waveform(
        self,
        label: str,
        y: float,
        transitions: Sequence[tuple[float, int | str]],
        *,
        x0: float = 240,
        x1: float = 1640,
        low: float = 24,
        high: float = 0,
        color: str = BLUE,
        width: float = 3,
        bus: bool = False,
    ) -> None:
        self.text(60, y - 18, 155, 36, label, font_size=16, bold=True, align="right")
        # transitions contains normalized x fraction and state/value.
        pts: list[tuple[float, float]] = []
        last_x = x0
        last_state = transitions[0][1]
        def state_y(state: int | str) -> float:
            if bus:
                return y
            return y + (high if int(state) else low)
        pts.append((x0, state_y(last_state)))
        for frac, state in transitions[1:]:
            xx = x0 + (x1 - x0) * frac
            pts.append((xx, state_y(last_state)))
            if not bus:
                pts.append((xx, state_y(state)))
            last_x = xx
            last_state = state
        pts.append((x1, state_y(last_state)))
        self.line(pts, stroke=color, stroke_width=width, arrow=False)
        if bus:
            # Draw value labels and separators.
            for i, (frac, value) in enumerate(transitions):
                xx = x0 + (x1 - x0) * frac
                if i > 0:
                    self.line([(xx, y - 18), (xx, y + 18)], stroke=color, stroke_width=1.3, arrow=False)
                next_frac = transitions[i + 1][0] if i + 1 < len(transitions) else 1.0
                mid = x0 + (x1 - x0) * ((frac + next_frac) / 2)
                self.text(mid - 65, y - 20, 130, 40, str(value), font_size=14, font_color=color, bold=True)
        else:
            self.text(x0 - 30, y - 13, 24, 20, "1", font_size=12, font_color=MID, align="right")
            self.text(x0 - 30, y + low - 13, 24, 20, "0", font_size=12, font_color=MID, align="right")

    def base(self) -> None:
        # Background and title region.
        self.rect(0, 0, self.width, self.height, "", fill=WHITE, stroke=WHITE, stroke_width=0, radius=0, element_id="background")
        self.rect(0, 0, self.width, 86, "", fill=NAVY, stroke=NAVY, stroke_width=0, radius=0, element_id="titlebar")
        self.text(48, 13, 1260, 44, self.title, font_size=30, font_color=WHITE, bold=True, align="left")
        if self.subtitle:
            self.text(50, 53, 1450, 25, self.subtitle, font_size=14, font_color="#DDE7F2", align="left")
        self.rect(0, self.height - 44, self.width, 44, "", fill=PALE, stroke=GRID, stroke_width=1, radius=0, element_id="footerbar")
        self.text(38, self.height - 34, self.width - 76, 24, NOTICE_SHORT, font_size=12, font_color=MID, align="center")


# ---------------------------------------------------------------------------
# SVG renderer
# ---------------------------------------------------------------------------

def _svg_text_lines(label: str) -> list[str]:
    return label.split("\n") if label else []


def _svg_escape(value: str) -> str:
    return escape(value, {'"': '&quot;'})


def _svg_text(element: Element) -> str:
    lines = _svg_text_lines(element.label)
    if not lines:
        return ""
    x = element.x + element.w / 2
    if element.align == "left":
        x = element.x + 8
        anchor = "start"
    elif element.align == "right":
        x = element.x + element.w - 8
        anchor = "end"
    else:
        anchor = "middle"

    line_height = element.font_size * 1.22
    total = line_height * len(lines)
    if element.valign == "top":
        y = element.y + element.font_size + 4
    elif element.valign == "bottom":
        y = element.y + element.h - total + element.font_size
    else:
        y = element.y + (element.h - total) / 2 + element.font_size
    weight = "700" if element.bold else "400"
    transform = ""
    if element.rotation:
        cx = element.x + element.w / 2
        cy = element.y + element.h / 2
        transform = f' transform="rotate({element.rotation} {cx:.2f} {cy:.2f})"'
    tspans = []
    for index, line in enumerate(lines):
        dy = 0 if index == 0 else line_height
        tspans.append(f'<tspan x="{x:.2f}" dy="{dy:.2f}">{_svg_escape(line)}</tspan>')
    return (
        f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="{anchor}" '
        f'font-family="DejaVu Sans, Arial, sans-serif" font-size="{element.font_size}" '
        f'font-weight="{weight}" fill="{element.font_color}"{transform}>'
        + "".join(tspans)
        + "</text>"
    )


def _svg_shape(element: Element) -> str:
    common = (
        f'fill="{element.fill}" stroke="{element.stroke}" '
        f'stroke-width="{element.stroke_width}" opacity="{element.opacity}"'
    )
    if element.kind in {"rect", "register", "memory"}:
        shape = f'<rect x="{element.x}" y="{element.y}" width="{element.w}" height="{element.h}" rx="{element.radius}" {common}/>'
    elif element.kind == "ellipse":
        shape = f'<ellipse cx="{element.x + element.w/2}" cy="{element.y + element.h/2}" rx="{element.w/2}" ry="{element.h/2}" {common}/>'
    elif element.kind in {"polygon", "mux", "alu", "diamond"}:
        points = " ".join(f"{x},{y}" for x, y in element.points)
        shape = f'<polygon points="{points}" {common}/>'
    elif element.kind == "text":
        shape = ""
    elif element.kind == "line":
        points = " ".join(f"{x},{y}" for x, y in element.points)
        dash = ' stroke-dasharray="10 7"' if element.dashed else ""
        marker = ' marker-end="url(#arrow)"' if element.arrow else ""
        shape = (
            f'<polyline points="{points}" fill="none" stroke="{element.stroke}" '
            f'stroke-width="{element.stroke_width}" stroke-linejoin="round" '
            f'stroke-linecap="round"{dash}{marker}/>'
        )
        if element.label:
            mid = element.points[len(element.points) // 2]
            temp = Element(
                kind="text",
                id=element.id + "_label",
                x=mid[0] - 100,
                y=mid[1] - 30,
                w=200,
                h=25,
                label=element.label,
                font_size=element.font_size,
                font_color=element.font_color,
                bold=True,
            )
            shape += _svg_text(temp)
        return shape
    else:
        shape = ""
    return shape + _svg_text(element)


def render_svg(diagram: Diagram) -> str:
    comment_lines = "\n".join(f" * {line}" if line else " *" for line in NOTICE_FULL.splitlines())
    body = "\n  ".join(_svg_shape(element) for element in diagram.elements)
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!--
/**
{comment_lines}
 */
-->
<svg xmlns="http://www.w3.org/2000/svg" width="{diagram.width}" height="{diagram.height}" viewBox="0 0 {diagram.width} {diagram.height}" role="img" aria-labelledby="title desc">
  <title id="title">{_svg_escape(diagram.title)}</title>
  <desc id="desc">{_svg_escape(diagram.description)}</desc>
  <metadata>{_svg_escape(NOTICE_FULL)}</metadata>
  <defs>
    <marker id="arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L10,4 L0,8 z" fill="context-stroke"/>
    </marker>
    <filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#0B1F3A" flood-opacity="0.12"/>
    </filter>
  </defs>
  {body}
</svg>
'''


# ---------------------------------------------------------------------------
# draw.io XML renderer
# ---------------------------------------------------------------------------

def _drawio_value(label: str) -> str:
    if not label:
        return ""
    lines = label.split("\n")
    return "<br>".join(escape(line) for line in lines)


def _drawio_vertex_style(element: Element) -> str:
    base = [
        "html=1",
        "whiteSpace=wrap",
        f"fillColor={element.fill if element.fill != 'none' else 'none'}",
        f"strokeColor={element.stroke if element.stroke != 'none' else 'none'}",
        f"strokeWidth={element.stroke_width}",
        f"fontColor={element.font_color}",
        f"fontSize={element.font_size}",
        f"fontStyle={1 if element.bold else 0}",
        f"align={element.align}",
        f"verticalAlign={element.valign}",
        f"opacity={int(element.opacity * 100)}",
    ]
    if element.kind in {"rect", "register", "memory"}:
        base += ["rounded=1" if element.radius else "rounded=0", "arcSize=8"]
    elif element.kind == "ellipse":
        base += ["ellipse"]
    elif element.kind == "diamond":
        base += ["rhombus"]
    elif element.kind == "mux":
        base += ["shape=mxgraph.basic.trapezoid", "direction=east"]
    elif element.kind == "alu":
        base += ["shape=mxgraph.basic.pentagon", "direction=east"]
    elif element.kind == "text":
        base += ["strokeColor=none", "fillColor=none", "resizable=0"]
    elif element.kind == "polygon":
        base += ["shape=mxgraph.basic.polygon", "polyCoords=0.5,0,1,0.5,0.5,1,0,0.5"]
    if element.rotation:
        base.append(f"rotation={element.rotation}")
    return ";".join(base) + ";"


def _drawio_cell(element: Element, parent: str = "1") -> str:
    if element.kind == "line":
        style = [
            "edgeStyle=orthogonalEdgeStyle",
            "rounded=0",
            "orthogonalLoop=1",
            "jettySize=auto",
            "html=1",
            f"strokeColor={element.stroke}",
            f"strokeWidth={element.stroke_width}",
            f"fontColor={element.font_color}",
            f"fontSize={element.font_size}",
            "endArrow=block" if element.arrow else "endArrow=none",
            "endFill=1" if element.arrow else "endFill=0",
            f"dashed={1 if element.dashed else 0}",
        ]
        source = element.points[0]
        target = element.points[-1]
        intermediate = element.points[1:-1]
        points_xml = ""
        if intermediate:
            points_xml = '<Array as="points">' + "".join(
                f'<mxPoint x="{x:.2f}" y="{y:.2f}"/>' for x, y in intermediate
            ) + "</Array>"
        return (
            f'<mxCell id="{element.id}" value={quoteattr(_drawio_value(element.label))} '
            f'style={quoteattr(";".join(style) + ";")} edge="1" parent="{parent}">'
            f'<mxGeometry relative="1" as="geometry">'
            f'<mxPoint x="{source[0]:.2f}" y="{source[1]:.2f}" as="sourcePoint"/>'
            f'<mxPoint x="{target[0]:.2f}" y="{target[1]:.2f}" as="targetPoint"/>'
            f'{points_xml}</mxGeometry></mxCell>'
        )
    style = _drawio_vertex_style(element)
    return (
        f'<mxCell id="{element.id}" value={quoteattr(_drawio_value(element.label))} '
        f'style={quoteattr(style)} vertex="1" parent="{parent}">'
        f'<mxGeometry x="{element.x:.2f}" y="{element.y:.2f}" width="{element.w:.2f}" height="{element.h:.2f}" as="geometry"/>'
        f'</mxCell>'
    )


def drawio_graph_model(diagram: Diagram) -> str:
    cells = "\n        ".join(_drawio_cell(element) for element in diagram.elements)
    return f'''<mxGraphModel dx="1800" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{diagram.width}" pageHeight="{diagram.height}" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        {cells}
      </root>
    </mxGraphModel>'''


def drawio_document(diagrams: Sequence[Diagram]) -> str:
    comment_lines = "\n".join((f"  {line}" if line else "") for line in NOTICE_FULL.splitlines())
    pages = []
    for diagram in diagrams:
        page_id = uuid.uuid5(uuid.NAMESPACE_URL, f"nexvantis:{diagram.stem}").hex[:16]
        pages.append(
            f'<diagram id="{page_id}" name={quoteattr(diagram.title)}>{drawio_graph_model(diagram)}</diagram>'
        )
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!--
{comment_lines}
-->
<mxfile host="app.diagrams.net" modified="2026-09-12T00:00:00.000Z" agent="Nexvantis draw.io generator" version="24.7.17" type="device" pages="{len(diagrams)}">
  {"".join(pages)}
</mxfile>
'''


# ---------------------------------------------------------------------------
# Diagram content helpers
# ---------------------------------------------------------------------------

def add_legend(d: Diagram, entries: Sequence[tuple[str, str]], x: float, y: float) -> None:
    cursor = x
    for label, color in entries:
        d.line([(cursor, y + 10), (cursor + 42, y + 10)], stroke=color, stroke_width=5, arrow=False)
        d.text(cursor + 48, y - 2, 118, 24, label, font_size=13, align="left")
        cursor += 176


def add_bus_label(d: Diagram, x: float, y: float, text: str, color: str = BLUE) -> None:
    d.rect(x, y, max(70, 10 * len(text)), 26, text, fill=WHITE, stroke=color, stroke_width=1.2, font_size=13, font_color=color, bold=True, radius=5)


def add_card(d: Diagram, x: float, y: float, w: float, h: float, number: str, title: str, body: str, color: str) -> None:
    d.rect(x, y, w, h, "", fill=WHITE, stroke=color, stroke_width=2.2, radius=13)
    d.ellipse(x + 16, y + 16, 46, 46, number, fill=color, stroke=color, font_color=WHITE, font_size=16, bold=True)
    d.text(x + 74, y + 12, w - 88, 46, title, font_size=16, font_color=NAVY, bold=True, align="left")
    d.text(x + 18, y + 70, w - 36, h - 84, body, font_size=13, font_color=INK, align="left", valign="top")


def diagram_01() -> Diagram:
    d = Diagram(
        "01_processor_architecture",
        "Single-Cycle RV32I-Subset Processor Architecture",
        "architecture",
        "Top-level RV32I-subset datapath and control flow.",
        "Processor-style block schematic with distinct datapath, control, memory, and next-PC networks",
    )
    d.base()

    # Functional regions provide the visual rhythm used in processor textbooks.
    d.section(45, 110, 300, "Instruction fetch", BLUE)
    d.section(365, 110, 475, "Decode and operands", TEAL)
    d.section(860, 110, 410, "Execute", PURPLE)
    d.section(1290, 110, 275, "Memory", ORANGE)
    d.section(1585, 110, 170, "Write-back", GREEN)

    # Central control block sits above the datapath and fans out vertically.
    d.rect(650, 170, 505, 118,
           "CONTROL UNIT\nMain decoder | ALU decoder | BEQ qualification",
           fill="#FFF7E8", stroke=ORANGE, stroke_width=2.8,
           font_size=18, bold=True, radius=15)

    # Main datapath row.
    d.mux(50, 410, 76, 138, "PC\nMUX", fill=PALE_RED, stroke=RED,
          font_size=14, bold=True)
    d.register(158, 424, 112, 110, "PC", fill=PALE_BLUE, stroke=BLUE,
               font_size=22, bold=True)
    d.memory(315, 350, 205, 245, "Instruction\nMemory", fill=PALE_BLUE,
             stroke=BLUE, font_size=20, bold=True)
    d.register(620, 335, 245, 275,
               "Register File\n\n2 read ports\n1 write port\nx0 = 0",
               fill=PALE_TEAL, stroke=TEAL, font_size=18, bold=True)
    d.mux(965, 420, 86, 160, "SrcB", fill=PALE_PURPLE, stroke=PURPLE,
          font_size=17, bold=True)
    d.alu(1100, 355, 190, 250, "ALU", fill=PALE_PURPLE, stroke=PURPLE,
          font_size=25, bold=True)
    d.memory(1350, 370, 190, 225, "Data\nMemory", fill=PALE_ORANGE,
             stroke=ORANGE, font_size=21, bold=True)
    d.mux(1625, 420, 82, 160, "WB", fill=PALE_GREEN, stroke=GREEN,
          font_size=18, bold=True)

    # Address-generation row.
    d.rect(315, 700, 190, 92, "PC + 4", fill=PALE_BLUE, stroke=BLUE,
           font_size=20, bold=True, radius=12)
    d.rect(620, 690, 245, 105, "Immediate Generator", fill=PALE_TEAL,
           stroke=TEAL, font_size=19, bold=True, radius=12)
    d.rect(1090, 700, 210, 92, "Branch Target\nPC + ImmExt",
           fill=PALE_RED, stroke=RED, font_size=18, bold=True, radius=12)

    # Fetch and decode buses.
    d.line([(126, 479), (158, 479)], stroke=RED, stroke_width=5, arrow=True)
    d.line([(270, 479), (315, 479)], stroke=BLUE, stroke_width=5, arrow=True,
           label="PC")
    d.line([(520, 395), (580, 395), (580, 385), (620, 385)],
           stroke=BLUE, stroke_width=4.5, arrow=True, label="rs1")
    d.line([(520, 470), (620, 470)], stroke=BLUE, stroke_width=4.5,
           arrow=True, label="rs2")
    d.line([(520, 548), (580, 548), (580, 555), (620, 555)],
           stroke=BLUE, stroke_width=4.5, arrow=True, label="rd")
    d.line([(520, 570), (560, 570), (560, 742), (620, 742)],
           stroke=TEAL, stroke_width=4, arrow=True, label="Instr[31:7]")
    d.line([(520, 375), (555, 375), (555, 315), (650, 315), (650, 245)],
           stroke=ORANGE, stroke_width=2.5, arrow=True, dashed=True)
    d.text(505, 285, 140, 26, "opcode / funct", font_size=13,
           font_color=ORANGE, bold=True)

    # Execute and memory buses.
    d.line([(865, 385), (1075, 385), (1075, 420), (1100, 420)],
           stroke=TEAL, stroke_width=5, arrow=True, label="RD1")
    d.line([(865, 500), (965, 500)], stroke=TEAL, stroke_width=5,
           arrow=True, label="RD2")
    d.line([(865, 500), (900, 500), (900, 635), (1320, 635),
            (1320, 515), (1350, 515)],
           stroke=TEAL, stroke_width=4.2, arrow=True, label="WriteData")
    d.line([(865, 742), (920, 742), (920, 550), (965, 550)],
           stroke=TEAL, stroke_width=5, arrow=True, label="ImmExt")
    d.line([(1051, 500), (1100, 500)], stroke=PURPLE, stroke_width=5,
           arrow=True)
    d.line([(1290, 480), (1350, 480)], stroke=PURPLE, stroke_width=5,
           arrow=True, label="ALUResult")
    d.line([(1290, 480), (1320, 480), (1320, 445), (1625, 445)],
           stroke=PURPLE, stroke_width=4, arrow=True)
    d.line([(1540, 445), (1625, 540)], stroke=ORANGE, stroke_width=5,
           arrow=True, label="ReadData")

    # Write-back bus runs above the datapath, clearly separated from controls.
    d.line([(1707, 500), (1740, 500), (1740, 320), (590, 320),
            (590, 580), (620, 580)],
           stroke=GREEN, stroke_width=5, arrow=True)
    d.text(1160, 294, 90, 24, "Result", font_size=13,
           font_color=GREEN, bold=True)

    # PC+4 and branch-target networks occupy the lower layer.
    d.line([(215, 534), (215, 746), (315, 746)],
           stroke=BLUE, stroke_width=4, arrow=True)
    d.line([(505, 746), (535, 746), (535, 850), (82, 850), (82, 548)],
           stroke=BLUE, stroke_width=4, arrow=True, label="PCPlus4")
    d.line([(215, 534), (215, 820), (1060, 820), (1060, 746), (1090, 746)],
           stroke=RED, stroke_width=4, arrow=True)
    d.line([(865, 742), (1030, 742), (1030, 770), (1090, 770)],
           stroke=RED, stroke_width=4, arrow=True)
    d.line([(1300, 746), (1330, 746), (1330, 875), (113, 875), (113, 548)],
           stroke=RED, stroke_width=4, arrow=True, label="PCTarget")

    # Control fan-out uses short, orthogonal, dashed routes.
    d.line([(705, 288), (705, 335)], stroke=ORANGE, stroke_width=2.7,
           arrow=True, dashed=True)
    d.line([(790, 288), (790, 645), (742, 645), (742, 690)],
           stroke=ORANGE, stroke_width=2.5, arrow=True, dashed=True)
    d.line([(900, 288), (900, 395), (1008, 395), (1008, 420)],
           stroke=ORANGE, stroke_width=2.5, arrow=True, dashed=True)
    d.line([(1015, 288), (1015, 325), (1195, 325), (1195, 355)],
           stroke=ORANGE, stroke_width=2.5, arrow=True, dashed=True)
    d.line([(1090, 288), (1245, 288), (1245, 335), (1445, 335), (1445, 370)],
           stroke=ORANGE, stroke_width=2.5, arrow=True, dashed=True)
    d.line([(1125, 288), (1565, 288), (1565, 615), (1666, 615), (1666, 580)],
           stroke=ORANGE, stroke_width=2.5, arrow=True, dashed=True)
    d.line([(650, 230), (610, 230), (610, 900), (65, 900), (65, 548)],
           stroke=RED, stroke_width=2.8, arrow=True, dashed=True)

    add_legend(d, [("Datapath", BLUE), ("Control", ORANGE),
                   ("Branch", RED), ("Write-back", GREEN)], 485, 905)
    return d

def diagram_02() -> Diagram:
    d = Diagram(
        "02_verification_workflow",
        "Self-Checking RTL Verification Workflow",
        "verification",
        "Stimulus, DUT, checks, waveforms, and verdict flow.",
        "Deterministic tests, independent expected values, and reproducible evidence",
    )
    d.base()
    d.section(60, 120, 420, "Test intent and stimulus", BLUE)
    d.section(520, 120, 410, "Design under test", PURPLE)
    d.section(970, 120, 380, "Observation and checking", TEAL)
    d.section(1390, 120, 350, "Evidence and verdict", GREEN)

    add_card(d, 70, 185, 370, 150, "1", "Test plan", "Requirements, corner cases, expected architectural effects, and pass/fail criteria.", BLUE)
    add_card(d, 70, 380, 370, 150, "2", "Stimulus driver", "Clock/reset sequencing, directed vectors, instruction images, and legal timing.", BLUE)
    add_card(d, 70, 575, 370, 150, "3", "Reference data", "Golden arithmetic values, final register/memory state, and trace expectations.", BLUE)

    d.rect(570, 255, 310, 335, "DUT\n\nRTL modules\n+\nprocessor integration\n\nCombinational logic\nSequential state", fill=PALE_PURPLE, stroke=PURPLE, font_size=22, bold=True, radius=18)
    d.rect(585, 625, 280, 104, "QuestaSim / ModelSim\nor Icarus Verilog", fill=WHITE, stroke=PURPLE, font_size=18, bold=True, radius=12)

    add_card(d, 995, 190, 330, 145, "4", "Monitors", "Sample outputs, internal observation ports, memory writes, PC flow, and flags.", TEAL)
    add_card(d, 995, 380, 330, 145, "5", "Scoreboard", "Compare actual behavior against directed expectations and architectural state.", TEAL)
    add_card(d, 995, 570, 330, 145, "6", "Assertions", "Detect unknown values, illegal side effects, skipped addresses, and timing violations.", TEAL)

    d.rect(1430, 205, 270, 105, "Waveform evidence\nVCD / GTKWave", fill=PALE_BLUE, stroke=BLUE, font_size=18, bold=True, radius=12)
    d.rect(1430, 370, 270, 105, "Console evidence\ncycle trace + checks", fill=PALE_TEAL, stroke=TEAL, font_size=18, bold=True, radius=12)
    d.diamond(1480, 550, 170, 120, "All checks\npass?", fill=PALE_ORANGE, stroke=ORANGE, font_size=17, bold=True)
    d.rect(1375, 735, 165, 82, "PASS", fill=PALE_GREEN, stroke=GREEN, font_size=24, font_color=GREEN, bold=True, radius=16)
    d.rect(1585, 735, 165, 82, "FAIL", fill=PALE_RED, stroke=RED, font_size=24, font_color=RED, bold=True, radius=16)

    # Flow.
    d.line([(440, 260), (570, 320)], stroke=BLUE, stroke_width=4, arrow=True)
    d.line([(440, 455), (540, 455), (540, 420), (570, 420)], stroke=BLUE, stroke_width=4, arrow=True)
    d.line([(440, 650), (520, 650), (520, 505), (570, 505)], stroke=BLUE, stroke_width=4, arrow=True)
    d.line([(725, 590), (725, 625)], stroke=PURPLE, stroke_width=4, arrow=True)
    d.line([(880, 335), (995, 260)], stroke=PURPLE, stroke_width=4, arrow=True)
    d.line([(880, 420), (995, 450)], stroke=PURPLE, stroke_width=4, arrow=True)
    d.line([(880, 505), (995, 642)], stroke=PURPLE, stroke_width=4, arrow=True)
    d.line([(1325, 260), (1430, 260)], stroke=TEAL, stroke_width=4, arrow=True)
    d.line([(1325, 450), (1430, 420)], stroke=TEAL, stroke_width=4, arrow=True)
    d.line([(1325, 642), (1480, 610)], stroke=TEAL, stroke_width=4, arrow=True)
    d.line([(1565, 670), (1460, 735)], stroke=GREEN, stroke_width=4, arrow=True, label="yes")
    d.line([(1565, 670), (1665, 735)], stroke=RED, stroke_width=4, arrow=True, label="no")
    d.line([(1565, 550), (1565, 475)], stroke=ORANGE, stroke_width=2.4, arrow=True, dashed=True, label="evidence")
    d.callout(560, 785, 770, 105, "Regression principle", "Every milestone remains independently runnable. The final processor test combines cycle-level observation with end-state checks rather than relying on waveforms alone.", NAVY)
    return d


def diagram_03() -> Diagram:
    d = Diagram(
        "03_milestone_roadmap",
        "Eleven-Milestone Integration Roadmap",
        "workflow",
        "Progression from a 2:1 mux to the complete processor.",
        "Each milestone adds one architectural responsibility and its own regression",
    )
    d.base()
    stages = [
        ("01", "MUX", "Selection"),
        ("02", "PC + adders", "State / address"),
        ("03", "ALU", "Execute"),
        ("04", "Register file", "Operands"),
        ("05", "Immediate", "Decode data"),
        ("06", "Memories", "Fetch / load / store"),
        ("07", "Control unit", "Decode policy"),
        ("08", "Arithmetic", "First integration"),
        ("09", "Load / store", "Memory path"),
        ("10", "BEQ", "Control flow"),
        ("11", "Final CPU", "Regression"),
    ]
    colors = [BLUE, BLUE, PURPLE, TEAL, TEAL, ORANGE, ORANGE, PURPLE, ORANGE, RED, GREEN]
    y_positions = [210, 210, 210, 210, 210, 520, 520, 520, 520, 520, 520]
    x_positions = [60, 375, 690, 1005, 1320, 60, 340, 620, 900, 1180, 1460]
    widths = [270, 270, 270, 270, 270, 235, 235, 235, 235, 235, 235]
    for i, ((num, title, body), color, x, y, w) in enumerate(zip(stages, colors, x_positions, y_positions, widths)):
        add_card(d, x, y, w, 205, num, title, body + "\n\nStandalone RTL + self-checking testbench", color)
        if i < 4:
            d.line([(x + w, y + 103), (x_positions[i + 1], y + 103)], stroke=MID, stroke_width=3, arrow=True)
        if i == 4:
            d.line([(x + w / 2, y + 205), (x + w / 2, 475), (60 + widths[5] / 2, 475), (60 + widths[5] / 2, 520)], stroke=MID, stroke_width=3, arrow=True)
        if 5 <= i < 10:
            d.line([(x + w, y + 103), (x_positions[i + 1], y + 103)], stroke=MID, stroke_width=3, arrow=True)
    d.callout(60, 780, 520, 105, "Foundation", "Milestones 01-06 isolate primitive datapath blocks and their timing contracts.", BLUE)
    d.callout(640, 780, 520, 105, "Integration", "Milestones 07-10 connect decode, arithmetic, memory, and branch responsibilities.", PURPLE)
    d.callout(1220, 780, 520, 105, "Acceptance", "Milestone 11 executes a program and checks the complete architectural end state.", GREEN)
    return d


def diagram_04() -> Diagram:
    d = Diagram(
        "04_mux_structure",
        "Parameterized 2:1 Multiplexer",
        "subproject",
        "Combinational data-selection contract.",
        "The selected input propagates without clocked state",
    )
    d.base()
    d.section(70, 130, 1020, "RTL structure", BLUE)
    d.section(1160, 130, 570, "Contract", TEAL)
    d.rect(110, 260, 260, 95, "A [WIDTH-1:0]", fill=PALE_BLUE, stroke=BLUE, font_size=21, bold=True)
    d.rect(110, 520, 260, 95, "B [WIDTH-1:0]", fill=PALE_TEAL, stroke=TEAL, font_size=21, bold=True)
    d.rect(285, 715, 170, 75, "Sel", fill=PALE_ORANGE, stroke=ORANGE, font_size=20, bold=True)
    d.mux(620, 265, 285, 360, "2:1\nMUX", fill=PALE_PURPLE, stroke=PURPLE, font_size=28, bold=True)
    d.rect(990, 390, 250, 105, "Y [WIDTH-1:0]", fill=PALE_GREEN, stroke=GREEN, font_size=21, bold=True)
    d.line([(370, 307), (620, 335)], stroke=BLUE, stroke_width=6, arrow=True, label="0")
    d.line([(370, 567), (620, 555)], stroke=TEAL, stroke_width=6, arrow=True, label="1")
    d.line([(455, 752), (755, 752), (755, 625)], stroke=ORANGE, stroke_width=4, arrow=True)
    d.line([(905, 445), (990, 445)], stroke=GREEN, stroke_width=6, arrow=True)
    d.callout(1190, 220, 500, 155, "Boolean equation", "Y = Sel ? B : A\n\nNo clock, reset, or storage is present.", PURPLE)
    # truth table
    d.rect(1190, 430, 500, 270, "", fill=WHITE, stroke=GRID, stroke_width=2, radius=10)
    d.rect(1190, 430, 500, 55, "Selection truth table", fill=NAVY, stroke=NAVY, font_color=WHITE, font_size=18, bold=True, radius=10)
    d.text(1220, 505, 130, 40, "Sel", font_size=17, bold=True)
    d.text(1370, 505, 280, 40, "Y", font_size=17, bold=True)
    d.line([(1210, 555), (1670, 555)], stroke=GRID, stroke_width=1.5, arrow=False)
    d.text(1220, 575, 130, 40, "0", font_size=18, bold=True)
    d.text(1370, 575, 280, 40, "A", font_size=18, font_color=BLUE, bold=True)
    d.line([(1210, 630), (1670, 630)], stroke=GRID, stroke_width=1.5, arrow=False)
    d.text(1220, 647, 130, 40, "1", font_size=18, bold=True)
    d.text(1370, 647, 280, 40, "B", font_size=18, font_color=TEAL, bold=True)
    d.callout(1190, 750, 500, 115, "Review point", "Parameterized width changes only the bus size; selection behavior is invariant.", ORANGE)
    return d


def diagram_05() -> Diagram:
    d = Diagram(
        "05_mux_timing",
        "Multiplexer Timing",
        "timing",
        "Immediate output response to data and select changes.",
        "Combinational propagation: Y follows the currently selected input",
    )
    d.base()
    # Grid and markers.
    for i in range(9):
        x = 240 + i * 175
        d.line([(x, 150), (x, 820)], stroke=GRID, stroke_width=1, arrow=False, dashed=(i % 2 == 1))
        d.text(x - 25, 132, 50, 24, f"t{i}", font_size=13, font_color=MID)
    d.waveform("A", 220, [(0.0, 0), (0.18, 1), (0.46, 0), (0.70, 1)], color=BLUE)
    d.waveform("B", 350, [(0.0, 1), (0.32, 0), (0.60, 1), (0.84, 0)], color=TEAL)
    d.waveform("Sel", 480, [(0.0, 0), (0.25, 1), (0.55, 0), (0.78, 1)], color=ORANGE)
    # Y follows A for sel=0, B for sel=1; illustrative transitions.
    d.waveform("Y", 650, [(0.0, 0), (0.18, 1), (0.25, 0), (0.32, 0), (0.55, 0), (0.70, 1), (0.78, 1), (0.84, 0)], color=GREEN, width=5)
    d.line([(590, 510), (590, 610)], stroke=ORANGE, stroke_width=2.2, arrow=True, dashed=True, label="Sel=1")
    d.line([(1010, 510), (1010, 610)], stroke=ORANGE, stroke_width=2.2, arrow=True, dashed=True, label="Sel=0")
    d.callout(270, 820, 1260, 88, "Interpretation", "Output changes are caused by input or select changes, not by a clock edge. In zero-delay RTL simulation, the update appears in the next delta cycle.", NAVY)
    return d


def diagram_06() -> Diagram:
    d = Diagram(
        "06_pc_update_path",
        "Program-Counter Update Path",
        "subproject",
        "Sequential PC state with PC+4 and branch alternatives.",
        "One state register, two address adders, and a next-PC selector",
    )
    d.base()
    d.register(700, 330, 220, 180, "Program Counter\nPC", fill=PALE_BLUE, stroke=BLUE, font_size=23, bold=True)
    d.mux(395, 330, 130, 180, "Next PC", fill=PALE_RED, stroke=RED, font_size=19, bold=True)
    d.rect(1070, 230, 250, 120, "PC + 4\nAdder", fill=PALE_BLUE, stroke=BLUE, font_size=21, bold=True)
    d.rect(1070, 540, 250, 120, "PC + ImmExt\nBranch adder", fill=PALE_RED, stroke=RED, font_size=20, bold=True)
    d.rect(1470, 220, 230, 100, "PCPlus4", fill=WHITE, stroke=BLUE, font_size=19, bold=True)
    d.rect(1470, 550, 230, 100, "PCTarget", fill=WHITE, stroke=RED, font_size=19, bold=True)
    d.rect(620, 690, 380, 105, "Synchronous active-low reset\nPC <= 0 on a rising edge when Reset_n=0", fill=PALE_ORANGE, stroke=ORANGE, font_size=17, bold=True)
    d.rect(145, 365, 175, 105, "PCNext", fill=WHITE, stroke=RED, font_size=19, bold=True)
    d.rect(145, 570, 175, 90, "PCSrc", fill=PALE_ORANGE, stroke=ORANGE, font_size=18, bold=True)
    d.line([(320, 417), (395, 417)], stroke=RED, stroke_width=5, arrow=True)
    d.line([(525, 420), (700, 420)], stroke=RED, stroke_width=5, arrow=True)
    d.line([(810, 330), (810, 185), (1040, 185), (1040, 290), (1070, 290)], stroke=BLUE, stroke_width=5, arrow=True, label="PC")
    d.line([(810, 510), (810, 600), (1070, 600)], stroke=RED, stroke_width=5, arrow=True, label="PC")
    d.line([(1320, 290), (1470, 270)], stroke=BLUE, stroke_width=5, arrow=True)
    d.line([(1320, 600), (1470, 600)], stroke=RED, stroke_width=5, arrow=True)
    d.line([(1470, 270), (1400, 270), (1400, 165), (450, 165), (450, 330)], stroke=BLUE, stroke_width=4, arrow=True, label="0")
    d.line([(1470, 600), (1390, 600), (1390, 835), (480, 835), (480, 510)], stroke=RED, stroke_width=4, arrow=True, label="1")
    d.line([(320, 615), (460, 615), (460, 510)], stroke=ORANGE, stroke_width=3, arrow=True, dashed=True)
    d.line([(1000, 743), (1050, 743), (1050, 420), (920, 420)], stroke=ORANGE, stroke_width=3, arrow=True, dashed=True, label="Reset_n")
    d.callout(115, 730, 420, 110, "State boundary", "Only the PC register stores state. Adders and selection logic are purely combinational.", BLUE)
    return d


def diagram_07() -> Diagram:
    d = Diagram(
        "07_pc_timing",
        "Synchronous Active-Low Reset Timing",
        "timing",
        "PC reset and update behavior at rising edges.",
        "PC changes only at clock edges; Reset_n is sampled synchronously",
    )
    d.base()
    for i in range(9):
        x = 240 + i * 175
        d.line([(x, 145), (x, 820)], stroke=GRID, stroke_width=1, arrow=False)
        d.text(x - 35, 125, 70, 22, f"edge {i}", font_size=12, font_color=MID)
    # Clock manually with repeated transitions.
    clock = [(0.0, 0), (0.0625, 1), (0.125, 0), (0.1875, 1), (0.25, 0), (0.3125, 1), (0.375, 0), (0.4375, 1), (0.5, 0), (0.5625, 1), (0.625, 0), (0.6875, 1), (0.75, 0), (0.8125, 1), (0.875, 0), (0.9375, 1)]
    d.waveform("CLK", 205, clock, color=NAVY)
    d.waveform("Reset_n", 360, [(0.0, 0), (0.26, 1), (0.86, 0), (0.94, 1)], color=ORANGE)
    d.waveform("PCNext", 520, [(0.0, "0x04"), (0.25, "0x08"), (0.375, "0x0C"), (0.5, "0x20"), (0.625, "0x24"), (0.75, "0x28"), (0.875, "0x00")], color=TEAL, bus=True)
    d.waveform("PC", 690, [(0.0, "0x00"), (0.3125, "0x08"), (0.4375, "0x0C"), (0.5625, "0x20"), (0.6875, "0x24"), (0.8125, "0x28"), (0.9375, "0x00")], color=BLUE, bus=True, width=5)
    d.callout(285, 820, 1230, 88, "Key observation", "Reset_n going low does not change PC immediately. PC becomes zero at the next rising edge because the reset is synchronous.", ORANGE)
    return d


def diagram_08() -> Diagram:
    d = Diagram(
        "08_alu_architecture",
        "32-bit ALU Architecture",
        "subproject",
        "Operation selection, result path, and status flags.",
        "Arithmetic, logic, signed comparison, result selection, and flag derivation",
    )
    d.base()
    d.rect(90, 240, 210, 95, "A [31:0]", fill=PALE_BLUE, stroke=BLUE, font_size=21, bold=True)
    d.rect(90, 520, 210, 95, "B [31:0]", fill=PALE_TEAL, stroke=TEAL, font_size=21, bold=True)
    d.rect(95, 730, 250, 85, "ALUControl [2:0]", fill=PALE_ORANGE, stroke=ORANGE, font_size=19, bold=True)
    d.rect(460, 180, 270, 145, "33-bit adder\nADD / SUB", fill=PALE_PURPLE, stroke=PURPLE, font_size=20, bold=True)
    d.rect(460, 370, 270, 130, "Bitwise logic\nAND / OR", fill=PALE_PURPLE, stroke=PURPLE, font_size=20, bold=True)
    d.rect(460, 545, 270, 130, "Signed comparator\nSLT", fill=PALE_PURPLE, stroke=PURPLE, font_size=20, bold=True)
    d.mux(870, 260, 180, 360, "Result\nselect", fill=PALE_PURPLE, stroke=PURPLE, font_size=20, bold=True)
    d.rect(1190, 360, 270, 135, "Result [31:0]", fill=PALE_GREEN, stroke=GREEN, font_size=24, bold=True)
    d.rect(1510, 190, 220, 100, "Carry", fill=WHITE, stroke=ORANGE, font_size=20, bold=True)
    d.rect(1510, 335, 220, 100, "Overflow", fill=WHITE, stroke=RED, font_size=20, bold=True)
    d.rect(1510, 480, 220, 100, "Zero", fill=WHITE, stroke=GREEN, font_size=20, bold=True)
    d.rect(1510, 625, 220, 100, "Negative", fill=WHITE, stroke=PURPLE, font_size=20, bold=True)

    for y in (230, 435, 610):
        d.line([(300, 287), (385, 287), (385, y), (460, y)], stroke=BLUE, stroke_width=4, arrow=True)
        d.line([(300, 567), (410, 567), (410, y + 45), (460, y + 45)], stroke=TEAL, stroke_width=4, arrow=True)
    d.line([(730, 250), (870, 330)], stroke=PURPLE, stroke_width=4, arrow=True, label="ADD/SUB")
    d.line([(730, 435), (870, 435)], stroke=PURPLE, stroke_width=4, arrow=True, label="logic")
    d.line([(730, 610), (870, 550)], stroke=PURPLE, stroke_width=4, arrow=True, label="SLT")
    d.line([(345, 772), (790, 772), (790, 640), (960, 640), (960, 620)], stroke=ORANGE, stroke_width=3, arrow=True, dashed=True)
    d.line([(1050, 440), (1190, 427)], stroke=GREEN, stroke_width=6, arrow=True)
    d.line([(730, 215), (1410, 215), (1410, 240), (1510, 240)], stroke=ORANGE, stroke_width=3, arrow=True)
    d.line([(730, 285), (1380, 285), (1380, 385), (1510, 385)], stroke=RED, stroke_width=3, arrow=True)
    d.line([(1460, 427), (1480, 427), (1480, 530), (1510, 530)], stroke=GREEN, stroke_width=3, arrow=True)
    d.line([(1460, 427), (1490, 427), (1490, 675), (1510, 675)], stroke=PURPLE, stroke_width=3, arrow=True)
    d.callout(1160, 760, 550, 105, "Flag semantics", "Carry is unsigned. Overflow is signed. Zero and Negative are derived from the selected Result value.", NAVY)
    return d


def diagram_09() -> Diagram:
    d = Diagram(
        "09_alu_control_map",
        "ALU Control Map",
        "reference",
        "Internal control encodings and intended operations.",
        "Decoder output values used by the RTL ALU",
    )
    d.base()
    # Table frame.
    x0, y0 = 110, 180
    col_w = [170, 250, 260, 330, 480]
    headers = ["ALUControl", "Operation", "Expression", "Used by", "Flags / notes"]
    x = x0
    for width, header in zip(col_w, headers):
        d.rect(x, y0, width, 62, header, fill=NAVY, stroke=WHITE, font_color=WHITE, font_size=16, bold=True, radius=0)
        x += width
    rows = [
        ("000", "ADD", "A + B", "ADD, ADDI, LW, SW", "Carry + signed overflow are meaningful"),
        ("001", "SUB", "A - B", "SUB, BEQ compare", "Zero qualifies BEQ; Carry is no-borrow"),
        ("010", "AND", "A & B", "AND, ANDI", "Arithmetic flags clear"),
        ("011", "OR", "A | B", "OR, ORI", "Arithmetic flags clear"),
        ("101", "SLT", "signed(A) < signed(B)", "SLT, SLTI", "Result is 0 or 1"),
        ("other", "DEFAULT", "0", "Unsupported internal code", "Deterministic benign output"),
    ]
    colors = [BLUE, PURPLE, TEAL, TEAL, ORANGE, MID]
    for r, (row, color) in enumerate(zip(rows, colors)):
        y = y0 + 62 + r * 96
        values = row
        x = x0
        for c, (width, value) in enumerate(zip(col_w, values)):
            fill = PALE if r % 2 == 0 else WHITE
            if c == 0:
                fill = color
                fc = WHITE
                bold = True
            else:
                fc = INK
                bold = c == 1
            d.rect(x, y, width, 96, value, fill=fill, stroke=GRID, stroke_width=1.2, font_size=15, font_color=fc, bold=bold, radius=0)
            x += width
    d.callout(110, 840, 1580, 70, "Decoder rule", "ALUOp=00 forces ADD, ALUOp=01 forces SUB, and ALUOp=10 decodes funct3 plus the R-type SUB qualifier.", ORANGE)
    return d


def diagram_10() -> Diagram:
    d = Diagram(
        "10_register_file_architecture",
        "RV32I Register File",
        "subproject",
        "Two asynchronous reads, one synchronous write, and x0 protection.",
        "32 registers x 32 bits with architectural zero-register enforcement",
    )
    d.base()
    d.rect(620, 190, 520, 590, "", fill=PALE_TEAL, stroke=TEAL, stroke_width=3, radius=18)
    d.text(650, 205, 460, 52, "32 x 32-bit register array", font_size=26, font_color=NAVY, bold=True)
    # Internal register rows.
    y = 300
    labels = ["x0 = 0 (hardwired)", "x1", "x2", "...", "x30", "x31"]
    for i, label in enumerate(labels):
        fill = PALE_GREEN if i == 0 else WHITE
        stroke = GREEN if i == 0 else GRID
        d.rect(720, y + i * 68, 320, 48, label, fill=fill, stroke=stroke, font_size=16, bold=(i == 0), radius=6)
    # Ports.
    d.rect(80, 230, 230, 85, "A1 [4:0]", fill=PALE_BLUE, stroke=BLUE, font_size=19, bold=True)
    d.rect(80, 400, 230, 85, "A2 [4:0]", fill=PALE_BLUE, stroke=BLUE, font_size=19, bold=True)
    d.rect(80, 650, 230, 85, "A3 [4:0]", fill=PALE_ORANGE, stroke=ORANGE, font_size=19, bold=True)
    d.rect(80, 765, 230, 85, "WD3 [31:0]", fill=PALE_ORANGE, stroke=ORANGE, font_size=19, bold=True)
    d.rect(355, 795, 165, 70, "WE3", fill=PALE_ORANGE, stroke=ORANGE, font_size=18, bold=True)
    d.rect(1440, 250, 250, 95, "RD1 [31:0]", fill=PALE_GREEN, stroke=GREEN, font_size=20, bold=True)
    d.rect(1440, 470, 250, 95, "RD2 [31:0]", fill=PALE_GREEN, stroke=GREEN, font_size=20, bold=True)
    d.rect(1250, 715, 300, 110, "Rising-edge write\nif WE3 && A3 != 0", fill=PALE_ORANGE, stroke=ORANGE, font_size=18, bold=True)
    d.line([(310, 272), (620, 272)], stroke=BLUE, stroke_width=4, arrow=True)
    d.line([(310, 442), (620, 442)], stroke=BLUE, stroke_width=4, arrow=True)
    d.line([(310, 692), (620, 692)], stroke=ORANGE, stroke_width=4, arrow=True)
    d.line([(310, 807), (620, 807), (620, 760)], stroke=ORANGE, stroke_width=4, arrow=True)
    d.line([(520, 830), (610, 830), (610, 735), (620, 735)], stroke=ORANGE, stroke_width=3, arrow=True, dashed=True)
    d.line([(1140, 298), (1440, 298)], stroke=GREEN, stroke_width=5, arrow=True)
    d.line([(1140, 518), (1440, 518)], stroke=GREEN, stroke_width=5, arrow=True)
    d.line([(1140, 735), (1250, 770)], stroke=ORANGE, stroke_width=3, arrow=True, dashed=True)
    d.callout(1190, 600, 500, 88, "Read timing", "RD1 and RD2 update combinationally when A1, A2, or the addressed register changes.", TEAL)
    return d


def diagram_11() -> Diagram:
    d = Diagram(
        "11_register_file_timing",
        "Register-File Timing",
        "timing",
        "Edge-triggered write followed by combinational readback.",
        "A legal write becomes visible immediately after the active edge",
    )
    d.base()
    for i in range(9):
        x = 240 + i * 175
        d.line([(x, 145), (x, 835)], stroke=GRID, stroke_width=1, arrow=False)
        d.text(x - 25, 125, 50, 22, f"t{i}", font_size=12, font_color=MID)
    clock = [(0.0, 0), (0.0625, 1), (0.125, 0), (0.1875, 1), (0.25, 0), (0.3125, 1), (0.375, 0), (0.4375, 1), (0.5, 0), (0.5625, 1), (0.625, 0), (0.6875, 1), (0.75, 0), (0.8125, 1), (0.875, 0), (0.9375, 1)]
    d.waveform("CLK", 195, clock, color=NAVY)
    d.waveform("WE3", 320, [(0.0, 0), (0.18, 1), (0.36, 0), (0.56, 1), (0.70, 0)], color=ORANGE)
    d.waveform("A3", 440, [(0.0, "x5"), (0.50, "x0"), (0.75, "x6")], color=PURPLE, bus=True)
    d.waveform("WD3", 555, [(0.0, "0x00000005"), (0.50, "0xFFFFFFFF"), (0.75, "0x00000004")], color=TEAL, bus=True)
    d.waveform("RD1", 700, [(0.0, "x5: 0"), (0.3125, "x5: 5"), (0.8125, "x6: 4")], color=GREEN, bus=True, width=5)
    d.line([(677, 250), (677, 655)], stroke=ORANGE, stroke_width=2.2, arrow=True, dashed=True, label="write x5")
    d.line([(1377, 250), (1377, 655)], stroke=ORANGE, stroke_width=2.2, arrow=True, dashed=True, label="write x6")
    d.callout(270, 820, 1260, 88, "x0 protection", "The attempted write to A3=x0 is suppressed even when WE3 is high; subsequent reads of x0 remain zero.", GREEN)
    return d


def diagram_12() -> Diagram:
    d = Diagram(
        "12_riscv_instruction_formats",
        "RISC-V Instruction Formats",
        "reference",
        "R, I, S, and B field placement for the supported subset.",
        "32-bit encodings used by the implemented processor",
    )
    d.base()
    d.text(65, 128, 1670, 28, "Bit positions", font_size=14, font_color=MID, bold=True, align="left")
    # top bit ruler
    x0, total_w = 180, 1480
    for bit in [31, 25, 20, 15, 12, 7, 0]:
        x = x0 + total_w * (31 - bit) / 32
        d.text(x - 30, 145, 60, 28, str(bit), font_size=13, font_color=MID)
        d.line([(x, 175), (x, 820)], stroke=GRID, stroke_width=1, arrow=False)

    def field_row(y: float, label: str, fields: Sequence[tuple[str, int, str]]) -> None:
        d.text(60, y + 18, 95, 50, label, font_size=22, font_color=NAVY, bold=True, align="right")
        cursor = x0
        for name, bits, color in fields:
            w = total_w * bits / 32
            d.rect(cursor, y, w, 85, name, fill=color, stroke=WHITE, stroke_width=2, font_size=16, bold=True, radius=0)
            cursor += w

    field_row(205, "R-type", [("funct7", 7, PALE_RED), ("rs2", 5, PALE_TEAL), ("rs1", 5, PALE_BLUE), ("funct3", 3, PALE_ORANGE), ("rd", 5, PALE_GREEN), ("opcode", 7, PALE_PURPLE)])
    field_row(355, "I-type", [("imm[11:0]", 12, PALE_RED), ("rs1", 5, PALE_BLUE), ("funct3", 3, PALE_ORANGE), ("rd", 5, PALE_GREEN), ("opcode", 7, PALE_PURPLE)])
    field_row(505, "S-type", [("imm[11:5]", 7, PALE_RED), ("rs2", 5, PALE_TEAL), ("rs1", 5, PALE_BLUE), ("funct3", 3, PALE_ORANGE), ("imm[4:0]", 5, PALE_RED), ("opcode", 7, PALE_PURPLE)])
    field_row(655, "B-type", [("imm[12|10:5]", 7, PALE_RED), ("rs2", 5, PALE_TEAL), ("rs1", 5, PALE_BLUE), ("funct3", 3, PALE_ORANGE), ("imm[4:1|11]", 5, PALE_RED), ("opcode", 7, PALE_PURPLE)])
    d.callout(180, 810, 1480, 85, "Supported mapping", "R: ADD/SUB/AND/OR/SLT | I: ADDI/ANDI/ORI/SLTI/LW | S: SW | B: BEQ. Branch bit 0 is implicit zero.", NAVY)
    return d


def diagram_13() -> Diagram:
    d = Diagram(
        "13_immediate_reconstruction",
        "Immediate Reconstruction and Sign Extension",
        "subproject",
        "I-, S-, and B-type bit gathering and sign extension.",
        "ImmSrc selects field gathering; instruction bit 31 supplies the sign",
    )
    d.base()
    d.rect(80, 200, 280, 110, "Instruction [31:0]", fill=PALE_BLUE, stroke=BLUE, font_size=22, bold=True)
    d.rect(80, 720, 280, 90, "ImmSrc [1:0]", fill=PALE_ORANGE, stroke=ORANGE, font_size=20, bold=True)
    d.rect(560, 165, 700, 650, "", fill=PALE, stroke=GRID, stroke_width=2, radius=16)
    d.text(590, 185, 640, 45, "Field reconstruction paths", font_size=24, font_color=NAVY, bold=True)
    # Three paths.
    path_specs = [
        ("00", "I-type", "Instr[31:20]", "{{20{Instr[31]}}, Instr[31:20]}", BLUE, 285),
        ("01", "S-type", "Instr[31:25] + Instr[11:7]", "{{20{Instr[31]}}, Instr[31:25], Instr[11:7]}", TEAL, 470),
        ("10", "B-type", "Instr[31], [7], [30:25], [11:8], 0", "{{19{Instr[31]}}, Instr[31], Instr[7], Instr[30:25], Instr[11:8], 1'b0}", RED, 655),
    ]
    for code, name, source, expr, color, y in path_specs:
        d.rect(600, y, 115, 70, code, fill=color, stroke=color, font_color=WHITE, font_size=20, bold=True)
        d.rect(740, y, 190, 70, name, fill=WHITE, stroke=color, font_size=18, font_color=color, bold=True)
        d.rect(955, y, 270, 70, source, fill=WHITE, stroke=color, font_size=14, bold=True)
        d.text(600, y + 80, 625, 58, expr, font_size=13, font_color=INK, align="left", valign="top")
    d.mux(1375, 280, 130, 360, "ImmSrc\nselect", fill=PALE_ORANGE, stroke=ORANGE, font_size=19, bold=True)
    d.rect(1570, 400, 170, 110, "ImmExt\n[31:0]", fill=PALE_GREEN, stroke=GREEN, font_size=22, bold=True)
    d.line([(360, 255), (520, 255), (520, 350), (560, 350)], stroke=BLUE, stroke_width=5, arrow=True)
    d.line([(360, 765), (1390, 765), (1390, 640)], stroke=ORANGE, stroke_width=3, arrow=True, dashed=True)
    d.line([(1260, 335), (1375, 355)], stroke=BLUE, stroke_width=4, arrow=True)
    d.line([(1260, 520), (1375, 465)], stroke=TEAL, stroke_width=4, arrow=True)
    d.line([(1260, 705), (1375, 575)], stroke=RED, stroke_width=4, arrow=True)
    d.line([(1505, 460), (1570, 455)], stroke=GREEN, stroke_width=6, arrow=True)
    d.callout(80, 390, 390, 170, "Branch alignment", "B-type immediates append a zero as bit 0. The result is already a byte displacement; no extra shift is performed in the datapath.", RED)
    return d


def diagram_14() -> Diagram:
    d = Diagram(
        "14_memory_architecture",
        "Harvard Memory Model and Address Mapping",
        "subproject",
        "Instruction and data memories with byte-to-word indexing.",
        "Separate instruction/data arrays simplify a single-cycle implementation",
    )
    d.base()
    d.section(70, 130, 760, "Instruction memory", BLUE)
    d.section(970, 130, 760, "Data memory", ORANGE)
    d.register(100, 255, 180, 120, "PC", fill=PALE_BLUE, stroke=BLUE, font_size=23, bold=True)
    d.rect(370, 230, 180, 170, "Address mapping\n\nword_index = PC[9:2]", fill=WHITE, stroke=BLUE, font_size=18, bold=True)
    d.memory(645, 200, 160, 230, "ROM\n64 x 32", fill=PALE_BLUE, stroke=BLUE, font_size=22, bold=True)
    d.rect(640, 530, 170, 100, "$readmemh\nprogram.hex", fill=PALE, stroke=MID, font_size=17, bold=True)
    d.rect(370, 535, 180, 90, "Instr [31:0]", fill=PALE_GREEN, stroke=GREEN, font_size=19, bold=True)
    d.line([(280, 315), (370, 315)], stroke=BLUE, stroke_width=5, arrow=True)
    d.line([(550, 315), (645, 315)], stroke=BLUE, stroke_width=5, arrow=True)
    d.line([(645, 555), (550, 555)], stroke=GREEN, stroke_width=5, arrow=True)
    d.line([(640, 580), (605, 580), (605, 400), (645, 400)], stroke=MID, stroke_width=2.5, arrow=True, dashed=True)

    d.rect(1000, 210, 200, 90, "ALUResult", fill=PALE_PURPLE, stroke=PURPLE, font_size=20, bold=True)
    d.rect(1000, 500, 200, 90, "WriteData", fill=PALE_TEAL, stroke=TEAL, font_size=20, bold=True)
    d.rect(1030, 680, 140, 75, "MemWrite", fill=PALE_ORANGE, stroke=ORANGE, font_size=18, bold=True)
    d.rect(1260, 240, 190, 180, "Address mapping\n\nword_index = A[9:2]\nA[1:0] assumed 00", fill=WHITE, stroke=ORANGE, font_size=17, bold=True)
    d.memory(1510, 210, 170, 270, "RAM\n64 x 32", fill=PALE_ORANGE, stroke=ORANGE, font_size=22, bold=True)
    d.rect(1450, 600, 230, 95, "ReadData [31:0]", fill=PALE_GREEN, stroke=GREEN, font_size=19, bold=True)
    d.line([(1200, 255), (1260, 300)], stroke=PURPLE, stroke_width=5, arrow=True)
    d.line([(1450, 330), (1510, 330)], stroke=ORANGE, stroke_width=5, arrow=True)
    d.line([(1200, 545), (1470, 545), (1470, 420), (1510, 420)], stroke=TEAL, stroke_width=5, arrow=True)
    d.line([(1170, 717), (1430, 717), (1430, 455), (1510, 455)], stroke=ORANGE, stroke_width=3, arrow=True, dashed=True)
    d.line([(1595, 480), (1595, 600)], stroke=GREEN, stroke_width=5, arrow=True)
    d.callout(100, 735, 690, 120, "Memory behavior", "Instruction read: combinational. Data read: combinational. Data write: rising-edge synchronous when MemWrite=1.", NAVY)
    d.callout(1000, 800, 680, 75, "Alignment boundary", "Misaligned byte addresses are outside this project scope; the implementation indexes words with address bits [9:2].", RED)
    return d


def diagram_15() -> Diagram:
    d = Diagram(
        "15_memory_timing",
        "Data-Memory Timing",
        "timing",
        "Synchronous store and asynchronous load behavior.",
        "WriteData is captured on a rising edge; ReadData follows the addressed word",
    )
    d.base()
    for i in range(9):
        x = 240 + i * 175
        d.line([(x, 145), (x, 840)], stroke=GRID, stroke_width=1, arrow=False)
        d.text(x - 25, 125, 50, 22, f"t{i}", font_size=12, font_color=MID)
    clock = [(0.0, 0), (0.0625, 1), (0.125, 0), (0.1875, 1), (0.25, 0), (0.3125, 1), (0.375, 0), (0.4375, 1), (0.5, 0), (0.5625, 1), (0.625, 0), (0.6875, 1), (0.75, 0), (0.8125, 1), (0.875, 0), (0.9375, 1)]
    d.waveform("CLK", 185, clock, color=NAVY)
    d.waveform("MemWrite", 305, [(0.0, 0), (0.18, 1), (0.36, 0), (0.62, 1), (0.76, 0)], color=ORANGE)
    d.waveform("Address", 430, [(0.0, "0x00000000"), (0.50, "0x00000004"), (0.78, "0x00000000")], color=PURPLE, bus=True)
    d.waveform("WriteData", 545, [(0.0, "0x00000005"), (0.50, "0x00000002"), (0.78, "don't care")], color=TEAL, bus=True)
    d.waveform("ReadData", 690, [(0.0, "0x00000000"), (0.3125, "0x00000005"), (0.6875, "0x00000002"), (0.78, "0x00000005")], color=GREEN, bus=True, width=5)
    d.line([(677, 245), (677, 645)], stroke=ORANGE, stroke_width=2.2, arrow=True, dashed=True, label="store [0]")
    d.line([(1202, 245), (1202, 645)], stroke=ORANGE, stroke_width=2.2, arrow=True, dashed=True, label="store [1]")
    d.callout(280, 820, 1240, 88, "Read contract", "After an address change, ReadData updates combinationally. A store becomes visible only after the active clock edge.", NAVY)
    return d


def diagram_16() -> Diagram:
    d = Diagram(
        "16_control_unit_hierarchy",
        "Control-Unit Hierarchy",
        "subproject",
        "Main decoder, ALU decoder, and branch qualification.",
        "Two-level decode separates instruction class from the exact ALU function",
    )
    d.base()
    d.rect(70, 180, 300, 120, "Opcode [6:0]", fill=PALE_BLUE, stroke=BLUE, font_size=22, bold=True)
    d.rect(70, 380, 300, 120, "funct3 [2:0]", fill=PALE_TEAL, stroke=TEAL, font_size=22, bold=True)
    d.rect(70, 580, 300, 120, "funct7 [6:0]", fill=PALE_TEAL, stroke=TEAL, font_size=22, bold=True)
    d.rect(70, 760, 300, 85, "Zero", fill=PALE_GREEN, stroke=GREEN, font_size=21, bold=True)
    d.rect(540, 185, 400, 300, "Main Decoder\n\nOpcode class\n\nRegWrite, ImmSrc, ALUSrc\nMemWrite, ResultSrc\nBranch, ALUOp", fill=PALE_ORANGE, stroke=ORANGE, font_size=20, bold=True, radius=16)
    d.rect(540, 570, 400, 230, "ALU Decoder\n\nALUOp + funct3 + funct7 + opcode\n\nALUControl [2:0]", fill=PALE_PURPLE, stroke=PURPLE, font_size=19, bold=True, radius=16)
    d.rect(1120, 250, 360, 170, "Datapath controls\n\nRegWrite / ImmSrc / ALUSrc\nMemWrite / ResultSrc", fill=PALE_BLUE, stroke=BLUE, font_size=19, bold=True, radius=14)
    d.diamond(1130, 545, 330, 190, "BEQ decision\n\nBranch & Zero\n& (funct3 == 000)", fill=PALE_RED, stroke=RED, font_size=19, bold=True)
    d.rect(1570, 585, 170, 100, "PCSrc", fill=PALE_GREEN, stroke=GREEN, font_size=23, bold=True)
    d.rect(1570, 310, 170, 100, "ALUControl", fill=PALE_PURPLE, stroke=PURPLE, font_size=18, bold=True)
    d.line([(370, 240), (540, 260)], stroke=BLUE, stroke_width=4, arrow=True)
    d.line([(370, 240), (500, 240), (500, 645), (540, 645)], stroke=BLUE, stroke_width=3, arrow=True)
    d.line([(370, 440), (490, 440), (490, 690), (540, 690)], stroke=TEAL, stroke_width=4, arrow=True)
    d.line([(370, 640), (540, 735)], stroke=TEAL, stroke_width=4, arrow=True)
    d.line([(940, 335), (1120, 335)], stroke=ORANGE, stroke_width=5, arrow=True)
    d.line([(940, 430), (1000, 430), (1000, 625), (1130, 625)], stroke=ORANGE, stroke_width=3, arrow=True, dashed=True, label="Branch")
    d.line([(940, 695), (1570, 360)], stroke=PURPLE, stroke_width=5, arrow=True)
    d.line([(370, 440), (1020, 440), (1020, 595), (1130, 595)], stroke=TEAL, stroke_width=3, arrow=True, dashed=True)
    d.line([(370, 802), (1030, 802), (1030, 680), (1130, 680)], stroke=GREEN, stroke_width=3, arrow=True, dashed=True)
    d.line([(1460, 640), (1570, 635)], stroke=GREEN, stroke_width=5, arrow=True)
    d.callout(1110, 785, 620, 95, "Safe default", "Unsupported opcodes deassert architectural write enables and branch selection.", ORANGE)
    return d


def diagram_17() -> Diagram:
    d = Diagram(
        "17_control_decode_flow",
        "Instruction Decode Flow",
        "workflow",
        "Opcode and function fields to datapath control signals.",
        "From a 32-bit instruction word to one deterministic control vector",
    )
    d.base()
    stages = [
        (100, "Instruction\n[31:0]", PALE_BLUE, BLUE),
        (390, "Extract fields\nopcode / funct3 / funct7", PALE_TEAL, TEAL),
        (700, "Class decode\nload / store / R / I / branch", PALE_ORANGE, ORANGE),
        (1020, "ALU decode\nADD / SUB / AND / OR / SLT", PALE_PURPLE, PURPLE),
        (1330, "Branch qualify\nBEQ + Zero", PALE_RED, RED),
        (1580, "Control vector", PALE_GREEN, GREEN),
    ]
    widths = [210, 240, 250, 250, 205, 170]
    for (x, label, fill, stroke), w in zip(stages, widths):
        d.rect(x, 330, w, 190, label, fill=fill, stroke=stroke, stroke_width=3, font_size=19, bold=True, radius=16)
    for i in range(len(stages) - 1):
        x = stages[i][0] + widths[i]
        nx = stages[i + 1][0]
        d.line([(x, 425), (nx, 425)], stroke=MID, stroke_width=4, arrow=True)
    d.rect(720, 650, 270, 105, "Main controls\nRegWrite / ImmSrc / ALUSrc\nMemWrite / ResultSrc / Branch", fill=WHITE, stroke=ORANGE, font_size=16, bold=True)
    d.rect(1050, 650, 250, 105, "ALUControl [2:0]", fill=WHITE, stroke=PURPLE, font_size=18, bold=True)
    d.rect(1375, 650, 170, 105, "PCSrc", fill=WHITE, stroke=RED, font_size=20, bold=True)
    d.line([(825, 520), (825, 650)], stroke=ORANGE, stroke_width=3, arrow=True)
    d.line([(1145, 520), (1145, 650)], stroke=PURPLE, stroke_width=3, arrow=True)
    d.line([(1432, 520), (1432, 650)], stroke=RED, stroke_width=3, arrow=True)
    d.callout(300, 795, 1200, 85, "Determinism", "The decoder uses explicit defaults before case analysis, preventing latch inference and accidental state updates for unsupported encodings.", NAVY)
    return d


def diagram_18() -> Diagram:
    d = Diagram(
        "18_arithmetic_integration",
        "Arithmetic Datapath Integration",
        "integration",
        "Fetch, decode, ALU execution, and register write-back.",
        "Active path for R-type and I-type arithmetic instructions",
    )
    d.base()
    d.register(110, 350, 150, 120, "PC", fill=PALE_BLUE, stroke=BLUE, font_size=22, bold=True)
    d.memory(340, 285, 220, 250, "Instruction\nMemory", fill=PALE_BLUE, stroke=BLUE, font_size=21, bold=True)
    d.register(660, 255, 300, 320, "Register File\n\nRD1 / RD2\nWD3", fill=PALE_TEAL, stroke=TEAL, font_size=21, bold=True)
    d.rect(670, 690, 270, 110, "Immediate Generator", fill=PALE_TEAL, stroke=TEAL, font_size=20, bold=True)
    d.mux(1050, 430, 105, 160, "SrcB", fill=PALE_PURPLE, stroke=PURPLE, font_size=18, bold=True)
    d.alu(1240, 300, 250, 300, "ALU", fill=PALE_PURPLE, stroke=PURPLE, font_size=27, bold=True)
    d.rect(1540, 380, 200, 120, "Result", fill=PALE_GREEN, stroke=GREEN, font_size=24, bold=True)
    d.rect(1110, 710, 350, 100, "Control\nRegWrite / ALUSrc / ALUControl", fill=PALE_ORANGE, stroke=ORANGE, font_size=17, bold=True)
    d.line([(260, 410), (340, 410)], stroke=BLUE, stroke_width=5, arrow=True)
    d.line([(560, 350), (660, 330)], stroke=BLUE, stroke_width=5, arrow=True, label="rs1")
    d.line([(560, 410), (660, 410)], stroke=BLUE, stroke_width=5, arrow=True, label="rs2")
    d.line([(560, 475), (620, 475), (620, 515), (660, 515)], stroke=BLUE, stroke_width=5, arrow=True, label="rd")
    d.line([(560, 520), (620, 520), (620, 745), (670, 745)], stroke=TEAL, stroke_width=4, arrow=True)
    d.line([(960, 330), (1210, 330), (1210, 390), (1240, 390)], stroke=TEAL, stroke_width=5, arrow=True, label="RD1")
    d.line([(960, 470), (1050, 470)], stroke=TEAL, stroke_width=5, arrow=True, label="RD2")
    d.line([(940, 745), (1020, 745), (1020, 550), (1050, 550)], stroke=TEAL, stroke_width=5, arrow=True, label="ImmExt")
    d.line([(1155, 510), (1240, 510)], stroke=PURPLE, stroke_width=5, arrow=True)
    d.line([(1490, 450), (1540, 440)], stroke=PURPLE, stroke_width=6, arrow=True)
    d.line([(1740, 440), (1760, 440), (1760, 185), (625, 185), (625, 540), (660, 540)], stroke=GREEN, stroke_width=5, arrow=True, label="write-back")
    d.line([(1285, 710), (1285, 600)], stroke=ORANGE, stroke_width=3, arrow=True, dashed=True)
    d.line([(1170, 710), (1100, 710), (1100, 590)], stroke=ORANGE, stroke_width=3, arrow=True, dashed=True)
    d.line([(1410, 710), (1510, 710), (1510, 440), (1540, 440)], stroke=ORANGE, stroke_width=3, arrow=True, dashed=True)
    d.callout(100, 740, 430, 110, "Active instructions", "ADD, SUB, AND, OR, SLT, ADDI, ANDI, ORI, and SLTI.", PURPLE)
    return d


def diagram_19() -> Diagram:
    d = Diagram(
        "19_load_store_paths",
        "Load and Store Data Paths",
        "integration",
        "Address generation, store data, load data, and write-back.",
        "The ALU computes base + immediate for both LW and SW",
    )
    d.base()
    # Two lanes.
    d.section(65, 130, 800, "LW - load word", GREEN)
    d.section(935, 130, 800, "SW - store word", ORANGE)
    # LW lane.
    d.rect(95, 235, 175, 85, "rs1 base", fill=PALE_TEAL, stroke=TEAL, font_size=18, bold=True)
    d.rect(95, 390, 175, 85, "I-immediate", fill=PALE_BLUE, stroke=BLUE, font_size=18, bold=True)
    d.alu(365, 265, 210, 225, "ADD", fill=PALE_PURPLE, stroke=PURPLE, font_size=24, bold=True)
    d.memory(655, 235, 170, 235, "Data\nMemory", fill=PALE_ORANGE, stroke=ORANGE, font_size=21, bold=True)
    d.rect(655, 570, 170, 85, "ReadData", fill=PALE_GREEN, stroke=GREEN, font_size=19, bold=True)
    d.rect(360, 700, 230, 85, "rd write-back", fill=PALE_GREEN, stroke=GREEN, font_size=20, bold=True)
    d.line([(270, 278), (365, 315)], stroke=TEAL, stroke_width=5, arrow=True)
    d.line([(270, 432), (365, 430)], stroke=BLUE, stroke_width=5, arrow=True)
    d.line([(575, 375), (655, 350)], stroke=PURPLE, stroke_width=5, arrow=True, label="address")
    d.line([(740, 470), (740, 570)], stroke=GREEN, stroke_width=5, arrow=True)
    d.line([(655, 612), (590, 612), (590, 742)], stroke=GREEN, stroke_width=5, arrow=True)
    d.callout(95, 805, 730, 75, "LW controls", "RegWrite=1 | ALUSrc=1 | ResultSrc=1 | MemWrite=0", GREEN)

    # SW lane.
    d.rect(965, 235, 175, 85, "rs1 base", fill=PALE_TEAL, stroke=TEAL, font_size=18, bold=True)
    d.rect(965, 390, 175, 85, "S-immediate", fill=PALE_BLUE, stroke=BLUE, font_size=18, bold=True)
    d.alu(1235, 265, 210, 225, "ADD", fill=PALE_PURPLE, stroke=PURPLE, font_size=24, bold=True)
    d.rect(965, 570, 175, 85, "rs2 WriteData", fill=PALE_TEAL, stroke=TEAL, font_size=18, bold=True)
    d.memory(1530, 235, 170, 260, "Data\nMemory", fill=PALE_ORANGE, stroke=ORANGE, font_size=21, bold=True)
    d.rect(1390, 650, 230, 85, "MemWrite", fill=PALE_ORANGE, stroke=ORANGE, font_size=19, bold=True)
    d.line([(1140, 278), (1235, 315)], stroke=TEAL, stroke_width=5, arrow=True)
    d.line([(1140, 432), (1235, 430)], stroke=BLUE, stroke_width=5, arrow=True)
    d.line([(1445, 375), (1530, 350)], stroke=PURPLE, stroke_width=5, arrow=True, label="address")
    d.line([(1140, 612), (1500, 612), (1500, 430), (1530, 430)], stroke=TEAL, stroke_width=5, arrow=True)
    d.line([(1505, 650), (1580, 650), (1580, 495)], stroke=ORANGE, stroke_width=3, arrow=True, dashed=True)
    d.callout(965, 805, 735, 75, "SW controls", "RegWrite=0 | ALUSrc=1 | ResultSrc=0 | MemWrite=1", ORANGE)
    return d


def diagram_20() -> Diagram:
    d = Diagram(
        "20_branch_path",
        "BEQ Branch Path",
        "integration",
        "Equality comparison, target generation, and next-PC selection.",
        "BEQ redirects control flow only when rs1 equals rs2",
    )
    d.base()
    d.register(90, 335, 170, 120, "PC", fill=PALE_BLUE, stroke=BLUE, font_size=23, bold=True)
    d.rect(390, 210, 220, 110, "PC + 4", fill=PALE_BLUE, stroke=BLUE, font_size=22, bold=True)
    d.rect(390, 600, 250, 110, "PC + ImmExt", fill=PALE_RED, stroke=RED, font_size=22, bold=True)
    d.rect(730, 230, 220, 90, "rs1", fill=PALE_TEAL, stroke=TEAL, font_size=21, bold=True)
    d.rect(730, 420, 220, 90, "rs2", fill=PALE_TEAL, stroke=TEAL, font_size=21, bold=True)
    d.alu(1060, 260, 250, 280, "SUB", fill=PALE_PURPLE, stroke=PURPLE, font_size=26, bold=True)
    d.rect(1085, 630, 200, 95, "Zero", fill=PALE_GREEN, stroke=GREEN, font_size=22, bold=True)
    d.diamond(1390, 525, 210, 160, "Branch & Zero\n& funct3=000", fill=PALE_ORANGE, stroke=ORANGE, font_size=18, bold=True)
    d.mux(1500, 245, 130, 210, "PCSrc", fill=PALE_RED, stroke=RED, font_size=18, bold=True)
    d.rect(1655, 310, 110, 80, "PCNext", fill=PALE_GREEN, stroke=GREEN, font_size=17, bold=True)
    d.rect(730, 655, 220, 90, "B-immediate", fill=PALE_RED, stroke=RED, font_size=20, bold=True)
    d.line([(260, 395), (330, 395), (330, 265), (390, 265)], stroke=BLUE, stroke_width=5, arrow=True)
    d.line([(260, 395), (330, 395), (330, 655), (390, 655)], stroke=RED, stroke_width=5, arrow=True)
    d.line([(610, 265), (1470, 265), (1470, 315), (1500, 315)], stroke=BLUE, stroke_width=5, arrow=True, label="PCPlus4")
    d.line([(640, 655), (700, 655), (700, 700), (730, 700)], stroke=RED, stroke_width=4, arrow=True)
    d.line([(950, 700), (1000, 700), (1000, 675), (390, 675)], stroke=RED, stroke_width=4, arrow=True, label="ImmExt")
    d.line([(640, 655), (1450, 655), (1450, 400), (1500, 400)], stroke=RED, stroke_width=5, arrow=True, label="PCTarget")
    d.line([(950, 275), (1060, 335)], stroke=TEAL, stroke_width=5, arrow=True)
    d.line([(950, 465), (1060, 465)], stroke=TEAL, stroke_width=5, arrow=True)
    d.line([(1185, 540), (1185, 630)], stroke=GREEN, stroke_width=4, arrow=True)
    d.line([(1285, 675), (1390, 610)], stroke=GREEN, stroke_width=4, arrow=True)
    d.line([(1600, 605), (1630, 605), (1630, 455), (1565, 455)], stroke=ORANGE, stroke_width=3, arrow=True, dashed=True)
    d.line([(1630, 350), (1655, 350)], stroke=GREEN, stroke_width=5, arrow=True)
    d.callout(85, 785, 760, 95, "Taken branch evidence", "When Zero=1, PCNext selects PCTarget. Otherwise execution continues at PCPlus4.", RED)
    d.callout(920, 785, 810, 95, "Immediate rule", "The B-type immediate is sign-extended with an implicit low zero, so the branch adder consumes a byte displacement directly.", NAVY)
    return d


def diagram_21() -> Diagram:
    d = Diagram(
        "21_final_datapath",
        "Complete Nexvantis Single-Cycle Datapath",
        "architecture",
        "Full processor with debug observation ports.",
        "Detailed processor-style schematic used as the release overview and report cover figure",
    )
    d.base()
    d.rect(30, 103, 1740, 720, "", fill="#FBFCFE", stroke=GRID,
           stroke_width=1.5, radius=18)
    d.section(48, 118, 292, "Fetch", BLUE)
    d.section(360, 118, 470, "Decode", TEAL)
    d.section(850, 118, 420, "Execute", PURPLE)
    d.section(1290, 118, 270, "Memory", ORANGE)
    d.section(1580, 118, 170, "Write-back", GREEN)

    # Control plane above the datapath.
    d.rect(610, 175, 575, 112,
           "CONTROL UNIT\nOpcode class | ALU function | BEQ decision",
           fill="#FFF7E8", stroke=ORANGE, stroke_width=2.8,
           font_size=18, bold=True, radius=15)

    # Main datapath blocks.
    d.mux(48, 395, 74, 132, "PC", fill=PALE_RED, stroke=RED,
          font_size=15, bold=True)
    d.register(150, 407, 110, 108, "PC", fill=PALE_BLUE, stroke=BLUE,
               font_size=22, bold=True)
    d.memory(300, 330, 200, 245, "Instruction\nMemory", fill=PALE_BLUE,
             stroke=BLUE, font_size=20, bold=True)
    d.register(575, 315, 245, 285,
               "Register File\n\nA1 / A2 / A3\nRD1 / RD2 / WD3",
               fill=PALE_TEAL, stroke=TEAL, font_size=18, bold=True)
    d.mux(930, 420, 82, 158, "B", fill=PALE_PURPLE, stroke=PURPLE,
          font_size=18, bold=True)
    d.alu(1060, 345, 190, 250, "ALU", fill=PALE_PURPLE, stroke=PURPLE,
          font_size=25, bold=True)
    d.memory(1325, 360, 190, 225, "Data\nMemory", fill=PALE_ORANGE,
             stroke=ORANGE, font_size=21, bold=True)
    d.mux(1600, 415, 82, 160, "WB", fill=PALE_GREEN, stroke=GREEN,
          font_size=18, bold=True)

    # Lower address-generation layer.
    d.rect(300, 685, 190, 90, "PC + 4", fill=PALE_BLUE, stroke=BLUE,
           font_size=20, bold=True, radius=12)
    d.rect(575, 675, 245, 105, "Immediate Generator", fill=PALE_TEAL,
           stroke=TEAL, font_size=19, bold=True, radius=12)
    d.rect(1050, 685, 210, 90, "Branch Target\nPC + ImmExt",
           fill=PALE_RED, stroke=RED, font_size=18, bold=True, radius=12)

    # Fetch/decode buses.
    d.line([(122, 461), (150, 461)], stroke=RED, stroke_width=5, arrow=True)
    d.line([(260, 461), (300, 461)], stroke=BLUE, stroke_width=5,
           arrow=True, label="PC")
    d.line([(500, 375), (545, 375), (545, 365), (575, 365)],
           stroke=BLUE, stroke_width=4.4, arrow=True, label="rs1")
    d.line([(500, 455), (575, 455)], stroke=BLUE, stroke_width=4.4,
           arrow=True, label="rs2")
    d.line([(500, 535), (545, 535), (545, 550), (575, 550)],
           stroke=BLUE, stroke_width=4.4, arrow=True, label="rd")
    d.line([(500, 555), (535, 555), (535, 728), (575, 728)],
           stroke=TEAL, stroke_width=4, arrow=True, label="Instr[31:7]")
    d.line([(500, 355), (530, 355), (530, 310), (610, 310), (610, 235)],
           stroke=ORANGE, stroke_width=2.5, arrow=True, dashed=True)
    d.text(470, 278, 135, 25, "opcode / funct", font_size=13,
           font_color=ORANGE, bold=True)

    # Execute/memory/write-back buses.
    d.line([(820, 365), (1030, 365), (1030, 410), (1060, 410)],
           stroke=TEAL, stroke_width=5, arrow=True, label="RD1")
    d.line([(820, 500), (930, 500)], stroke=TEAL, stroke_width=5,
           arrow=True, label="RD2")
    d.line([(820, 500), (855, 500), (855, 625), (1295, 625),
            (1295, 505), (1325, 505)],
           stroke=TEAL, stroke_width=4.2, arrow=True, label="WriteData")
    d.line([(820, 728), (885, 728), (885, 552), (930, 552)],
           stroke=TEAL, stroke_width=5, arrow=True, label="ImmExt")
    d.line([(1012, 500), (1060, 500)], stroke=PURPLE, stroke_width=5,
           arrow=True)
    d.line([(1250, 470), (1325, 470)], stroke=PURPLE, stroke_width=5,
           arrow=True, label="ALUResult")
    d.line([(1250, 470), (1285, 470), (1285, 438), (1600, 438)],
           stroke=PURPLE, stroke_width=4, arrow=True)
    d.line([(1515, 438), (1600, 535)], stroke=ORANGE, stroke_width=5,
           arrow=True, label="ReadData")
    d.line([(1682, 495), (1735, 495), (1735, 305), (545, 305),
            (545, 575), (575, 575)],
           stroke=GREEN, stroke_width=5, arrow=True)
    d.text(1135, 279, 85, 23, "Result", font_size=13,
           font_color=GREEN, bold=True)

    # Next-PC layer.
    d.line([(205, 515), (205, 730), (300, 730)],
           stroke=BLUE, stroke_width=4, arrow=True)
    d.line([(490, 730), (520, 730), (520, 842), (80, 842), (80, 527)],
           stroke=BLUE, stroke_width=4, arrow=True, label="PCPlus4")
    d.line([(205, 515), (205, 812), (1020, 812), (1020, 730), (1050, 730)],
           stroke=RED, stroke_width=4, arrow=True)
    d.line([(820, 728), (990, 728), (990, 754), (1050, 754)],
           stroke=RED, stroke_width=4, arrow=True)
    d.line([(1260, 730), (1290, 730), (1290, 865), (108, 865), (108, 527)],
           stroke=RED, stroke_width=4, arrow=True, label="PCTarget")

    # Neatly routed control fan-out.
    d.line([(675, 287), (675, 315)], stroke=ORANGE, stroke_width=2.6,
           arrow=True, dashed=True)
    d.line([(760, 287), (760, 640), (698, 640), (698, 675)],
           stroke=ORANGE, stroke_width=2.5, arrow=True, dashed=True)
    d.line([(865, 287), (865, 390), (971, 390), (971, 420)],
           stroke=ORANGE, stroke_width=2.5, arrow=True, dashed=True)
    d.line([(985, 287), (985, 320), (1155, 320), (1155, 345)],
           stroke=ORANGE, stroke_width=2.5, arrow=True, dashed=True)
    d.line([(1080, 287), (1235, 287), (1235, 325), (1420, 325), (1420, 360)],
           stroke=ORANGE, stroke_width=2.5, arrow=True, dashed=True)
    d.line([(1140, 287), (1570, 287), (1570, 610), (1641, 610), (1641, 575)],
           stroke=ORANGE, stroke_width=2.5, arrow=True, dashed=True)
    d.line([(610, 220), (570, 220), (570, 890), (63, 890), (63, 527)],
           stroke=RED, stroke_width=2.8, arrow=True, dashed=True)

    # Observation-only interface is deliberately outside the architectural path.
    d.rect(360, 835, 1080, 52,
           "DEBUG OBSERVATION ONLY: PC | Instr | ALUResult | MemWrite | WriteData | ReadData | Result | registers",
           fill=WHITE, stroke=MID, font_size=14, bold=True, radius=10)
    add_legend(d, [("32-bit datapath", BLUE), ("Control", ORANGE),
                   ("Branch", RED), ("Write-back", GREEN)], 480, 910)
    return d

def diagram_22() -> Diagram:
    d = Diagram(
        "22_final_regression",
        "Final Architectural Regression Evidence",
        "verification",
        "Architectural end-state, store count, branch evidence, and terminal loop.",
        "Independent evidence combined by the final self-checking testbench",
    )
    d.base()
    # KPIs.
    metrics = [
        ("40", "cycles", BLUE),
        ("2", "stores", ORANGE),
        ("27", "taken branches", RED),
        ("0x0000003C", "final PC", PURPLE),
    ]
    x = 75
    for value, label, color in metrics:
        d.rect(x, 155, 380, 125, "", fill=WHITE, stroke=color, stroke_width=3, radius=16)
        d.text(x + 20, 170, 340, 55, value, font_size=30, font_color=color, bold=True)
        d.text(x + 20, 225, 340, 35, label.upper(), font_size=14, font_color=MID, bold=True)
        x += 420
    # Registers and memory.
    d.rect(75, 335, 785, 455, "", fill=PALE, stroke=GRID, stroke_width=2, radius=14)
    d.rect(75, 335, 785, 52, "Final register state", fill=NAVY, stroke=NAVY, font_color=WHITE, font_size=20, bold=True, radius=14)
    regs = [("x5", "5"), ("x6", "4"), ("x7", "5"), ("x8", "4"), ("x9", "1"), ("x10", "1"), ("x11", "5"), ("x12", "2"), ("x13", "FFFFFFFF"), ("x14", "1"), ("x15", "FFFFFFFF")]
    for i, (reg, val) in enumerate(regs):
        col = i % 3
        row = i // 3
        xx = 110 + col * 240
        yy = 420 + row * 82
        d.rect(xx, yy, 210, 58, f"{reg} = {val}", fill=WHITE, stroke=TEAL if val not in {"FFFFFFFF"} else PURPLE, font_size=17, bold=True, radius=8)
    d.rect(925, 335, 800, 215, "", fill=PALE, stroke=GRID, stroke_width=2, radius=14)
    d.rect(925, 335, 800, 52, "Memory and control-flow evidence", fill=NAVY, stroke=NAVY, font_color=WHITE, font_size=20, bold=True, radius=14)
    d.rect(970, 420, 300, 75, "memory[0] = 5", fill=PALE_GREEN, stroke=GREEN, font_size=20, bold=True)
    d.rect(1370, 420, 300, 75, "memory[1] = 2", fill=PALE_GREEN, stroke=GREEN, font_size=20, bold=True)
    d.rect(925, 595, 800, 195, "", fill=WHITE, stroke=RED, stroke_width=2.5, radius=14)
    d.text(955, 615, 740, 42, "Branch and termination checks", font_size=21, font_color=RED, bold=True)
    d.text(970, 675, 720, 90, "- PC jumps from 0x20 to 0x28\n- skipped instruction address is never executed\n- terminal loop remains stable at 0x3C", font_size=18, font_color=INK, align="left", valign="top")
    d.rect(575, 835, 650, 70, "REGRESSION PASS", fill=PALE_GREEN, stroke=GREEN, stroke_width=3, font_size=28, font_color=GREEN, bold=True, radius=18)
    return d


def diagram_23() -> Diagram:
    d = Diagram(
        "23_script_toolchain",
        "Automation and Script Toolchain",
        "workflow",
        "Make, Python, shell, Questa, Icarus, assembler, model, diagrams, report, and CI relationships.",
        "One repository entry point coordinates simulation, documentation, and release checks",
    )
    d.base()
    d.rect(70, 360, 260, 150, "Makefile\n\npublic targets", fill=PALE_BLUE, stroke=BLUE, font_size=23, bold=True, radius=18)
    # Tool cards.
    tools = [
        (450, 155, "repository_check.py", "structure / links / notices", TEAL),
        (450, 320, "run_iverilog.py", "compile / run / verdict", PURPLE),
        (450, 485, "reference_model.py", "architectural oracle", GREEN),
        (450, 650, "mini_assembler.py", "ASM -> HEX", ORANGE),
        (880, 155, "run_all_linux.sh", "Questa batch regression", PURPLE),
        (880, 320, "run_all_windows.ps1", "Windows regression", PURPLE),
        (880, 485, "generate_diagrams.py", "draw.io sources + exports", BLUE),
        (880, 650, "build_report.sh", "XeLaTeX report", BLUE),
    ]
    for x, y, title, body, color in tools:
        d.rect(x, y, 330, 115, f"{title}\n{body}", fill=WHITE, stroke=color, font_size=17, bold=True, radius=12)
    # Outputs / CI.
    d.rect(1325, 150, 400, 125, "GitHub Actions\npreflight + Icarus regression", fill=PALE_GREEN, stroke=GREEN, font_size=20, bold=True, radius=16)
    d.rect(1325, 350, 400, 125, "Simulation evidence\nPASS/FAIL + VCD", fill=PALE_PURPLE, stroke=PURPLE, font_size=20, bold=True, radius=16)
    d.rect(1325, 550, 400, 125, "Release documentation\nREADME + PDF + ISA workbook", fill=PALE_BLUE, stroke=BLUE, font_size=20, bold=True, radius=16)
    d.rect(1325, 750, 400, 95, "SHA-256 inventory", fill=PALE_ORANGE, stroke=ORANGE, font_size=20, bold=True, radius=16)
    # Connections.
    for _, y, _, _, color in tools:
        d.line([(330, 435), (390, 435), (390, y + 58), (450 if y != 155 or True else 450, y + 58)], stroke=color, stroke_width=3, arrow=True)
    # Right-hand tool connections.
    for x, y, _, _, color in tools[4:]:
        d.line([(780, 435), (830, 435), (830, y + 58), (880, y + 58)], stroke=color, stroke_width=3, arrow=True)
    d.line([(780, 212), (1325, 212)], stroke=TEAL, stroke_width=3, arrow=True)
    d.line([(1210, 377), (1325, 412)], stroke=PURPLE, stroke_width=3, arrow=True)
    d.line([(780, 542), (1270, 542), (1270, 612), (1325, 612)], stroke=GREEN, stroke_width=3, arrow=True)
    d.line([(780, 707), (1250, 707), (1250, 625), (1325, 625)], stroke=ORANGE, stroke_width=3, arrow=True)
    d.line([(1210, 542), (1325, 600)], stroke=BLUE, stroke_width=3, arrow=True)
    d.line([(1210, 707), (1325, 640)], stroke=BLUE, stroke_width=3, arrow=True)
    d.line([(1525, 675), (1525, 750)], stroke=ORANGE, stroke_width=3, arrow=True)
    d.callout(70, 785, 1110, 95, "Reproducibility contract", "All public flows are command-line driven. Generated assets, program images, and expected architectural results are checked before release.", NAVY)
    return d


DIAGRAM_BUILDERS = [
    diagram_01,
    diagram_02,
    diagram_03,
    diagram_04,
    diagram_05,
    diagram_06,
    diagram_07,
    diagram_08,
    diagram_09,
    diagram_10,
    diagram_11,
    diagram_12,
    diagram_13,
    diagram_14,
    diagram_15,
    diagram_16,
    diagram_17,
    diagram_18,
    diagram_19,
    diagram_20,
    diagram_21,
    diagram_22,
    diagram_23,
]


def diagrams() -> list[Diagram]:
    return [builder() for builder in DIAGRAM_BUILDERS]


def write_drawio_sources(items: Sequence[Diagram]) -> None:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    # Remove incompatible structural-source files before writing native Draw.io assets.
    for old in SOURCE_DIR.glob("*.dot"):
        old.unlink()
    for item in items:
        (SOURCE_DIR / f"{item.stem}.drawio").write_text(drawio_document([item]), encoding="utf-8")
    COMBINED_DRAWIO.write_text(drawio_document(items), encoding="utf-8")


def _run(command: Sequence[str]) -> None:
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


def export_svg_png_pdf(items: Sequence[Diagram]) -> None:
    SVG_DIR.mkdir(parents=True, exist_ok=True)
    PNG_DIR.mkdir(parents=True, exist_ok=True)
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    inkscape = shutil.which("inkscape")
    if not inkscape:
        raise RuntimeError("Inkscape is required to convert SVG release assets to PNG and PDF")
    for item in items:
        svg_path = SVG_DIR / f"{item.stem}.svg"
        png_path = PNG_DIR / f"{item.stem}.png"
        pdf_path = PDF_DIR / f"{item.stem}.pdf"
        svg_path.write_text(render_svg(item), encoding="utf-8")
        _run([
            inkscape,
            str(svg_path),
            "--export-area-page",
            f"--export-filename={png_path}",
            "--export-width=2700",
        ])
        _run([
            inkscape,
            str(svg_path),
            "--export-area-page",
            f"--export-filename={pdf_path}",
        ])
        if Image is not None and PngImagePlugin is not None:
            with Image.open(png_path) as image:
                info = PngImagePlugin.PngInfo()
                info.add_text("Title", item.title)
                info.add_text("Description", item.description)
                info.add_text("Project", PROJECT)
                info.add_text("Copyright", COPYRIGHT)
                info.add_text("License", LICENSE_NAME)
                info.add_text("Source", f"13_diagrams/source/{item.stem}.drawio")
                image.save(png_path, pnginfo=info)
        if fitz is not None:
            doc = fitz.open(pdf_path)
            metadata = dict(doc.metadata or {})
            metadata.update(
                {
                    "title": item.title,
                    "author": "Jordan Nzokou and Doeg Tiozang",
                    "subject": item.description,
                    "keywords": "Nexvantis, RISC-V, RV32I, Verilog, draw.io",
                    "creator": "Nexvantis draw.io diagram system",
                    "producer": "Native draw.io source with Inkscape release export",
                }
            )
            doc.set_metadata(metadata)
            temp = pdf_path.with_suffix(".tmp.pdf")
            doc.save(temp, garbage=4, deflate=True)
            doc.close()
            temp.replace(pdf_path)


def write_manifest(items: Sequence[Diagram]) -> None:
    manifest = {
        "project": PROJECT,
        "version": "6.0.0",
        "copyright": COPYRIGHT,
        "license": LICENSE_NAME,
        "license_notice": NOTICE_FULL,
        "canonical_format": "drawio",
        "generator": "scripts/generate_diagrams.py",
        "formats": ["drawio", "svg", "png", "pdf"],
        "combined_source": "source/Nexvantis_Diagram_Library.drawio",
        "diagrams": [
            {
                "stem": item.stem,
                "title": item.title,
                "category": item.category,
                "description": item.description,
                "source": f"source/{item.stem}.drawio",
            }
            for item in items
        ],
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def validate(items: Sequence[Diagram]) -> list[str]:
    errors: list[str] = []
    if len(items) != 23:
        errors.append(f"Expected 23 diagram definitions, found {len(items)}")
    expected = {item.stem for item in items}
    for item in items:
        paths = [
            SOURCE_DIR / f"{item.stem}.drawio",
            SVG_DIR / f"{item.stem}.svg",
            PNG_DIR / f"{item.stem}.png",
            PDF_DIR / f"{item.stem}.pdf",
        ]
        for path in paths:
            if not path.is_file() or path.stat().st_size == 0:
                errors.append(f"Missing or empty diagram asset: {path.relative_to(ROOT)}")
        drawio_path = SOURCE_DIR / f"{item.stem}.drawio"
        if drawio_path.is_file():
            text = drawio_path.read_text(encoding="utf-8")
            if "<mxfile" not in text or "<mxGraphModel" not in text:
                errors.append(f"Invalid draw.io XML: {drawio_path.relative_to(ROOT)}")
            if COPYRIGHT not in text:
                errors.append(f"Missing notice in draw.io source: {drawio_path.relative_to(ROOT)}")
    if not COMBINED_DRAWIO.is_file():
        errors.append("Missing combined draw.io library")
    if any(SOURCE_DIR.glob("*.dot")):
        errors.append("Obsolete DOT sources remain in 13_diagrams/source")
    if MANIFEST_PATH.is_file():
        try:
            manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
            stems = {entry["stem"] for entry in manifest.get("diagrams", [])}
            if stems != expected:
                errors.append("Manifest stems do not match diagram definitions")
            if manifest.get("canonical_format") != "drawio":
                errors.append("Manifest canonical format is not drawio")
        except Exception as exc:
            errors.append(f"Cannot parse diagram manifest: {exc}")
    else:
        errors.append("Missing diagram manifest")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-only", action="store_true", help="validate existing assets without regenerating")
    parser.add_argument("--sources-only", action="store_true", help="write draw.io sources and manifest only")
    args = parser.parse_args()

    items = diagrams()
    if not args.validate_only:
        write_drawio_sources(items)
        write_manifest(items)
        if not args.sources_only:
            export_svg_png_pdf(items)
    errors = validate(items)
    if errors:
        print("Diagram validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        f"Validated {len(items)} draw.io diagram families "
        f"({len(items) + 1} native .drawio sources including the combined library)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
