from __future__ import annotations


def test_run_extract_https_is_exposed() -> None:
    from urlcheck_smith import run_extract_https
    from urlcheck_smith.cli import run_extract_https as cli_run_extract_https

    assert run_extract_https is cli_run_extract_https


def test_crawl_url_layers_is_exposed() -> None:
    from urlcheck_smith import CrawledURL, crawl_url_layers
    from urlcheck_smith.core.crawl import (
        CrawledURL as core_crawled_url,
        crawl_url_layers as core_crawl_url_layers,
    )

    assert crawl_url_layers is core_crawl_url_layers
    assert CrawledURL is core_crawled_url
