import xml.etree.ElementTree as ET

import pytest

from build_html import normalize_mathml_alignment

MATHML_NS = "http://www.w3.org/1998/Math/MathML"
MATHML = f"{{{MATHML_NS}}}"

BOUNDARY_ALIGNMENT = r"""<math xmlns="http://www.w3.org/1998/Math/MathML" display="block"><semantics><mtable><mtr><mtd><mi>p</mi></mtd><mtd><mo>=</mo><mn>0</mn></mtd><mtd></mtd><mtd><mtext>at </mtext><mi>z</mi><mo>=</mo><mn>0</mn></mtd></mtr><mtr><mtd><mi>w</mi></mtd><mtd><mo>=</mo><mn>0</mn></mtd><mtd></mtd><mtd><mtext>at </mtext><mi>z</mi><mo>=</mo><mo>−</mo><mi>D</mi></mtd></mtr></mtable><annotation encoding="application/x-tex">\begin{aligned}p &amp;=0 &amp;&amp; \text{at }z=0,\\ w &amp;=0 &amp;&amp; \text{at }z=-D\end{aligned}</annotation></semantics></math>"""

ORDINARY_MULTI_PAIR = r"""<math xmlns="http://www.w3.org/1998/Math/MathML" display="block"><semantics><mtable><mtr><mtd><mi>a</mi></mtd><mtd><mo>=</mo><mn>1</mn></mtd><mtd><mi>b</mi></mtd><mtd><mo>=</mo><mn>2</mn></mtd></mtr><mtr><mtd><mi>c</mi></mtd><mtd><mo>=</mo><mn>3</mn></mtd></mtr></mtable><annotation encoding="application/x-tex">\begin{aligned}a&amp;=1&amp;b&amp;=2\\c&amp;=3\end{aligned}</annotation></semantics></math>"""

CASES = r"""<math xmlns="http://www.w3.org/1998/Math/MathML" display="block"><semantics><mtable><mtr><mtd><mi>x</mi></mtd><mtd><mo>&lt;</mo><mn>0</mn></mtd><mtd><mo>−</mo><mn>1</mn></mtd></mtr><mtr><mtd><mi>x</mi></mtd><mtd><mo>≥</mo><mn>0</mn></mtd><mtd><mn>1</mn></mtd></mtr></mtable><annotation encoding="application/x-tex">\begin{cases}-1&amp;x&lt;0\\1&amp;x\geq0\end{cases}</annotation></semantics></math>"""

ARRAY = r"""<math xmlns="http://www.w3.org/1998/Math/MathML" display="block"><semantics><mtable><mtr><mtd><mi>a</mi></mtd><mtd></mtd><mtd><mi>b</mi></mtd></mtr><mtr><mtd><mi>c</mi></mtd><mtd><mo>=</mo></mtd><mtd><mi>d</mi></mtd></mtr></mtable><annotation encoding="application/x-tex">\begin{array}{ccl}a&amp;&amp;b\\c&amp;= &amp;d\end{array}</annotation></semantics></math>"""

NUMBERED_WAVEALIGN = r"""<math xmlns="http://www.w3.org/1998/Math/MathML" display="block"><semantics><mtable><mtr><mtd><mi>G</mi><mi>z</mi></mtd><mtd><mo>=</mo><mn>0</mn></mtd></mtr></mtable><annotation encoding="application/x-tex">\begin{aligned}G_z&amp;=0\end{aligned}</annotation></semantics></math>"""

INLINE_FUNCTION = r"""<math xmlns="http://www.w3.org/1998/Math/MathML" display="inline"><semantics><mrow><mi>sin</mi><mo>⁡</mo><mi>x</mi><mo>+</mo><mi>y</mi></mrow><annotation encoding="application/x-tex">\sin x+y</annotation></semantics></math>"""


def first_table(markup: str) -> ET.Element:
    root = ET.fromstring(markup)
    table = root.find(f".//{MATHML}mtable")
    assert table is not None
    return table


def test_boundary_alignment_keeps_semantics_and_removes_spacer_column() -> None:
    normalized = normalize_mathml_alignment(BOUNDARY_ALIGNMENT)
    root = ET.fromstring(normalized)
    table = first_table(normalized)
    rows = root.findall(f".//{MATHML}mtr")

    assert root.get("display") == "block"
    assert table.get("columnalign") == "right left"
    assert [len(row.findall(f"{MATHML}mtd")) for row in rows] == [2, 2]
    assert all(
        "".join(cell.itertext()).strip()
        for row in rows
        for cell in row.findall(f"{MATHML}mtd")
    )
    assert all(
        any(
            "at" in " ".join("".join(node.itertext()).split())
            for node in cell.iter(f"{MATHML}mtext")
        )
        for cell in (row.findall(f"{MATHML}mtd")[1] for row in rows)
    )
    assert all(
        node.get("width") == "1em" for node in root.findall(f".//{MATHML}mspace")
    )
    assert r"\begin{aligned}p &=0 && \text{at }z=0" in "".join(
        root.find(f".//{MATHML}annotation").itertext()
    )
    assert normalize_mathml_alignment(normalized) == normalized


def test_ordinary_aligned_uses_right_left_columns() -> None:
    normalized = normalize_mathml_alignment(NUMBERED_WAVEALIGN)
    table = first_table(normalized)

    assert table.get("columnalign") == "right left"
    assert ["".join(cell.itertext()) for cell in table[0]] == ["Gz", "=0"]
    assert r"\begin{aligned}G_z&amp;=0\end{aligned}" in normalized


def test_multi_pair_aligned_keeps_rows_and_uses_alternating_columns() -> None:
    normalized = normalize_mathml_alignment(ORDINARY_MULTI_PAIR)
    table = first_table(normalized)
    rows = table.findall(MATHML + "mtr")

    assert table.get("columnalign") == "right left right left"
    assert [len(row.findall(MATHML + "mtd")) for row in rows] == [4, 2]
    assert ["".join(cell.itertext()) for cell in rows[0]] == ["a", "=1", "b", "=2"]
    assert ["".join(cell.itertext()) for cell in rows[1]] == ["c", "=3"]
    assert r"\begin{aligned}a&amp;=1&amp;b&amp;=2\\c&amp;=3\end{aligned}" in normalized


@pytest.mark.parametrize("markup", [CASES, ARRAY, INLINE_FUNCTION])
def test_cases_array_and_inline_math_remain_untouched(markup: str) -> None:
    assert normalize_mathml_alignment(markup) == markup


def test_non_aligned_table_with_boundary_text_remains_untouched() -> None:
    markup = BOUNDARY_ALIGNMENT.replace(r"\begin{aligned}", r"\begin{array}").replace(
        r"\end{aligned}", r"\end{array}"
    )

    assert normalize_mathml_alignment(markup) == markup
