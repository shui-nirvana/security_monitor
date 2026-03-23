import WDK from "@tetherto/wdk";
import WalletManagerEvm from "@tetherto/wdk-wallet-evm";

const readStdin = async () => {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }
  return chunks.join("").trim();
};

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

const main = async () => {
  const raw = await readStdin();
  if (!raw) {
    fail("missing request payload");
  }
  let payload;
  try {
    payload = JSON.parse(raw);
  } catch {
    fail("invalid json payload");
  }

  const seedPhrase = String(payload.seedPhrase || "").trim();
  const rpcUrl = String(payload.rpcUrl || "").trim();
  const chainKey = String(payload.chainKey || "ethereum").trim() || "ethereum";
  const accountIndex = Number(payload.accountIndex || 0);
  if (!seedPhrase) {
    fail("seedPhrase is required");
  }
  if (!rpcUrl) {
    fail("rpcUrl is required");
  }

  const wdk = new WDK(seedPhrase).registerWallet(chainKey, WalletManagerEvm, {
    provider: rpcUrl,
  });
  const account = await wdk.getAccount(chainKey, accountIndex);
  const action = String(payload.action || "").trim();

  if (action === "get_address") {
    const address = await account.getAddress();
    process.stdout.write(JSON.stringify({ success: true, address }));
    return;
  }

  if (action === "get_balance") {
    const tokenContract = payload.tokenContract
      ? String(payload.tokenContract)
      : "";
    const balance = tokenContract
      ? await account.getTokenBalance(tokenContract)
      : await account.getBalance();
    process.stdout.write(
      JSON.stringify({ success: true, balance: balance.toString() }),
    );
    return;
  }

  if (action === "sign") {
    const message = String(payload.message || "");
    const signature = await account.sign(message);
    process.stdout.write(JSON.stringify({ success: true, signature }));
    return;
  }

  if (action === "transfer") {
    const toAddress = String(payload.toAddress || "").trim();
    if (!toAddress) {
      fail("toAddress is required");
    }
    const amountUnits = toBigInt(payload.amountUnits || "0");
    if (amountUnits <= 0n) {
      fail("amountUnits must be > 0");
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

    process.stdout.write(
      JSON.stringify({
        success: true,
        txHash: String(result?.hash || ""),
        blockNumber,
      }),
    );
    return;
  }

  fail(`unsupported action: ${action}`);
};

main().catch((error) => fail(error?.message || String(error)));
