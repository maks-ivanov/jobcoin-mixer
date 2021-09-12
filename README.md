# Jobcoin

This repo is a small collection of starter templates for the Jobcoin Mixer programming challenge. There are three different versions provided for you to choose: Scala, Python, and NodeJS. It's perfectly okay to use another language you feel more comfortable writing in and simply use these examples as a loose guide.

All the implementations provided are roughly identical in what they provide to you:
 * a basic CLI app that accepts return addresses and gives back a deposit address to send funds to
 * a recommended library to use for Jobcoin API calls
 * a recommended library to use for tests
 
The mixing algorithm and any other changes are left for you to implement.

Mixer flow:
1. User provides a list of new, unused addresses to mixer
2. Mixer provides user with a new deposit address owned by mixer
3. User transfers coins to deposit address
4. Mixer transfers from deposit address to house address
5. Over time mixer distributes user's btc to unused addresses from (1)

## Jobcoin Mixer:

To run: `python cli.py`
Tests: `pytest tests/test_jobcoin.py`
* CLI
    * Creates and starts up a mixer
    * Prompts user for input, performs basic input checks
    * Generates a deposit address, passes it along with return addresses to the mixer
    * Displays deposit address back to the user
* Mixer
    * A configurable number of poller threads watch deposit addresses for balance
        * Once balance is detected, transfers coins to house account and puts a mix request (balance, return addresses) on the queue
    * A configurable number of request processor threads are monitoring the mix request queue
        * Gets a request from the queue
        * If there is only one address remaining in the request, returns the entire requested amount to that address
        * Else picks a random address from the list of return addresses, along with a random amount uniformly between 10E-9 and requested amount, and sends the transaction
        * Generates a new mix request with remaining addresses and remaining amounts and puts it back on the queue
    * Mixer numeric precision is configured to be truncated to 9 digits, any dust below that amount may be considered a mixing fee.

## What’s next:
* Fault Tolerance and Scalability
    * Right now the whole app is in memory. If it shuts down in the middle of mixing, coins will be lost. The following changes needs to be persisted for the mixer to be able to scale and recover from failures
        * Persist the deposit address : return_addresses mappings in a database
            * Mixer needs to remember previous addresses already provided to it to recover from unexpected shutdowns
            * The in-memory dict growing too large can cause out of memory exception
            * If there are two many addresses for one mixer, storing address mappings in DB allows us to spin up multiple mixer processes in parallel, perhaps configuring them to be responsible for smaller address segments
        * Persist and update how many coins are owed to each address pair
    * Lots of places in code assume that rest api just works all the time
* Security
    * All methods and variables are currently public to make unit testing easier, but essentially everything about the mixer except start, stop, and create_mix_account should be private
    * Sanitize inputs
    * All addresses should be encrypted
* Maintainability and usability
    * Add logging to mixer
    * Make a package
    * Deploy to cloud
* Mixer algorithm
    * Right now each mixed sum is split into N transactions where N=number of provided return addresses, one per address. Could potentially obfuscate further by splitting into M>N transactions and send to each return address more than once
    * Could further randomize return delay
    * Could potentially use some decoy wash transactions with house account to mitigate transaction patterns with low number of concurrent users
* General
    * Coupling could be looser

