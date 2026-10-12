"""Software check with artificial counters, not a mining experiment."""
import json
import tempfile
from pathlib import Path
from collect_reference import collect
from analyze_reference import summarize


def main():
    counter = iter(str(i * 13) for i in range(1001))
    ticks = iter(range(1001))
    with tempfile.TemporaryDirectory() as tmp:
        run = Path(tmp) / 'synthetic-software-check'
        report = collect(lambda: next(counter), run, sleep=lambda _: None, clock=lambda: next(ticks))
        saved = [int(x) for x in (run / 'reference.logs.txt').read_text().split(',')]
        assert saved == [i * 13 for i in range(10, 1001)]
        summary = summarize(run)
        assert report['acquired_samples'] == 1001 and report['retained_samples'] == 991
        assert summary['rate_samples'] == 990 and summary['mean_hps'] == 13
        assert summary['pool_correctness'] == 'not established'
        assert not summary['pool_log_available']
        # The upstream strict filter excludes an exactly constant series.
        # Preserve the raw rate; never invent filtered values.
        assert summary['reference_filtered_samples'] == 0
        assert summary['reference_filtered_median_hps'] is None
    print(json.dumps(dict(status='passed', synthetic=True, wasm_executed=False,
                         external_connection=False, acquired_samples=1001,
                         retained_samples=991, interval_samples=990,
                         missing_pool_log_not_treated_as_correct=True)))


if __name__ == '__main__':
    main()
