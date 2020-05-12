__version__ = '0.1'

import click
from simple_exporter import falcon_app


@click.group(help='')
def cli():
    pass


@click.command()
@click.option('-f', '--config-file', help='config file with idrac hosts', required=True, type=str)
@click.option('-i', '--ip', help='app ip exposed', required=True, type=str)
@click.option('-p', '--port', help='', required=True, type=int)
def start(config_file, ip, port):
    falcon_app(config_file, ip, port)

cli.add_command(start)

if __name__ == '__main__':
    cli()
