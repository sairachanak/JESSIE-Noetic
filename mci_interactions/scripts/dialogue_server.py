#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import rospy
import json
import threading
import tkinter as tk
import queue
from mci_interactions.srv import DialoguePrompt, DialoguePromptResponse
from std_msgs.msg import String

dialogue_pub = None
user_response_pub = None
tk_queue = queue.Queue()
user_response_event = threading.Event()
user_response_value = ['']

def on_user_response(msg):
    user_response_value[0] = msg.data
    user_response_event.set()

def show_tkinter(prompt, is_text_input):
    done = threading.Event()
    root = tk.Tk()
    root.title("JESSIE")
    root.geometry("640x400")
    root.configure(bg="#0d1320")
    root.attributes("-topmost", True)

    tk.Label(root, text=prompt, wraplength=580, font=("Arial", 14),
             justify="left", bg="#0d1320", fg="#dde6f5", pady=8
             ).pack(padx=24, pady=20, fill="x")

    if is_text_input:
        entry = tk.Text(root, height=4, font=("Arial", 13),
                        bg="#1a2540", fg="#dde6f5", insertbackground="white",
                        relief="flat", padx=8, pady=8)
        entry.pack(padx=24, pady=6, fill="x")
        def submit():
            val = entry.get("1.0", "end").strip()
            if val:
                user_response_pub.publish(String(data=val))
                rospy.loginfo("[TKINTER] Submitted: %s", val)
            done.set()
            root.destroy()
        tk.Button(root, text="Submit", command=submit,
                  font=("Arial", 13, "bold"), bg="#9b7dff", fg="white",
                  relief="flat", padx=20, pady=10).pack(pady=12)
    else:
        def cont():
            rospy.loginfo("[TKINTER] Continue clicked")
            done.set()
            root.destroy()
        tk.Button(root, text="Continue", command=cont,
                  font=("Arial", 13, "bold"), bg="#00e5c0", fg="#000000",
                  relief="flat", padx=20, pady=10).pack(pady=12)

    root.mainloop()
    done.set()

def handle_dialogue(req):
    try:
        parsed = json.loads(req.dialogue)
        prompt = parsed.get("Prompt", req.dialogue)
        responses = parsed.get("Responses", [])
    except:
        prompt = req.dialogue
        responses = []

    rospy.loginfo("=== ROBOT SAYS: %s ===" % prompt)

    if dialogue_pub:
        dialogue_pub.publish(String(data=prompt))

    # No responses — return immediately
    if not responses:
        return DialoguePromptResponse(success=True, selected_response="")

    is_text_input = "$TEXT_INPUT" in responses or "$NUMBER_INPUT" in responses

    if is_text_input:
        # Reset event before showing popup
        user_response_event.clear()
        user_response_value[0] = ''

    # Show tkinter popup
    result_event = threading.Event()
    tk_queue.put((prompt, is_text_input, result_event))
    result_event.wait()

    if is_text_input:
        # Wait for user_response topic (published by tkinter submit)
        user_response_event.wait(timeout=300.0)
        return DialoguePromptResponse(success=True, selected_response=user_response_value[0])

    return DialoguePromptResponse(success=True, selected_response="Continue")

if __name__ == '__main__':
    rospy.init_node('dialogue_server')
    dialogue_pub = rospy.Publisher('/jessie_dialogue', String, queue_size=10)
    user_response_pub = rospy.Publisher('/mci_interactions/user_response', String, queue_size=10)
    rospy.Subscriber('/mci_interactions/user_response', String, on_user_response)
    rospy.sleep(1.0)
    rospy.Service('dialogue/speak_and_display', DialoguePrompt, handle_dialogue)
    rospy.loginfo("Dialogue server ready.")
    while not rospy.is_shutdown():
        try:
            prompt, is_text_input, result_event = tk_queue.get(timeout=0.1)
            show_tkinter(prompt, is_text_input)
            result_event.set()
        except:
            pass
