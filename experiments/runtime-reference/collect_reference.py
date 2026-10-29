"""RQ3 collector adapted from upstream puppetercollect.py; no mining setup."""
import argparse
import csv
import json
import re
import time
from pathlib import Path
from urllib.parse import urlparse


def collect(read_counter, destination, sleep=time.sleep, clock=time.monotonic):
    """Preserve TO_COLLECT=1000, <0 termination and SAMPLES[10:]."""
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    samples = []
    remaining = 1000
    # The runner may already have saved process logs here. Never replace samples.
    for filename in ('reference.logs.txt', 'collection.json', 'collection-failure.json'):
        if (destination / filename).exists():
            raise FileExistsError('Existing collection artifact: ' + filename)
    with (destination / 'hash-samples.csv').open('x', newline='', encoding='utf-8') as h:
        writer = csv.writer(h)
        writer.writerow(['sample_index', 'monotonic_seconds', 'cumulative_hashes'])
        while True:
            sleep(1)
            raw = read_counter()
            # Displayed grouping separators do not change the hash count.
            normalized = re.sub(r'[,\s]', '', raw)
            if not normalized.isdigit():
                raise ValueError('Hash counter is not a nonnegative integer: ' + repr(raw))
            count = int(normalized)
            if samples and count < samples[-1]:
                raise ValueError('Hash counter reset during measurement')
            writer.writerow([len(samples), clock(), count])
            h.flush()
            samples.append(count)
            remaining -= 1
            if remaining < 0:
                break
    (destination / 'reference.logs.txt').write_text(','.join(map(str, samples[10:])), encoding='utf-8')
    result = dict(status='collected', acquired_samples=len(samples), discarded_samples=10,
                  retained_samples=len(samples[10:]), sampling='upstream nominal one-second intervals',
                  mining_correctness='not established by the hash counter')
    (destination / 'collection.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:7676')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    url = urlparse(args.url)
    if url.scheme != 'http' or url.hostname not in ('127.0.0.1', 'localhost'):
        parser.error('Only the local experiment page may be opened')
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    options = webdriver.ChromeOptions()
    # Modern API and container execution, rather than a bundled old driver.
    for option in ('--headless=new', '--no-sandbox', '--disable-gpu', '--disable-extensions',
                   '--disable-dev-shm-usage', '--dns-prefetch-disable', '--disable-background-networking',
                   '--window-size=1200,3000', '--proxy-server=http://127.0.0.1:9',
                   '--proxy-bypass-list=127.0.0.1;localhost'):
        options.add_argument(option)
    driver = webdriver.Chrome(options=options)
    destination = Path(args.output)
    def read_counter():
        states = driver.find_elements(By.ID, 'runtime-status')
        if states and states[0].text in ('failed', 'disconnected', 'stopped'):
            raise RuntimeError('Local mining runtime terminated: ' + states[0].text)
        return driver.find_element(By.ID, 'hashes-total').text
    try:
        driver.get(args.url)
        time.sleep(1)
        driver.find_element(By.ID, 'mining-button-text').click()
        result = collect(read_counter, destination)
        print(json.dumps(result))
    except Exception as error:
        destination.mkdir(parents=True, exist_ok=True)
        (destination / 'collection-failure.json').write_text(json.dumps({
            'status':'failed', 'exception_type':type(error).__name__, 'message':str(error),
            'mining_correctness':'not established by collection failure'
        }, indent=2), encoding='utf-8')
        raise
    finally:
        try:
            buttons = driver.find_elements(By.ID, 'stop-mining')
            if buttons:
                buttons[0].click()
            if destination.exists():
                (destination / 'browser-environment.json').write_text(json.dumps({
                    'browser_version':driver.capabilities.get('browserVersion'),
                    'chromedriver':driver.capabilities.get('chrome'),
                    'sampling':'1001 samples; retain samples[10:]'
                }, indent=2), encoding='utf-8')
        finally:
            driver.quit()


if __name__ == '__main__':
    main()
