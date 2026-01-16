"""
Plex Health Monitor Service

Polls the Plex server and alerts via Discord if it becomes unresponsive.
Retrieves Docker container logs when running on Unraid.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Optional, Callable, Awaitable

import requests

logger = logging.getLogger("Autoalex.PlexMonitor")

# Try to import Docker SDK - may not be available in all environments
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    logger.warning("Docker SDK not installed. Log retrieval will be unavailable.")


class PlexMonitor:
    """
    Background service that monitors Plex health and alerts on failures.
    """

    def __init__(
        self,
        plex_url: str,
        container_name: str = "binhex-plexpass",
        poll_interval: int = 30,
        alert_cooldown: int = 1800,
        alert_channel_id: Optional[int] = None,
    ):
        self.plex_url = plex_url
        self.container_name = container_name
        self.poll_interval = poll_interval
        self.alert_cooldown = alert_cooldown
        self.alert_channel_id = alert_channel_id

        # State tracking
        self._is_running = False
        self._task: Optional[asyncio.Task] = None
        self._last_alert_time: float = 0
        self._plex_was_down = False
        self._docker_client: Optional["docker.DockerClient"] = None

        # Callback for sending Discord messages
        self._send_alert: Optional[Callable[[str], Awaitable[None]]] = None

        # Initialize Docker client
        self._init_docker()

    def _init_docker(self) -> None:
        """Initialize Docker client if available."""
        if not DOCKER_AVAILABLE:
            logger.info("Docker SDK not available - running in mock mode")
            return

        try:
            self._docker_client = docker.from_env()
            # Test connection
            self._docker_client.ping()
            logger.info("Docker client connected successfully")
        except Exception as e:
            logger.warning(f"Docker not available: {e}. Running in mock mode.")
            self._docker_client = None

    @property
    def is_mock_mode(self) -> bool:
        """Returns True if running without Docker access (dev mode)."""
        return self._docker_client is None

    def set_alert_callback(self, callback: Callable[[str], Awaitable[None]]) -> None:
        """Set the callback function for sending Discord alerts."""
        self._send_alert = callback

    async def start(self) -> None:
        """Start the background monitoring loop."""
        if self._is_running:
            logger.warning("Monitor is already running")
            return

        self._is_running = True
        self._task = asyncio.create_task(self._polling_loop())
        logger.info(
            f"Plex monitor started (interval={self.poll_interval}s, "
            f"cooldown={self.alert_cooldown}s, mock={self.is_mock_mode})"
        )

    async def stop(self) -> None:
        """Stop the background monitoring loop."""
        self._is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Plex monitor stopped")

    async def _polling_loop(self) -> None:
        """Main polling loop that checks Plex health."""
        while self._is_running:
            try:
                is_healthy, error_msg = await self._check_plex_health()

                if is_healthy:
                    await self._handle_plex_up()
                else:
                    await self._handle_plex_down(error_msg)

            except Exception as e:
                logger.error(f"Error in polling loop: {e}")

            await asyncio.sleep(self.poll_interval)

    async def _check_plex_health(self) -> tuple[bool, Optional[str]]:
        """
        Check if Plex is responding.

        Returns:
            (is_healthy, error_message)
        """
        try:
            response = await asyncio.to_thread(
                requests.get,
                self.plex_url,
                timeout=10
            )

            if response.status_code == 200:
                return True, None
            elif response.status_code >= 500:
                return False, f"HTTP {response.status_code}"
            else:
                # 4xx errors might be auth issues, not necessarily "down"
                return True, None

        except requests.exceptions.Timeout:
            return False, "Connection timeout"
        except requests.exceptions.ConnectionError:
            return False, "Connection refused"
        except Exception as e:
            return False, str(e)

    async def _handle_plex_up(self) -> None:
        """Handle Plex being healthy - send recovery message if it was down."""
        if self._plex_was_down:
            self._plex_was_down = False
            logger.info("Plex has recovered")

            if self._send_alert:
                await self._send_alert(self._format_recovery_message())

    async def _handle_plex_down(self, error_msg: str) -> None:
        """Handle Plex being down - send alert if cooldown allows."""
        current_time = time.time()
        time_since_last_alert = current_time - self._last_alert_time

        # Only alert on state change OR if cooldown has passed
        should_alert = (
            not self._plex_was_down or
            time_since_last_alert >= self.alert_cooldown
        )

        if should_alert and self._send_alert:
            self._last_alert_time = current_time
            logs = self._get_container_logs()
            await self._send_alert(self._format_down_message(error_msg, logs))

        self._plex_was_down = True
        logger.warning(f"Plex is down: {error_msg}")

    def _get_container_logs(self, lines: int = 25) -> str:
        """
        Retrieve recent logs from the Plex Docker container.

        Returns mock message if Docker is not available.
        """
        if self._docker_client is None:
            return "[DEV MODE] Plex is down, but cannot fetch remote logs from local machine."

        try:
            container = self._docker_client.containers.get(self.container_name)
            logs = container.logs(tail=lines, stdout=True, stderr=True)

            if isinstance(logs, bytes):
                return logs.decode("utf-8", errors="replace")
            return str(logs)

        except docker.errors.NotFound:
            return f"[ERROR] Container '{self.container_name}' not found"
        except docker.errors.APIError as e:
            return f"[ERROR] Docker API error: {e}"
        except Exception as e:
            return f"[ERROR] Failed to fetch logs: {e}"

    def _format_down_message(self, error: str, logs: str) -> str:
        """Format the Plex down alert message."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Truncate logs if too long for Discord (max ~2000 chars in code block)
        max_log_length = 1500
        if len(logs) > max_log_length:
            logs = logs[-max_log_length:] + "\n... (truncated)"

        return (
            f"**Plex is Down!**\n"
            f"**Status:** {error}\n"
            f"**Time:** {timestamp}\n\n"
            f"**Recent Logs:**\n```\n{logs}\n```"
        )

    def _format_recovery_message(self) -> str:
        """Format the Plex recovery message."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"**Plex is Back Up!**\n**Time:** {timestamp}"

    async def check_status(self) -> dict:
        """
        Manual status check - returns current Plex health info.

        Returns dict with:
            - healthy: bool
            - error: Optional[str]
            - logs: str (if unhealthy or requested)
            - mock_mode: bool
        """
        is_healthy, error_msg = await self._check_plex_health()

        result = {
            "healthy": is_healthy,
            "error": error_msg,
            "mock_mode": self.is_mock_mode,
            "monitoring": self._is_running,
            "last_alert": (
                datetime.fromtimestamp(self._last_alert_time).strftime("%Y-%m-%d %H:%M:%S")
                if self._last_alert_time > 0
                else "Never"
            ),
        }

        # Include logs if unhealthy
        if not is_healthy:
            result["logs"] = self._get_container_logs()

        return result
