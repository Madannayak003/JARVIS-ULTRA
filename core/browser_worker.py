_running = False


def browser_busy():

    return _running


def browser_start():

    global _running

    _running = True


def browser_stop():

    global _running

    _running = False