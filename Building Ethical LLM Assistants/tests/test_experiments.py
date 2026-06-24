from core.experiments import run_experiment


def test_experiment_k_sweep_reports_deltas():
    results = run_experiment("k", [3, 5], golden_split="dev")
    assert [r["value"] for r in results] == [3, 5]
    assert results[0]["delta_recall"] == 0.0  # baseline
    assert "recall_at_5" in results[1] and "mrr" in results[1]
