from app.external.account_manager import AccountManager


def test_account_manager_dev_flow_and_encrypted_storage() -> None:
    mgr = AccountManager()
    session = mgr.create_account("example.com", {"username": "a", "password": "secret"})
    assert session.encrypted_secret != "secret"
    mgr.login_and_action(session, {"type": "login"})
    res = mgr.post_content(session, {"body": "hello"})
    assert res["status"] == "posted"
