import click

from overhave.cli.group import overhave
from overhave.factory import ConsumerFactory
from overhave.redis import RedisStream


@overhave.command(short_help='Run redis consumer')
@click.option(
    "-s",
    "--stream",
    type=click.Choice(RedisStream.__members__),
    callback=lambda c, p, v: getattr(RedisStream, v),
    help="Redis stream, which defines application",
)
def consumer(stream: RedisStream) -> None:
    ConsumerFactory(stream).runner.run()