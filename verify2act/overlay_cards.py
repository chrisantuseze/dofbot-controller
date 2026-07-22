#!/usr/bin/env python3
"""
verify2act/overlay_cards.py
============================
Generates the REJECT and ACCEPT critic verdict card PNG assets for post-production
video overlay. Based on the card templates in video_submission_guide.md.

Output files (900 x 220 px PNG):
    verify2act/assets/card_reject_attempt1.png
    verify2act/assets/card_accept_attempt2.png

Usage
-----
    # Default: Task 1 scores from the guide
    python3 verify2act/overlay_cards.py

    # Custom scores
    python3 verify2act/overlay_cards.py \\
        --reject_scores 0.12 0.31 \\
        --accept_scores 0.87 0.91

    # Custom output directory
    python3 verify2act/overlay_cards.py --output_dir verify2act/assets/custom/

    # Generate multiple named cards
    python3 verify2act/overlay_cards.py --card reject --label "Attempt 1"
    python3 verify2act/overlay_cards.py --card accept --label "Attempt 2"
"""

import argparse
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    raise SystemExit("ERROR: Pillow not installed. Run: pip install Pillow")

# ── Card dimensions ───────────────────────────────────────────────────────────
CARD_W  = 900
CARD_H  = 220
RADIUS  = 12     # corner radius (simulated with rounded rect)
BORDER  = 4      # border thickness

# ── Colour palette ────────────────────────────────────────────────────────────
C_BG_DARK   = (14,  17,  23)      # near-black body
C_BG_PANEL  = (22,  27,  36)      # slightly lighter header panel
C_RED_VIVID = (220, 60,  60)      # reject accent
C_RED_DIM   = (140, 35,  35)
C_GREEN_VIVID = (50, 200, 100)    # accept accent
C_GREEN_DIM   = (25, 120, 60)
C_DIVIDER   = (45,  52,  68)
C_TEXT_PRI  = (235, 238, 245)     # primary text
C_TEXT_SEC  = (140, 148, 165)     # secondary / dim text
C_FAIL_TAG  = (220, 60,  60)
C_PASS_TAG  = (50,  200, 100)

# ── Fonts ─────────────────────────────────────────────────────────────────────
# Falls back to the PIL default bitmap font if the system monospace is missing.

def _load_font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold
            else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf" if bold
            else "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/truetype/ubuntu/UbuntuMono-B.ttf" if bold
            else "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


# ── Drawing helpers ───────────────────────────────────────────────────────────

def _rounded_rect(draw: ImageDraw.ImageDraw,
                  xy: tuple, radius: int, fill: tuple, outline: tuple = None,
                  outline_width: int = 1) -> None:
    """Draw a rounded rectangle (PIL doesn't have this in older versions)."""
    x0, y0, x1, y1 = xy
    r = radius
    draw.rectangle([x0 + r, y0, x1 - r, y1], fill=fill)
    draw.rectangle([x0, y0 + r, x1, y1 - r], fill=fill)
    draw.ellipse([x0, y0, x0 + 2*r, y0 + 2*r], fill=fill)
    draw.ellipse([x1 - 2*r, y0, x1, y0 + 2*r], fill=fill)
    draw.ellipse([x0, y1 - 2*r, x0 + 2*r, y1], fill=fill)
    draw.ellipse([x1 - 2*r, y1 - 2*r, x1, y1], fill=fill)

    if outline:
        draw.arc([x0, y0, x0 + 2*r, y0 + 2*r], 180, 270, fill=outline, width=outline_width)
        draw.arc([x1 - 2*r, y0, x1, y0 + 2*r], 270, 360, fill=outline, width=outline_width)
        draw.arc([x0, y1 - 2*r, x0 + 2*r, y1], 90, 180, fill=outline, width=outline_width)
        draw.arc([x1 - 2*r, y1 - 2*r, x1, y1], 0, 90, fill=outline, width=outline_width)
        draw.line([x0 + r, y0, x1 - r, y0], fill=outline, width=outline_width)
        draw.line([x0 + r, y1, x1 - r, y1], fill=outline, width=outline_width)
        draw.line([x0, y0 + r, x0, y1 - r], fill=outline, width=outline_width)
        draw.line([x1, y0 + r, x1, y1 - r], fill=outline, width=outline_width)


def _tag_pill(draw: ImageDraw.ImageDraw, text: str, x: int, y: int,
              color: tuple, font) -> int:
    """Draw a small coloured pill label. Returns the right edge x coordinate."""
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 10, 4
    rx0, ry0 = x, y - th - pad_y
    rx1, ry1 = x + tw + pad_x * 2, y + pad_y
    _rounded_rect(draw, (rx0, ry0, rx1, ry1), radius=6,
                  fill=(*color[:3], 30),
                  outline=color, outline_width=1)
    draw.text((rx0 + pad_x, ry0 + pad_y), text, font=font, fill=color)
    return rx1


def make_card(kind: str,
              score_h1: float,
              score_h2: float,
              label: str = "",
              reflect_reason: str = "") -> Image.Image:
    """
    Render a REJECT or ACCEPT critic card as a PIL Image.

    Args:
        kind:           "reject" or "accept"
        score_h1:       Head 1 (Goal Proximity) score 0.0–1.0
        score_h2:       Head 2 (Temporal Consistency) score 0.0–1.0
        label:          Optional subtitle (e.g. "Attempt 1")
        reflect_reason: If rejecting, the reflect reason text.
    """
    kind = kind.lower()
    assert kind in ("reject", "accept"), f"kind must be 'reject' or 'accept', got {kind!r}"

    is_reject    = (kind == "reject")
    accent       = C_RED_VIVID  if is_reject else C_GREEN_VIVID
    accent_dim   = C_RED_DIM    if is_reject else C_GREEN_DIM
    verdict_text = "CRITIC: REJECTED" if is_reject else "CRITIC: ACCEPTED"
    icon         = "X" if is_reject else "OK"
    action_text  = (f"Triggering REFLECT & REPLAN"
                    + (f": \"{reflect_reason}\"" if reflect_reason else ""))  \
                   if is_reject else "Executing Action"

    img  = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # ── Background ────────────────────────────────────────────────────────────
    _rounded_rect(draw, (0, 0, CARD_W - 1, CARD_H - 1), radius=RADIUS,
                  fill=C_BG_DARK, outline=accent, outline_width=BORDER)

    # ── Header strip ──────────────────────────────────────────────────────────
    header_h = 56
    _rounded_rect(draw, (BORDER, BORDER, CARD_W - BORDER, header_h),
                  radius=RADIUS - 2, fill=accent_dim)

    # Icon circle
    cx, cy, cr = 36, header_h // 2, 18
    draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=accent)
    f_icon = _load_font(16, bold=True)
    bbox   = f_icon.getbbox(icon)
    iw, ih = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((cx - iw // 2, cy - ih // 2 - 1), icon, font=f_icon,
              fill=C_BG_DARK)

    # Verdict text
    f_verdict = _load_font(22, bold=True)
    draw.text((64, header_h // 2 - 14), verdict_text,
              font=f_verdict, fill=C_TEXT_PRI)

    # Optional label (right-aligned)
    if label:
        f_label = _load_font(14)
        lbbox   = f_label.getbbox(label)
        lw      = lbbox[2] - lbbox[0]
        draw.text((CARD_W - BORDER - lw - 16, header_h // 2 - 8), label,
                  font=f_label, fill=C_TEXT_SEC)

    # ── Divider ───────────────────────────────────────────────────────────────
    draw.line([(BORDER + 10, header_h + 4), (CARD_W - BORDER - 10, header_h + 4)],
              fill=C_DIVIDER, width=1)

    # ── Score rows ────────────────────────────────────────────────────────────
    f_label_sm = _load_font(13)
    f_score    = _load_font(15, bold=True)
    f_tag      = _load_font(11, bold=True)

    rows = [
        ("Head 1  ·  Goal Proximity",       score_h1, is_reject),
        ("Head 2  ·  Temporal Consistency", score_h2, is_reject),
    ]
    row_y_start = header_h + 18

    for i, (row_label, score, is_fail) in enumerate(rows):
        ry = row_y_start + i * 36

        # Row label
        draw.text((24, ry), row_label, font=f_label_sm, fill=C_TEXT_SEC)

        # Score value
        score_str = f"{score:.2f}"
        sbbox     = f_score.getbbox(score_str)
        sw        = sbbox[2] - sbbox[0]
        score_x   = 580
        draw.text((score_x, ry - 1), score_str, font=f_score, fill=C_TEXT_PRI)

        # FAIL / PASS pill
        tag_text  = "FAIL" if is_fail else "PASS"
        tag_color = C_FAIL_TAG if is_fail else C_PASS_TAG
        _tag_pill(draw, tag_text, score_x + sw + 16, ry + 14,
                  tag_color, f_tag)

    # ── Bottom divider ────────────────────────────────────────────────────────
    footer_y = CARD_H - 44
    draw.line([(BORDER + 10, footer_y), (CARD_W - BORDER - 10, footer_y)],
              fill=C_DIVIDER, width=1)

    # ── Action line ───────────────────────────────────────────────────────────
    f_action = _load_font(14, bold=True)
    arrow    = "> "
    draw.text((24, footer_y + 10), arrow + action_text,
              font=f_action, fill=accent)

    return img


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate REJECT/ACCEPT critic verdict card PNG assets.")
    parser.add_argument("--reject_scores", nargs=2, type=float,
                        default=[0.12, 0.31], metavar=("H1", "H2"),
                        help="Goal-proximity and temporal-consistency scores for the REJECT card "
                             "(default: 0.12 0.31)")
    parser.add_argument("--accept_scores", nargs=2, type=float,
                        default=[0.87, 0.91], metavar=("H1", "H2"),
                        help="Goal-proximity and temporal-consistency scores for the ACCEPT card "
                             "(default: 0.87 0.91)")
    parser.add_argument("--reflect_reason", default="Path blocked by blue and green cubes",
                        help="Reason text on the REJECT card action line.")
    parser.add_argument("--reject_label", default="Attempt 1",
                        help="Subtitle shown on the REJECT card (default: 'Attempt 1')")
    parser.add_argument("--accept_label", default="Attempt 2 — Reflected",
                        help="Subtitle shown on the ACCEPT card (default: 'Attempt 2 - Reflected')")
    parser.add_argument("--output_dir", default="verify2act/assets",
                        help="Directory for output PNG files (default: verify2act/assets/)")
    parser.add_argument("--card", choices=["reject", "accept", "both"], default="both",
                        help="Which card(s) to generate (default: both)")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    generated = []

    if args.card in ("reject", "both"):
        img_reject = make_card(
            kind           = "reject",
            score_h1       = args.reject_scores[0],
            score_h2       = args.reject_scores[1],
            label          = args.reject_label,
            reflect_reason = args.reflect_reason,
        )
        p = out_dir / "card_reject_attempt1.png"
        img_reject.save(p)
        generated.append(p)
        print(f"[overlay_cards] Saved: {p}")

    if args.card in ("accept", "both"):
        img_accept = make_card(
            kind     = "accept",
            score_h1 = args.accept_scores[0],
            score_h2 = args.accept_scores[1],
            label    = args.accept_label,
        )
        p = out_dir / "card_accept_attempt2.png"
        img_accept.save(p)
        generated.append(p)
        print(f"[overlay_cards] Saved: {p}")

    print(f"\nGenerated {len(generated)} card(s) in {out_dir}/")
    print("Import these PNGs into your video editor as overlay graphics.")


if __name__ == "__main__":
    main()
