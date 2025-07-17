"""
runner.py allows for easy process handling of CLI Terminal Agent Programs.
Easily manage running processes and trigger voice events.
See https://docs.python.org/3/library/subprocess.html for subprocess docs
See https://docs.python.org/3/library/threading.html for threading docs
"""
import subprocess
import signal
import sys
import os
import threading
import time
import fcntl
import psutil
import random
from concurrent.futures import ThreadPoolExecutor, Future
from subprocess import Popen, PIPE, CompletedProcess
from typing import Tuple, Any, Optional
from ctxflow.logger import logger
from pathlib import Path


_SUCCEED: int = 0
_FAIL: int = 1
_VOICE_ENTRY: str = 'entry'
_VOICE_EXIT: str = 'exit'


class TerminalAgentRunner:
    """ Allows for ease of use when running terminal agents. """

    def __init__(self, agent_alias: str, cmd: str, workers: int = 1):
        self._tts_executor: ThreadPoolExecutor = ThreadPoolExecutor(
            max_workers=workers, thread_name_prefix="tts")
        self._should_stop: threading.Event = threading.Event()
        self._start_time: float = 0.00
        self._end_time: float = 0.00
        self.proc: Optional[Popen[Any]] = None
        self.alias: str = agent_alias
        self.cmd: str = cmd

    def get_message(self, vtype: str) -> str:
        """
        Returns messages that make for a personalized experience
        while using ctxflow. There are entry messages, exit messages,
        and custom messages that can be passed through to generate an
        AI voice.
        """
        if vtype == "entry":
            # list of messages that can be played upon entry;
            # randomized and not repetitive
            entry_messages = [
                "Another day another codebase to conquer Ready to ship some quality commits",
                "Back in the terminal where we belong Time to turn coffee into code",
                "Alright hotshot lets see what architectural masterpiece we're building today",
                "Terminal is booted brain is caffeinated Lets make something that doesnt break in production",
                "Welcome back to the command line where real programmers thrive",
                "Ready to debug the world one elegant solution at a time",
                "Firing up the dev environment Hope you brought your A-game today",
                "Another sprint another chance to write code that future you will actually thank you for",
                "Terminal agent reporting for duty Lets turn those feature requests into reality",
                "Back to the grind Time to prove why they pay us the big bucks",
                "Vim is loaded stack overflow is bookmarked Lets write some legendary code",
                "Time to make the rubber duck proud with some clean readable solutions",
                "Ready to refactor the world one function at a time",
                "Booting up another session of architectural wizardry and caffeine dependency",
                "Welcome to the danger zone where semicolons matter and whitespace has opinions",
                "Another day dodging memory leaks and hunting down those sneaky race conditions",
                "Locked and loaded with fresh ideas and a full pot of coffee",
                "Time to turn those product requirements into something that actually compiles",
                "Ready to write code so clean it makes the linter weep tears of joy",
                "Welcome back to the trenches where tabs vs spaces wars are still being fought"
            ]
            return random.choice(entry_messages)

        elif vtype == "exit":
            # list of messages that can be played upon exit;
            # randomized and not repetitive
            exit_messages = [
                "Session terminated successfully No segfaults detected today",
                "Logging off before the code reviews pile up See you in the next commit",
                "Another productive session in the books Time to push to main and call it a day",
                "Exit code 0 Clean shutdown complete Go grab that well deserved coffee",
                "Disconnecting from the matrix Remember to actually test your code this time",
                "Session ended gracefully Unlike that last merge conflict we dont talk about",
                "Shutting down dev environment Hope you remembered to save your work",
                "Terminal agent going offline May your builds be fast and your bugs be obvious",
                "Signing off Time to let the CI pipeline do its thing",
                "Peace out coder May your documentation be clear and your deadlines be reasonable",
                "Closing all processes No orphaned threads left behind this time",
                "Git add git commit git push git home",
                "Session complete Time to let the code monkeys take over for testing",
                "Powering down May your next compilation be faster than your last",
                "Signing off before the rubber duck starts questioning our life choices",
                "Terminal session ended May your stack traces be short and your logs be verbose",
                "Logging out Remember the first rule of programming It works on my machine",
                "Session terminated Time to go pretend we understand what the frontend team is doing",
                "Shutting down gracefully Unlike that database connection we forgot about last week",
                "Till next time May your code be bug free and your coffee be strong",
                "See you space cowboy",
            ]
            return random.choice(exit_messages)

        # custom message; just return it back
        return vtype

    def _get_tts_script_path(self) -> Optional[str]:
        """
        Determine which TTS script to use based on available API keys.
        For now its just elevenlabs
        """
        script_dir: Path = Path(__file__).parent
        tts_dir: Path = script_dir / "claude" / "hooks" / "utils" / "tts"
        logger.debug(f"This is the TTS directory: {tts_dir}")

        if os.getenv('ELEVENLABS_API_KEY'):
            logger.debug(f"Found: ELEVENLABS_***_***")
            elevenlabs_script = tts_dir / "elevenlabs_tts.py"
            if elevenlabs_script.exists():
                return str(elevenlabs_script)

        return None

    def play_voice(self, message_type: str) -> None:
        """
        Announce subagent completion available TTS service.
        This process will only trigger once, if multiple events
        are triggered sequentially or within a already running
        process.
        """
        future: Future[Any] = self._tts_executor.submit(
            self._play_voice_worker, message_type)
        future.add_done_callback(self._tts_completion_callback)

        # testing out threadpool implementation
        # Run in a separate thread to avoid blocking
        # thread = threading.Thread(
        #     target=self._play_voice_worker,
        #     args=(message_type,),
        #     daemon=True  # Dies when main program exits
        # )
        # thread.start()

    def _tts_completion_callback(self, future: Future[Any]) -> None:
        """ Called when TTS completes; logging/information purposes. """
        try:
            future.result()
            logger.debug(f"TTS task completed in the background")
        except Exception as e:
            logger.exception(f"TTS task failed: {e}")

    def _play_voice_worker(self, message_type: str) -> None:
        """
        Worker method that runs in a separate thread.
        Experimenting with threading voice output process,
        slowed startup and close.
        """
        lock_path: str = os.path.join("/tmp", "play_voice.lock")
        logger.debug(f"Lock path: {lock_path}")

        # Check if lock file exists and if the process is still running
        if os.path.exists(lock_path):
            try:
                with open(lock_path, 'r') as f:
                    old_pid = int(f.read().strip())

                # Check if process is still running
                if psutil.pid_exists(old_pid):
                    logger.debug(
                        f"TTS already running (PID {old_pid}) - skipping")
                    return
                else:
                    logger.debug(
                        f"Stale lock file found (PID {old_pid} no longer exists) - removing")
                    os.remove(lock_path)
            except (ValueError, FileNotFoundError):
                logger.debug("Invalid lock file found - removing")
                try:
                    os.remove(lock_path)
                except FileNotFoundError:
                    pass

        try:
            with open(lock_path, 'x') as lock_file:
                lock_file.write(str(os.getpid()))
                lock_file.flush()

                logger.debug("Lock file created and is open")
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                logger.debug("File lock acquired")

                tts_script: str | None = self._get_tts_script_path()
                if not tts_script:
                    logger.debug("No TTS script found")
                    return

                completion_message: str = self.get_message(vtype=message_type)
                logger.debug(f"Path to TTS Script: {tts_script}")
                logger.debug(f"Completion message: {completion_message}")

                cmd = ["uv", "run", tts_script, completion_message]
                logger.debug(f"Running command: {cmd}")

                result: CompletedProcess[Any] = subprocess.run(
                    cmd,
                    capture_output=True,
                    timeout=10,
                    check=True
                )
                if result.returncode == _SUCCEED:
                    logger.debug("TTS completed successfully")
                else:
                    logger.error(f"TTS failed: {result.stderr}")

            # okay so this automatically happens when exiting with,
            # but to be explicit...
            if os.path.exists(lock_path):
                os.remove(lock_path)
                logger.debug("Lock file removed")

        except subprocess.TimeoutExpired as e:
            logger.error(f"Subprocess timed out: {e}")
            self._cleanup_lock_file(lock_path)
            return

        except subprocess.CalledProcessError as e:
            logger.error(f"Subprocess failed with return code {e.returncode}")
            logger.error(f"Command: {e.cmd}")
            logger.error(f"Stdout: {e.stdout}")
            logger.error(f"Stderr: {e.stderr}")
            self._cleanup_lock_file(lock_path)
            return

        except subprocess.SubprocessError as e:
            logger.error(f"Subprocess error: {e}")
            self._cleanup_lock_file(lock_path)
            return

        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            self._cleanup_lock_file(lock_path)
            return

        except BlockingIOError:
            logger.debug("Could not acquire lock, another process is running")
            return

        except FileExistsError:
            logger.debug(
                "Lock file already exists, TTS already in progress - skipping")
            return

        except Exception as e:
            logger.exception(f"Unexpected error in TTS worker: {e}")
            self._cleanup_lock_file(lock_path)
            return

    def _cleanup_lock_file(self, lock_path: str) -> None:
        """ helper to safely clean up the lock file. """
        try:
            if os.path.exists(lock_path):
                os.remove(lock_path)
                logger.debug(f"Cleaned up lock file: {lock_path}")
        except FileNotFoundError:
            pass  # more than likely removed by another process
        except Exception as e:
            logger.warning(f"Failed to cleanup lock file {lock_path}: {e}")

    def _stream_stderr_to_logs(self) -> None:
        """ Allows for streaming of stderr messages to logs. """
        try:
            if self.proc and self.proc.stderr is not None:
                for line in self.proc.stderr:
                    if self._should_stop.is_set():
                        break
                    if line.strip():
                        logger.debug(f"[{self.alias} STDERR] {line.rstrip()}")
            else:
                logger.error(f"Terminal agent process is not running")
        except Exception as e:
            logger.exception(f"Error occured streaming agent stderr: {e}")

    def run(self) -> int:
        """
        Function that handles process spawning and voice events for entry and
        exit of CLI Terminal Agents.
        """

        def signal_handler(signum, frame):
            logger.debug("User interrupted the terminal agent session.")
            self.stop()
            sys.exit(_SUCCEED)

        signal.signal(signalnum=signal.SIGINT, handler=signal_handler)
        try:
            logger.debug(f"Starting terminal agent: {self.cmd}")
            self.play_voice(message_type=_VOICE_ENTRY)

            self._start_time = time.time()
            self.proc = Popen(
                self.cmd,
                stderr=PIPE,
                shell=True,
                text=True,
                bufsize=1
            )

            logger.debug(f"Agent started with PID: {self.proc.pid}")
            stderr_thread: threading.Thread = threading.Thread(
                target=self._stream_stderr_to_logs)
            stderr_thread.daemon = True
            stderr_thread.start()

            return_code: int = self.proc.wait()

            if return_code == _SUCCEED:
                self._end_time = time.time()
                logger.debug("Agent session completed successfully")
                self.play_voice(message_type=_VOICE_EXIT)
            else:
                self._end_time = time.time()
                logger.warning(f"Agent session ended with code: {return_code}")
                engineer_name = os.getenv("ENGINEER_NAME", "").strip()
                if engineer_name:
                    self.play_voice(
                        message_type="{engineer_name}, looks like your agent crashed")
                else:
                    self.play_voice(
                        message_type="Looks like your agent crashed")

            elasped_time: str = '{0:.2f}'.format(
                (self._end_time - self._start_time) / 60)
            logger.info(
                f"Terminal Agent session duration: {elasped_time} minutes")

            return _SUCCEED

        except KeyboardInterrupt:
            logger.debug("Agent session interrupted by user")
            self.play_voice(message_type=_VOICE_EXIT)
            # I keyboard InterruptedError most of the time, so this would more likely be a success
            return _SUCCEED
        except Exception as e:
            logger.exception(f"Error running agent: {e}")
            engineer_name = os.getenv("ENGINEER_NAME", "").strip()
            if engineer_name:
                self.play_voice(
                    message_type="{engineer_name}, looks like your agent crashed")
            else:
                self.play_voice(
                    message_type="Looks like your agent crashed")

            return _FAIL

        finally:
            self._cleanup()

    def stop(self) -> None:
        """
        Graceful stop of Terminal Agent process.
        Terminates the child process and ensure that it is closed,
        and stops thread(s) from blocking.
        """
        if self.proc and self.proc.poll() is None:
            logger.debug("Terminating terminal agent process...")
            self.proc.terminate()
            self.proc.wait()
        self._should_stop.set()

    def _cleanup(self) -> None:
        """
        `Cleans` up after terminal agent program.
        Ensure that any tmp files, pipes, etc are closed.
        Just making sure stderr is closed for now.
        """
        logger.debug("Cleaning up agent session...")
        if self.proc and self.proc.stderr:
            self.proc.stderr.close()

        logger.debug("Shutting down TTS thread pool...")
        # don't wait for it to complete
        self._tts_executor.shutdown(wait=False)
        logger.debug("TTS thread pool shutdown initiated")
