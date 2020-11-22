import weakref
import binascii
import util
import StringIO
import ltc_scrypt
import yac_scrypt
from twisted.internet import defer
from lib.exceptions import SubmitException

import lib.logger

log = lib.logger.get_logger('template_registry')

from mining.interfaces import Interfaces
from extranonce_counter import ExtranonceCounter


class JobIdGenerator(object):
    '''Generate pseudo-unique job_id. It does not need to be absolutely unique,
    because pool sends "clean_jobs" flag to clients and they should drop all previous jobs.'''
    counter = 0

    @classmethod
    def get_new_id(cls):
        cls.counter += 1
        if cls.counter % 0xffff == 0:
            cls.counter = 1
        return "%x" % cls.counter


class TemplateRegistry(object):
    '''Implements the main logic of the pool. Keep track
    on valid block templates, provide internal interface for stratum
    service and implements block validation and submits.'''

    def __init__(self, block_template_class, coinbaser, bitcoin_rpc, instance_id,
                 on_template_callback, on_block_callback):
        log.debug("TemplateRegistry init")
        self.prevhashes = {}
        self.jobs = weakref.WeakValueDictionary()

        # set extranonce size 4
        # set extranonce2 size 4
        self.extranonce_counter = ExtranonceCounter(instance_id)
        self.extranonce2_size = block_template_class.coinbase_transaction_class.extranonce_size \
                                - self.extranonce_counter.get_size()

        self.coinbaser = coinbaser
        self.block_template_class = block_template_class
        self.bitcoin_rpc = bitcoin_rpc
        self.on_block_callback = on_block_callback
        self.on_template_callback = on_template_callback

        self.last_block = None
        self.update_in_progress = False
        self.last_update = None

        # Create first block template on startup
        self.update_block()

    def get_new_extranonce1(self):
        '''Generates unique extranonce1 (e.g. for newly
        subscribed connection.'''
        log.debug("TemplateRegistry get_new_extranonce1")
        return self.extranonce_counter.get_new_bin()

    def get_last_broadcast_args(self):
        '''Returns arguments for mining.notify
        from last known template.'''
        log.debug("TemplateRegistry get_last_broadcast_args")
        return self.last_block.broadcast_args

    def add_template(self, block, block_height):
        '''Adds new template to the registry.
        It also clean up templates which should
        not be used anymore.'''
        log.debug("TemplateRegistry add_template")
        prevhash = block.prevhash_hex

        if prevhash in self.prevhashes.keys():
            new_block = False
        else:
            new_block = True
            self.prevhashes[prevhash] = []

        # Blocks sorted by prevhash, so it's easy to drop
        # them on blockchain update
        self.prevhashes[prevhash].append(block)

        # Weak reference for fast lookup using job_id
        self.jobs[block.job_id] = block

        # Use this template for every new request
        self.last_block = block

        # Drop templates of obsolete blocks
        for ph in self.prevhashes.keys():
            if ph != prevhash:
                del self.prevhashes[ph]

        log.debug("New template for %s" % prevhash)

        if new_block:
            # Tell the system about new block
            # It is mostly important for share manager
            self.on_block_callback(prevhash, block_height)

        # Everything is ready, let's broadcast jobs!
        self.on_template_callback(new_block)

        # from twisted.internet import reactor
        # reactor.callLater(10, self.on_block_callback, new_block)

    def update_block(self):
        '''Registry calls the getblocktemplate() RPC
        and build new block template.'''
        log.debug("TemplateRegistry update_block")
        if self.update_in_progress:
            # Block has been already detected
            return

        self.update_in_progress = True
        self.last_update = Interfaces.timestamper.time()

        d = self.bitcoin_rpc.getblocktemplate()
        d.addCallback(self._update_block)
        d.addErrback(self._update_block_failed)

    def _update_block_failed(self, failure):
        log.debug("TemplateRegistry _update_block_failed")
        log.error(str(failure))
        self.update_in_progress = False

    def _update_block(self, data):
        log.debug("TemplateRegistry _update_block")
        start = Interfaces.timestamper.time()

        template = self.block_template_class(Interfaces.timestamper, self.coinbaser, JobIdGenerator.get_new_id())
        template.fill_from_rpc(data)
        self.add_template(template, data['height'])

        log.debug("Update finished, %.03f sec, %d txes" % \
                  (Interfaces.timestamper.time() - start, len(template.vtx)))

        self.update_in_progress = False
        return data

    def diff_to_target(self, difficulty):
        '''Converts difficulty to target'''
        log.debug("TemplateRegistry diff_to_target")
        diff1 = 0x00000000ffff0000000000000000000000000000000000000000000000000000
        # diff1 = 0x0000ffff00000000000000000000000000000000000000000000000000000000
        return diff1 / difficulty

    def get_job(self, job_id):
        log.debug("TemplateRegistry get_job")
        '''For given job_id returns BlockTemplate instance or None'''
        try:
            j = self.jobs[job_id]
        except:
            log.debug("Job id '%s' not found" % job_id)
            return None

        # Now we have to check if job is still valid.
        # Unfortunately weak references are not bulletproof and
        # old reference can be found until next run of garbage collector.
        if j.prevhash_hex not in self.prevhashes:
            log.debug("Prevhash of job '%s' is unknown" % job_id)
            return None

        if j not in self.prevhashes[j.prevhash_hex]:
            log.debug("Job %s is unknown" % job_id)
            return None

        return j

    def submit_share(self, job_id, worker_name, session, extranonce1_bin, extranonce2, ntime, nonce,
                     difficulty):
        '''Check parameters and finalize block template. If it leads
           to valid block candidate, asynchronously submits the block
           back to the bitcoin network.
        
            - extranonce1_bin is binary. No checks performed, it should be from session data
            - job_id, extranonce2, ntime, nonce - in hex form sent by the client
            - difficulty - decimal number from session, again no checks performed
            - submitblock_callback - reference to method which receive result of submitblock()
        '''

        log.debug("TemplateRegistry submit_share")
        log.debug(
            "from %s, (%s %s %s %s)" % (worker_name, binascii.hexlify(extranonce1_bin), extranonce2, ntime, nonce))
        # Check if extranonce2 looks correctly. extranonce2 is in hex form...
        if len(extranonce2) != self.extranonce2_size * 2:
            raise SubmitException("Incorrect size of extranonce2. Expected %d chars" % (self.extranonce2_size * 2))

        # Check for job
        job = self.get_job(job_id)
        if job == None:
            raise SubmitException("Job '%s' not found" % job_id)

        # Check if ntime looks correct
        if len(ntime) != 8:
            raise SubmitException("Incorrect size of ntime. Expected 8 chars")

        if not job.check_ntime(int(ntime, 16)):
            raise SubmitException("Ntime out of range")

        # Check nonce        
        if len(nonce) != 8:
            raise SubmitException("Incorrect size of nonce. Expected 8 chars")

        # Check for duplicated submit
        if not job.register_submit(extranonce1_bin, extranonce2, ntime, nonce):
            log.debug("Duplicate from %s, (%s %s %s %s)" % \
                      (worker_name, binascii.hexlify(extranonce1_bin), extranonce2, ntime, nonce))
            raise SubmitException("Duplicate share")

        # Now let's do the hard work!
        # ---------------------------

        # 0. Some sugar
        extranonce2_bin = binascii.unhexlify(extranonce2)
        ntime_bin = binascii.unhexlify(ntime)
        nonce_bin = binascii.unhexlify(nonce)

        # 1. Build coinbase
        coinbase_bin = job.serialize_coinbase(extranonce1_bin, extranonce2_bin)
        coinbase_hash = util.doublesha(coinbase_bin)

        # 2. Calculate merkle root
        merkle_root_bin = job.merkletree.withFirst(coinbase_hash)
        merkle_root_int = util.uint256_from_str(merkle_root_bin)

        # 3. Serialize header with given merkle, ntime and nonce
        header_bin = job.serialize_header(merkle_root_int, ntime_bin, nonce_bin)

        # 4. Reverse header and compare it with target of the user hash_bin = yac_scrypt.getPoWHash (''. join ([
        # header_bin [i * 4: i * 4 +4] [:: -1] for i in range (0, 20)]), int (ntime, 16))
        hash_bin = ltc_scrypt.getPoWHash(''.join([header_bin[i * 4: i * 4 + 4][:: -1] for i in range(0, 20)]))
        hash_int = util.uint256_from_str(hash_bin)
        scrypt_hash_hex = "%064x" % hash_int
        header_hex = binascii.hexlify(header_bin)
        header_hex = header_hex + "000000800000000000000000000000000000000000000000000000000000000000000000000000000000000080020000"

        target_user = self.diff_to_target(difficulty)
        log.debug("hash_int: %064x, target_user: %064x" % (hash_int, target_user))
        if hash_int > target_user and \
                ('prev_jobid' not in session or session['prev_jobid'] < job_id
                 or 'prev_diff' not in session or hash_int > self.diff_to_target(session['prev_diff'])):
            raise SubmitException("Share is above target")

        # Mostly for debugging purposes
        target_info = self.diff_to_target(100000)
        if hash_int <= target_info:
            log.debug("Yay, share with diff above 100000")

        # Algebra tells us the diff_to_target is the same as hash_to_diff
        share_diff = int(self.diff_to_target(hash_int))

        # 5. Compare hash with target of the network
        if hash_int <= job.target:
            # Yay! It is block candidate! 
            log.debug("We found a block candidate! %s" % scrypt_hash_hex)

            # 6. Finalize and serialize block object 
            job.finalize(merkle_root_int, extranonce1_bin, extranonce2_bin, int(ntime, 16), int(nonce, 16))

            # if not job.is_valid():
            # Should not happen
            #   log.error("Final job validation failed!")

            # 7. Submit block to the network
            serialized = binascii.hexlify(job.serialize())
            on_submit = self.bitcoin_rpc.submitblock(serialized, scrypt_hash_hex)

            return header_hex, scrypt_hash_hex, share_diff, on_submit

        return header_hex, scrypt_hash_hex, share_diff, None
