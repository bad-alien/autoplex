import os
import discord
from discord.ext import commands
import asyncio
import logging
from config import Config
from clients import clients
from services.tautulli_service import TautulliService
from services.plex_service import PlexService

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Autoplex")

# Validate Config
try:
    Config.validate()
except ValueError as e:
    logger.critical(str(e))
    exit(1)

# Initialize Services
tautulli_service = TautulliService()
plex_service = PlexService()

# Initialize Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!plex ", intents=intents)

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    
    # Initialize Plex Connection
    try:
        clients.initialize_plex()
    except Exception as e:
        logger.error("Could not connect to Plex on startup. Commands requiring Plex will fail.")
    
    # Initialize MusicBrainz
    clients.initialize_musicbrainz()
    
    logger.info('Autoplex is ready to serve.')

@bot.event
async def on_message(message):
    # DEBUG: Log every message seen
    logger.info(f"DEBUG: Message received from {message.author}: {message.content}")
    
    # This is crucial: without this line, commands won't work if on_message is defined
    await bot.process_commands(message)

@bot.command()
async def usage(ctx):
    """
    Shows current stream activity from Tautulli.
    """
    await ctx.typing()
    activity = await tautulli_service.get_activity()
    
    if not activity:
        await ctx.send("Unable to fetch activity from Tautulli.")
        return

    stream_count = int(activity.get('stream_count', 0))
    
    if stream_count == 0:
        embed = discord.Embed(title="Plex Usage", description="No active streams.", color=discord.Color.green())
        await ctx.send(embed=embed)
        return

    embed = discord.Embed(title=f"Plex Usage ({stream_count} Active)", color=discord.Color.blue())
    
    for session in activity.get('sessions', []):
        title = session.get('full_title') or session.get('title')
        user = session.get('user')
        device = session.get('player')
        quality = session.get('quality_profile')
        state = session.get('state') # playing, paused, buffering
        
        status_icon = "▶️" if state == 'playing' else "II" if state == 'paused' else "buffer"
        
        embed.add_field(
            name=f"{status_icon} {user}",
            value=f"**{title}**\nDevice: {device}\nQuality: {quality}",
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command()
async def completion(ctx, artist_name: str, arg1: str = None, arg2: str = None):
    """
    Calculates percentage of artist's discography played.
    Usage: !plex completion "Aphex Twin" [username] [full]
    """
    await ctx.typing()
    
    # Parse arguments flexibly
    user = None
    show_full = False
    
    for arg in [arg1, arg2]:
        if not arg:
            continue
        if arg.lower() == "full":
            show_full = True
        else:
            user = arg

    try:
        # We pass tautulli_service to enable user-specific lookups
        data = await plex_service.get_artist_completion(artist_name, user, tautulli_service)
    except RuntimeError:
        await ctx.send("Plex is not connected.")
        return

    if not data:
        await ctx.send(f"Artist '{artist_name}' not found in music libraries.")
        return

    # Unpack Data
    artist = data['artist']
    global_percent = data['global_percent']
    unique_played = data['unique_played']
    total_tracks = data['total_tracks']
    total_plays = data['total_plays']
    albums = data['albums']

    title = f"Artist Completion: {artist}"
    if user:
        title += f" ({user})"
        
    embed = discord.Embed(title=title, color=discord.Color.gold())
    
    # Global Stats
    embed.add_field(name="Total Plays", value=str(total_plays), inline=True)
    embed.add_field(name="Unique Tracks", value=f"{unique_played} / {total_tracks} ({global_percent:.1f}%)", inline=True)
    
    # Global Progress Bar
    bar_length = 20
    filled_length = int(bar_length * global_percent // 100)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    embed.add_field(name="Collection Progress", value=f"`[{bar}]`", inline=False)
    
    # Album Breakdown
    # Separation: 100% completed vs In Progress
    completed_albums = []
    in_progress_albums = []
    
    for album in albums:
        if album['percent'] >= 100:
            completed_albums.append(album['title'])
        else:
            in_progress_albums.append(album)
            
    # Limit logic: We prioritize showing In-Progress albums
    # Discord limit is 25 fields total. 
    # Used so far: 3 (Stats) + 1 (Visual Bar) + 1 (Header) = 5
    # Footer might add 1.
    # Safe limit for albums = 18.
    limit = 18 if show_full else 6
    
    embed.add_field(name="In Progress", value="\u200b", inline=False)
    
    count = 0
    for album in in_progress_albums:
        if count >= limit: 
            remaining = len(in_progress_albums) - limit
            embed.add_field(name="...", value=f"And {remaining} more in-progress...", inline=False)
            break
            
        p = album['percent']
        mini_bar_len = 10
        mini_fill = int(mini_bar_len * p // 100)
        mini_bar = '▓' * mini_fill + '░' * (mini_bar_len - mini_fill)
        
        value_str = f"`{mini_bar}` **{p:.0f}%** ({album['played']}/{album['total']})"
        embed.add_field(name=f"{album['title']} ({album['year']})", value=value_str, inline=False)
        count += 1
        
    # Show Completed List at bottom
    if completed_albums:
        completed_str = ", ".join(completed_albums)
        if len(completed_str) > 1000: # Truncate if insanely long
            completed_str = completed_str[:1000] + "..."
        embed.add_field(name="🏆 Completed Albums", value=completed_str, inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def sync_top(ctx):
    """
    Syncs 'Top Rated' playlist with 4+ star tracks.
    """
    await ctx.typing()
    try:
        count = plex_service.create_playlist_from_rating(min_rating=8.0)
        await ctx.send(f"✅ Synced 'Top Rated' playlist with {count} tracks.")
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        await ctx.send("Failed to sync playlist. Check logs.")

@bot.command()
async def enrich(ctx, *, query: str):
    """
    Enriches an album's metadata from MusicBrainz.
    Usage: !plex enrich Kind of Blue
    """
    await ctx.typing()
    try:
        album = plex_service.enrich_jazz_album(query)
        if album:
            await ctx.send(f"✅ Enriched metadata for **{album.title}**.")
        else:
            await ctx.send(f"❌ Could not find album or enrich metadata for '{query}'.")
    except Exception as e:
        logger.error(f"Enrich failed: {e}")
        await ctx.send("An error occurred during enrichment.")

@bot.command()
async def compare(ctx, artist_name: str, user1: str, user2: str):
    """
    Compares two users' progress for an artist.
    Usage: !plex compare "Aphex Twin" user1 user2
    """
    await ctx.typing()
    
    try:
        # Fetch data for both users concurrently? 
        # For simplicity/safety with the shared service, we do sequential await.
        data1 = await plex_service.get_artist_completion(artist_name, user1, tautulli_service)
        data2 = await plex_service.get_artist_completion(artist_name, user2, tautulli_service)
    except RuntimeError:
        await ctx.send("Plex is not connected.")
        return

    if not data1 or not data2:
        await ctx.send(f"Could not fetch data for artist '{artist_name}'. Check names.")
        return

    # Unpack
    p1 = data1['global_percent']
    p2 = data2['global_percent']
    plays1 = data1['total_plays']
    plays2 = data2['total_plays']
    
    # Determine Winner
    if p1 > p2:
        winner = f"🏆 **{user1}** leads by {p1-p2:.1f}%"
        color = discord.Color.blue()
    elif p2 > p1:
        winner = f"🏆 **{user2}** leads by {p2-p1:.1f}%"
        color = discord.Color.red()
    else:
        winner = "🤝 It's a Tie!"
        color = discord.Color.gold()

    embed = discord.Embed(title=f"⚔️ Battle: {data1['artist']}", description=winner, color=color)
    
    # Side by Side Stats
    embed.add_field(name=f"👤 {user1}", value=f"**{p1:.1f}%**\n{data1['unique_played']} tracks\n{plays1} plays", inline=True)
    embed.add_field(name="VS", value="|", inline=True)
    embed.add_field(name=f"👤 {user2}", value=f"**{p2:.1f}%**\n{data2['unique_played']} tracks\n{plays2} plays", inline=True)
    
    # Visual Bar Comparison
    # Normalize to max 20 chars
    # If p1=50, p2=20 -> [█████-----] vs [██--------]
    
    def make_bar(percent):
        fill = int(20 * percent // 100)
        return '█' * fill + '░' * (20 - fill)

    embed.add_field(name="Visual Comparison", value=f"**{user1}**\n`[{make_bar(p1)}]`\n\n**{user2}**\n`[{make_bar(p2)}]`", inline=False)

    await ctx.send(embed=embed)

if __name__ == "__main__":
    try:
        bot.run(Config.DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Error running bot: {e}")
