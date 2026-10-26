import pandas as pd

from compilador import changelog
from compilador.schema import empty, tidy
from tests.test_validate import obs


def test_diff_detects_new_series_additions_and_revisions():
    old = tidy(obs({2000: 50.0, 2001: 49.0}))
    new = tidy(pd.concat([obs({2000: 50.0, 2001: 48.5, 2002: 48.0}), obs({2000: 45.0}, geo="MEX")]))
    changes = changelog.diff(old, new)
    assert changes.new_series == ["wdi.si_pov_gini MEX"]
    assert changes.added == 2
    assert changes.removed == 0
    assert changes.revised == ["wdi.si_pov_gini BRA 2001: 49.0 → 48.5"]


def test_identical_data_has_no_changes():
    df = tidy(obs({2000: 50.0}))
    assert not changelog.diff(df, df.copy())


def test_first_build_against_empty_reports_everything_as_new():
    changes = changelog.diff(empty(), tidy(obs({2000: 50.0})))
    assert changes.new_series == ["wdi.si_pov_gini BRA"]
    assert changes.added == 1


def test_render_is_bilingual_and_dated():
    text = changelog.render(changelog.Changes(added=3), "2026-10-25", {"wdi": "2026-10-08"})
    assert text.startswith("## 2026-10-25")
    assert "Observações adicionadas / Observations added: 3" in text
