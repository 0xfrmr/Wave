import requests
import questionary
import os
import subprocess
import tempfile
from typing import List, Dict
import sys

movies_base_link = "https://yts.mx/api/v2/list_movies.json"
filters = {"sort": "seeds", "order": "desc", "limit": "50"}


def search(query: str) -> List[Dict]:
    filters["query_term"] = query
    res = requests.get(movies_base_link, params=filters)
    if res.json()["data"]["movie_count"] == 0:
        return []
    return res.json()["data"]["movies"]


def movie_fetch(query: str) -> List[questionary.Choice]:
    movies = search(query)
    if len(movies) == 0:
        return []
    movie_choices: List[questionary.Choice] = []
    torrent_choices: List[questionary.Choice] = []
    for movie in movies:
        title_long = movie.get("title_long", "N/A")
        torrents = movie.get("torrents", [])
        for torrent in torrents:
            quality = torrent.get("quality", "N/A")
            seeds = torrent.get("seeds", "N/A")
            torrent_choices.append(
                questionary.Choice(
                    f"Quality: {quality}  Seeds: {seeds} ", torrent.get("url")
                )
            )
        movie_choices.append(questionary.Choice(f"{title_long}", torrent_choices))
        torrent_choices = []
    return movie_choices


def select_torrent(movie_choices: List[questionary.Choice]) -> str:

    movie_torrents = questionary.select(
        "Select a movie:",
        choices=movie_choices,
        default=None,
        pointer=">> ",
    ).ask()

    torrent_link = questionary.select(
        "Select a torrent:",
        choices=movie_torrents,
        default=None,
        pointer=">> ",
    ).ask()

    return torrent_link


def download_and_open_torrent(torrent_url: str):

    response = requests.get(torrent_url, stream=True)
    if response.status_code != 200:
        print("❌ Failed to download the torrent.")
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

    query = questionary.text("Enter what you're looking for : ").ask()
    movies = movie_fetch(query)

    if len(movies) == 0:
        print("No results were found")
        return
    url = select_torrent(movies)
    download_and_open_torrent(url)


if __name__ == "__main__":
    main()
