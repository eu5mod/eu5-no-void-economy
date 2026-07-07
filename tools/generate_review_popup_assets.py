#!/usr/bin/env python3
"""Generate PR157 review-popup SVG assets from a URL source of truth."""

from __future__ import annotations

import re
from pathlib import Path
import xml.etree.ElementTree as ET

import qrcode
import qrcode.image.svg

ROOT = Path(__file__).resolve().parent.parent
PR157 = ROOT / "docs" / "assets" / "pr157"

QR_URL_PATH = PR157 / "review_popup_1524_qr_url.txt"
QR_SVG_PATH = PR157 / "review_popup_1524_qr.svg"
EVENT_TEMPLATE_PATH = PR157 / "review_popup_1524_event_template.svg"
EVENT_SOURCE_PATH = PR157 / "review_popup_1524_event_source.svg"

MARKER = "<!-- MODEU5_QR_OVERLAY -->"
CARD_X = 1170
CARD_Y = 612
CARD_W = 320
CARD_H = 238
QR_X = 86
QR_Y = 72
QR_SIZE = 148


def generate_qr_svg(url: str, output_path: Path) -> None:
    factory = qrcode.image.svg.SvgPathImage
    img = qrcode.make(url, image_factory=factory, box_size=1, border=4)
    with output_path.open("wb") as handle:
        img.save(handle)


def read_qr_inner_svg(qr_svg_path: Path) -> tuple[str, float, float]:
    svg = qr_svg_path.read_text(encoding="utf-8")
    root = ET.fromstring(svg)
    view_box = root.attrib.get("viewBox")
    if not view_box:
        raise SystemExit(f"QR SVG has no viewBox: {qr_svg_path}")

    parts = [float(part) for part in view_box.split()]
    if len(parts) != 4 or parts[2] <= 0 or parts[3] <= 0:
        raise SystemExit(f"Unsupported QR SVG viewBox: {view_box}")

    match = re.search(r"<svg\b[^>]*>(.*)</svg>", svg, flags=re.DOTALL)
    if not match:
        raise SystemExit(f"Could not extract QR SVG content: {qr_svg_path}")

    return match.group(1).strip(), parts[2], parts[3]


def build_qr_overlay(qr_inner_svg: str, qr_width: float, qr_height: float) -> str:
    scale = min(QR_SIZE / qr_width, QR_SIZE / qr_height)
    scaled_w = qr_width * scale
    scaled_h = qr_height * scale
    qr_origin_x = QR_X + (QR_SIZE - scaled_w) / 2
    qr_origin_y = QR_Y + (QR_SIZE - scaled_h) / 2

    return f"""
  <g id="modeu5_support_qr_overlay" transform="translate({CARD_X} {CARD_Y})">
    <rect x="8" y="10" width="{CARD_W}" height="{CARD_H}" rx="14" fill="#3f2b1d" opacity="0.32"/>
    <rect x="0" y="0" width="{CARD_W}" height="{CARD_H}" rx="14" fill="#ead9b8" stroke="#38271b" stroke-width="5"/>
    <rect x="12" y="12" width="{CARD_W - 24}" height="{CARD_H - 24}" rx="10" fill="none" stroke="#7a5433" stroke-width="2" opacity="0.75"/>
    <text x="{CARD_W / 2}" y="36" text-anchor="middle" font-size="28" fill="#38271b" font-family="serif" font-weight="700">Support the mod</text>
    <text x="{CARD_W / 2}" y="60" text-anchor="middle" font-size="14" fill="#5a4330" font-family="serif">Scan to open the forum thread</text>
    <rect x="{QR_X - 8}" y="{QR_Y - 8}" width="{QR_SIZE + 16}" height="{QR_SIZE + 16}" fill="#ffffff" stroke="#38271b" stroke-width="3"/>
    <g transform="translate({qr_origin_x:.4f} {qr_origin_y:.4f}) scale({scale:.8f})">
      {qr_inner_svg}
    </g>
  </g>
""".rstrip()


def main() -> None:
    if not QR_URL_PATH.exists():
        raise SystemExit(f"Missing QR URL file: {QR_URL_PATH}")
    if not EVENT_TEMPLATE_PATH.exists():
        raise SystemExit(f"Missing review popup template SVG: {EVENT_TEMPLATE_PATH}")

    url = QR_URL_PATH.read_text(encoding="utf-8").strip()
    if not url:
        raise SystemExit(f"QR URL file is empty: {QR_URL_PATH}")

    generate_qr_svg(url, QR_SVG_PATH)
    qr_inner_svg, qr_width, qr_height = read_qr_inner_svg(QR_SVG_PATH)
    overlay = build_qr_overlay(qr_inner_svg, qr_width, qr_height)

    template_svg = EVENT_TEMPLATE_PATH.read_text(encoding="utf-8")
    if MARKER not in template_svg:
        raise SystemExit(f"Template marker not found in {EVENT_TEMPLATE_PATH}: {MARKER}")

    EVENT_SOURCE_PATH.write_text(template_svg.replace(MARKER, overlay), encoding="utf-8")
    print(f"Generated {QR_SVG_PATH.relative_to(ROOT)}")
    print(f"Generated {EVENT_SOURCE_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
