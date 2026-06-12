/**
 * SmallEffv3 — Register the effv3-gateway WASM contract on the T3N tenant.
 *
 * BUG-001: tenant.contracts.register() returns the contractId only on the first
 * registration of a given version. Re-registering the same version returns no ID.
 * We probe the raw SDK response for any numeric id field.
 */

import { readFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import type { TenantClient } from "@terminal3/t3n-sdk";

const __dirname = dirname(fileURLToPath(import.meta.url));
const WASM_PATH = join(__dirname, "../../contract/target/wasm32-wasip2/release/effv3_gateway.wasm");

export const CONTRACT_TAIL    = "effv3-gateway";
export const CONTRACT_VERSION = "1.0.0";

export interface ContractInfo {
  tail: string;
  version: string;
  contractId?: number;
}

function extractId(raw: unknown): number | undefined {
  if (!raw || typeof raw !== "object") return undefined;
  const obj = raw as Record<string, unknown>;
  for (const key of ["id", "contractId", "contract_id"]) {
    const v = obj[key];
    if (typeof v === "number" && Number.isInteger(v) && v > 0) return v;
    if (typeof v === "string" && /^\d+$/.test(v)) return parseInt(v, 10);
  }
  return undefined;
}

export function wasmExists(): boolean {
  return existsSync(WASM_PATH);
}

export async function registerGatewayContract(tenant: TenantClient): Promise<ContractInfo> {
  if (!existsSync(WASM_PATH)) {
    throw new Error(`WASM not found: ${WASM_PATH}`);
  }

  const wasm = readFileSync(WASM_PATH);
  const raw = await tenant.contracts.register({
    tail: CONTRACT_TAIL,
    version: CONTRACT_VERSION,
    wasm,
  });

  const contractId = extractId(raw);
  return { tail: CONTRACT_TAIL, version: CONTRACT_VERSION, contractId };
}
