# Index within the parent VisionDetectionArray; contiguous from 0.
uint32 detection_index
# Only bottle or cup in the first version.
string class_name
# Class score, not a position confidence.
float32 confidence
vision_msgs/BoundingBox2D bbox
