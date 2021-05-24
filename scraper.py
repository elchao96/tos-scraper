import argparse
from pathlib import Path
from typing import Optional
import bs4
import requests
from bs4 import BeautifulSoup

WEB_ARCHIVE_CDX_URL = "http://web.archive.org/cdx/search/cdx?url=https://help.twitter.com/en/rules-and-policies&output=json"
TIMESTAMPS = "timestamps.txt"

WEB_ARCHIVE_URL = "https://web.archive.org/web/{timestamp}/https://help.twitter.com/en/rules-and-policies"


def get_all_timestamps() -> None:
    r = requests.get(WEB_ARCHIVE_CDX_URL)
    json_list = r.json()
    json_list.pop(0)
    timestamps = sorted(list(set([f"{item[1]}\n" for item in json_list])))
    with open(TIMESTAMPS, "w") as timestamps_file:
        timestamps_file.writelines(timestamps)


def scrape_rules_for_each_timestamp(starting_timestamp: Optional[str]):
    last = set()
    if starting_timestamp:
        with open(f"diffs/{starting_timestamp}.txt", "r") as starting_ts_file:
            for line in starting_ts_file.readlines():
                last.add(line.strip())
    current = set()
    with open(TIMESTAMPS, "r") as timestamps_file:
        lines = timestamps_file.readlines()
        for line in lines:
            if line.startswith("2"):
                timestamp = line.strip()
                if not starting_timestamp or (
                    starting_timestamp and timestamp >= starting_timestamp
                ):
                    web_archive_ts = WEB_ARCHIVE_URL.format(timestamp=timestamp)
                    r = requests.get(web_archive_ts)
                    soup = BeautifulSoup(r.text, "html.parser")
                    for li in soup.find_all("li", class_="tp02__list-item"):
                        for child in li.children:
                            if isinstance(child, bs4.element.Tag):
                                rule_name = []
                                for content in child.contents:
                                    if isinstance(content, bs4.element.Tag):
                                        rule_name.append(
                                            "".join(content.contents).strip()
                                        )
                                    else:
                                        rule_name.append(content.strip())
                                current.add(" ".join(rule_name).strip())
                    if current != last:
                        with open(f"diffs/{timestamp}.txt", "w") as ts_file:
                            ts_file.write("\n".join(current))
                            print(f"wrote diffs/{timestamp}.txt")
                        last = set(item for item in current)
                        current.clear()
                    print(f"just processed {timestamp}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="ScraperTwitterRules")
    parser.add_argument("-t", type=str)
    args = parser.parse_args()
    timestamp_file = Path(TIMESTAMPS)
    if not timestamp_file.is_file():
        get_all_timestamps()
    scrape_rules_for_each_timestamp(args.t)
