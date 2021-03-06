import rone, sys, math, math2, leds, velocity, poseX, motionX

################################################################################
##                      Student code - hand this section in                   ##
################################################################################

# Ryan Spring - rds4
# Kori Macdonald - kum1

#### Pose estimator ####
WHEEL_BASE = 78
ENCODER_MM_PER_TICKS = 0.0625

#update the pose state
# Ryan Spring - rds4 and Kori Macdonald - kum1
def pose_update(pose_state):
    # 1. Get the left and right encoder ticks
    left = rone.encoder_get_ticks("l")
    right = rone.encoder_get_ticks("r")
    
    # 2. Compute the left and right delta ticks
    # Don't forget to use encoder_delta_ticks() to properly compute the change in tick values
    dleft = velocity.encoder_delta_ticks(left, pose_state['ticksL'])
    dright = velocity.encoder_delta_ticks(right, pose_state['ticksR'])

    # 3. compute the left and right distance for each wheel
    # cast the delta ticks from step 2 to floats before you do the distance computation
    dl = float(dleft) * ENCODER_MM_PER_TICKS
    dr = float(dright) * ENCODER_MM_PER_TICKS

    # 4. save the left and right ticks to pose_state so we can measure the difference next time
    pose_state['ticksL'] = left
    pose_state['ticksR'] = right
    
    # 5. Compute the distance traveled by the center of the robot in millimeters
    center = (dr + dl) / 2.0

    # 6. Add the distance to the odometer variable in pose_state
    pose_state['odometer'] = pose_state['odometer'] + abs(center)
    
    # 7. compute the arc angle in radians
    # don't call atan here, use the small angle approximation: arctan(theta) ~ theta
    dtheta = (dr - dl) / float(WHEEL_BASE)
    
    # 8. finally, update x, y, and theta, and save them to the pose state
    # use math2.normalize_angle() to normalize theta before storing it in the pose_state
    l = ((dr - dl) / 2.0) * math.sin(90 - dtheta)
    ntheta = pose_state['theta'] + dtheta
    pose_state['x'] = (center + l) * math.cos(ntheta) + pose_state['x']
    pose_state['y'] = (center + l) * math.sin(ntheta) + pose_state['y']
    pose_state['theta'] = math2.normalize_angle(ntheta)
    return 0

#### Waypoint controller constants ####
MOTION_CAPTURE_DISTANCE = 16
MOTION_RELEASE_DISTANCE = 32
MOTION_CAPTURE_ANGLE = math.pi/2
MOTION_RELEASE_ANGLE = math.pi/10
MOTION_TV_MIN = 20
MOTION_TV_GAIN = 3
MOTION_RV_GAIN = 1300
MOTION_RV_MAX = 7000

# Convert rectangular to polar
# return a tuple of the form (r, theta)
# theta lies between (-pi, pi] 
# Ryan Spring - rds4 and Kori Macdonald - kum1
def topolar(x, y):
    # student code start
    r2 = (x*x) + (y*y)
    r = math.sqrt(r2)
    theta = math.atan2(y,x)
    #student code end
    return (r, theta)

# compute the distance and heading to the goal position
# return a tuple of the form: (goal_distance, goal_heading, robot_heading)
# Ryan Spring - rds4 and Kori Macdonald - kum1
def compute_goal_distance_and_heading(goal_position, robot_pose):
    # student code start
    (goal_distance, goal_heading) = topolar(goal_position[0] - robot_pose[0], goal_position[1] - robot_pose[1])
    robot_heading = robot_pose[2]
    # student code end
    return (goal_distance, goal_heading, robot_heading)

# Compute the smallest angle difference between two angles
# This difference will lie between (-pi, pi]
# Ryan Spring - rds4
def smallest_angle_diff(current_angle, goal_angle):
    # student code start
    if (current_angle >= 0 and goal_angle >= 0) or (current_angle < 0 and goal_angle < 0):
        return math2.normalize_angle(goal_angle - current_angle)
    elif (current_angle >= 0):
        return -math2.normalize_angle(abs(current_angle) + abs(goal_angle))
    else:
        return math2.normalize_angle(abs(current_angle) + abs(goal_angle))
    # student code end

# compute the tv profile for the velocity controller.
# this should match the plot from the handout
# Ryan Spring - rds4 and Kori Macdonald - kum1
def motion_controller_tv(d, tv_max):
    # student code start
    tv_temp = MOTION_TV_GAIN * d + MOTION_TV_MIN
    # student code end
    return math2.bound(tv_temp, tv_max)

# compute the rv controller for the velocity controller
# this should bound the value to MOTION_RV_MAX
# Ryan Spring - rds4 and Kori Macdonald - kum1
def motion_controller_rv(heading, heading_to_goal):
    # student code start
    bearing_error = smallest_angle_diff(heading, heading_to_goal)
    rv = math2.bound(MOTION_RV_GAIN * bearing_error, MOTION_RV_MAX)
    print heading
    print heading_to_goal
    print bearing_error
    print rv
    print "\n"
    # student code end
    return (rv, bearing_error)

################################################################################
##                         Helper and main function                           ##
##                Distribution code - do not print or hand in                 ##
################################################################################

MOTION_TV = 100
LED_BRIGHTNESS = 40
MODE_INACTIVE = 0
MODE_ACTIVE = 1

def waypoint_motion(): 
    velocity.init(0.22, 40, 0.5, 0.1)
    leds.init()
    poseX.init(pose_update)
    motionX.init(compute_goal_distance_and_heading, motion_controller_tv, motion_controller_rv)

    pose_estimator_print_time = sys.time()
    mode = MODE_INACTIVE
    pose_old = (0.0, 0.0, 0.0)

    waypoint_list = []
    while True:
        # update the LED animations
        leds.update()

        # update the pose estimator
        poseX.update()
        
        # update the motion controller
        (tv, rv) = motionX.update()
        velocity.set_tvrv(tv, rv)

        # update the velocity controller if you are active, otherwise coast so the robot can be pushed
        if mode == MODE_ACTIVE:
            velocity.update()
        else:
            rone.motor_set_pwm('l', 0)
            rone.motor_set_pwm('r', 0)

        # print status every 500ms
        current_time = sys.time()
        if sys.time() > pose_estimator_print_time:
            pose_estimator_print_time += 250
            print 'goal', motionX.get_goal(), 'pose', poseX.get_pose(), 'odo', poseX.get_odometer()
            if mode == MODE_INACTIVE:
                if (math2.pose_subtract(poseX.get_pose(), pose_old) != (0.0, 0.0, 0.0)): 
                    # We're moving!  Yay!  Blink excitedly!
                    leds.set_pattern('r', 'blink_fast', int(LED_BRIGHTNESS * 1.5))
                else:
                    # not moving. sad face.
                    leds.set_pattern('r', 'circle', LED_BRIGHTNESS)
            pose_old = poseX.get_pose()

        # check the buttons.  If the red button is pressed, load the waypoint list
        if rone.button_get_value('r'):
            if mode == MODE_INACTIVE:
                poseX.set_pose(0, 0, 0)
                waypoint_list = [(1000, 0), (1000, 1000), (0, 1000), (0, 0)]
                mode = MODE_ACTIVE
            
        # check to see if you are at your waypoint.  If so, go to the next one
        if mode == MODE_ACTIVE:
            leds.set_pattern('g', 'blink_fast', LED_BRIGHTNESS)
            if motionX.is_done():
                ## Do we have another waypoint?
                if len(waypoint_list) > 0:
                    leds.set_pattern('rgb', 'group', LED_BRIGHTNESS)
                    sys.sleep(250)
                    waypoint = waypoint_list.pop(0)
                    print 'waypoint', waypoint
                    motionX.set_goal(waypoint, MOTION_TV)
                else:
                    print 'waypoint list empty'
                    mode = MODE_INACTIVE
                    velocity.set_tvrv(0, 0)
                    
waypoint_motion()