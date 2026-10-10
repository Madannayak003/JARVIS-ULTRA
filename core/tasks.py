import re


def split_commands(query):

    query = query.lower()

    separators = [
        " then ",
        " and then ",
        " and ",
        ",",
        " after that ",
        " next "
    ]

    commands = [query]

    for sep in separators:

        temp = []

        for cmd in commands:
            temp.extend(cmd.split(sep))

        commands = temp

    return [c.strip() for c in commands if c.strip()]