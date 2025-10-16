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
import shutil
import subprocess
from subprocess import PIPE
from InquirerPy import inquirer, prompt

import logging
from ctxflow.runner import TerminalAgentRunner
from ctxflow.logger import setup_logging, logger
from ctxflow.utils import cmd_builder, initial


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
# end

OC_VERSION: str = str(subprocess.check_output(
    f"{OC_ALIAS} --version", shell=True, text=True)).strip()
AGENT_PREF: str = "claude"
SCRIPT_DIR: str = os.path.dirname((os.path.abspath(__file__)))
HOME_DIR: str = os.path.expanduser("~")
F = TypeVar("F", bound=Callable[..., None])

SUCCEED = 0
FAIL = 1


def get_ctxflow_logo(pad: str = "", fallback: bool = False, max_width: Optional[int] = None) -> str:
    """
    Generate CTXFLOW ASCII art logo string

    Args:
        pad: String to prepend to each line (e.g., "  " for indentation)
        fallback: Force ASCII-only characters
        max_width: Force fallback if terminal is narrower than this

    Returns:
        String containing the logo
    """

    LOGO_UNICODE = [
        [" ██████╗████████╗██╗  ██╗", "███████╗██╗      ██████╗ ██╗    ██╗"],
        ["██╔════╝╚══██╔══╝╚██╗██╔╝", "██╔════╝██║     ██╔═══██╗██║    ██║"],
        ["██║        ██║    ╚███╔╝ ", "█████╗  ██║     ██║   ██║██║ █╗ ██║"],
        ["██║        ██║    ██╔██╗ ", "██╔══╝  ██║     ██║   ██║██║███╗██║"],
        ["╚██████╗   ██║   ██╔╝ ██╗", "██║     ███████╗╚██████╔╝╚███╔███╔╝"],
        [" ╚═════╝   ╚═╝   ╚═╝  ╚═╝", "╚═╝     ╚══════╝ ╚═════╝  ╚══╝╚══╝"],
    ]

    LOGO_ASCII = [
        [" ######  ########  #    #", "#######  #        ######  #    # "],
        ["#       #  ##  # # #  # ", "#        #       #    #   #    # "],
        ["#          ##     ###   ", "#####    #       #    #   # ## # "],
        ["#          ##    # ##   ", "#        #       #    #   ######"],
        ["######     ##   #    #  ", "#        ####### ######  #    # "],
        [" ######    ##   #    #  ", "#        ####### ######  #    # "],
    ]

    term_width = shutil.get_terminal_size().columns
    use_fallback = fallback
    if max_width and term_width < max_width:
        use_fallback = True

    if not use_fallback:
        encoding = sys.stdout.encoding
        term = os.environ.get('TERM', '')

        unicode_supported = (
            encoding and 'utf' in encoding.lower()
        ) or any(x in term for x in ['xterm', 'screen', 'tmux'])

        if not unicode_supported:
            use_fallback = True

    if term_width < 40:
        return f"{pad}CTXFLOW - Context Flow Management"

    logo_data = LOGO_ASCII if use_fallback else LOGO_UNICODE
    supports_color = (
        hasattr(sys.stdout, 'isatty') and
        sys.stdout.isatty() and
        os.environ.get('TERM') != 'dumb'
    )

    result = []
    for row in logo_data:
        if pad:
            result.append(pad)

        if supports_color:
            # First part in gray, second part normal
            # result.append("\x1b[90m")  # Gray
            result.append("\x1b[32m")  # Green
            result.append(row[0])
            result.append("\x1b[0m")   # Reset
            result.append(row[1])
        else:
            # No color - just concatenate
            result.append(row[0] + row[1])

        result.append("\n")

    return "".join(result).rstrip()


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


@click.group(invoke_without_command=True, help=f"{get_ctxflow_logo(pad='  ')}\n\nContext Flow Management Tool")
@click.version_option(version=__version__, prog_name=__application__)
@click.pass_context
@click.option(
    "--log-lvl",
    default='WARNING',  # NOTSET=0, DEBUG=10, INFO=20, WARNING=30, ERROR=40, CRITICAL=50
    help='DEBUG, INFO, WARNING, ERROR, CRITICAL',
    type=click.STRING,
)
@click.option("--agent", default=AGENT_PREF, type=click.Choice(['opencode', 'claude']), help="choose the terminal agent you want to stage context for")
@click.option("--new-digest", default=False, is_flag=True, help="generate a new digest.txt file")
def ctx(cli_ctx: click.Context, log_lvl: str, agent: str, new_digest: bool) -> None:
    """
    CTXFLOW 💭 control the enviroment and context passed to your Terminal Agent
    """
    numeric_loglevel = getattr(logging, log_lvl)
    if isinstance(numeric_loglevel, int):
        setup_logging(numeric_loglevel)
    else:
        setup_logging(log_lvl_stdout=TextualAppContext().loglvl)

    cli_ctx.ensure_object(dict)
    cli_ctx.obj['ctx'] = {
        "flags": {"--log-lvl": log_lvl, "--agent": agent, "--new-digest": new_digest},
        "args": {},
        "commands": {
            "browsr": {},
            "opencode": {},
            "gitingest": {},
        }
    }

    cwd: str = os.getcwd()
    if new_digest:
        # if flag enabled this will only update a digest and exit
        click.echo("updating the git digest file...")
        for root, dirs, files in os.walk(cwd):
            for name in files:
                if name == 'digest.txt':
                    cmd: str = cmd_builder(
                        prog=GI_ALIAS,
                        cmds=tuple(["."]),
                        flags={
                            "--output": os.path.join(root, name),
                            "--exclude-pattern": "logs/",
                            "-e": ["logs/", "*.log*", "*.env*", "*.claude*", "ai_docs/", "specs/"],
                        },
                        exclude_logs=True,
                    )
                    with subprocess.Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True, text=True) as proc:
                        stdout, stderr = proc.communicate()
                        if stderr:
                            msg: List[str] = stderr.strip().split('\n')
                            logger.debug("Gitingest: " + " ".join(msg))

                        if stdout:
                            # don't care about index: 1 (Summary:) or 2 (Directory:)
                            # fragil as its dependent on output of another cli prog
                            try:
                                output: List[str] = [
                                    x for x in stdout.split('\n') if x != ""]
                                output = output[0:1] + output[3:]
                                if len(output) != 3:
                                    raise IndexError
                                output_structured: dict[str, str] = {
                                    "output_path": "", "files_analyzed": "", "token_size": ""}
                                for idx, line in enumerate(output):
                                    # index: 0 key: output val: path,
                                    # index: 1 key: files analyzed val: int,
                                    # index: 2 key: token size val: float K
                                    key_val: List[str] = line.split(":")
                                    if len(key_val) != 2:
                                        raise IndexError
                                    if idx == 0:
                                        output_structured["output_path"] = str(
                                            key_val[1]).strip()
                                    elif idx == 1:
                                        output_structured["files_analyzed"] = str(
                                            key_val[1]).strip()
                                    elif idx == 2:
                                        output_structured["token_size"] = str(
                                            key_val[1]).strip()
                                for key, val in output_structured.items():
                                    # don't care for output_path right now; redundent
                                    if key != "output_path":
                                        click.echo(f"{key}: {val}")
                            except IndexError:
                                pass
                            except Exception as e:
                                logger.exception(
                                    "stdout output might have changed, details: {e}")

                    click.echo(
                        f"{os.path.relpath(os.path.join(root, name))} updated")
                    cli_ctx.exit(SUCCEED)

        click.echo("no git digest file found")
        cli_ctx.exit(FAIL)

    cpydirs: tuple[tuple[str, str], ...] = (
        # directory - persistent storage
        (os.path.join(SCRIPT_DIR, '.ctxflow'),
         os.path.join(HOME_DIR, '.ctxflow')),
        # directory - implanting .claude
        (os.path.join(SCRIPT_DIR, 'claude'),
         os.path.join(cwd, '.claude')),
        (os.path.join(SCRIPT_DIR, 'claude', 'hooks'),
         os.path.join(cwd, '.claude', 'hooks')),
        (os.path.join(SCRIPT_DIR, 'claude', 'commands'),
         os.path.join(cwd, '.claude', 'commands'))
    )
    cpyfiles: tuple[tuple[str, str], ...] = (
        # file
        (os.path.join(SCRIPT_DIR, 'prompts', 'template_prime.xml'),
         os.path.join(cwd, '.claude', 'templates', 'prime.xml')),
        # file
        (os.path.join(SCRIPT_DIR, 'prompts', 'user', 'web_builder.xml'),
         os.path.join(cwd, '.claude', 'templates', 'web-builder.xml')),
        # file - constructor for md file with xml context
        (os.path.join(SCRIPT_DIR, 'scripts', 'template-processor.sh'),
         os.path.join(cwd, '.claude', 'templates', 'template-processor.sh')),
        # file - important don't EVER remove
        (os.path.join(SCRIPT_DIR, '.env.dev'),
         os.path.join(cwd, '.env')),
    )
    cpydocs: tuple[tuple[str, str], ...] = cpydirs + cpyfiles

    if cli_ctx.invoked_subcommand is None:
        confirm: bool = inquirer.confirm(message="Start ctxflow?").execute()
        if confirm:
            click.echo("Creating the necessary directories/files...")
            initial(cpyf=cpydocs)
            # starting up gitingest, for proj indexing and priming
            click.echo("\nMaking a git digest file...")
            cmd = cmd_builder(
                prog=GI_ALIAS,
                cmds=tuple(["."]),
                flags={
                    "--output": os.path.join(cwd, 'ai_docs', 'digest.txt'),
                    "-e": ["logs/", "*.log*", "*.env*", "*.claude*", "ai_docs/", "specs/"],
                },
                exclude_logs=True,
            )
            with subprocess.Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True, text=True) as proc:
                stdout, stderr = proc.communicate()
                if stderr:
                    msg = stderr.strip().split('\n')
                    logger.debug("Gitingest: " + " ".join(msg))

                if stdout:
                    # don't care about index: 1 (Summary:) or 2 (Directory:)
                    # fragil as its dependent on output of another cli prog
                    try:
                        output = [
                            x for x in stdout.split('\n') if x != ""]
                        output = output[0:1] + output[3:]
                        if len(output) != 3:
                            raise IndexError
                        output_structured = {
                            "output_path": "", "files_analyzed": "", "token_size": ""}
                        for idx, line in enumerate(output):
                            # index: 0 key: output val: path,
                            # index: 1 key: files analyzed val: int,
                            # index: 2 key: token size val: float K
                            key_val = line.split(":")
                            if len(key_val) != 2:
                                raise IndexError
                            if idx == 0:
                                output_structured["output_path"] = str(
                                    key_val[1]).strip()
                            elif idx == 1:
                                output_structured["files_analyzed"] = str(
                                    key_val[1]).strip()
                            elif idx == 2:
                                output_structured["token_size"] = str(
                                    key_val[1]).strip()
                        for key, val in output_structured.items():
                            # don't care for output_path right now; redundent
                            if key != "output_path":
                                click.echo(f"{key}: {val}")
                    except IndexError:
                        pass
                    except Exception as e:
                        logger.exception(
                            "stdout output might have changed, details: {e}")

            click.echo("\nInitialization complete!")

    cli_ctx.obj['ctx']['kwargs'] = {
        "cpydocs": cpydocs,
        "cpydirs": cpydirs,
        "cpyfiles": cpyfiles,
        # experimenting
        "remove": (os.path.join(cwd, '.claude'), os.path.join(cwd, 'ai_docs'), os.path.join(cwd, 'specs'))
    }


@ctx.command(name="init", cls=rich_click.rich_command.RichCommand)
@click.pass_context
def init(cli_ctx: click.Context) -> None:
    """
    📄 initialize prime command with .env variables
    """
    questions: List[dict[str, str]] = [
        {"type": "input", "message": "Project Name:", "name": "PROJECT_NAME"},
        {"type": "input", "message": "Tech Stack:", "name": "TECH_STACK"},
        {"type": "input", "message": "Current Status:", "name": "CURRENT_STATUS"},
        {"type": "input", "message": "Priority:", "name": "PRIORITY"},
        {"type": "confirm", "message": "Confirm?", "name": "confirm"},
    ]
    while True:
        result: dict[str, Any] = prompt(questions)
        if result["confirm"] == True:
            for key, val in result.items():
                click.echo(f'{key}="{val}"')
            break

    cwd: str = os.getcwd()
    for root, dirs, files in os.walk(cwd):
        for name in files:
            if name == '.env':
                path_env: str = os.path.join(root, name)
                click.echo("Updating the .env file...")
                if os.path.getsize(path_env) == 0:
                    with open(path_env, 'w') as fd:
                        for key, val in result.items():
                            if key != 'confirm':
                                fd.write(f'{key}="{val}"\n')
                else:
                    with open(path_env, 'a') as fd:
                        for key, val in result.items():
                            if key != 'confirm':
                                fd.write(f'{key}="{val}"\n')

                click.echo(f"{os.path.relpath(path_env)} updated")
                cli_ctx.exit(SUCCEED)

    path_env = os.path.join(cwd, ".env")
    click.echo(
        f".env file not found, creating one at {os.path.relpath(path_env)}")
    open(path_env, 'x')
    click.echo("Updating the .env file...")
    with open(path_env, 'w') as fd:
        for key, val in result.items():
            if key != 'confirm':
                fd.write(f'{key}="{val}"\n')
    click.echo(f"{os.path.relpath(path_env)} updated")
    cli_ctx.exit(SUCCEED)


@ctx.command(name="done", cls=rich_click.rich_command.RichCommand)
@click.pass_context
def done(cli_ctx: click.Context) -> None:
    """
    🧹 Cleanup dirs/files that were created during ctxflow use.
    \f
    !!! Be MINDFUL of the data that you are deleting, ALWAYS double check any removals !!!
    """
    cli_ctx.obj['ctx']['commands']['done'] = {
        "flags": {},
        "args": {},
        "commands": {},
    }
    confirm: bool = inquirer.confirm(message="Are you sure?").execute()
    if confirm:
        root_cli_ctx = cli_ctx.find_root()
        ctx_teardown: Tuple[str, ...] = root_cli_ctx.obj['ctx']['kwargs']['remove']
        for path in ctx_teardown:
            file: str = os.path.basename(path)
            try:
                # just in case; absolutely don't want to remove these
                if file == '.env' or file == '.ctxflow':
                    continue
                elif os.path.isdir(path) and os.path.exists(path):
                    shutil.rmtree(path)
                    click.echo(f"{os.path.relpath(path)} was removed")
                elif os.path.isfile(path) and os.path.exists(path):
                    os.remove(path)
                    click.echo(f"{os.path.relpath(path)} was removed")
                else:
                    click.echo(
                        f"{os.path.relpath(path)} was not removed, likely the file was already deleted")
            except Exception as e:
                logger.exception(f"An error of {type(e)} occured. Details:")
                click.echo(f"couldn't remove {file}. see logs for details")
                continue

    cli_ctx.exit(SUCCEED)


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


@command_with_aliases(ctx, OC_ALIAS, name="opencode", cls=rich_click.rich_command.RichCommand, context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True,
    allow_interspersed_args=False
))
@click.pass_context
def opencode(cli_ctx: click.Context) -> None:
    """ 🤖 wrapper around opencode cli """
    all_args: List[str] = cli_ctx.args
    if not all_args:
        all_args = ["."]

    cmd: str = cmd_builder(prog=OC_ALIAS, cmds=tuple(all_args))
    agent: TerminalAgentRunner = TerminalAgentRunner(
        agent_alias=OC_ALIAS, cmd=cmd)
    exit_code: int = agent.run()
    cli_ctx.exit(exit_code)


@command_with_aliases(ctx, CLD_ALIAS, name="claude", cls=rich_click.rich_command.RichCommand, context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True,
    allow_interspersed_args=False
))
@click.pass_context
def claude(cli_ctx: click.Context) -> None:
    """ 🤖 wrapper around claude cli """
    all_args: List[str] = cli_ctx.args
    cmd: str = cmd_builder(prog=CLD_ALIAS, cmds=tuple(
        all_args) if all_args is not None else None, exclude_logs=True)
    agent: TerminalAgentRunner = TerminalAgentRunner(
        agent_alias=CLD_ALIAS, cmd=cmd)
    exit_code: int = agent.run()
    cli_ctx.exit(exit_code)


if __name__ == "__main__":
    ctx()
