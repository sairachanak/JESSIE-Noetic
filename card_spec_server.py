#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from http.server import HTTPServer, BaseHTTPRequestHandler
import json, re, sys

sys.path.append('/home/rachana16/catkin_ws/src/JESSIE/Code_Materials/cards_to_spec')
from qrcode_reader import get_activities_and_sensors

SLUGSIN_TEMPLATE = '/home/rachana16/catkin_ws/src/LTL_stack/controller_executor/examples/mci_ltl/mci_ltl_anon.slugsin'
SLUGSIN_OUT      = '/home/rachana16/catkin_ws/src/LTL_stack/controller_executor/examples/mci_ltl/mci_ltl.slugsin'

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers['Content-Length'])
        cards = json.loads(self.rfile.read(length))

        node_order = [[c['Name'], {'Type': c['Type'], 'Rect': [i,0,1,1]}]
                      for i, c in enumerate(cards)]

        activities, sensors = get_activities_and_sensors(node_order)
        print("Activities: " + str(activities))
        print("Sensors: " + str(sensors))

        # Build ordering section — exactly matching local template format
        new_ordering  = '###### Change order of event nodes here ######\n'
        new_ordering += '# Ordering constraints\n'
        for first, second in zip(activities, activities[1:]):
            new_ordering += '| ! ! {0}Complete ! {1}\'\n'.format(first, second)
        new_ordering += '###### Change reactive nodes here #####\n'
        new_ordering += '# Reactions to person\n'
        if sensors:
            for sensor, reaction in sensors:
                new_ordering += '| ! & {0}\' ! {1}Complete\' {1}\'\n'.format(sensor, reaction)
        else:
            new_ordering += '| ! & scoreHigh\' ! congratulateComplete\' congratulate\'\n'

        with open(SLUGSIN_TEMPLATE, 'r') as f:
            spec = f.read()

        # Replace only the ordering section
        spec = re.sub(
            r'###### Change order of event nodes here ######\n.*?(?=############)',
            new_ordering + '\n',
            spec, flags=re.DOTALL
        )

        # Update SYS_LIVENESS to last activity in sequence
        spec = re.sub(
            r'(\[SYS_LIVENESS\].*?# Finish running the instructions\n)\w+',
            r'\g<1>' + activities[-1],
            spec, flags=re.DOTALL
        )

        with open(SLUGSIN_OUT, 'w') as f:
            f.write(spec)
        print("Spec written to " + SLUGSIN_OUT)

        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'ok': True, 'order': activities}).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args): pass

print("Card spec server running on port 8765...")
HTTPServer(('localhost', 8765), Handler).serve_forever()
