import pytest

from app.humans.job_market import JobMarket, JobPosting
from app.humans.payment_system import PaymentSystem
from app.humans.task_dispatcher import TaskDispatcher
from app.justice.system import JudgeSystem


def test_drone_delivery_lifecycle_with_escrow() -> None:
    market = JobMarket()
    payments = PaymentSystem()
    dispatcher = TaskDispatcher(payments, JudgeSystem())
    job = market.post_job(JobPosting(title="Drone delivery A->B", location="Paris", budget=100))
    assert dispatcher.dispatch(job) == "dispatched"
    assert payments.log.verify()


def test_high_value_hire_escalates() -> None:
    with pytest.raises(ValueError):
        TaskDispatcher(PaymentSystem(), JudgeSystem()).dispatch(
            JobPosting(title="On-site hardware installation", location="Paris", budget=1000)
        )
