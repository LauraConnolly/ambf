# //==============================================================================
# /*
#     Software License Agreement (BSD License)
#     Copyright (c) 2020, AMBF
#     (https://github.com/WPI-AIM/ambf)
#
#     All rights reserved.
#
#     Redistribution and use in source and binary forms, with or without
#     modification, are permitted provided that the following conditions
#     are met:
#
#     * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#
#     * Redistributions in binary form must reproduce the above
#     copyright notice, this list of conditions and the following
#     disclaimer in the documentation and/or other materials provided
#     with the distribution.
#
#     * Neither the name of authors nor the names of its contributors may
#     be used to endorse or promote products derived from this software
#     without specific prior written permission.
#
#     THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#     "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#     LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
#     FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
#     COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
#     INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
#     BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#     LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#     CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#     LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
#     ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#     POSSIBILITY OF SUCH DAMAGE.
#
#     \author    <amunawar@wpi.edu>
#     \author    Adnan Munawar
#     \version   1.0
# */
# //==============================================================================


# ROS version
import os
__ros_version_string = os.environ['ROS_VERSION']
if __ros_version_string == '1':
    ROS = 1
    import rospy
elif __ros_version_string == '2':
    ROS = 2
    import rclpy
else:
    print('environment variable ROS_VERSION must be either 1 or 2, did you source your setup.bash?')


class WatchDog(object):
    def __init__(self, node, time_out = 0.1):
        self._node = node
        self.set_timeout(time_out)
        self._next_cmd_expected_time = self.now()
        self._initialized = False

    def now(self):
        if ROS == 1:
            return rospy.Time.now()
        else:
            return self._node.get_clock().now()

    def acknowledge_wd(self):
        self._initialized = True
        self._next_cmd_expected_time = self.now() + self._expire_duration

    def is_wd_expired(self):
            return (self.now() > self._next_cmd_expected_time and self._initialized)

    def console_print(self, class_name):
        if self._initialized:
            print('Watch Dog Expired, Resetting {} command'.format(class_name))
            self._initialized = False

    def set_timeout(self, time_out):
        if ROS == 1:
            self._expire_duration = rospy.Duration.from_sec(time_out)
        else:
            self._expire_duration = rclpy.time.Duration(seconds = time_out)
