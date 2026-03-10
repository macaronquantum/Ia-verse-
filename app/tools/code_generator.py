from __future__ import annotations


def run(params: dict) -> dict:
    language = params.get("language", "python")
    task = params.get("task", "print hello")
    return {"language": language, "code": f"# generated\n# task: {task}\nprint('hello from agent')"}
