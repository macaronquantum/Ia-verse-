from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    from solders.keypair import Keypair
    from solders.pubkey import Pubkey
    SOLANA_AVAILABLE = True
except ImportError:
    SOLANA_AVAILABLE = False
    logger.warning("solders not available — Solana wallet generation disabled")


@dataclass
class SolanaWallet:
    public_key: str
    private_key: str
    agent_id: str


class SolanaWalletManager:
    def __init__(self) -> None:
        self._wallets: dict[str, SolanaWallet] = {}

    def get_or_create(self, agent_id: str) -> SolanaWallet | None:
        if agent_id in self._wallets:
            return self._wallets[agent_id]

        if not SOLANA_AVAILABLE:
            return None

        try:
            kp = Keypair()
            wallet = SolanaWallet(
                public_key=str(kp.pubkey()),
                private_key=str(kp),
                agent_id=agent_id,
            )
            self._wallets[agent_id] = wallet
            return wallet
        except Exception as e:
            logger.warning(f"Failed to create Solana wallet for {agent_id}: {e}")
            return None

    def get_wallet(self, agent_id: str) -> SolanaWallet | None:
        return self._wallets.get(agent_id)

    def get_all_wallets(self) -> list[SolanaWallet]:
        return list(self._wallets.values())

    def wallet_count(self) -> int:
        return len(self._wallets)
