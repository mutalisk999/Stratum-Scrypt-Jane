from service import MiningService
from subscription import MiningSubscription
from twisted.internet import defer
from twisted.internet.error import ConnectionRefusedError
import time
import simplejson as json
from twisted.internet import reactor


@defer.inlineCallbacks
def setup(on_startup):
    """Setup mining service internal environment.
    You should not need to change this. If you
    want to use another Worker manager or Share manager,
    you should set proper reference to Interfaces class
    *before* you call setup() in the launcher script."""

    import lib.settings as settings

    # Get logging online as soon as possible
    import lib.logger
    log = lib.logger.get_logger('mining')

    from interfaces import Interfaces

    from lib.block_updater import BlockUpdater
    from lib.template_registry import TemplateRegistry
    from lib.bitcoin_rpc_manager import BitcoinRPCManager
    from lib.block_template import BlockTemplate
    from lib.coinbaser import SimpleCoinbaser

    bitcoin_rpc = BitcoinRPCManager()

    # Check Dashcoind
    #         Check we can connect (sleep)
    # Check the results:
    #         - getblocktemplate is avalible        (Die if not)
    #         - we are not still downloading the blockchain        (Sleep)
    log.info("Connecting to Dashcoind...")
    while True:
        try:
            result = yield bitcoin_rpc.getblocktemplate()
            if isinstance(result, dict):
                # Dashcoind implements version 1 of getblocktemplate
                if result['version'] >= 1:
                    break

        except ConnectionRefusedError, e:
            log.error(
                "Connection refused while trying to connect to dashcoin (are your DASHCOIN_TRUSTED_* settings correct?)")
            reactor.stop()

        except Exception, e:
            if isinstance(e[2], str):
                if isinstance(json.loads(e[2])['error']['message'], str):
                    error = json.loads(e[2])['error']['message']
                    if error == "Method not found":
                        log.error("Dashcoind does not support getblocktemplate!!! (time to upgrade.)")
                        reactor.stop()
                    elif error == "Dashcoind is downloading blocks...":
                        log.error("Dashcoind downloading blockchain... will check back in 30 sec")
                        time.sleep(29)
                    else:
                        log.error("Dashcoind Error: %s", error)
        time.sleep(1)  # If we didn't get a result or the connect failed

    log.info('Connected to Dashcoind - Ready to GO!')

    # Start the coinbaser
    coinbaser = SimpleCoinbaser(bitcoin_rpc, getattr(settings, 'CENTRAL_WALLET'))
    yield coinbaser.on_load

    registry = TemplateRegistry(BlockTemplate,
                                coinbaser,
                                bitcoin_rpc,
                                getattr(settings, 'INSTANCE_ID'),
                                MiningSubscription.on_template,  # on template callback
                                Interfaces.share_manager.on_network_block)  # on block callback

    # Template registry is the main interface between Stratum service
    # and pool core logic
    Interfaces.set_template_registry(registry)

    # Set up polling mechanism for detecting new block on the network
    # This is just failsafe solution when -blocknotify
    # mechanism is not working properly    
    BlockUpdater(registry, bitcoin_rpc)

    log.info("MINING SERVICE IS READY")
    on_startup.callback(True)
