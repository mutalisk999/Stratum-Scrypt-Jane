# Eloipool - Python Bitcoin pool server
# Copyright (C) 2011-2012  Luke Dashjr <luke-jr+eloipool@utopios.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from hashlib import sha256
from util import doublesha


class MerkleTree:
    def __init__(self, data, detailed=False):
        self.data = data
        self.recalculate(detailed)
        self._hash_steps = None

    def recalculate(self, detailed=False):
        L = self.data
        steps = []
        if detailed:
            detail = []
            PreL = []
            StartL = 0
        else:
            detail = None
            PreL = [None]
            StartL = 2
        Ll = len(L)
        if detailed or Ll > 1:
            while True:
                if detailed:
                    detail += L
                if Ll == 1:
                    break
                steps.append(L[1])
                if Ll % 2:
                    L += [L[-1]]
                L = PreL + [doublesha(L[i] + L[i + 1]) for i in range(StartL, Ll, 2)]
                Ll = len(L)
        self._steps = steps
        self.detail = detail

    def hash_steps(self):
        if self._hash_steps == None:
            self._hash_steps = doublesha(''.join(self._steps))
        return self._hash_steps

    def withFirst(self, f):
        steps = self._steps
        for s in steps:
            f = doublesha(f + s)
        return f

    def merkleRoot(self):
        return self.withFirst(self.data[0])


# MerkleTree tests
def _test():
    import binascii
    import time

    mt = MerkleTree([None] + [binascii.unhexlify(a) for a in [
        '999d2c8bb6bda0bf784d9ebeb631d711dbbbfe1bc006ea13d6ad0d6a2649a971',
        '3f92594d5a3d7b4df29d7dd7c46a0dac39a96e751ba0fc9bab5435ea5e22a19d',
        'a5633f03855f541d8e60a6340fc491d49709dc821f3acb571956a856637adcb6',
        '28d97c850eaf917a4c76c02474b05b70a197eaefb468d21c22ed110afe8ec9e0',
    ]])
    assert (
            b'82293f182d5db07d08acf334a5a907012bbb9990851557ac0ec028116081bd5a' ==
            binascii.b2a_hex(
                mt.withFirst(binascii.unhexlify('d43b669fb42cfa84695b844c0402d410213faa4f3e66cb7248f688ff19d5e5f7')))
    )

    print '82293f182d5db07d08acf334a5a907012bbb9990851557ac0ec028116081bd5a'
    txes = [binascii.unhexlify(a) for a in [
        'd43b669fb42cfa84695b844c0402d410213faa4f3e66cb7248f688ff19d5e5f7',
        '999d2c8bb6bda0bf784d9ebeb631d711dbbbfe1bc006ea13d6ad0d6a2649a971',
        '3f92594d5a3d7b4df29d7dd7c46a0dac39a96e751ba0fc9bab5435ea5e22a19d',
        'a5633f03855f541d8e60a6340fc491d49709dc821f3acb571956a856637adcb6',
        '28d97c850eaf917a4c76c02474b05b70a197eaefb468d21c22ed110afe8ec9e0',
    ]]

    s = time.time()
    mt = MerkleTree(txes)
    for x in range(100):
        y = int('d43b669fb42cfa84695b844c0402d410213faa4f3e66cb7248f688ff19d5e5f7', 16)
        # y += x
        coinbasehash = binascii.unhexlify("%x" % y)
        x = binascii.b2a_hex(mt.withFirst(coinbasehash))

    print x
    print time.time() - s


def _testTxesMerkleRoot():
    import binascii
    import util

    # 6960d019913a8958642415b92836304a2f39275df60bfbc30e65020489ac2b64

    mt = MerkleTree([None] + [util.ser_uint256(int(a, 16)) for a in [
        'aec5799ca150e2e25efd3e78aa649701f8a02444f50a75ba4938602f127f4700',
        '18ac6e72a78a062fd24d74d7e86e3605ab96df036c24ce792d2a471a38631b26',
        'a23426065899dc8b8995f8e2baaabb5c423eaa432034c8d6c54c54dfc2e91739',
        'bcc145c463a1ed5198a9ef84644b173ce0db298a1331f23f7befb42115da9f49',
        'b57db2bea71e2cbdcb4044ec5ff346f5497b91a76311506078c86ac0de452158',
        '3b1e3d37c2c472e2696cdad3e2ce0794152a66d59d83a6acf1b16f4499d71f5f',
        '2ad70917e86b8018d3c17604c2916eb88e18185c315a74d88d7fb8fe0fee5d63',
        '17b1d3806ff59c286c12d0621cd417e0e47620567af9503d606b4dbb88491170',
        '3c82e59bd388f08e05e1e2dc4314a561383157eb6dfa8676b5686b5e916fa970',
        '0ab031ea9298b421a3a670fc9b0c7b7ca6b76601e2f9e347393174cd737859b0',
        '9b79043a62ebce175aef786c009d96043cfea9a2f77e0c1243f76b3f6c841df2',
        'a5dcda71dd39ec1185d80fa5573a44c67a88e95d1529884e78a9207693ff1300',
        '34c337b6d5b602ba892026fc42ecb8d6256cb1b9839fe9fd0cbbe50eab143723',
        'eacab53b71b916f1b49a7154f5afa6f0f6c9a3b58770d288aebf442e9bb0ae35',
        '87c36b4657253492c33f483c42fd8e6f65758f2fddce1ee13cc6468ace6aa064',
        '6b8b0adc9198a355c77b43028b3b36cb266de984fd4da077a3ab8aa17489528b',
        '50e66a0de514fc0365afd845cd785ec9b57fec01171f61eaf92fad159242579d',
        '6fd61260acdc0c08713914ae4f3b7a959216b3f2759d1591c0872d065bb4c09f',
        '3238992ec1cd9daef3f066e8d5d88370ab7fe5fe31f782dc7dbf8df7e2a3c3ce',
        'd0e9717782e05a89c67d7c97a3293d3e93377de8bffb7fb578e0d4d671e567f7'
    ]])

    print binascii.b2a_hex(mt.withFirst(util.ser_uint256(int("a9c02cb69f753ef724110f7a0b95724492ded6ac1333f22424de0b8eafdb35a2", 16))))
    

if __name__ == '__main__':
    # _test()
    _testTxesMerkleRoot()
