from app.economy.central_bank import CentralBank
from app.economy.markets import Order, OrderBook


def test_order_matching_and_central_bank_logging() -> None:
    book = OrderBook()
    book.place(Order("bid", 10, 5))
    book.place(Order("ask", 9, 3))
    trades = book.match()
    assert trades and trades[0][1] == 3

    cb = CentralBank()
    cb.mint(100)
    cb.burn(10)
    assert cb.log.verify()
