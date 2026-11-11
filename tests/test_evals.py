import importlib.util

from conftest import ROOT

spec = importlib.util.spec_from_file_location("run_evals", ROOT / "evals" / "run_evals.py")
run_evals = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_evals)


def test_offline_mode_passes_every_eval(capsys):
    assert run_evals.main([]) == 0
    assert "checks passed (100%)" in capsys.readouterr().out
