import os

from app.wallets.manager import WalletManager


def test_wallet_encrypt_decrypt_reveal():
    os.environ["OPERATOR_PASSPHRASE"] = "pw"
    wm = WalletManager(master_key="master")
    created = wm.create_wallet("agent-1")
    pk = wm.export_private_key("agent-1", created["wallet_id"], "pw")
    assert pk.startswith("priv_")
    assert wm.audit_log
