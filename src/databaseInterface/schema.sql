-- Clarity Library Database Schema
-- All IDs use NSID format (namespace:id) for consistency

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA cache_size = 10000;

PRAGMA user_version = 1; -- Increment on non-backwards compatible changes
PRAGMA application_id = 0x434C5259;  -- 'CLRY' in hex

-- Songs table
CREATE TABLE IF NOT EXISTS songs (
    id TEXT PRIMARY KEY,  -- NSID format (youtube:VIDEO_ID)
    title TEXT NOT NULL,
    album_id TEXT,  -- NSID, nullable
    duration INTEGER NOT NULL,  -- seconds
    thumbnail_url TEXT,
    material_color TEXT,  -- hex color, nullable
    liked INTEGER NOT NULL DEFAULT 0,  -- boolean
    play_count INTEGER NOT NULL DEFAULT 0,  -- aggregated from stats
    date_added TEXT NOT NULL,  -- ISO timestamp
    last_played TEXT,  -- ISO timestamp, nullable
    download_status INTEGER NOT NULL DEFAULT 0  -- 0: not_downloaded, 1: downloading, 2: downloaded
);

-- Playlists table
CREATE TABLE IF NOT EXISTS playlists (
    id TEXT PRIMARY KEY,  -- NSID format (local:playlist:UUID or provider:playlist:ID)
    title TEXT NOT NULL,
    description TEXT,
    thumbnail_url TEXT,
    created_date TEXT NOT NULL,  -- ISO timestamp
    modified_date TEXT NOT NULL,  -- ISO timestamp
    is_system INTEGER NOT NULL DEFAULT 0,  -- boolean
    is_remote INTEGER NOT NULL DEFAULT 0,  -- boolean
    playlist_type TEXT NOT NULL DEFAULT 'basic',  -- basic, smart, composite
    json_rules TEXT,  -- JSON, nullable - for smart/composite playlists
    CHECK(playlist_type IN ('basic', 'smart', 'composite'))
);

-- Artists table
CREATE TABLE IF NOT EXISTS artists (
    id TEXT PRIMARY KEY,  -- NSID format
    name TEXT NOT NULL,
    thumbnail_url TEXT,
    date_added TEXT NOT NULL,  -- ISO timestamp
    last_accessed TEXT  -- ISO timestamp, nullable
);

-- Albums table
CREATE TABLE IF NOT EXISTS albums (
    id TEXT PRIMARY KEY,  -- NSID format
    title TEXT NOT NULL,
    artist_id TEXT,  -- NSID for primary artist
    release_year INTEGER,
    thumbnail_url TEXT,
    date_added TEXT NOT NULL,  -- ISO timestamp
    last_accessed TEXT  -- ISO timestamp, nullable
);

-- Lyrics table
CREATE TABLE IF NOT EXISTS lyrics (
    song_id TEXT PRIMARY KEY,  -- NSID
    lyric_id TEXT NOT NULL,  -- NSID (probably in format lyrics:SOURCE:(Song NSID), e.g., lyrics:genius:youtube:VIDEO_ID)
    source TEXT NOT NULL,  -- e.g., 'genius', 'azlyrics'
    lyrics_text TEXT NOT NULL
);

-- -- Stats table - log of all plays
-- CREATE TABLE IF NOT EXISTS stats (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     song_id TEXT NOT NULL,  -- NSID
--     play_time TEXT NOT NULL,  -- ISO timestamp
--     play_duration REAL NOT NULL  -- seconds, as float
-- );

-- Listen Events
CREATE TABLE IF NOT EXISTS listen_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    song_id TEXT NOT NULL,  -- NSID
    event_id TEXT NOT NULL UNIQUE,  -- NSID
    event_time TEXT NOT NULL,  -- ISO timestamp
    event_end_time TEXT NOT NULL,  -- ISO timestamp
    event_duration REAL NOT NULL,  -- seconds, as float
    liked INTEGER NOT NULL DEFAULT 0,  -- boolean, whether the song was liked at the time of this listen
    skipped INTEGER NOT NULL DEFAULT 0,  -- boolean, whether the song was skipped during this listen
    completed INTEGER NOT NULL DEFAULT 0,  -- boolean, whether the song was played to completion during this listen
    downloaded INTEGER NOT NULL DEFAULT 0  -- boolean, whether the song was downloaded at the time of this listen
);

-- Interaction Events
CREATE TABLE IF NOT EXISTS interaction_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    interaction_type TEXT NOT NULL,  -- "like", "download", "playlist_add", "playlist_remove", "tag_add", "tag_remove", etc.
    primary_id TEXT NOT NULL,  -- NSID of the primary entity involved (e.g., song ID for likes/downloads, playlist ID for playlist additions/removals, tag ID for tag additions/removals)
    involved_entity_ids TEXT,  -- JSON array of other entities involved in this interaction.
    interaction_id TEXT UNIQUE NOT NULL,  -- NSID in the format "interaction:TYPE:PRIMARY_ID,TIMESTAMP"
    extra_field TEXT,  -- nullable, for misc additional info
    interaction_time TEXT NOT NULL  -- ISO timestamp of when the interaction occurred
);

-- Search History table
CREATE TABLE IF NOT EXISTS search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    provider TEXT NOT NULL,  -- e.g., "local", "youtube", "spotify"
    timestamp TEXT NOT NULL  -- ISO timestamp
);

-- Tag Groups table
CREATE TABLE IF NOT EXISTS tag_groups (
    id TEXT PRIMARY KEY,  -- NSID (local:taggroup:UUID)
    name TEXT NOT NULL UNIQUE,
    date_created TEXT NOT NULL,  -- ISO timestamp
    description TEXT
);

-- Tags table
CREATE TABLE IF NOT EXISTS tags (
    id TEXT PRIMARY KEY,  -- NSID (local:tag:UUID)
    name TEXT NOT NULL UNIQUE,
    date_created TEXT NOT NULL,  -- ISO timestamp
    description TEXT,
    use_count INTEGER NOT NULL DEFAULT 0
);

-- Junction Tables / Maps

-- Tag-Tag Group map
CREATE TABLE IF NOT EXISTS tag_tag_group_map (
    tag_id TEXT NOT NULL,  -- NSID
    tag_group_id TEXT NOT NULL,  -- NSID
    date_mapped TEXT NOT NULL,  -- ISO timestamp
    PRIMARY KEY (tag_id, tag_group_id),
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_group_id) REFERENCES tag_groups(id) ON DELETE CASCADE
);

-- Song-Tag map
CREATE TABLE IF NOT EXISTS song_tag_map (
    song_id TEXT NOT NULL,  -- NSID
    tag_id TEXT NOT NULL,  -- NSID
    date_tagged TEXT NOT NULL,  -- ISO timestamp
    PRIMARY KEY (song_id, tag_id),
    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- Artist-Album map
CREATE TABLE IF NOT EXISTS artist_album_map (
    artist_id TEXT NOT NULL,  -- NSID
    album_id TEXT NOT NULL,  -- NSID
    PRIMARY KEY (artist_id, album_id),
    FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE,
    FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE
);

-- Artist-Song map (for features/collaborations)
CREATE TABLE IF NOT EXISTS artist_song_map (
    artist_id TEXT NOT NULL,  -- NSID
    song_id TEXT NOT NULL,  -- NSID
    PRIMARY KEY (artist_id, song_id),
    FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE,
    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
);

-- Playlist-Song map
CREATE TABLE IF NOT EXISTS playlist_song_map (
    playlist_id TEXT NOT NULL,  -- NSID
    song_id TEXT NOT NULL,  -- NSID
    position INTEGER NOT NULL,
    date_added TEXT NOT NULL,  -- ISO timestamp
    date_modified TEXT NOT NULL,  -- ISO timestamp
    cache_generated TEXT,  -- ISO timestamp, nullable - for smart/composite playlists
    PRIMARY KEY (playlist_id, song_id),
    FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
);

-- Indexes for performance

-- Listen event indexes
CREATE INDEX IF NOT EXISTS idx_listen_events_song_time ON listen_events(song_id, event_time);
CREATE INDEX IF NOT EXISTS idx_listen_events_time ON listen_events(event_time);

-- Interaction event indexes
CREATE INDEX IF NOT EXISTS idx_interaction_events_primary_time ON interaction_events(primary_id, interaction_time);
CREATE INDEX IF NOT EXISTS idx_interaction_events_type_time ON interaction_events(interaction_type, interaction_time);

-- Search history indexes
CREATE INDEX IF NOT EXISTS idx_search_history_provider_time ON search_history(provider, timestamp);
CREATE INDEX IF NOT EXISTS idx_search_history_query_time ON search_history(query, timestamp);

-- Tag name index for search
CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);

-- Tag group name index for search
CREATE INDEX IF NOT EXISTS idx_tag_groups_name ON tag_groups(name);

-- Playlist-Song position index for ordering
CREATE INDEX IF NOT EXISTS idx_playlist_song_position ON playlist_song_map(playlist_id, position);

-- Song indexes for common queries
CREATE INDEX IF NOT EXISTS idx_songs_liked ON songs(liked);
CREATE INDEX IF NOT EXISTS idx_songs_play_count ON songs(play_count);
CREATE INDEX IF NOT EXISTS idx_songs_date_added ON songs(date_added);
CREATE INDEX IF NOT EXISTS idx_songs_last_played ON songs(last_played);
CREATE INDEX IF NOT EXISTS idx_songs_download_status ON songs(download_status);
CREATE INDEX IF NOT EXISTS idx_songs_album_id ON songs(album_id);

-- Playlist indexes for common queries
CREATE INDEX IF NOT EXISTS idx_playlists_modified_date ON playlists(modified_date);
CREATE INDEX IF NOT EXISTS idx_playlists_playlist_type ON playlists(playlist_type);

-- Artist and album indexes for library lookup
CREATE INDEX IF NOT EXISTS idx_artists_name ON artists(name);
CREATE INDEX IF NOT EXISTS idx_albums_artist_id ON albums(artist_id);
CREATE INDEX IF NOT EXISTS idx_albums_title ON albums(title);

-- Artist-Song map indexes
CREATE INDEX IF NOT EXISTS idx_artist_song_song_id ON artist_song_map(song_id);
CREATE INDEX IF NOT EXISTS idx_artist_song_artist_id ON artist_song_map(artist_id);

-- Artist-Album map indexes
CREATE INDEX IF NOT EXISTS idx_artist_album_album_id ON artist_album_map(album_id);
CREATE INDEX IF NOT EXISTS idx_artist_album_artist_id ON artist_album_map(artist_id);

-- Song-Tag map indexes
CREATE INDEX IF NOT EXISTS idx_song_tag_tag_id ON song_tag_map(tag_id);
CREATE INDEX IF NOT EXISTS idx_song_tag_song_id ON song_tag_map(song_id);

-- Tag group map indexes
CREATE INDEX IF NOT EXISTS idx_tag_tag_group_group_id ON tag_tag_group_map(tag_group_id);

-- Playlist-Song reverse lookup indexes
CREATE INDEX IF NOT EXISTS idx_playlist_song_song_id ON playlist_song_map(song_id);