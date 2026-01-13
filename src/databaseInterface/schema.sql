-- Clarity Library Database Schema
-- All IDs use NSID format (namespace:id) for consistency

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA cache_size = 10000;

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
    last_played TEXT  -- ISO timestamp, nullable
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
    lyrics_text TEXT NOT NULL
);

-- Stats table - log of all plays
CREATE TABLE IF NOT EXISTS stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    song_id TEXT NOT NULL,  -- NSID
    play_time TEXT NOT NULL,  -- ISO timestamp
    play_duration REAL NOT NULL  -- seconds, as float
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

-- Stats indexes (for efficient filtering by song and time)
CREATE INDEX IF NOT EXISTS idx_stats_song_id ON stats(song_id);
CREATE INDEX IF NOT EXISTS idx_stats_play_time ON stats(play_time);

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

-- Artist-Song map indexes
CREATE INDEX IF NOT EXISTS idx_artist_song_song_id ON artist_song_map(song_id);
CREATE INDEX IF NOT EXISTS idx_artist_song_artist_id ON artist_song_map(artist_id);

-- Artist-Album map indexes
CREATE INDEX IF NOT EXISTS idx_artist_album_album_id ON artist_album_map(album_id);
CREATE INDEX IF NOT EXISTS idx_artist_album_artist_id ON artist_album_map(artist_id);

-- Song-Tag map indexes
CREATE INDEX IF NOT EXISTS idx_song_tag_tag_id ON song_tag_map(tag_id);
CREATE INDEX IF NOT EXISTS idx_song_tag_song_id ON song_tag_map(song_id);