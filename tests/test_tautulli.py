import unittest
from unittest.mock import MagicMock, patch, AsyncMock
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

from services.tautulli_service import TautulliService
from config import Config

class TestTautulliService(unittest.IsolatedAsyncioTestCase):
    
    def setUp(self):
        Config.TAUTULLI_URL = "http://mock-url"
        Config.TAUTULLI_API_KEY = "mock-key"
        self.service = TautulliService()

    async def test_get_activity_success(self):
        # Setup Mock Response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            'response': {
                'result': 'success',
                'data': {
                    'stream_count': 1,
                    'sessions': [{'title': 'Test Movie', 'user': 'TestUser'}]
                }
            }
        }
        
        # Setup session.get to return a mock context manager
        mock_get_ctx = MagicMock()
        mock_get_ctx.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get_ctx.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.get.return_value = mock_get_ctx
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            # We also need to mock aiohttp.ClientSession as a context manager if used that way
            # but in our code we use: async with aiohttp.ClientSession() as session:
            mock_session_ctx = MagicMock()
            mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_ctx.__aexit__ = AsyncMock(return_value=None)
            
            with patch('aiohttp.ClientSession', return_value=mock_session_ctx):
                result = await self.service.get_activity()
                
                self.assertIsNotNone(result)
                self.assertEqual(result['stream_count'], 1)
                self.assertEqual(result['sessions'][0]['user'], 'TestUser')

if __name__ == '__main__':
    unittest.main()
