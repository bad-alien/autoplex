import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Mock EVERYTHING
mock_mods = [
    'aiohttp', 'plexapi', 'plexapi.server', 'musicbrainzngs', 
    'discord', 'discord.ext', 'discord.ext.commands', 'dotenv'
]
for mod in mock_mods:
    sys.modules[mod] = MagicMock()

from services.plex_service import PlexService
from clients import clients

class TestPlexService(unittest.TestCase):

    def setUp(self):
        self.mock_plex_client = MagicMock()
        clients.plex = self.mock_plex_client
        self.service = PlexService()

    def test_get_artist_completion_found(self):
        mock_lib = MagicMock()
        mock_lib.type = 'artist'
        
        mock_artist = MagicMock()
        mock_lib.search.return_value = [mock_artist]
        
        track1 = MagicMock(viewCount=1)
        track2 = MagicMock(viewCount=0)
        mock_artist.tracks.return_value = [track1, track2]
        
        self.mock_plex_client.library.sections.return_value = [mock_lib]
        
        percentage, played, total = self.service.get_artist_completion("Test Artist")
        
        self.assertEqual(played, 1)
        self.assertEqual(total, 2)
        self.assertEqual(percentage, 50.0)

if __name__ == '__main__':
    unittest.main()
