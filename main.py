import requests
import questionary
import os
import subprocess
import tempfile
from typing import List, Dict
import sys
from bs4 import BeautifulSoup
import argparse
import urllib.parse
import re

movies_base_link = "https://yts.mx/api/v2/list_movies.json"
series_base_link = "https://1337x.to/category-search/"
filters = {"sort": "seeds", "order": "desc", "limit": "50"}


def menu():
    print("\n=== Wave Help Menu ===\n")
    print("Usage: wave [options]")
    print("\nOptions:")
    print("  -m, --movies     Search for movies only")
    print("  -s, --series     Search for TV series only")
    print("  --help           Display this help menu")
    print("\nExample:")
    print("  wave -m Inception")
    print("  wave -s Breaking Bad")
    print("============================\n")


def search_movies(query: str) -> str:
    filters["query_term"] = query
    res = requests.get(movies_base_link, params=filters)
    if res.json()["data"]["movie_count"] == 0:
        return []
    return res.json()["data"]["movies"]


def scrape_series_page(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://1337x.to",
        "Accept-Language": "en-US,en;q=0.9",
    }
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        print("Failed to fetch results.")
        return None

    soup = BeautifulSoup(res.text, "html.parser")

    mirror_links = soup.select(".dropdown-menu li a")

    for link in mirror_links:
        if "ITORRENTS MIRROR" in link.text:
            return link.get("href")

    return None


def search_series(query: str) -> List[Dict]:
    parsed_query = urllib.parse.quote(query, safe="~_-.")
    search_url = f"{series_base_link}{parsed_query}/TV/1/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://1337x.to",
        "Accept-Language": "en-US,en;q=0.9",
    }

    res = requests.get(search_url, headers=headers)

    if res.status_code != 200:
        print("Failed to fetch results.")
        return []

    results = []
    soup = BeautifulSoup(res.text, "html.parser")
    soup = soup.select(
        "table.table-list.table.table-responsive.table-striped > tbody > tr"
    )
    for row in soup:
        columns = row.find_all("td")
        if len(columns) < 5:
            continue

        title_column = columns[0]
        title_link = title_column.find_all("a")[1]

        title = re.sub(r"[^\x00-\x7F]+", "", title_link.text.strip().replace(".", " "))
        series_page_link = "https://1337x.to" + title_link["href"]
        seeders = columns[1].text.strip()
        peers = columns[2].text.strip()
        size = columns[4].text.strip()

        results.append(
            {
                "title": title,
                "page_link": series_page_link,
                "seeds": seeders,
                "peers": peers,
                "size": size,
            }
        )
    return results


def movie_fetch(query: str) -> List[questionary.Choice]:
    movies = search_movies(query)
    if len(movies) == 0:
        return []
    movie_choices: List[questionary.Choice] = []
    torrent_choices: List[questionary.Choice] = []
    for movie in movies:
        title = movie.get("title", "N/A")
        year = movie.get("year", "N/A")
        torrents = movie.get("torrents", [])

        for torrent in torrents:
            quality = torrent.get("quality", "N/A")
            seeds = torrent.get("seeds", "N/A")
            peers = torrent.get("peers", "N/A")
            size = torrent.get("size", "N/A")
            torrent_choices.append(
                questionary.Choice(
                    f"Quality: {quality}  Seeds: {seeds}  Peers: {peers}  Size: {size}",
                    torrent.get("url"),
                )
            )
        movie_choices.append(questionary.Choice(f"{title}     {year}", torrent_choices))
        torrent_choices = []
    return movie_choices


def series_fetch(query: str) -> List[questionary.Choice]:
    series = search_series(query)
    if len(series) == 0:
        return []
    serie_choices: List[questionary.Choice] = []

    for serie in series:
        title = serie.get("title", "N/A")
        seeds = serie.get("seeds", "N/A")
        peers = serie.get("peers", "N/A")
        size = serie.get("size", "N/A")
        page_link = serie.get("page_link", "N/A")

        serie_choices.append(
            questionary.Choice(
                f"{title.replace("â­<90>", "")}",
                {"seeds": seeds, "peers": peers, "size": size, "page_link": page_link},
            )
        )

    return serie_choices


def select_torrent(choices: List[questionary.Choice]) -> str:

    if not choices:
        return None

    selected = questionary.select(
        "Select what you like:",
        choices=choices,
        default=None,
        pointer=">> ",
    ).ask()

    if not selected:
        return None

    # If it's a series, we need to fetch the actual torrent link now
    if isinstance(selected, dict) and "page_link" in selected:
        print(f"Fetching torrent link...")
        torrent_link = scrape_series_page(selected["page_link"])
        if not torrent_link:
            print("Failed to get torrent link.")
            sys.exit(1)

        seeds = selected.get("seeds", "N/A")
        peers = selected.get("peers", "N/A")
        size = selected.get("size", "N/A")
        print(f"Selected torrent with Seeds: {seeds}  Peers: {peers}  Size: {size}")

        return torrent_link
    else:
        # For movies, the torrent link is directly selected
        torrent_choices = questionary.select(
            "Select a torrent:",
            choices=selected,
            default=None,
            pointer=">> ",
        ).ask()

        return torrent_choices


def download_and_open_torrent(torrent_url: str):

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://1337x.to/",
        "Connection": "keep-alive",
    }

    response = requests.get(torrent_url, headers=headers, stream=True)
    if response.status_code != 200 or not response.content:
        print("❌ Failed to download the torrent.")
        print(f"You can open this URL manually in your browser: {torrent_url}")
        sys.exit()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".torrent") as temp_file:
        save_path = temp_file.name
        temp_file.write(response.content)
    print(f"✅ Torrent file saved as {save_path}")
    try:
        if os.name == "nt":  # Windows
            os.startfile(os.path.abspath(save_path))
        elif os.name == "posix":  # Linux & Mac
            process = "xdg-open" if "linux" in os.sys.platform else "open"
            subprocess.run([process, save_path])
    except Exception as e:
        print(f"❌ Failed to open the torrent: {e} \n")
        print(f"You can still manually open the torrent file at : {save_path}")
        sys.exit()


def main():

    try:
        parser = argparse.ArgumentParser(description="Wave: Torrent Searcher")
        parser.add_argument(
            "-m", "--movies", action="store_true", help="Search for movies"
        )
        parser.add_argument(
            "-s", "--series", action="store_true", help="Search for series"
        )

        args = parser.parse_args()
        results = []

        if not args.movies and not args.series:
            print("Please specify a valid category from the menu : ")
            menu()
            return
        else:
            query = questionary.text("Enter what you're looking for : ").ask()
            if args.movies:
                results = movie_fetch(query)
            elif args.series:
                results = series_fetch(query)

        if len(results) == 0:
            print("No results were found")
            return
        url = select_torrent(results)
        download_and_open_torrent(url)
    except KeyboardInterrupt:
        print("\nExiting program...")
        sys.exit(0)
    except Exception as e:
        sys.exit(1)


if __name__ == "__main__":
    main()
