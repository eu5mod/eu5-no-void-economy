#!/usr/bin/env python3
"""Generate PR157 review-popup SVG assets from URL and raw SVG sources."""

from __future__ import annotations

import os
import re
from pathlib import Path
import xml.etree.ElementTree as ET

import qrcode
import qrcode.image.svg

ROOT = Path(__file__).resolve().parent.parent
LOCAL_ENV_PATH = ROOT / ".cbp.local.env"
PR157 = ROOT / "docs" / "assets" / "pr157"
SOURCE_DIR = PR157 / "source"
GENERATED_DIR = PR157 / "generated"
QR_URL_PATH = PR157 / "review_popup_1524_qr_url.txt"
QR_SVG_PATH = PR157 / "review_popup_1524_qr.svg"
EVENT_TEMPLATE_PATH = SOURCE_DIR / "review_popup_1524_event_template.svg"
EVENT_SOURCE_PATH = PR157 / "review_popup_1524_event_source.svg"
DEFAULT_SELECTED_SOURCE = "review_popup_1524_event_choice_situation_wide_source.svg"


def load_local_env() -> None:
    if not LOCAL_ENV_PATH.exists():
        return

    for raw_line in LOCAL_ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key.startswith("MODEU5_REVIEW_POPUP_"):
            continue
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def env_int(name: str, default: int) -> int:
    raw_value = os.environ.get(name)
    if raw_value is None or raw_value.strip() == "":
        return default
    try:
        return int(raw_value.strip())
    except ValueError as exc:
        raise SystemExit(f"{name} must be an integer, got: {raw_value}") from exc


def env_str(name: str, default: str) -> str:
    raw_value = os.environ.get(name)
    if raw_value is None or raw_value.strip() == "":
        return default
    return raw_value.strip()


load_local_env()

MARKER = "<!-- MODEU5_QR_OVERLAY -->"
CARD_X = env_int("MODEU5_REVIEW_POPUP_CARD_X", 1060)
CARD_Y = env_int("MODEU5_REVIEW_POPUP_CARD_Y", 50)
CARD_W = env_int("MODEU5_REVIEW_POPUP_CARD_W", 430)
CARD_H = env_int("MODEU5_REVIEW_POPUP_CARD_H", 475)
QR_X = env_int("MODEU5_REVIEW_POPUP_QR_X", 37)
QR_Y = env_int("MODEU5_REVIEW_POPUP_QR_Y", 92)
QR_SIZE = env_int("MODEU5_REVIEW_POPUP_QR_SIZE", 355)
SELECTED_SOURCE = env_str("MODEU5_REVIEW_POPUP_SELECTED_SOURCE", DEFAULT_SELECTED_SOURCE)


def read_qr_url() -> str:
    env_url = env_str("MODEU5_REVIEW_POPUP_QR_URL", "")
    if env_url:
        return env_url
    if not QR_URL_PATH.exists():
        raise SystemExit(f"Missing QR URL file: {QR_URL_PATH}")
    return QR_URL_PATH.read_text(encoding="utf-8").strip()


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
  <g id="cbp_support_qr_overlay" transform="translate({CARD_X} {CARD_Y})">
    <rect x="8" y="10" width="{CARD_W}" height="{CARD_H}" rx="14" fill="#3f2b1d" opacity="0.32"/>
    <rect x="0" y="0" width="{CARD_W}" height="{CARD_H}" rx="14" fill="#ead9b8" stroke="#38271b" stroke-width="5"/>
    <rect x="12" y="12" width="{CARD_W - 24}" height="{CARD_H - 24}" rx="10" fill="none" stroke="#7a5433" stroke-width="2" opacity="0.75"/>
    <text x="{CARD_W / 2}" y="36" text-anchor="middle" font-size="28" fill="#38271b" font-family="serif" font-weight="700">Support the mod</text>
    <text x="{CARD_W / 2}" y="60" text-anchor="middle" font-size="14" fill="#5a4330" font-family="serif">Forum thread</text>
    <rect x="{QR_X - 8}" y="{QR_Y - 8}" width="{QR_SIZE + 16}" height="{QR_SIZE + 16}" fill="#ffffff" stroke="#38271b" stroke-width="3"/>
    <g transform="translate({qr_origin_x:.4f} {qr_origin_y:.4f}) scale({scale:.8f})">
      {qr_inner_svg}
    </g>
  </g>
""".rstrip()


def inject_overlay(svg_text: str, overlay: str, source_path: Path) -> str:
    if MARKER in svg_text:
        return svg_text.replace(MARKER, overlay)
    if "</svg>" not in svg_text:
        raise SystemExit(f"Source SVG has no closing </svg>: {source_path}")
    return svg_text.replace("</svg>", f"\n{overlay}\n</svg>", 1)


def generate_overlay_svg(source_path: Path, output_path: Path, overlay: str) -> None:
    svg_text = source_path.read_text(encoding="utf-8")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(inject_overlay(svg_text, overlay, source_path), encoding="utf-8")
    print(f"Generated {output_path.relative_to(ROOT)} from {source_path.relative_to(ROOT)}")


def source_svg_candidates() -> list[Path]:
    if not SOURCE_DIR.exists():
        return []
    return sorted(path for path in SOURCE_DIR.glob("*.svg") if path.is_file())


def cleanup_generated_variants() -> None:
    if not GENERATED_DIR.exists():
        return
    for pattern in ("*_qr.svg", "*_qr.dds"):
        for generated_path in GENERATED_DIR.glob(pattern):
            generated_path.unlink()
            print(f"Removed stale generated asset {generated_path.relative_to(ROOT)}")


def main() -> None:
    url = read_qr_url()
    if not url:
        raise SystemExit("QR URL is empty")

    generate_qr_svg(url, QR_SVG_PATH)
    qr_inner_svg, qr_width, qr_height = read_qr_inner_svg(QR_SVG_PATH)
    overlay = build_qr_overlay(qr_inner_svg, qr_width, qr_height)

    cleanup_generated_variants()
    candidates = source_svg_candidates()
    selected_generated_path: Path | None = None
    for source_path in candidates:
        output_path = GENERATED_DIR / f"{source_path.stem}_qr.svg"
        generate_overlay_svg(source_path, output_path, overlay)
        if SELECTED_SOURCE and source_path.name == SELECTED_SOURCE:
            selected_generated_path = output_path

    if SELECTED_SOURCE and selected_generated_path is None:
        available = ", ".join(path.name for path in candidates) or "none"
        raise SystemExit(
            f"Selected source not found in {SOURCE_DIR}: {SELECTED_SOURCE}. "
            f"Available source SVGs: {available}"
        )

    if selected_generated_path is not None:
        EVENT_SOURCE_PATH.write_text(selected_generated_path.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Generated {EVENT_SOURCE_PATH.relative_to(ROOT)} from selected source {SELECTED_SOURCE}")
        return

    if not EVENT_TEMPLATE_PATH.exists():
        raise SystemExit(f"Missing review popup template SVG: {EVENT_TEMPLATE_PATH}")

    generate_overlay_svg(EVENT_TEMPLATE_PATH, EVENT_SOURCE_PATH, overlay)


if __name__ == "__main__":
    main()
