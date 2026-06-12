import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import time

from opensnake.config import PID_PATH, SOCKET_PATH, TIMEOUT_MS

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("opensnake")


class Daemon:
    def __init__(self) -> None:
        self._running = False
        self._start_time: float | None = None
        self._server: asyncio.AbstractServer | None = None
        self._game_proc: subprocess.Popen[bytes] | None = None

    def _write_pid(self) -> None:
        PID_PATH.parent.mkdir(parents=True, exist_ok=True)
        PID_PATH.write_text(str(os.getpid()))

    def _remove_pid(self) -> None:
        try:
            PID_PATH.unlink(missing_ok=True)
        except Exception:
            pass

    @staticmethod
    def is_running() -> bool:
        if not PID_PATH.exists():
            return False
        try:
            pid = int(PID_PATH.read_text().strip())
            os.kill(pid, 0)
            return True
        except (ValueError, OSError, ProcessLookupError):
            PID_PATH.unlink(missing_ok=True)
            return False

    async def _handle(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        try:
            data = await asyncio.wait_for(reader.readline(), timeout=10)
            if not data:
                return
            msg = json.loads(data.decode().strip())
            action = msg.get("action")
            if action == "start":
                if self._running:
                    writer.write(b'{"status":"ok"}\n')
                    await writer.drain()
                    return
                logger.info("start")
                self._start_time = time.monotonic()
                self._running = True
                self._launch_game()
                writer.write(b'{"status":"ok"}\n')
            elif action == "stop":
                logger.info("stop")
                self._running = False
                self._start_time = None
                self._kill_game()
                writer.write(b'{"status":"ok"}\n')
            elif action == "ping":
                writer.write(b'{"status":"ok"}\n')
            else:
                writer.write(b'{"status":"error","reason":"unknown_action"}\n')
            await writer.drain()
        except Exception:
            logger.exception("handle error")
        finally:
            writer.close()

    def _launch_game(self) -> None:
        self._kill_game()
        self._game_proc = subprocess.Popen(
            [sys.executable, "-m", "opensnake", "once"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _kill_game(self) -> None:
        if self._game_proc:
            try:
                self._game_proc.terminate()
                self._game_proc.wait(timeout=3)
            except Exception:
                try:
                    self._game_proc.kill()
                except Exception:
                    pass
            self._game_proc = None

    async def _timeout_check(self) -> None:
        while True:
            await asyncio.sleep(5)
            if self._running and self._start_time is not None:
                elapsed = (time.monotonic() - self._start_time) * 1000
                if elapsed > TIMEOUT_MS:
                    logger.info("timeout — auto-stopping")
                    self._running = False
                    self._start_time = None
                    self._kill_game()

    async def run(self) -> None:
        SOCKET_PATH.parent.mkdir(parents=True, exist_ok=True)
        if SOCKET_PATH.exists():
            SOCKET_PATH.unlink()

        self._write_pid()

        self._server = await asyncio.start_unix_server(
            self._handle, path=str(SOCKET_PATH)
        )

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._shutdown)

        async with self._server:
            logger.info(f"daemon ready at {SOCKET_PATH}")
            await asyncio.gather(
                self._server.serve_forever(),
                self._timeout_check(),
            )

    def _shutdown(self) -> None:
        self._remove_pid()
        if self._server:
            self._server.close()
        sys.exit(0)


def run_daemon() -> None:
    if Daemon.is_running():
        logger.info("daemon already running")
        return
    daemon = Daemon()
    asyncio.run(daemon.run())
