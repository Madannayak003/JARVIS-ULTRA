def spotify_route(command):

    command = command.lower().strip()

    # * =====================================================
    # * Open / Close
    # * =====================================================

    if command == "open spotify":
        return [{"action": "spotify_open"}]

    if command == "close spotify":
        return [{"action": "spotify_close"}]

    # * =====================================================
    # * Play / Resume
    # * =====================================================

    if command in [

        "play spotify",
        "play music",
        "play song",
        "resume spotify",
        "resume music",
        "continue music",
        "continue spotify",
        "start music",
        "start spotify",

    ]:
        return [{"action": "spotify_play"}]

    # * =====================================================
    # * Pause
    # * =====================================================

    if command in [

        "pause spotify",
        "pause music",
        "stop music",
        "stop spotify",

    ]:
        return [{"action": "spotify_pause"}]

    # * =====================================================
    # * Next
    # * =====================================================

    if command in [

        "next song",
        "next music",
        "spotify next",
        "play next song",

    ]:
        return [{"action": "spotify_next"}]

    # * =====================================================
    # * Previous
    # * =====================================================

    if command in [

        "previous song",
        "previous music",
        "spotify previous",
        "play previous song",

    ]:
        return [{"action": "spotify_previous"}]

    # * =====================================================
    # * Spotify Volume Up
    # * =====================================================

    if command in [

        "volume up spotify",
        "volume up music",
        "spotify volume up",
        "increase spotify volume",
        "increase music volume",
        "make spotify louder",
        "make music louder",

    ]:
        return [{"action": "spotify_volume_up"}]

    # * =====================================================
    # * Spotify Volume Down
    # * =====================================================

    if command in [

        "volume down spotify",
        "volume down music",
        "spotify volume down",
        "decrease spotify volume",
        "decrease music volume",
        "make spotify quieter",
        "make music quieter",

    ]:
        return [{"action": "spotify_volume_down"}]

    # * =====================================================
    # ! IMPORTANT:
    # ! YouTube commands must NOT be captured by Spotify.
    # * =====================================================

    if command in [

        # * First video
        "play first video",
        "play the first video",
        "play first youtube video",
        "play the first youtube video",

        # * YouTube video
        "play youtube video",
        "play the youtube video",

        # * Next
        "play next video",
        "play the next video",
        "play next youtube video",
        "play the next youtube video",

        # * Previous
        "play previous video",
        "play the previous video",
        "play previous youtube video",
        "play the previous youtube video",

    ]:
        return None

    # * =====================================================
    # * Play Specific Spotify Song
    # * =====================================================

    if command.startswith("play "):

        song = command[5:].strip()

        if song.endswith(" on spotify"):
            song = song[:-11].strip()

        # * =====================================================
        # * CONTEXTUAL / ORDINAL REFERENCES
        #
        # ! These commands must NEVER be interpreted as a
        # * Spotify song name.
        #
        # * Examples:
        #
        # * play the first one
        # * play the second one
        # * play the third one
        # * play the last one
        # * play that one
        # * play this one
        #
        # * Natural Conversation / Follow-Up routing owns these.
        # * =====================================================

        contextual_play_phrases = {

            "the first one",
            "the second one",
            "the third one",
            "the fourth one",
            "the fifth one",
            "the last one",
            "the next one",
            "the previous one",

            "first one",
            "second one",
            "third one",
            "fourth one",
            "fifth one",
            "last one",
            "next one",
            "previous one",

            "that one",
            "this one",

        }

        if song in contextual_play_phrases:

            return None

        # * =====================================================
        # * Explicit YouTube references
        # * =====================================================

        if (
            "youtube" in song
            or "video" in song
        ):

            return None

        # * =====================================================
        # * Generic Spotify song
        # * =====================================================

        if song not in [
            "spotify",
            "music",
            "song",
        ]:

            return [{
                "action": "spotify_play_song",
                "song": song
            }]

    return None