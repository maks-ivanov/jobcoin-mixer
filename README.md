# Jobcoin

This repo is a small collection of starter templates for the Jobcoin Mixer programming challenge. There are three different versions provided for you to choose: Scala, Python, and NodeJS. It's perfectly okay to use another language you feel more comfortable writing in and simply use these examples as a loose guide.

All the implementations provided are roughly identical in what they provide to you:
 * a basic CLI app that accepts return addresses and gives back a deposit address to send funds to
 * a recommended library to use for Jobcoin API calls
 * a recommended library to use for tests
 
The mixing algorithm and any other changes are left for you to implement.

Mixer flow:
1. User provides a lsit of new, unused addresses to mixer
2. Mixer provides user with a new deposit address owned by mixer
3. User transfers coins to deposit address
4. Mixer transfers from deposit address to house address
5. Over time mixer distributes user's btc to unused addresses from (1)
