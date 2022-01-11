import sys

import googleapiclient.errors

import gam
from gam.var import *
from gam import controlflow
from gam import display
from gam import fileutils
from gam import gapi
from gam import utils
from gam.gapi import errors as gapi_errors

# Chat scope isn't in discovery doc so need to manually set
CHAT_SCOPES = ['https://www.googleapis.com/auth/chat.bot']


def build():
    return gam.buildGAPIServiceObject('chat',
                                      act_as=None,
                                      scopes=CHAT_SCOPES)


THROW_REASONS = [
        gapi_errors.ErrorReason.FOUR_O_FOUR,     # Chat API not configured
        ]

def _chat_error_handler(chat, err):
    if err.status_code == 404:
        project_id = chat._http.credentials.project_id
        url = f'https://console.cloud.google.com/apis/api/chat.googleapis.com/hangouts-chat?project={project_id}'
        print('ERROR: you need to configure Google Chat for your API project. Please go to:')
        print()
        print(f'  {url}')
        print()
        print('and complete all fields.')
    else:
        raise err
    sys.exit(1)


def print_spaces():
    chat = build()
    todrive = False
    i =3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'todrive':
            todrive = True
            i += 1
        else:
            controlflow.invalid_argument_exit(myarg, 'gam print chatspaces')
    try:
        spaces = gapi.get_all_pages(chat.spaces(), 'list', 'spaces', throw_reasons=THROW_REASONS)
    except googleapiclient.errors.HttpError as err:
        _chat_error_handler(chat, err)
    if not spaces:
        print('Bot not added to any Chat rooms or users yet.')
    else:
        display.write_csv_file(spaces, spaces[0].keys(), 'Chat Spaces', todrive)


def print_members():
    chat = build()
    space = None
    todrive = False
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'space':
            space = sys.argv[i+1]
            if space[:7] != 'spaces/':
                space = f'spaces/{space}'
            i += 2
        elif myarg == 'todrive':
            todrive = True
            i += 1
        else:
            controlflow.invalid_argument_exit(myarg, 'gam print chatmembers')
    if not space:
        controlflow.system_error_exit(2,
                                      'space <ChatSpace> is required.')
    try:
        results = gapi.get_all_pages(chat.spaces().members(), 'list', 'memberships', parent=space)
    except googleapiclient.errors.HttpError as err:
        _chat_error_handler(chat, err)
    members = []
    titles = []
    for result in results:
        member = utils.flatten_json(result)
        for key in member:
            if key not in titles:
                titles.append(key)
        members.append(utils.flatten_json(result))
    display.write_csv_file(members, titles, 'Chat Members', todrive)


def create_message():
    chat = build()
    body = {}
    i = 3
    while i < len(sys.argv):
      myarg = sys.argv[i].lower()
      if myarg == 'text':
          body['text'] = sys.argv[i+1].replace('\\r', '\r').replace('\\n', '\n')
          i += 2
      elif myarg == 'textfile':
          filename = sys.argv[i + 1]
          i, encoding = gam.getCharSet(i + 2)
          body['text'] = fileutils.read_file(filename, encoding=encoding)
      elif myarg == 'space':
          space = sys.argv[i+1]
          if space[:7] != 'spaces/':
              space = f'spaces/{space}'
          i += 2
      elif myarg == 'thread':
          body['thread'] = {'name': sys.argv[i+1]}
          i += 2
      else:
          controlflow.invalid_argument_exit(myarg, 'gam create chat')
    if not space:
        controlflow.system_error_exit(2,
                                      'space <ChatSpace> is required.')
    if 'text' not in body:
        controlflow.system_error_exit(2,
                                      'text <String> or textfile <FileName> is required.')
    if len(body['text']) > 4096:
        body['text'] = body['text'][:4095]
        print('WARNING: trimmed message longer than 4k to be 4k in length.')
    try:
        resp = gapi.call(chat.spaces().messages(),
                         'create',
                          parent=space,
                          body=body,
                          throw_reasons=THROW_REASONS)
    except googleapiclient.errors.HttpError as err:
        _chat_error_handler(chat, err)
    if 'thread' in body:
        print(f'responded to thread {resp["thread"]["name"]}')
    else:
        print(f'started new thread {resp["thread"]["name"]}')
    print(f'message {resp["name"]}')

def delete_message():
    chat = build()
    name = None
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'name':
            name = sys.argv[i+1]
            i += 2
        else:
          controlflow.invalid_argument_exit(myarg, 'gam delete chat')
    if not name:
        controlflow.system_error_exit(2,
                                      'name <String> is required.')
    try:
        gapi.call(chat.spaces().messages(),
                  'delete',
                  name=name)
    except googleapiclient.errors.HttpError as err:
        _chat_error_handler(chat, err)


def update_message():
    chat = build()
    body = {}
    name = None
    updateMask = 'text'
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'text':
            body['text'] = sys.argv[i+1].replace('\\r', '\r').replace('\\n', '\n')
            i += 2
        elif myarg == 'textfile':
            filename = sys.argv[i + 1]
            i, encoding = gam.getCharSet(i + 2)
            body['text'] = fileutils.read_file(filename, encoding=encoding)
        elif myarg == 'name':
            name = sys.argv[i+1]
            i += 2
        else:
          controlflow.invalid_argument_exit(myarg, 'gam update chat')
    if not name:
        controlflow.system_error_exit(2,
                                      'name <String> is required.')
    if 'text' not in body:
        controlflow.system_error_exit(2,
                                      'text <String> or textfile <FileName> is required.')
    if len(body['text']) > 4096:
        body['text'] = body['text'][:4095]
        print('WARNING: trimmed message longer than 4k to be 4k in length.')
    try:
        resp = gapi.call(chat.spaces().messages(),
                         'update',
                         name=name,
                         updateMask=updateMask,
                         body=body)
    except googleapiclient.errors.HttpError as err:
        _chat_error_handler(chat, err)
    if 'thread' in body:
        print(f'updated response to thread {resp["thread"]["name"]}')
    else:
        print(f'updated message on thread {resp["thread"]["name"]}')
    print(f'message {resp["name"]}')
