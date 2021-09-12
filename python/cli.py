#!/usr/bin/env python
import uuid
import sys
import click
from jobcoin import jobcoin, mixer


@click.command()
def main(args=None):
    print('Welcome to the Jobcoin mixer!\n')
    coin_mixer = mixer.Mixer()
    coin_mixer.start()
    while True:
        addresses = click.prompt(
            'Please enter a comma-separated list of new, unused Jobcoin '
            'addresses where your mixed Jobcoins will be sent.',
            prompt_suffix='\n[blank to quit] > ',
            default='',
            show_default=False)
        if addresses.strip() == '':
            coin_mixer.stop()
            sys.exit(0)

        addresses = addresses.split(',')
        deposit_address = uuid.uuid4().hex
        coin_mixer.create_mix_account(deposit_address, addresses)
        click.echo(
            '\nYou may now send Jobcoins to address {deposit_address}. They '
            'will be mixed and sent to your destination addresses.\n'
              .format(deposit_address=deposit_address))



if __name__ == '__main__':
    sys.exit(main())
