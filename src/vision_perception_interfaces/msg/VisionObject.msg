# Source RGB acquisition timestamp and measured optical coordinate frame.
std_msgs/Header header

# Same observation key as the matching VisionDetection2D; not array-order association.
uint32 detection_index
# Stable only inside VisionObjectArray.tracking_session_id; empty before tracking (V2).
string object_id
string class_name
# Classification score, not a position confidence or calibrated probability.
float32 confidence
vision_msgs/BoundingBox2D bbox

# Metres in header.frame_id. Store NaN and set position_valid=false when invalid.
geometry_msgs/Point position
bool position_valid
# Always visible_surface_sample when a surface sample is intended; do not encode failures here.
string position_reference
# OK / DEPTH_UNPAIRED / MASK_TOO_SMALL / DEPTH_INSUFFICIENT / DEPTH_DISCONTINUITY / INPUT_INVALID / STALE.
string invalid_reason
float64 reference_u
float64 reference_v
float32 valid_depth_fraction

# Unknown in V1/V2/V3; store NaN components and orientation_valid=false.
geometry_msgs/Quaternion orientation
bool orientation_valid
bool tracking_valid
