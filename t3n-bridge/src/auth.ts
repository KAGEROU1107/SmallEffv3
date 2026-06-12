/**
 * SmallEffv3 — Terminal 3 authentication layer.
 * Real T3N testnet auth via the official @terminal3/t3n-sdk.
 * The API key is an Ethereum private key; eth_get_address derives the address;
 * metamask_sign handles EIP-191 signing offline (no browser required).
 */

import {
  T3nClient,
  TenantClient,
  setEnvironment,
  loadWasmComponent,
  eth_get_address,
  metamask_sign,
  createDefaultHandlers,
  createEthAuthInput,
  getNodeUrl,
} from "@terminal3/t3n-sdk";

export interface T3nSession {
  t3n: T3nClient;
  tenant: TenantClient;
  tenantDid: string;
  address: string;
}

export async function createSession(apiKey: string): Promise<T3nSession> {
  setEnvironment("testnet");
  const nodeUrl = getNodeUrl();
  const wasmComponent = await loadWasmComponent();
  const address = eth_get_address(apiKey);

  const t3n = new T3nClient({
    baseUrl: nodeUrl,
    wasmComponent,
    handlers: {
      ...createDefaultHandlers(nodeUrl),
      EthSign: metamask_sign(address, undefined, apiKey),
    },
  });

  await t3n.handshake();
  const didResult = await t3n.authenticate(createEthAuthInput(address));
  const tenantDid = didResult.value;

  const tenant = new TenantClient({ t3n, baseUrl: nodeUrl, tenantDid });
  return { t3n, tenant, tenantDid, address };
}
