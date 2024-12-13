#! /usr/bin/env python

from atproto import Client, client_utils, IdResolver, models
from pathlib import Path
import os
import traceback
from random import randrange

session_file_name = "session.txt"
words_filename = "words.txt"

post_size = 300

def get_client():
    uname = os.environ.get('BSKY_NAME')
    pw = os.environ.get('BSKY_PASS')
    client = Client()
    if os.path.isfile(session_file_name):
        with open(session_file_name) as inf:
            session_str = inf.read()
        try:
            client.login(session_string=session_str)
        except: # This should catch the proper exception
            client.login(uname, pw)
    else:
        client.login(uname, pw)
    return client


def save_session_string(client):
    session_string = client.export_session_string()
    with open(session_file_name, 'w') as outf:
        outf.write(session_string)


def construct_post_text(words):
    n_words = len(words)
    msg = ""
    while 1:
        next_word = words[randrange(n_words)]
        if len(msg) + len(next_word) + 1 <= post_size:
            msg += f" {next_word}"
        else:
            break
    return msg.strip().capitalize()


def send_dm(client, msg):
    """
    Sends a direct message to the bsky user specified in BSKY_DM_TARGET.
    Used when starting a book, when the last of the book has been posted,
    and if an error occurs after client creation
    """
    dm_target = os.environ.get("BSKY_DM_TARGET")
    id_resolver = IdResolver()
    chat_to = id_resolver.handle.resolve(dm_target)

    dm_client = client.with_bsky_chat_proxy()
    dm = dm_client.chat.bsky.convo

    convo = dm.get_convo_for_members(
        models.ChatBskyConvoGetConvoForMembers.Params(members=[chat_to]),
    ).convo

    dm.send_message(
        models.ChatBskyConvoSendMessage.Data(
            convo_id=convo.id,
            message=models.ChatBskyConvoDefs.MessageInput(
                text=msg,
            ),
        )
    )


def post_text(client, text):
    p = client_utils.TextBuilder().text(text)
    client.send_post(p)

if __name__ == '__main__':
    # Connect to bluesky
    client = get_client()
    try:
        # Read in the words
        with open(words_filename) as inf:
            word_list = inf.read().splitlines()

        noise = construct_post_text(word_list)

        # Post the next noise
        post_text(client, noise)
        save_session_string(client)

    except Exception as exp:
        # This only works if the client was successfully created
        trace = "\n" + "\n".join(traceback.format_exception(exp))
        err_message = f"Error in noisebot: {trace}"
        send_dm(client, err_message)
