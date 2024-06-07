import { TonClient } from 'ton';
import { Address } from 'ton-core';

export const toncenter = new TonClient({
	endpoint: 'https://testnet.toncenter.com/api/v2/jsonRPC',
});

export const nftCollectionAddress = Address.parse('EQDf6HCOggN_ZGL6YsYleN6mDiclQ_NJOMY-x8G5cTRDOBW4');
//https://testnet.explorer.tonnft.tools/collection/EQDf6HCOggN_ZGL6YsYleN6mDiclQ_NJOMY-x8G5cTRDOBW4




export async function getCollectionData() {

	let { stack } = await toncenter.callGetMethod(
		nftCollectionAddress, 
		'get_collection_data'
	);
	let nextItemIndex = stack.readBigNumber();
	let contentRoot = stack.readCell();
	let owner = stack.readAddress();

	console.log('Collection info, from get_collection_data() method:')	
	console.log('Next item index:', nextItemIndex.toString());
	console.log('Content root cell:', contentRoot);
	console.log('Collection owner adress:', owner);

	return nextItemIndex;
}

getCollectionData();

