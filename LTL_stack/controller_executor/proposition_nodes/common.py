#!/usr/bin/env python3
import rospy
from mci_interactions.srv import DialoguePrompt
from std_msgs.msg import Bool, String, Float32
import json
import argparse

speak_and_display = rospy.ServiceProxy('dialogue/speak_and_display', DialoguePrompt)

def publish_animation(publisher, animation):
    # Kuri robot animation removed — not used with Turtlebot
    rospy.loginfo("[common] Animation skipped: %s" % animation)
