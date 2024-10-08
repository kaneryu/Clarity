import ytmusicapi
import asyncio
import blessed, json

def createTerminal():
    term = blessed.Terminal()
    return term

def createYTMusic():
    ytmusic = ytmusicapi.YTMusic()
    return ytmusic

def initialize():
    term = createTerminal()
    print(term.clear())
    print(term.move_xy(0, 0))
    print(term.bold('InnerTuneDesktop "Onyx" Music Player'))

def createInput(term, txt="Enter a song name: "):
    print(term.move_xy(0, 1))
    print(term.bold(txt), end='')
    song = input()
    return song


        
async def search(ytmusic: ytmusicapi.YTMusic, song):
    search_results = await ytmusic.search(song)
    return search_results

async def searchCategory(ytmusic: ytmusicapi.YTMusic, song):
    search_results = await search(ytmusic, song)
    artists = []
    podcasts = []
    song = []
    playlists = []
    albums = []
    episodes = []
    videos = []
    
    for i, result in enumerate(search_results):
        category = result['category']
        if category == "Top Result":
            continue
        if category == "Episodes":
            episodes.append(result)
        if category == "Podcasts":
            podcasts.append(result)
        if category == "Songs":
            song.append(result)
        if category == "Profiles":
            artists.append(result)
        if category == "Playlists":
            playlists.append(result)
        if category == "Albums":
            albums.append(result)
        if category == "Videos":
            videos.append(result)
        
    return {"artists": artists, "podcasts": podcasts, "song": song, "playlists": playlists, "albums": albums, "episodes": episodes, "videos": videos}

    
def prettyPrintResults(search_results):
    artists = []
    podcasts = []
    song = []
    playlists = []
    albums = []
    episodes = []
    videos = []
    
    
    for i, result in enumerate(search_results):
        category = result['category']
        if category == "Top Result":
            continue
        if category == "Episodes":
            episodes.append(result)
        if category == "Podcasts":
            podcasts.append(result)
        if category == "Songs":
            song.append(result)
        if category == "Profiles":
            artists.append(result)
        if category == "Playlists":
            playlists.append(result)
        if category == "Albums":
            albums.append(result)
        if category == "Videos":
            videos.append(result)
    
    pretty_results = ""
    
    if len(artists) > 0:
        print("Artists:")
        for i, artist in enumerate(artists):
            i+=1
            print("\t" + f"{i}: {artist["artist"]}" )
            
    if len(podcasts) > 0:
        print("Podcasts:")
        for i, podcast in enumerate(podcasts):
            i+=1
            print("\t" + f"{i}: {podcast["title"]}" )
            
    if len(song) > 0:
        print("Songs:")
        for i, s in enumerate(song):
            i+=1
            print("\t" + f"{i}: {s["title"] + " by " + s["artists"][0]["name"]}" )
            
    if len(playlists) > 0:
        print("Playlists:")
        for i, playlist in enumerate(playlists):
            i+=1
            print("\t" + f"{i}: {playlist["title"] + " by " + playlist["author"]}" )
            
    if len(albums) > 0:
        print("Albums:")
        for i, album in enumerate(albums):
            i+=1
            print("\t" + f"{i}: {album["title"] + " by " + album["artists"][0]["name"]}" )
            
    if len(episodes) > 0:
        print("Episodes:")
        for i, episode in enumerate(episodes):
            i+=1
            print("\t" + f"{i}: {episode["title"]}" )
            
    if len(videos) > 0:
        print("Videos:")
        for i, video in enumerate(videos):
            i+=1
            print("\t" + f"{i}: {video["title"]}" )
            
def getLoop():
    loop = asyncio.new_event_loop()
    return loop


def inspectItem(search_results, category, index):
    item = search_results[category][int(index)-1]
    print(item)

async def main():
    global ytmusic
    term = createTerminal()
    initialize()
    ytmusic = createYTMusic()
    # query = createInput(term)
    # search_results = await search(ytmusic, query)
    # search_category_results = await searchCategory(ytmusic, query)
    # prettyPrintResults(search_results)
    # print("Enter the type, then the number of the item you want to inspect.")
    # print("Type: [S] Song, [A] Artist, [P] Playlist, [Al] Album, [E] Episode, [V] Video")
    # print("Example: S 1")
    # mapping = {"S": "song", "A": "artists", "P": "playlists", "Al": "albums", "E": "episodes", "V": "videos"}
    # item = input()
    # inspectItem(search_category_results, mapping[item.split(" ")[0]], item.split(" ")[1])
    # await ytmusic.close()
    
    write = await ytmusic.get_song("U3SNwZ-bmAE")
    with open("search_results.json", "w") as f:
        f.write(json.dumps(write))
    
    
if __name__ == '__main__':
    loop = getLoop()
    loop.run_until_complete(main())
    