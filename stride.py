#!/usr/bin/python

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: stride
version_addded: "2.6"
short_description: Send a message to Hipchat
description:
   - Send a message to a Stride room, with options to control the formatting.
options:
  token:
    description:
      - API token.
    required: true
  site_id:
    description:
      - ID of the cloud.
    required: true
  conversation_id:
    description:
      - ID of the room.
    required: true
  msg:
    description:
      - The message body.
    required: true
  msg_format:
    description:
      - Message format.
    default: text
    choices: [ "text", "markdown", "adf" ]
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be used
        on personally controlled sites using self-signed certificates.
    type: bool
    default: 'yes'
  api:
    description:
      - API url if using a self-hosted stride server.
    default: 'https://api.atlassian.com'
author: "NIEDBALA Dominik (@niedom)"
'''

EXAMPLES = '''
- stride:
    token: OAUTH2_TOKEN
    site_id: SITE_ID
    conversation_id: ROOM_ID
    msg: Ansible task finished
'''

RETURN = '''
msg:
    description: The original message param that was passed in
    type: str
'''

import json
import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils.six.moves.urllib.request import pathname2url
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import fetch_url

DEFAULT_URI = "https://api.atlassian.com/"


def send_msg_adf(module, token, site_id, conversation_id, msg,
                 msg_format='text', api=DEFAULT_URI):
    '''sending message to stride v1 server in adf format'''

    content_type = {
        'text': 'text/plain',
        'markdown': 'text/markdown',
        "adf": 'application/json'
    }

    headers = {'Authorization': 'Bearer %s' % token, 'Content-Type': content_type[msg_format]}

    uri = "site/{0}/conversation/{1}/message".format(site_id, conversation_id)
    url = api + uri

    if module.check_mode:
        # In check mode, exit before actually sending the message
        module.exit_json(changed=False)

    if msg_format == 'adf':
        body = {"version": 1, "type": "doc",
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": msg}]}]}
        data = json.dumps(body)
        response, info = fetch_url(module, url, data=data, headers=headers, method='POST')

    else:
        response, info = fetch_url(module, url, data=msg, headers=headers, method='POST')

    if info['status'] in [200, 201]:
        return response.read()
    else:
        module.fail_json(msg="failed to send message, return status=%s" % str(info['status']))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            token=dict(required=True, no_log=False),
            site_id=dict(required=True, no_log=False),
            conversation_id=dict(required=True, no_log=False),
            msg=dict(required=True),
            msg_format=dict(default="adf", choices=["text", "markdown", "adf"]),
            validate_certs=dict(default='yes', type='bool'),
            api=dict(default=DEFAULT_URI),
        ),
        supports_check_mode=True
    )

    token = module.params["token"]
    site_id = str(module.params["site_id"])
    conversation_id = str(module.params["conversation_id"])
    msg = module.params["msg"]
    msg_format = module.params["msg_format"]
    api = module.params["api"]

    try:
        send_msg_adf(module, token, site_id, conversation_id, msg, msg_format, api)
    except Exception as e:
        module.fail_json(msg="unable to send msg: %s" % to_native(e), exception=traceback.format_exc())

    changed = True
    module.exit_json(changed=changed, msg=msg)


if __name__ == '__main__':
    main()
