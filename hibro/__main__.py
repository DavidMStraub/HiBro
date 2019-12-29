"""Console script for hibro."""

import sys
import click

from .dashboard import create_app


@click.command()
@click.option("--port", default=8456, help="port")
@click.option("--config-file", default="hibro-config.yaml", help="configuration file")
def main(port, config_file):
    """Run the HiBro dashboard."""
    app = create_app(config_file=config_file)
    app.run(port=port, debug=True)


if __name__ == "__main__":
    main()
