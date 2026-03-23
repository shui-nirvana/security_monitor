import WDK from "@tetherto/wdk";
import WalletManagerEvm from "@tetherto/wdk-wallet-evm";
import readline from "node:readline";

const contextCache = new Map();

const toBigInt = (value) => {
  if (typeof value === "bigint") {
    return value;
  }
  if (typeof value === "number") {
    return BigInt(Math.trunc(value));
  }
  return BigInt(String(value));
};

const fail = (message) => {
  process.stderr.write(String(message));
  process.exit(1);
};

const getContext = async (payload) => {
  const seedPhrase = String(payload.seedPhrase || "").trim();
  const rpcUrl = String(payload.rpcUrl || "").trim();
  const chainKey = String(payload.chainKey || "ethereum").trim() || "ethereum";
  const accountIndex = Number(payload.accountIndex || 0);
  if (!seedPhrase) {
    throw new Error("seedPhrase is required");
  }
  if (!rpcUrl) {
    throw new Error("rpcUrl is required");
  }
  const cacheKey = `${seedPhrase}|${rpcUrl}|${chainKey}|${accountIndex}`;
  const cached = contextCache.get(cacheKey);
  if (cached) {
    return cached;
  }
  const wdk = new WDK(seedPhrase).registerWallet(chainKey, WalletManagerEvm, {
    provider: rpcUrl,
  });
  const account = await wdk.getAccount(chainKey, accountIndex);
  const context = { account };
  contextCache.set(cacheKey, context);
  return context;
};

const handleRequest = async (payload) => {
  const { account } = await getContext(payload);
  const action = String(payload.action || "").trim();

  if (action === "get_address") {
    const address = await account.getAddress();
    return { success: true, address };
  }

  if (action === "get_balance") {
    const tokenContract = payload.tokenContract
      ? String(payload.tokenContract)
      : "";
    const balance = tokenContract
      ? await account.getTokenBalance(tokenContract)
      : await account.getBalance();
    return { success: true, balance: balance.toString() };
  }

  if (action === "sign") {
    const message = String(payload.message || "");
    const signature = await account.sign(message);
    return { success: true, signature };
  }

  if (action === "transfer") {
    const toAddress = String(payload.toAddress || "").trim();
    if (!toAddress) {
      throw new Error("toAddress is required");
    }
    const amountUnits = toBigInt(payload.amountUnits || "0");
    if (amountUnits <= 0n) {
      throw new Error("amountUnits must be > 0");
    }
    const tokenContract = payload.tokenContract
      ? String(payload.tokenContract)
      : "";
    const waitForReceipt = Boolean(payload.waitForReceipt);

    let result;
    if (tokenContract) {
      result = await account.transfer({
        token: tokenContract,
        recipient: toAddress,
        amount: amountUnits,
      });
    } else {
      result = await account.sendTransaction({
        to: toAddress,
        value: amountUnits,
      });
    }

    const blockNumber = waitForReceipt ? Number(result?.blockNumber || 0) : 0;

    return {
      success: true,
      txHash: String(result?.hash || ""),
      blockNumber,
    };
  }

  throw new Error(`unsupported action: ${action}`);
};

const writeResponse = (response) => {
  process.stdout.write(`${JSON.stringify(response)}\n`);
};

const main = async () => {
  const rl = readline.createInterface({
    input: process.stdin,
    crlfDelay: Infinity,
    terminal: false,
  });
  for await (const line of rl) {
    const raw = String(line || "").trim();
    if (!raw) {
      continue;
    }
    try {
      const payload = JSON.parse(raw);
      const response = await handleRequest(payload);
      writeResponse(response);
    } catch (error) {
      writeResponse({
        success: false,
        error: error?.message || String(error),
      });
    }
  }
};

main().catch((error) => fail(error?.message || String(error)));
