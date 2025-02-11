from collections import deque


def trim_queue(q: deque, context_window_size: int, init_prompts: list[str]) -> None:
    if len(q) + 2 > context_window_size:
        for _ in range(len(init_prompts)):
            q.popleft()
        q.popleft()
        q.popleft()
        for prompt in reversed(init_prompts):
            q.appendleft(prompt)


def dump_message_to_file(role, message: str, filename: str) -> None:
    with open(filename, "a") as f:
        f.write(f"{role}: {message}\n")
        if role == "User":
            return
        f.write("\n")
