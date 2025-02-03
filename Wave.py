import requests
import questionary
import webbrowser
import os
import subprocess



movies_Baselink = "https://yts.mx/api/v2/list_movies.json"
filters= {'sort':'seeds','order' : 'desc', 'limit':'50'}
torrent_path = os.path.abspath("movie.torrent")



def search(query) :
    filters['query_term'] = query
    res = requests.get(movies_Baselink , params=filters )
    if res.json()['data']['movie_count'] != 0 :
        return res.json()['data']['movies']
    else : return 0

def movie_info(query):
    movies = search(query)
    choices = []
    if movies :
        for movie in movies:
            title_long = movie.get('title_long', 'N/A')
            torrents = movie.get('torrents', [])
            for torrent in torrents:
                quality = torrent.get('quality', 'N/A')
                seeds = torrent.get('seeds', 'N/A')
                choices.append({'name': f"{title_long} Quality : {quality}  seeds : {seeds}" , 'value' : torrent.get('url') })
    return choices
    
def download_and_open_torrent(torrent_url, movie):
    save_path=f"{movie}.torrent"
    response = requests.get(torrent_url, stream=True)
    if response.status_code == 200:
        with open(save_path, "wb") as file:
            file.write(response.content)
        print(f"✅ Torrent file saved as {save_path}")

        try:
            if os.name == "nt":  # Windows
                os.startfile(os.path.abspath(save_path))
            elif os.name == "posix":  # Linux & Mac
                subprocess.run(["xdg-open" if "linux" in os.sys.platform else "open", save_path])
        except Exception as e:
            print(f"❌ Failed to open the torrent: {e}")

    else:
        print("❌ Failed to download the torrent.")


def Choice(choices) :

    torrent = questionary.select(
        "Select a torrent:",
        choices=choices,
        default=None,
        pointer= '>> ',
    ).ask()
    return torrent


def main() :

    query= input("Enter what you're looking for : ")
    movies = movie_info(query)

    if movies :
        url = Choice(movies)
        download_and_open_torrent(url,query)

    else : 
        print("No results were found")

if __name__ == "__main__":
    main()