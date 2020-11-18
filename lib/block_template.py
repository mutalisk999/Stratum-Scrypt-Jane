import StringIO
import binascii
import struct

import util
import merkletree
import halfnode
from coinbasetx import CoinbaseTransaction
import lib
# Remove dependency to settings, coinbase extras should be
# provided from coinbaser
import settings

log = lib.logger.get_logger('template_registry')

class BlockTemplate(halfnode.CBlock):
    '''Template is used for generating new jobs for clients.
    Let's iterate extranonce1, extranonce2, ntime and nonce
    to find out valid bitcoin block!'''
    
    coinbase_transaction_class = CoinbaseTransaction
    
    def __init__(self, timestamper, coinbaser, job_id):
        super(BlockTemplate, self).__init__()
        
        self.job_id = job_id 
        self.timestamper = timestamper
        self.coinbaser = coinbaser
        
        self.prevhash_bin = '' # reversed binary form of prevhash
        self.prevhash_hex = ''
        self.timedelta = 0
        self.curtime = 0
        self.target = 0
        #self.coinbase_hex = None 
        self.merkletree = None
                
        self.broadcast_args = []
        
        # List of 4-tuples (extranonce1, extranonce2, ntime, nonce)
        # registers already submitted and checked shares
        # There may be registered also invalid shares inside!
        self.submits = [] 
                
    def fill_from_rpc(self, data):
        '''Convert getblocktemplate result into BlockTemplate instance'''
        
        #txhashes = [None] + [ binascii.unhexlify(t['hash']) for t in data['transactions'] ]
        txhashes = [None] + [ util.ser_uint256(int(t['hash'], 16)) for t in data['transactions'] ]
        mt = merkletree.MerkleTree(txhashes)

        coinbase = self.coinbase_transaction_class(self.timestamper, self.coinbaser, data['coinbasevalue'],
                        data['coinbaseaux']['flags'], data['height'], settings.COINBASE_EXTRAS, data['curtime'])
        
        self.height = data['height']
        self.nVersion = data['version']
        self.hashPrevBlock = int(data['previousblockhash'], 16)
        self.nBits = int(data['bits'], 16)
        self.hashMerkleRoot = 0
        self.nTime = 0
        self.nNonce = 0
        self.vtx = [ coinbase, ]
        
        for tx in data['transactions']:
            t = halfnode.CTransaction()
            t.deserialize(StringIO.StringIO(binascii.unhexlify(tx['data'])))
            self.vtx.append(t)
            
        self.curtime = data['curtime']
        self.timedelta = self.curtime - int(self.timestamper.time()) 
        self.merkletree = mt
        self.target = util.uint256_from_compact(self.nBits)
        
        # Reversed prevhash
        self.prevhash_bin = binascii.unhexlify(util.reverse_hash(data['previousblockhash']))
        self.prevhash_hex = "%064x" % self.hashPrevBlock
        log.debug("fill_from_rpc previousblockhash: %s", self.prevhash_hex)
        
        self.broadcast_args = self.build_broadcast_args()
                
    def register_submit(self, extranonce1, extranonce2, ntime, nonce):
        '''Client submitted some solution. Let's register it to
        prevent double submissions.'''
        
        t = (extranonce1, extranonce2, ntime, nonce)
        if t not in self.submits:
            self.submits.append(t)
            return True
        return False
            
    def build_broadcast_args(self):
        '''Build parameters of mining.notify call. All clients
        may receive the same params, because they include
        their unique extranonce1 into the coinbase, so every
        coinbase_hash (and then merkle_root) will be unique as well.'''
        job_id = self.job_id
        prevhash = binascii.hexlify(self.prevhash_bin)
        (coinb1, coinb2) = [ binascii.hexlify(x) for x in self.vtx[0]._serialized ]
        merkle_branch = [ binascii.hexlify(x) for x in self.merkletree._steps ]
        version = binascii.hexlify(struct.pack(">i", self.nVersion))
        nbits = binascii.hexlify(struct.pack(">I", self.nBits))
        ntime = binascii.hexlify(struct.pack(">I", self.curtime))
        clean_jobs = True
        
        return (job_id, prevhash, coinb1, coinb2, merkle_branch, version, nbits, ntime, clean_jobs)

    def serialize_coinbase(self, extranonce1, extranonce2):
        '''Serialize coinbase with given extranonce1 and extranonce2
        in binary form'''
        (part1, part2) = self.vtx[0]._serialized
        return part1 + extranonce1 + extranonce2 + part2
    
    def check_ntime(self, ntime):
        '''Check for ntime restrictions.'''
        log.debug("check_ntime, ntime %d, curtime %d, timestamper %d", int(ntime), int(self.curtime), int(self.timestamper.time()))

        if ntime < self.curtime:
            return False
        
        if ntime > (self.timestamper.time() + 7200):
            # Be strict on ntime into the near future
            # may be unnecessary
            return False
        
        return True

    def serialize_header(self, merkle_root_int, ntime_bin, nonce_bin):
        '''Serialize header for calculating block hash'''
        log.debug("serialize_header")
        log.debug("pack nVersion %s", struct.pack(">i", self.nVersion).encode("hex"))
        r  = struct.pack(">i", self.nVersion)
        log.debug("pack prevhash_bin %s", self.prevhash_bin.encode("hex"))
        r += self.prevhash_bin
        log.debug("pack merkle_root %s", util.ser_uint256_be(merkle_root_int).encode("hex"))
        r += util.ser_uint256_be(merkle_root_int)
        log.debug("pack ntime_bin %s", ntime_bin.encode("hex"))
        r += ntime_bin
        log.debug("pack nBits %s", struct.pack(">I", self.nBits).encode("hex"))
        r += struct.pack(">I", self.nBits)
        log.debug("pack nonce_bin %s", nonce_bin.encode("hex"))
        r += nonce_bin    
        return r


    def finalize(self, merkle_root_int, extranonce1_bin, extranonce2_bin, ntime, nonce):
        '''Take all parameters required to compile block candidate.
        self.is_valid() should return True then...'''
        
        self.hashMerkleRoot = merkle_root_int
        self.nTime = ntime
        self.nNonce = nonce
        self.vtx[0].set_extranonce(extranonce1_bin + extranonce2_bin)        
        self.sha256 = None # We changed block parameters, let's reset sha256 cache
