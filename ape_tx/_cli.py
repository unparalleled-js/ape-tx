import click
from ape import convert
from ape.cli import NetworkBoundCommand, ape_cli_context, network_option

from ._utils import deploy_contract, get_balance, transfer_money

verbose_option = click.option("--verbose", is_flag=True, help="Show more information on the trace.")
raw_option = click.option("--raw", is_flag=True, help="Show the raw, non-pretty trace.")


@click.group()
def cli():
    """Transaction utilities"""


@cli.command(cls=NetworkBoundCommand)
@ape_cli_context()
@network_option()
@click.argument("contract")
@click.argument("arguments", nargs=-1)
@click.option("--sender", help="Account to send deploy tx")
def deploy(cli_ctx, network, contract, arguments, sender):
    _ = network  # Needed for NetworkBoundCommand
    deploy_contract(cli_ctx, contract, *arguments, sender=sender)


def _value_callback(ctx, param, value):
    if not value.isnumeric():
        return convert(value, int)

    return int(value)


@cli.command(cls=NetworkBoundCommand)
@ape_cli_context()
@network_option()
@click.option("--from", "sender", help="The account to transfer from", required=True)
@click.option("--to", "receiver", help="The account to receiver", required=True)
@click.option("--value", help="The amount", required=True, callback=_value_callback)
def transfer(cli_ctx, network, sender, receiver, value):
    _ = network  # Needed for NetworkBoundCommand
    transfer_money(cli_ctx, sender, receiver, value)


@cli.command(cls=NetworkBoundCommand)
@ape_cli_context()
@network_option()
@click.argument("account")
@click.option("--pretty", is_flag=True)
def bal(cli_ctx, network, account, pretty):
    _ = network  # Needed for NetworkBoundCommand
    balance = get_balance(cli_ctx, account, pretty=pretty)
    click.echo(balance)


def txn_hash_callback(ctx, param, value):
    # Removes duplicate entries
    hash_set = set()
    for tx_hash in value:
        hash_set.add(tx_hash)

    return [h for h in hash_set]


@cli.command(cls=NetworkBoundCommand)
@ape_cli_context()
@network_option()
@verbose_option
@raw_option
@click.argument("txn_hash", nargs=-1, callback=txn_hash_callback)
def trace(cli_ctx, network, verbose, raw, txn_hash):
    _ = network  # Needed for NetworkBoundCommand
    if not txn_hash:
        return

    for index in range(len(txn_hash)):
        receipt = cli_ctx.network_manager.provider.get_transaction(txn_hash[index])

        if raw:
            call_tree = cli_ctx.provider.get_call_tree(receipt.txn_hash)
            click.echo(repr(call_tree))
        else:
            receipt.show_trace(verbose=verbose)

        if index < len(txn_hash) - 1:
            click.echo()
