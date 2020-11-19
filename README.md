#Description
Stratum-mining is a pooled mining protocol. It is a replacement for *getwork* based pooling servers by allowing clients to generate work. The stratum protocol is described [here](http://mining.bitcoin.cz/stratum-mining) in full detail.

This is a implementation of stratum-mining for scrypt based coins. It is compatible with *mmcfe-ng* as well as *mmcfe*, as it complies with the standards of *pushpool*. The end goal is to build on these standards to come up with a more stable solution.

The goal is to make a reliable stratum mining server for scrypt based coins. Over time I will develop this to be more feature rich and very stable. If you would like to see a feature please file a feature request. 

**NOTE:** This fork is still in development. Many features may be broken. Please report any broken features or issues.

#Features

* Stratum Mining Pool 
* Solved Block Confirmation
* Scrypt based coins
* Vardiff support
* Log Rotation
* Initial low difficulty share confirmation
* Multiple *Dashcoind* wallets
* On the fly addition of new *Dashcoind* wallets
* MySQL database support
* Adjustable database commit parameters
* Bypass password check for workers


#Requirements
*stratum-mining-dashcoin* is built in python. I have been testing it with 2.7.3, but it should work with other versions. The requirements for running the software are below.

* Python 2.7+
* python-twisted
* stratum
* MySQL Server 
* Dashcoind

Other coins have been known to work with this implementation. I have tested with the following coins, but there may be many others that work. 

* Litecoin
* Feathercoin
* Digitalcoin
* BBQcoin

#Installation

The installation of this *stratum-mining-dashcoin* can be found in the INSTALL.md file.

#Contact
I try to stay in #stratum-mining-dashcoin on freenode. I am more responsive to requests made through github.

#Credits

* Original version by Slush0
* Modified version by GeneralFault
* Modified version Wade Womersley (Media Skunk Works)
* Scrypt conversion from work done by viperaus
* Modified version by moopless ( Donations Welcome: LdaQyrh8PaLTuBxtgGo97Pj49CScqMTxvX)


#License
This software is provides AS-IS without any warranties of any kind. Please use at your own risk. 
