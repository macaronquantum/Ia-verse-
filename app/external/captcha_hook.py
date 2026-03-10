from __future__ import annotations

def solve_captcha_stub(dev_mode: bool = True) -> str:
    if not dev_mode:
        raise ValueError("Captcha solving requires approved production integration and Judge policy.")
    return "dev-captcha-token"
