import time

last_command = None
last_time = 0

def is_duplicate(command):

    global last_command, last_time

    current_time = time.time()

    if command == last_command and (current_time - last_time) < 2:
        return True

    last_command = command
    last_time = current_time

    return False