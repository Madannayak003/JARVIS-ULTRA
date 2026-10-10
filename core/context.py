"""
Current session context.

Stores only the current session.
This is NOT long-term memory.
"""

class Context:

    def __init__(self):
        
        self.state = "online"

        self.current_app = None
        self.last_action = None
        self.last_query = None
        self.last_result = None
        
        self.chat_mode = False

        self.current_task = None
        self.current_service = None
        self.current_intent = None
        self.stop_requested = False

        self.history = []

CONTEXT = Context()

# * -----------------------
# * Generic Context Methods
# * -----------------------

def set_value(key, value):

    setattr(CONTEXT, key, value)


def get_value(key):

    return getattr(CONTEXT, key, None)

# * -----------------------
# * Conversation History
# * -----------------------

def add_message(role, text):

    if not text:
        return

    CONTEXT.history.append({
        "role": role,
        "text": text
    })

    CONTEXT.history = CONTEXT.history[-20:]

def get_history():

    return CONTEXT.history


def clear():

    CONTEXT.history.clear()
    
def reset_session():

    CONTEXT.current_app = None
    CONTEXT.last_action = None
    CONTEXT.last_query = None
    CONTEXT.last_result = None

    CONTEXT.chat_mode = False

    CONTEXT.current_task = None
    CONTEXT.current_service = None
    CONTEXT.current_intent = None

    CONTEXT.stop_requested = False

    CONTEXT.history.clear()    

def update_result(result):

    CONTEXT.last_result = result

# * -----------------------
# ! Debug
# * -----------------------

def show():

    print("\n========== CONTEXT ==========")

    print("Current App :", CONTEXT.current_app)
    print("Last Action :", CONTEXT.last_action)
    print("Last Query  :", CONTEXT.last_query)
    print("Last Result :", CONTEXT.last_result)
    print("Chat Mode   :", CONTEXT.chat_mode)
    print("Task        :", CONTEXT.current_task)
    print("Intent      :", CONTEXT.current_intent)
    print("Stop Flag   :", CONTEXT.stop_requested)

    print("\nConversation:")

    for item in CONTEXT.history:

        print(f"{item['role']} : {item['text']}")

    print("=============================\n")