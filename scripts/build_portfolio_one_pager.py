"""Build the one-page ForgeBench application brief as a polished PDF."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output/pdf/forgebench-one-page-portfolio.pdf"
FONT = Path("C:/Windows/Fonts/malgun.ttf")
FONT_BOLD = Path("C:/Windows/Fonts/malgunbd.ttf")

NAVY = colors.HexColor("#111827")
SLATE = colors.HexColor("#334155")
MUTED = colors.HexColor("#64748B")
LIGHT = colors.HexColor("#F1F5F9")
LINE = colors.HexColor("#CBD5E1")
ORANGE = colors.HexColor("#F97316")
RED = colors.HexColor("#B91C1C")
GREEN = colors.HexColor("#047857")
WHITE = colors.white


def main() -> int:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    pdfmetrics.registerFont(TTFont("Malgun", str(FONT)))
    pdfmetrics.registerFont(TTFont("Malgun-Bold", str(FONT_BOLD)))
    canvas = Canvas(str(OUTPUT), pagesize=A4)
    canvas.setTitle("ForgeBench - AI Agent Harness and Evaluation Laboratory")
    canvas.setAuthor("ForgeBench")
    canvas.setSubject("Final V2 screening feasibility result and AI Agent Engineer evidence")
    width, height = A4
    _background(canvas, width, height)
    _header(canvas, width, height)
    _metric_cards(canvas, width, height)
    _pipeline(canvas, width, height)
    _result_table(canvas, width, height)
    _insight_and_fit(canvas, width, height)
    _footer(canvas, width)
    canvas.showPage()
    canvas.save()
    print(OUTPUT)
    return 0


def _background(c: Canvas, width: float, height: float) -> None:
    c.setFillColor(colors.white)
    c.rect(0, 0, width, height, fill=1, stroke=0)


def _header(c: Canvas, width: float, height: float) -> None:
    c.setFillColor(NAVY)
    c.rect(0, height - 58 * mm, width, 58 * mm, fill=1, stroke=0)
    c.setFillColor(ORANGE)
    c.rect(16 * mm, height - 18 * mm, 4 * mm, 4 * mm, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Malgun-Bold", 24)
    c.drawString(24 * mm, height - 19 * mm, "ForgeBench")
    c.setFont("Malgun", 10.5)
    c.setFillColor(colors.HexColor("#CBD5E1"))
    c.drawString(24 * mm, height - 27 * mm, "AI Agent Harness & Evaluation Laboratory")
    c.setFont("Malgun-Bold", 12.5)
    c.setFillColor(WHITE)
    c.drawString(16 * mm, height - 40 * mm, "에이전트의 성공뿐 아니라 실패한 주장까지 재현 가능하게 만든다")
    c.setFont("Malgun", 8.8)
    c.setFillColor(colors.HexColor("#CBD5E1"))
    c.drawString(
        16 * mm,
        height - 48 * mm,
        "Codex 기반 planning · tool loop · recovery · risk routing · replay · hidden evaluation firewall",
    )


def _metric_cards(c: Canvas, width: float, height: float) -> None:
    y = height - 79 * mm
    margin = 16 * mm
    gap = 4 * mm
    card_w = (width - 2 * margin - 2 * gap) / 3
    cards = [
        ("90", "frozen V2 Codex slots"),
        ("84", "externally graded V2 bases"),
        ("207", "automated regression tests"),
    ]
    for index, (value, label) in enumerate(cards):
        x = margin + index * (card_w + gap)
        c.setFillColor(LIGHT)
        c.roundRect(x, y, card_w, 17 * mm, 2.5 * mm, fill=1, stroke=0)
        c.setFillColor(NAVY)
        c.setFont("Malgun-Bold", 16)
        c.drawString(x + 5 * mm, y + 9.5 * mm, value)
        c.setFillColor(MUTED)
        c.setFont("Malgun", 7.6)
        c.drawString(x + 5 * mm, y + 4.5 * mm, label)


def _pipeline(c: Canvas, width: float, height: float) -> None:
    x = 16 * mm
    y = height - 112 * mm
    c.setFillColor(NAVY)
    c.setFont("Malgun-Bold", 10.5)
    c.drawString(x, y + 20 * mm, "SYSTEM")
    labels = ["Dev Tasks", "Public Gate", "Frozen Corpus", "External Grade", "Protocol Gate"]
    box_w = 31.5 * mm
    gap = 5.3 * mm
    for i, label in enumerate(labels):
        bx = x + i * (box_w + gap)
        c.setFillColor(WHITE)
        c.setStrokeColor(LINE)
        c.roundRect(bx, y, box_w, 11 * mm, 2 * mm, fill=1, stroke=1)
        c.setFillColor(SLATE)
        c.setFont("Malgun-Bold", 7.3)
        c.drawCentredString(bx + box_w / 2, y + 4.2 * mm, label)
        if i < len(labels) - 1:
            ax = bx + box_w
            c.setStrokeColor(ORANGE)
            c.setLineWidth(1.2)
            c.line(ax + 1 * mm, y + 5.5 * mm, ax + gap - 1 * mm, y + 5.5 * mm)
            c.line(ax + gap - 2.5 * mm, y + 7 * mm, ax + gap - 1 * mm, y + 5.5 * mm)
            c.line(ax + gap - 2.5 * mm, y + 4 * mm, ax + gap - 1 * mm, y + 5.5 * mm)
    c.setFillColor(MUTED)
    c.setFont("Malgun", 7.4)
    c.drawString(
        x,
        y - 5 * mm,
        "frozen model/config · SHA-256 catalog/corpus/oracle · private grader and labels outside Git",
    )


def _result_table(c: Canvas, width: float, height: float) -> None:
    x = 16 * mm
    y = height - 188 * mm
    c.setFillColor(NAVY)
    c.setFont("Malgun-Bold", 10.5)
    c.drawString(x, y + 55 * mm, "FINAL V2 SCREENING  /  PREREGISTERED GATE NOT MET")
    data = [
        ["Measure", "Wave 4", "Combined", "Required", "Decision"],
        ["Frozen slots", "30", "90", "-", "complete"],
        ["Eligible bases", "28", "84", "-", "sealed"],
        ["False completions", "0", "10", "-", "preserved"],
        ["False-completion clusters", "0", "4", "6", "insufficient"],
        ["Failure mechanisms", "0", "3", "4", "insufficient"],
        ["Passing-control clusters", "10", "27", "6", "passed"],
    ]
    table = Table(data, colWidths=[52 * mm, 24 * mm, 26 * mm, 25 * mm, 31 * mm], rowHeights=6.2 * mm)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Malgun"),
                ("FONTNAME", (0, 0), (-1, 0), "Malgun-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.4),
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("TEXTCOLOR", (0, 4), (-1, 5), RED),
                ("BACKGROUND", (0, 4), (-1, 5), colors.HexColor("#FEF2F2")),
                ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    table.wrapOn(c, 0, 0)
    table.drawOn(c, x, y + 7 * mm)
    c.setFillColor(RED)
    c.setFont("Malgun-Bold", 8.5)
    c.drawString(x, y, "Stage B blocked · Wave 5 prohibited · thresholds unchanged")
    c.setFillColor(MUTED)
    c.setFont("Malgun", 7.2)
    c.drawRightString(width - 16 * mm, y, "Three identical external evaluations · 0 infrastructure failures")


def _insight_and_fit(c: Canvas, width: float, height: float) -> None:
    top = height - 207 * mm
    gap = 7 * mm
    x1 = 16 * mm
    box_w = (width - 32 * mm - gap) / 2
    x2 = x1 + box_w + gap
    box_h = 55 * mm
    for x in (x1, x2):
        c.setFillColor(LIGHT)
        c.roundRect(x, top - box_h, box_w, box_h, 3 * mm, fill=1, stroke=0)

    c.setFillColor(NAVY)
    c.setFont("Malgun-Bold", 10)
    c.drawString(x1 + 5 * mm, top - 8 * mm, "WHAT THE FAILURE TAUGHT")
    left = [
        "• V1: 추가 compute로 ineffective repair를 해결 못함",
        "• V2: target failure 다양성이 먼저 필요함",
        "• raw failure 수는 cluster/mechanism을 대체 못함",
        "• terminal rule이 outcome-driven 확장을 차단함",
    ]
    c.setFillColor(SLATE)
    c.setFont("Malgun", 7.8)
    for i, line in enumerate(left):
        c.drawString(x1 + 5 * mm, top - (17 + i * 8) * mm, line)

    c.setFillColor(NAVY)
    c.setFont("Malgun-Bold", 10)
    c.drawString(x2 + 5 * mm, top - 8 * mm, "AI AGENT ENGINEER EVIDENCE")
    right = [
        "• Planning / Loop: plan·completion·repair contract",
        "• Tool / Safety: isolated workspace·protected evidence",
        "• Evaluation: 90 slots·3회 외부 평가·hash seal",
        "• Benchmark: 30 lineages·public/private firewall",
    ]
    c.setFillColor(SLATE)
    c.setFont("Malgun", 7.8)
    for i, line in enumerate(right):
        c.drawString(x2 + 5 * mm, top - (17 + i * 8) * mm, line)

    note_style = ParagraphStyle(
        "note",
        fontName="Malgun-Bold",
        fontSize=8.2,
        leading=11,
        textColor=GREEN,
        alignment=TA_LEFT,
    )
    note = Paragraph(
        "핵심 주장: 성공 점수가 아니라, 지원되지 않는 연구를 데이터 누수 없이 중단할 수 있는 평가 시스템을 만들었다.",
        note_style,
    )
    note.wrapOn(c, width - 32 * mm, 15 * mm)
    note.drawOn(c, 16 * mm, 15 * mm)


def _footer(c: Canvas, width: float) -> None:
    c.setStrokeColor(LINE)
    c.line(16 * mm, 11 * mm, width - 16 * mm, 11 * mm)
    c.setFont("Malgun", 7)
    c.setFillColor(MUTED)
    c.drawString(16 * mm, 6.7 * mm, "github.com/zzzrichard0101/forgebench")
    c.drawRightString(width - 16 * mm, 6.7 * mm, "Codex · Python · deterministic graders · reproducible evaluation")


if __name__ == "__main__":
    raise SystemExit(main())
