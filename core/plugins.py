import importlib
import pkgutil
import skills


class PluginManager:

    def __init__(self):
        self.plugins = []


    def execute(self, query):

        for plugin in self.plugins:

            try:

                if plugin.run(query):

                    return True

            except Exception as e:

                print(f"[PLUGIN ERROR] {plugin.__name__}: {e}")

        return False
    
    # * Command Registry

COMMANDS = []


def register(keywords, handler):
    """
    Register a command.

    keywords : list[str]
    handler  : function
    """
    COMMANDS.append({
        "keywords": keywords,
        "handler": handler
    })


def execute(query):

    query = query.lower()

    for command in COMMANDS:

        for keyword in command["keywords"]:

            if keyword in query:
                return command["handler"](query)

    return False