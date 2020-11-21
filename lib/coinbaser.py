import util
from twisted.internet import defer

import settings

import lib.logger

log = lib.logger.get_logger('coinbaser')


# TODO: Add on_* hooks in the app

class SimpleCoinbaser(object):
    """This very simple coinbaser uses constant bitcoin address
    for all generated blocks."""

    def __init__(self, bitcoin_rpc, wallet):
        self.wallet = wallet
        # Fire callback when coinbaser is ready
        self.on_load = defer.Deferred()
        self.on_load.callback(True)

    # def on_new_block(self):
    #    pass

    # def on_new_template(self):
    #    pass

    def get_script_pubkey(self):
        # pubkey
        if len(self.wallet) == 66:
            return util.get_p2pk_script(self.wallet)
        # address
        else:
            return util.get_p2pkh_script(self.wallet)

    def get_coinbase_data(self):
        return ''
