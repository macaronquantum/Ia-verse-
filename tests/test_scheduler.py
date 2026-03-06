from app.agents.scheduler import PriorityScheduler


def test_scheduler_priority_preemption() -> None:
    sched = PriorityScheduler()
    sched.enqueue("memory", "low")
    sched.enqueue("judge", "high")
    assert sched.pop() == "judge"
