# Testnet Deployment Guide — SmallEFFV3 Part 2

## Prerequisites

1. **Node.js** (v18+) — for the web interface
2. **Rust** — for Casper smart contract compilation
3. **Casper Testnet tokens** — from the Testnet faucet

## Wallet Preparation

1. Create a Casper Testnet wallet via CSPR.click or `casper-client`
2. Fund it from the Testnet faucet
3. Note the wallet address and secret key

## Environment Setup

```bash
cp .env.example .env
# Edit .env with your values:
# CASPER_NODE_URL=https://testnet.cspr.cloud/rpc
# CASPER_NETWORK=casper-test
# OPENROUTER_API_KEY=your-key
# CSPR_CLICK_API_KEY=your-key
# MAX_TEST_TRANSFER_MOTES=10000000000
# APPROVED_RECIPIENTS=your-testnet-address
# CASPER_CONTRACT_HASH=deployed-contract-hash
```

## Contract Deployment

```bash
# Install Odra (if available)
cargo install odra-cli

# Build the contract
cd contracts/governed_receipt/
cargo build --release

# Deploy to Testnet
odra-cli deploy --network casper-test --wallet <wallet-path>

# Record the contract hash in .env
```

## Verify Deployment

```bash
# Query contract state
casper-client query-state \
  --node-address https://testnet.cspr.cloud/rpc \
  --contract-hash <your-contract-hash>

# Check wallet balance
casper-client get-account-info \
  --node-address https://testnet.cspr.cloud/rpc \
  --account <your-account-hex>
```

## Run the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run demo
python demo/run_demo.py

# Start the app (when web interface is ready)
python app/main.py
```

## Record Evidence

For the buildathon submission, record:
1. Contract hash after deployment
2. Transaction hash after submission
3. Screenshot of on-chain state query
4. Screenshot of the governed receipt
