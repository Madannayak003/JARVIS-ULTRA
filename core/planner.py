from core.router import route

def execute_plan(intents):

    for intent in intents:

        print(intent)

        if intent.action == "open":

            route("open " + intent.target)

        elif intent.action == "search":

            route(intent.target)

        elif intent.action == "play":

            route(intent.target)

        elif intent.action == "whatsapp":

            route(intent.target)

        else:

            print("Unknown:", intent.target)