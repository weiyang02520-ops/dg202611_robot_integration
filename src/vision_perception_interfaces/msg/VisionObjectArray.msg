# All objects share this source acquisition timestamp and coordinate frame.
std_msgs/Header header
string source_session_id
uint64 observation_id
string calibration_id
string source_kind
# Empty before V3. Restart/reset creates a new ID namespace.
string tracking_session_id
VisionObject[] objects
