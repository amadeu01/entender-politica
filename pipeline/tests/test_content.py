import pandas as pd
import pytest

from compilador import content
from compilador.content import ContentError, Resolver
from tests.helpers import make_indicator
from tests.test_validate import obs


@pytest.mark.parametrize(
    "text",
    [
        "Entre 1995 e 2012, na 5ª visita e no 1º ano",
        "the 1980s and the 3rd term",
        "COVID-19 and the G20",
        'valor {{ v("wdi.si_pov_gini", "BRA", 2001) }}',
        "see [link](https://x.org/42)",
        "1. first item\n2. second item",
    ],
)
def test_allowed_text_has_no_bare_numbers(text):
    assert content.bare_numbers(text) == []


@pytest.mark.parametrize(
    ("text", "token"),
    [
        ("caiu 10%", "10"),
        ("de 0,58 para", "0,58"),
        ("caiu -5%", "5"),
        ("entre 10-20 pontos", "20"),
        ("em `42%` dos casos", "42"),
        ("cerca de 5thousand", "5thousand"),
    ],
)
def test_hand_typed_numbers_are_reported(text, token):
    assert f"line 1: '{token}'" in content.bare_numbers(text)


def test_unknown_placeholder_function_is_rejected():
    with pytest.raises(ContentError, match="unknown placeholder"):
        content.placeholders("{{ guess(1) }}")


@pytest.mark.parametrize(
    ("value", "decimals", "lang", "signed", "expected"),
    [
        (1430.72, 1, "pt", False, "1.430,7"),
        (1430.72, 1, "en", False, "1,430.7"),
        (-0.078, 3, "pt", True, "−0,078"),
        (2.1, 1, "en", True, "+2.1"),
        (-0.00001, 3, "en", True, "0.000"),
    ],
)
def test_format_number(value, decimals, lang, signed, expected):
    assert content.format_number(value, decimals, lang, signed) == expected


@pytest.fixture
def resolver():
    gini = make_indicator()
    data = obs({2001: 58.4, 2014: 52.1})
    return lambda lang: Resolver(data, {gini.id: gini}, ["10.1257/aer.20181506"], lang)


def test_render_links_each_number_to_its_source(resolver):
    text, cited = resolver("pt").render(
        'De {{ v("wdi.si_pov_gini", "BRA", 2001) }} '
        '({{ diff("wdi.si_pov_gini", "BRA", 2001, 2014) }}, '
        '{{ pct("wdi.si_pov_gini", "BRA", 2001, 2014) }})'
    )
    assert [c.text for c in cited] == ["58,4", "−6,3", "−10,8%"]
    assert cited[0].source_id == "wdi"
    assert '<a class="dado" href="#dado-1" id="ref-1">58,4</a>' in text


def test_missing_observation_fails(resolver):
    with pytest.raises(ContentError, match="no observation"):
        resolver("en").render('{{ v("wdi.si_pov_gini", "BRA", 1990) }}')


def test_cite_requires_doi_in_references(resolver):
    _, cited = resolver("en").render('{{ cite("45%", "10.1257/AER.20181506", "abstract") }}')
    assert cited[0].doi == "10.1257/AER.20181506"
    with pytest.raises(ContentError, match="not among"):
        resolver("en").render('{{ cite("45%", "10.9999/x", "abstract") }}')


def test_lit_requires_reason(resolver):
    with pytest.raises(ContentError, match="reason"):
        resolver("en").render('{{ lit("95%", " ") }}')


def test_data_keys_ignore_cite_and_lit_wording():
    pt = '{{ v("a.b", "BRA", 2000) }} {{ cite("menos de 1%", "10.1/x", "resumo") }}'
    en = '{{ v("a.b", "BRA", 2000) }} {{ cite("less than 1%", "10.1/x", "abstract") }}'
    assert content.data_keys(pt) == content.data_keys(en)
    assert content.data_keys(pt) != content.data_keys('{{ v("a.b", "BRA", 2001) }}')


def test_placeholders_against_empty_data_are_reported(resolver):
    empty = Resolver(pd.DataFrame(columns=obs({2000: 1.0}).columns), {}, [], "pt")
    with pytest.raises(ContentError, match="not in the catalog"):
        empty.render('{{ v("wdi.si_pov_gini", "BRA", 2001) }}')


def test_malformed_placeholder_is_reported():
    assert content.bare_numbers('{{ v ("a.b", "BRA", 2000) }}') == ["line 1: malformed placeholder"]


def test_placeholder_arguments_are_type_checked(resolver):
    with pytest.raises(ContentError, match="strings"):
        resolver("en").render('{{ cite(21, "10.1257/aer.20181506", "abstract") }}')
    with pytest.raises(ContentError, match="year"):
        resolver("en").render('{{ v("wdi.si_pov_gini", "BRA", "2001") }}')


def test_text_around_placeholders_is_html_escaped(resolver):
    text, _ = resolver("en").render('<script>x</script> {{ lit("<b>", "reason") }}')
    assert "<script>" not in text and "&lt;script&gt;" in text
    assert "&lt;b&gt;" in text
