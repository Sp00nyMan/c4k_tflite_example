# This example demonstrates Object Detection using Tensorflow Lite
# It is based on:
# https://github.com/tensorflow/examples/tree/master/lite/examples/object_detection
#
import time
from kivy.clock import mainthread
from kivy.graphics import Color, Line, Rectangle
from kivy.core.text import Label as CoreLabel
from kivy.metrics import dp, sp
from kivy.utils import platform
import numpy as np
from camera4kivy import Preview
from object_detection.object_detector import ObjectDetector
from object_detection.object_detector import ObjectDetectorOptions

import cv2


class ClassifyObject(Preview):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.classified = []
        num_threads = 4
        enable_edgetpu = False    ## Change this for Coral Accererator
        if platform == 'android':
            model = 'object_detection/model.tflite'
        elif enable_edgetpu:
            model = 'object_detection/efficientdet_lite0_edgetpu.tflite'
        else:
            model = r'C:\Users\mrsto\Desktop\c4k_tflite_example\object_detection\efficientdet_lite0.tflite'#'object_detection/efficientdet_lite0.tflite'
        options = ObjectDetectorOptions(
            num_threads = 4,
            score_threshold = 0.45,
            max_results = 3,
            enable_edgetpu = enable_edgetpu)
        self.detector = ObjectDetector(model_path=model, options=options)
        self.start_time = time.time()

    ####################################
    # Analyze a Frame - NOT on UI Thread
    ####################################

    def analyze_pixels_callback(self, pixels, image_size, image_pos,
                                image_scale, mirror):

        rgba = np.fromstring(pixels, np.uint8).reshape(image_size[1],
                                                       image_size[0], 4)
        image = cv2.cvtColor(rgba, cv2.COLOR_RGBA2RGB)
        detections = self.detector.detect(image)
        now = time.time()
        fps = 0
        if now - self.start_time:
            fps = 1 / (now - self.start_time)
        self.start_time = now
        found = []
        for detection in detections:
            # Bounding box, pixels coordinates
            x = detection.bounding_box.left
            y = detection.bounding_box.top
            w = detection.bounding_box.right - x 
            h = detection.bounding_box.bottom - y

            # Map tflite style coordinates to Kivy Preview coordinates
            y = max(image_size[1] -y -h, 0)
            if mirror:
                x = max(image_size[0] -x -w, 0)
                
            # Map Analysis Image coordinates to Preview coordinates
            x = round(x * image_scale + image_pos[0])
            y = round(y * image_scale + image_pos[1])
            w = round(w * image_scale)
            h = round(h * image_scale)

            # Category text for canvas
            category = detection.categories[0]
            class_name = category.label
            probability = round(category.score, 2)
            result_text = class_name +\
                ' (Probability: {:.2f} FPS: {:.1f} )'.format(probability,fps)
            label = CoreLabel(font_size = sp(20))
            label.text = result_text
            label.refresh()

            # Thread safe result
            found.append({'x':x, 'y':y, 'w':w, 'h':h, 't': label.texture})
        self.make_thread_safe(list(found)) ## A COPY of the list            

    @mainthread
    def make_thread_safe(self, found):
        self.classified = found

    ################################
    # Canvas Update  - on UI Thread
    ################################
        
    def canvas_instructions_callback(self, texture, tex_size, tex_pos):
        # Add the analysis annotations
        Color(0,1,0,1)
        for r in self.classified:
            # Draw box
            Line(rectangle=(r['x'], r['y'], r['w'], r['h']), width = dp(1.5))
            # Draw text
            Rectangle(size = r['t'].size,
                      pos = [r['x'] + dp(10), r['y'] + dp(10)],
                      texture = r['t'])       

