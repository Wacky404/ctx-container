# TODO: left off trying to get opencode to generate an AGENTS.md file for context priming on ctx command; can't figure out how to send down keys correctly!!
"""
ctx command line interface
"""
from pprint import pprint
from ctxflow.browsr import Browsr
from ctxflow.base import (
    TextualAppContext,
)
from ctxflow.__about__ import __application__, __version__
import rich_click
import click
from typing import Optional, Tuple, Any, Callable, TypeVar, List
import os
import sys
import subprocess
from subprocess import CompletedProcess, PIPE

import logging
from ctxflow.logger import setup_logging, logger
from ctxflow.utils import cmd_builder, initial

import pexpect


rich_click.rich_click.MAX_WIDTH = 100
rich_click.rich_click.STYLE_OPTION = "bold green"
rich_click.rich_click.STYLE_SWITCH = "bold blue"
rich_click.rich_click.STYLE_METAVAR = "bold red"
rich_click.rich_click.STYLE_HELPTEXT_FIRST_LINE = "bold blue"
rich_click.rich_click.STYLE_HELPTEXT = ""
rich_click.rich_click.STYLE_HEADER_TEXT = "bold green"
rich_click.rich_click.STYLE_OPTION_DEFAULT = "bold yellow"
rich_click.rich_click.STYLE_OPTION_HELP = ""
rich_click.rich_click.STYLE_ERRORS_SUGGESTION = "bold red"
rich_click.rich_click.STYLE_OPTIONS_TABLE_BOX = "SIMPLE_HEAVY"
rich_click.rich_click.STYLE_COMMANDS_TABLE_BOX = "SIMPLE_HEAVY"

# need to be made into enviroment vars with fallbacks
OC_ALIAS: str = "opencode"
CLD_ALIAS: str = "claude"
BS_ALIAS: str = "browsr"
GI_ALIAS: str = "gitingest"
OC_VERSION: str = str(subprocess.check_output(
    f"{OC_ALIAS} --version", shell=True, text=True)).strip()
AGENT_PREF: str = "opencode"
SCRIPT_DIR: str = os.path.dirname((os.path.abspath(__file__)))
F = TypeVar("F", bound=Callable[..., None])


def command_with_aliases(
        group: click.Group,
        *aliases: str,
        **command_kwargs: Any
) -> Callable[[F], F]:
    def decorator(f: F) -> F:
        cmd = click.command(**command_kwargs)(f)
        group.add_command(cmd)
        for alias in aliases:
            group.add_command(cmd, name=alias)
        return f
    return decorator


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name=__application__)
@click.pass_context
@click.option(
    "--log-lvl",
    default='WARNING',  # NOTSET=0, DEBUG=10, INFO=20, WARNING=30, ERROR=40, CRITICAL=50
    help='DEBUG: Detailed information for diagnosing problems | '

    'INFO: Confirmation that things are working | '

    'WARNING: Indication that something unexpected happened. Program still running | '

    'ERROR: Not able to perform some function of the program | '

    'CRITICAL: Serious error, program may be unable to continue running',
    type=click.STRING,
)
@click.option("--agent", default=AGENT_PREF, type=click.Choice(['opencode', 'claude']), help="choose the terminal agent you want to stage context for")
@click.option("--new-digest", default=False, is_flag=True, help="generate a new digest.txt file")
# TODO: Put my most used use-case here for very quick access
def ctx(cli_ctx: click.Context, log_lvl: str, agent: str, new_digest: bool) -> None:
    """
    CTXFLOW 💭 control the enviroment and context passed to your Terminal Agent
    """
    numeric_loglevel = getattr(logging, log_lvl)
    if isinstance(numeric_loglevel, int):
        setup_logging(numeric_loglevel)
    else:
        setup_logging(log_lvl_stdout=TextualAppContext().loglvl)

    cwd: str = os.getcwd()
    if new_digest:
        # if flag enabled this will only update a digest and exit
        click.echo("updating the git digest file...")
        for root, dirs, files in os.walk(cwd):
            for name in files:
                if name == 'digest.txt':
                    cmd: str = cmd_builder(
                        prog=GI_ALIAS,
                        cmds=tuple("."),
                        flags={
                            "--output": os.path.join(root, name)},
                        exclude_logs=True,
                    )
                    with subprocess.Popen(cmd, stderr=PIPE, shell=True) as proc:
                        if proc.stderr is not None:
                            for line in proc.stderr:
                                # logging as debug for now
                                logger.debug(line.strip())
                    return

    cpydocs: tuple[tuple[str, str], ...] = (
        (os.path.join(SCRIPT_DIR, 'prompts', 'agentic', 'CtxPrime.md'),
         os.path.join(cwd, 'ai_docs', 'agent', 'AgentPrime.md')),
        (os.path.join(SCRIPT_DIR, 'prompts', 'protocol', 'SharedProtocol.md'),
         os.path.join(cwd, 'ai_docs', 'protocol', 'SharedProtocol.md')),
        (os.path.join(SCRIPT_DIR, 'prompts', 'OrchCtxPrime.md'),
         os.path.join(cwd, 'ai_docs', 'OrchCtxPrime.md')),
        (os.path.join(SCRIPT_DIR, 'prompts', 'user', 'TEST_SCENARIOS.md'),
         os.path.join(cwd, 'ai_docs', 'EXAMPLE_SCENARIOS.md')),
    )

    click.echo("Creating the necessary directories...")
    initial(cpyf=cpydocs)

    cli_ctx.ensure_object(dict)
    cli_ctx.obj['ctx'] = {
        "flags": {"--log-lvl": log_lvl, "--agent": agent},
        "args": {},
        "commands": {
            "browsr": {},
            "opencode": {},
            "gitingest": {},
        }
    }

    if cli_ctx.invoked_subcommand is None:
        # starting up gitingest, for proj indexing and priming
        click.echo("Making a git digest file...")
        cmd = cmd_builder(
            prog=GI_ALIAS,
            cmds=tuple("."),
            flags={"--output": os.path.join(cwd, 'ai_docs', 'digest.txt')},
            exclude_logs=True,
        )
        with subprocess.Popen(cmd, stderr=PIPE, shell=True) as proc:
            if proc.stderr is not None:
                for line in proc.stderr:
                    # logging as debug for now
                    logger.debug(line.strip())
        click.echo("Initialization complete!")

        # chcmd: str = cmd_builder(
        #    prog=OC_ALIAS if agent == 'opencode' else CLD_ALIAS,
        #    cmds=None,
        #    exclude_logs=True,
        # )
        # ctrl+x i -> \x18 i
        # pattern = "enter"
        # exit_pattern = "Created Agents.md"
        # with pexpect.spawn(chcmd, encoding='utf-8') as child:
        #    # child.logfile = sys.stdout
        #    click.echo("spawned opencode...")
        #    # giving it 30sec but this might be to short for big projects...we'll see
        #    child.timeout = 30
        #    child.expect(pattern)
        #    child.sendcontrol("x")
        #    child.send('i')
        #    logger.info("pressed key combo for /init")
        #    while True:
        #        try:
        #            l = child.readline()
        #            if not l or exit_pattern.lower() == l.lower():
        #                logger.info("Agents.md created...exiting process")
        #                child.terminate()
        #                break
        #        except pexpect.exceptions.EOF as e:
        #            logger.exception(
        #                f"An exception of type {type(e).__name__} occurred. Details: {str(e)}")
        #            child.terminate()
        #            break
        #        except pexpect.exceptions.TIMEOUT as e:
        #            logger.exception(
        #                f"An exception of type {type(e).__name__} occurred. Details: {str(e)}")
        #            child.terminate()
        #            break


@ctx.command(name="browsr", cls=rich_click.rich_command.RichCommand)
@click.argument("path", default=".", required=False, type=click.Path(exists=True),  metavar="PATH_BROWSR")
@click.option("-f", "--file", multiple=True, type=click.Path(exists=True), help="Pass through individual file paths you want as context")
@click.option("-d", "--directory", multiple=True, type=click.Path(exists=True), help="Pass through individual directory paths you want as context")
@click.option(
    "-l",
    "--max-lines",
    default=1000,
    show_default=True,
    type=int,
    help="Maximum number of lines to display in the code browser",
    envvar="BROWSR_MAX_LINES",
    show_envvar=True,


)
@click.option(
    "-m",
    "--max-file-size",
    default=20,
    show_default=True,
    type=int,
    help="Maximum file size in MB for the application to open",
    envvar="BROWSR_MAX_FILE_SIZE",
    show_envvar=True,
)
@click.version_option(version=__version__, prog_name=__application__)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable extra debugging output",
    type=click.BOOL,
    envvar="BROWSR_DEBUG",
    show_envvar=True,
)
@click.option(
    "-k",
    "--kwargs",
    multiple=True,
    help="Key=Value pairs to pass to the filesystem",
    envvar="BROWSR_KWARGS",
    show_envvar=True,
)
@click.option(
    "--all-files",
    default=False,
    help="Select all files and sub-directories in a directory",
    is_flag=True,
)
@click.option(
    "--work-tree",
    default=False,
    help="create a new work-tree using git",
    is_flag=True,
)
@click.pass_context
def browsr(
        cli_ctx: click.Context,
        path: Optional[str],
        file: List[str],
        directory: List[str],
        debug: bool,
        max_lines: int,
        max_file_size: int,
        kwargs: Tuple[str, ...],
        all_files: bool,
        work_tree: bool,
) -> None:
    """
    🗂️ control the enviroment and view the context passed to Terminal Agent.

    Navigate through directories and select files whether they're hosted locally,
    over SSH, in GitHub, AWS S3, Google Cloud Storage, or Azure Blob Storage.
    View code files with syntax highlighting, format JSON files, render images,
    convert data files to navigable datatables, and more.

    \f

    ![browsr](https://raw.githubusercontent.com/juftin/browsr/main/docs/_static/screenshot_utils.png)

    ## Installation

    It's recommended to install **`ctx`** via [pipx](https://pypa.github.io/pipx/)
    with **`all`** optional dependencies, this enables **`ctx browsr`** to access
    remote cloud storage buckets and open parquet files.

    ```shell
    pipx install "ctx[all]"
    ```

    ## Usage Examples

    ### Local

    #### Browse your current working directory

    ```shell
    ctx browsr
    ```

    #### Browse a local directory

    ```shell
    ctx brosr /path/to/directory
    ```

    ### Cloud Storage

    #### Browse an S3 bucket

    ```shell
    ctx browsr s3://bucket-name
    ```

    #### Browse a GCS bucket

    ```shell
    ctx browsr gs://bucket-name
    ```

    #### Browse Azure Services

    ```shell
    ctx browsr adl://bucket-name
    ctx browsr az://bucket-name
    ```

    #### Pass Extra Arguments to Cloud Storage

    Some cloud storage providers require extra arguments to be passed to the
    filesystem. For example, to browse an anonymous S3 bucket, you need to pass
    the `anon=True` argument to the filesystem. This can be done with the `-k/--kwargs`
    argument.

    ```shell
    ctx browsr s3://anonymous-bucket -k anon=True
    ```

    ### GitHub

    #### Browse a GitHub repository

    ```shell
    ctx browsr github://juftin:browsr
    ```

    #### Browse a GitHub Repository Branch

    ```shell
    ctx browsr github://juftin:browsr@main
    ```

    #### Browse a Private GitHub Repository

    ```shell
    export GITHUB_TOKEN="ghp_1234567890"
    ctx browsr github://Wacky404:ctx-container-private@main
    ```

    #### Browse a GitHub Repository Subdirectory

    ```shell
    ctx browsr github://Wacky404:ctx-container@main/tests
    ```

    #### Browse a GitHub URL

    ```shell
    ctx browsr https://github.com/Wacky404/ctx-container
    ```

    #### Browse a Filesystem over SSH

    ```
    ctx browsr ssh://user@host:22
    ```

    #### Browse a SFTP Server

    ```
    ctx browsr sftp://user@host:22/path/to/directory
    ```

    ## Key Bindings
    - **`Q`** - Exit the application
    - **`F`** - Toggle the file tree sidebar
    - **`T`** - Toggle the rich theme for code formatting
    - **`N`** - Toggle line numbers for code formatting
    - **`D`** - Toggle dark mode for the application
    - **`.`** - Parent Directory - go up one directory
    - **`R`** - Reload the current directory
    - **`C`** - Copy the current file or directory path to the clipboard
    - **`X`** - Download the file from cloud storage
    - **`S`** - Toggle Select a directory/file to be added to list
    - **`O`** - Launch Agent
    """
    cli_ctx.obj['ctx']['commands']['browsr']['args'] = {"path": path}
    cli_ctx.obj['ctx']['commands']['browsr']['flags'] = {
        "--file": file,
        "--directory": directory,
        "--max-lines": max_lines,
        "--max-file-size": max_file_size,
        "--debug": debug,
    }
    if all_files:
        click.echo("This is going to grab all files")
    elif file or directory:
        click.echo("File(s) to be passed into context")
        grp: List[str] = file + directory
        for y in grp:
            click.echo(f"- {y}")
    elif work_tree:
        click.echo("create a git worktree")
    else:
        extra_kwargs = {}
        if kwargs:
            for kwarg in kwargs:
                try:
                    key, value = kwarg.split("=")
                    extra_kwargs[key] = value
                except ValueError as ve:
                    raise click.BadParameter(
                        message=(
                            f"Invalid Key/Value pair: `{kwarg}` "
                            "- must be in the format Key=Value"
                        ),
                        param_hint="kwargs",
                    ) from ve
        file_path = path or os.getcwd()
        config = TextualAppContext(
            file_path=file_path,
            debug=debug,
            max_file_size=max_file_size,
            max_lines=max_lines,
            kwargs=extra_kwargs,
        )
        app = Browsr(config_object=config)
        app.run()


@ctx.group(invoke_without_command=True)
@click.version_option(version=OC_VERSION, prog_name="opencode")
@click.pass_context
def opencode(cli_ctx: click.Context) -> None:
    """
    🤖 wrapper around opencode cli\n

    Commands:\n
        ctx opencode [project]         start opencode TUI\n
        ctx opencode run [message..]   Run opencode with a message\n
        ctx opencode auth              Manage credentials\n
        ctx opencode upgrade [target]  upgrade opencode to the latest version or a specific version\n

    Positionals:\n
        project: path to start opencode in
    """
    # TODO: SET cwd= TO whatever I want from ctx; cli_ctx
    if cli_ctx.invoked_subcommand is None:
        cmd: str = cmd_builder(prog=OC_ALIAS, cmds=tuple("."))
        with subprocess.Popen(cmd, stderr=PIPE, shell=True) as proc:
            if proc.stderr is not None:
                for line in proc.stderr:
                    # logging as debug for now
                    logger.debug(line.strip())


@opencode.command(name="run", cls=rich_click.rich_command.RichCommand)
@click.argument("message", default=None, required=True, metavar="message")
@click.version_option(version=OC_VERSION, prog_name="opencode")
@click.option("-c", "--continue", "cont", is_flag=True, help="Continue the last session")
@click.option("-s", "--session", type=click.STRING, help="Session ID to continue")
@click.option("--share", is_flag=True, help="Share the session")
@click.option("-m", "--model", type=click.STRING, help="Model to be used in the format of provider/model")
@click.pass_context
def run(cli_ctx: click.Context,
        message: str,
        cont: bool,
        session: str,
        share: bool,
        model: str,
        ) -> None:
    """
    Run opencode with a message\n

    Positionals:\n
        message: message to send
    """
    cli_ctx.obj['ctx']['commands']['opencode']['commands'] = {
        "run": {
            "args": {'message': message},
            "flags": {
                "--continue": cont,
                "--session": session,
                "--share": share,
                "--model": model,
            },
        }
    }
    click.echo(type(cli_ctx.obj))
    pprint(cli_ctx.obj)
    if message == "" or message == " ":
        logger.critical(
            f"run requires positional arg: ctx opencode run [message]")
        cli_ctx.exit(code=1)

    cmd: str = cmd_builder(
        prog=OC_ALIAS,
        cmds=("run", message),
        flags=cli_ctx.obj['ctx']['commands']['opencode']['commands']['run']['flags'],
        exclude_logs=True,
    )
    with subprocess.Popen(cmd, stderr=PIPE, shell=True) as proc:
        if proc.stderr is not None:
            # for some reason "opencode run" ouput
            # is coming for descriptor stderr
            # can't run --print--logs in tandem
            for line in proc.stderr:
                click.echo(line.strip())


@opencode.group(invoke_without_command=False)
@click.version_option(version=OC_VERSION, prog_name="opencode")
@click.pass_context
def auth(cli_ctx: click.Context) -> None:
    """
    Manage credentials\n

    Commands:\n
        ctx opencode auth login   login to a provider\n
        ctx opencode auth logout  logout from a configured provider\n
        ctx opencode auth list    list providers
    """
    if cli_ctx.invoked_subcommand is None:
        click.echo(ctx.get_help(cli_ctx))


@auth.command(name="login", cls=rich_click.rich_command.RichCommand)
@click.pass_context
def login(cli_ctx: click.Context) -> None:
    """ login to a provider """
    cmd: str = cmd_builder(prog=OC_ALIAS, cmds=("auth", "login"))
    with subprocess.Popen(cmd, stderr=PIPE, shell=True) as proc:
        if proc.stderr is not None:
            for line in proc.stderr:
                # logging as debug for now
                logger.debug(line.strip())


@auth.command(name="logout", cls=rich_click.rich_command.RichCommand)
@click.pass_context
def logout(cli_ctx: click.Context) -> None:
    """ logout from a configured provider """
    cmd: str = cmd_builder(prog=OC_ALIAS, cmds=("auth", "logout"))
    with subprocess.Popen(cmd, stderr=PIPE, shell=True) as proc:
        if proc.stderr is not None:
            for line in proc.stderr:
                # logging as debug for now
                logger.debug(line.strip())


@command_with_aliases(auth, "ls", name="list", cls=rich_click.rich_command.RichCommand)
@click.pass_context
def list(cli_ctx: click.Context) -> None:
    """ list providers """
    cmd: str = cmd_builder(prog=OC_ALIAS, cmds=("auth", "list"))
    with subprocess.Popen(cmd, stderr=PIPE, shell=True) as proc:
        if proc.stderr is not None:
            for line in proc.stderr:
                # logging as debug for now
                logger.debug(line.strip())


@opencode.command(name="upgrade", cls=rich_click.rich_command.RichCommand)
@click.argument("target", default=None, required=False, metavar="target", type=click.STRING)
@click.pass_context
def upgrade(cli_ctx: click.Context, target: str) -> None:
    """
    upgrade opencode to the latest version or a specific version\n

    Positionals:\n
        target:  specific version to upgrade to (e.g., '0.1.48' or 'v0.1.48')
    """
    cli_ctx.obj['ctx']['commands']['opencode']['commands'] = {
        "upgrade": {
            "args": {"target": target},
            "flags": {},
        },
    }
    cmd: str = cmd_builder(prog=OC_ALIAS, cmds=(
        "upgrade", f"{target}") if target else tuple("upgrade"))
    with subprocess.Popen(cmd, stderr=PIPE, shell=True) as proc:
        if proc.stderr is not None:
            for line in proc.stderr:
                # logging as debug for now
                logger.debug(line.strip())


@ctx.command(name="gitingest", cls=rich_click.rich_command.RichCommand)
@click.argument("dir_path", default=".", required=False, type=click.Path(exists=True), metavar="PATH_GITINGEST")
@click.option("-o", "--output", type=click.STRING, help="output file path (default: digest.txt in current directory)")
@click.option("-s", "--max-size", type=click.INT, help="maximum file size to process in bytes")
@click.option("-e", "--exclude-pattern", type=click.STRING, help="patterns to exclude. handles python's arbitrary subset of unix shell-style wildcards. see: https://docs.python.org/3/library/fnmatch.html")
@click.option("-i", "--include-pattern", type=click.STRING, help="patterns to include. handles python's arbitrary subset of unix shell-style wildcards. see: https://docs.python.org/3/library/fnmatch.html")
@click.option("-b", "--branch", type=click.STRING, help="branch to clone and ingest")
@click.option("--include-gitignored", is_flag=True, help="include files matched by .gitignore")
@click.pass_context
def gitingest(
    cli_ctx: click.Context,
    dir_path: str,
    output: str,
    max_size: int,
    exclude_pattern: str,
    include_pattern: str,
    branch: str,
    include_gitignored: bool,
) -> None:
    """
    👨‍🍳 wrapper around gitingest cli\n

    Commands:\n
        ctx gitingest [/path/to/directory]          basic usage (writes to digest.txt by default)\n
        ctx gitingest [github url]                  from url\n
        ctx gitingest [github url/subdirectory]     or from specific subdirectory\n

    Positionals:\n
        path: path to digest
    """
    cli_ctx.obj['gitingest'] = {
        "--output": output,
        "--max-size": max_size,
        "--exclude-pattern": exclude_pattern,
        "--include-pattern": include_pattern,
        "--branch": branch,
        "--include-gitignored": include_gitignored
    }
    cmd: str = cmd_builder(
        prog=GI_ALIAS,
        cmds=tuple(dir_path),
        flags=cli_ctx.obj['gitingest'],
        exclude_logs=True
    )
    with subprocess.Popen(cmd, stderr=PIPE, shell=True) as proc:
        if proc.stderr is not None:
            for line in proc.stderr:
                # logging as debug for now
                logger.debug(line.strip())


if __name__ == "__main__":
    ctx()
