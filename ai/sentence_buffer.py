def sentence_buffer():

    text = ""

    while True:

        token = yield

        text += token

        if token.endswith((".", "!", "?")):

            yield text.strip()

            text = ""