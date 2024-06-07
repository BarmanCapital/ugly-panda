# TON Speedrun 

## 🚩 Challenge 1: Simple NFT Deploy

🎫 Mint simple NFT on TON . Let's look at smart contracts of the NFT standard in TON. Get information about the deployed collection in the TON network. And send a message to the collection and thus deploy the NFT

🌟 The final deliverable will be NFT minted on the TON testnet.

💬 Meet other builders working in TON and get help in the [official dev chat](https://t.me/tondev_eng) or [TON learn tg](https://t.me/ton_learn)

---

# Checkpoint 0: 📦   Install 📚

Required: 
* [Git](https://git-scm.com/downloads)
* [Node](https://nodejs.org/en/download/) (Use Version 18 LTS)
* [Yarn](https://classic.yarnpkg.com/en/docs/install/#mac-stable)

(⚠️ Don't install the linux package `yarn` make sure you install yarn with `npm i -g yarn` or even `sudo npm i -g yarn`!)

```sh
git clone https://github.com/romanovichim/TONQuest1.git
```
```sh
cd challenge-1
yarn install
```
---

# Checkpoint 1:  🎓 NFT Standart in TON ✒️

So, non-fungible tokens are assets, each instance of which is unique (specific) and cannot be replaced by another similar asset. A non-fungible token is some kind of digital entity certificate with the ability to transfer the certificate through some mechanism.

In the TON network, the [NFT standard](https://github.com/ton-blockchain/TEPs/blob/master/text/0062-nft-standard.md) describes two types of contracts:

- collection smart contract
- smart contract for a separate NFT(NFT Item)

Collection smart contract allows you to mint NFT.

I think that's enough theory, let's look at the code!

---

# Checkpoint 2: 👓 Let's look at the contracts 💫

Open the contracts folder:

![1](https://user-images.githubusercontent.com/18370291/253742060-80b76594-d28d-4289-8d00-6f5d13900912.PNG)

Smart contracts in TON are usually written in [FunC](https://docs.ton.org/develop/func/overview) or [Tact](https://tact-lang.org/). In the folder, you can see the collection NFT smart contract and the NFT element smart contract written in the FunC language. The `imports` folder contains the helper code.

In the next quests, we will learn how to deploy smart contracts, but in this case, I decided to help you and have already deposited the smart contract of the collection. By the way, you can see its code in the `nft-collection.fc` file.

Smart contracts in TON communicate by messages, so usually smart contracts consist of message handlers and get methods.

Get methods - methods that can return some information, for example, about the NFT collection. Let's make a request to the collection and get information about the collection where we will mint our NFT.

---

# Checkpoint 3: 📐 Let's get information about the collection 📏

Ready to make a request to the testnet?!?

For a request in `scripts` folder in `getCollectionData.ts` file, I prepared the `getCollectionData()` function, which will execute a request to the `get_collection_data` get method:

![image](https://user-images.githubusercontent.com/18370291/253797801-5a41e949-8e55-4509-a197-5ade55cc3661.png)

Let's run it with the command `yarn getcol`:

```sh
yarn getcol
```

Result:

![image](https://i.imgur.com/1Goq23y.png)

`get_collection_data` mandatory NFT standard method, this method returns:

`next_item_index` - the count of currently deployed NFT items in collection.
`collection_content` - collection content in a format that complies with standard [TEP-64](https://github.com/ton-blockchain/TEPs/blob/master/text/0064-token-data-standard.md).
`owner_address` - collection owner address, zero address if no owner.

`next_item_index` is needed to understand what number we should release NFT with, i.e. what is the next number)

---

# Checkpoint 4:  💊 Сollect the body of the message for NFT mint 💾

As mentioned above, smart contracts exchange messages, in order to mint the NFT, you need to send a message to the collection contract.
You can put some paylod in the message - message body. Let's assemble the body for mint NFT. Open `deployNft.ts` file. It looks like this:

![image](https://i.imgur.com/W3B5ppj.png)

The body of the message will be a [cell](https://docs.ton.org/learn/overviews/cells) - the data type of the TON network. The first thing we will put in the message will be the service parameters `op` and `query_id`, we will not dwell on them in this quest.

Next is the index of our future NFT, a small number of coins and a cell with an address and, in fact, what will be stored inside the NFT. Since this is an example, we will simply use the `item.json` as a NFT item content.

P.S Assembly of the body is in the file `deployNFT.ts`

---

# Checkpoint 5: 💸  Testnet Coins 💰

An attentive reader may have a question, who should send a message with the body we have collected to the smart contract of the collection. There are wallets for this, the wallet can receive external messages and send internal ones, so for mint nft we need a wallet. There are many [different wallets](https://ton.org/wallets) in TON, but I suggest you use a [Tonkeeper](https://tonkeeper.com/).

Let's use the wallet by switching it to the test network and get coins in the test network - we need them to send a message:
1) Go to the settings and scroll to the very bottom until the inscription "Tonkeeper version X" 
2) Click 6 times in a row quickly on the Tonkeeper icon above the inscription - the menu for developers will open 
3) select switch to the test network in it 
4) to get to the wallet in the test network, test TON, you need to use the tap: https://t.me/testgiver_ton_bot

---

# Checkpoint 6: 📌 Mint NFT 📌 

Ready to mint to the testnet?!?

```sh
yarn deploynft 
```

On the screen you will see a QR code, scan it and confirm the transaction in the wallet.

Congratulations, you minted nft on the network TON!


## Mainnet 

If you want to mint your NFT on mainnet (for example, so that it is displayed in the [society.ton.org](https://society.ton.org) profile). Follow these steps:

1. Open `scripts/utils.ts` file and delete `testnet.` part from toncenter endpoint url. After that it should look like this:
```typescript
export const toncenter = new TonClient({
	endpoint: 'https://toncenter.com/api/v2/jsonRPC',
});
```
2. Use your mainnet wallet to scan this qr-code.

P.S. and don't forget to change the address in `script/deployNFT.ts` to your address =)

---

# Checkpoint 7: 🎫 Check NFT 😀

<img src="https://ton-devrel.s3.eu-central-1.amazonaws.com/tonspeedrun/-1/image.jpg" style="max-width: 50%; display: block; margin: 10pt auto">

Let's check if you did everything right. Let's find your NFT in the blockchain explorer.

## Testnet

Take the address of our collection and open it in the explorer:

https://testnet.explorer.tonnft.tools/collection/EQDf6HCOggN_ZGL6YsYleN6mDiclQ_NJOMY-x8G5cTRDOBW4

## Mainnet

For Mainnet, use you can use this link:

https://explorer.tonnft.tools/collection/EQDf6HCOggN_ZGL6YsYleN6mDiclQ_NJOMY-x8G5cTRDOBW4

## Check the NFT

Scroll down and find your NFT in the list!

Since this is an example, the link in the content of NFT is not working, but when you create your projects, you can sew up any links you want.

P.S. If you want to see an NFT in your wallet, don't forget to change owner address in `deployNft.ts` file!

---


# ⚔️ Side Quests

Quick results are great, but to play longer, enjoy the ecosystem, I suggest you the following tutorials:

- Understand how to [compile](https://github.com/romanovichim/TonFunClessons_Eng/blob/main/lessons/pipeline/simplesmartcontract.md) a smart contract
- Learn to write [tests](https://github.com/romanovichim/TonFunClessons_Eng/blob/main/lessons/pipeline/simpletest.md) for smart contracts
- And of course, [deploy](https://github.com/romanovichim/TonFunClessons_Eng/blob/main/lessons/pipeline/simpledeploy.md) your smart contract to the test network

After that, I suggest you delve into the language for TON smart contracts:

 - https://github.com/romanovichim/TonFunClessons_Eng






 
