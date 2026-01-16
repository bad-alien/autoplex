# Autoalex Commands

Prefix: `!alex`

## Stats
- `usage` - active Plex streams
- `status` - Plex health check (shows logs if down)
- `completion "Artist" [user]` - discography completion %
- `compare "Artist" user1 user2` - listening battle

## Library
- `sync_top` - sync "Top Rated" playlist
- `enrich "Album"` - add MusicBrainz credits

## AI Remix
Stems: `bass`, `drums`, `vocals`, `other`

- `boost [stem] [dB?] "Song"` - amplify stem (default +4dB)
- `reduce [stem] [dB?] "Song"` - attenuate stem (default -4dB)

### Examples
```
!alex boost bass "Billie Jean"
!alex boost vocals 8 "Halo"
!alex reduce bass 60 "Song"      # backing track (removes bass)
```
