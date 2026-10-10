from core.executor import execute_ai_plan

_running = False

def execute_plan(plan):

    global _running

    if _running:
        return

    _running = True

    try:

        execute_ai_plan(plan)

    finally:

        _running = False