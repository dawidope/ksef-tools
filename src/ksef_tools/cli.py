from __future__ import annotations

from pathlib import Path

import click

from ksef_tools.config import Config
from ksef_tools.logger import setup_logger
from ksef_tools.output import error, print_json
from ksef_tools.version import _VERSION

_COMMANDS = {
    "send": "ksef_tools.commands.send:send_command",
    "list": "ksef_tools.commands.list:list_command",
    "qr": "ksef_tools.commands.qr:qr_command",
}


class LazyGroup(click.Group):
    def list_commands(self, ctx: click.Context) -> list[str]:
        return sorted(_COMMANDS)

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        if cmd_name not in _COMMANDS:
            return None
        module_path, attr = _COMMANDS[cmd_name].rsplit(":", 1)
        from importlib import import_module

        mod = import_module(module_path)
        return getattr(mod, attr)


@click.group(cls=LazyGroup, invoke_without_command=True)
@click.version_option(version=_VERSION, prog_name="ksef-tools")
@click.option(
    "--config",
    "config_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to config.json.",
)
@click.pass_context
def cli(ctx: click.Context, config_path: Path | None) -> None:
    """KSeF Tools - CLI for the Polish National e-Invoice System."""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config_path
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


def load_config(ctx: click.Context) -> Config:
    """Load config and setup logger. Called by commands, not by --help."""
    if "config" in ctx.obj:
        return ctx.obj["config"]
    config_path = ctx.obj.get("config_path")
    cfg = Config.load(config_path)
    ctx.obj["config"] = cfg
    setup_logger(cfg.base_dir)
    return cfg


def main() -> None:
    import sys

    try:
        cli(standalone_mode=False)
    except click.exceptions.Abort:
        print_json(error("Aborted"))
        sys.exit(1)
    except Exception as exc:
        print_json(error(str(exc)))
        sys.exit(1)
