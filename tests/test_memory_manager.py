from app.memory.episodic import MemoryManager


def test_memory_condensation_and_retrieval() -> None:
    manager = MemoryManager()
    manager.remember("agent posted a tool")
    manager.remember("first customer acquired")
    summary = manager.condense()
    rows = manager.query("customer", 1)
    assert "customer" in summary
    assert rows
