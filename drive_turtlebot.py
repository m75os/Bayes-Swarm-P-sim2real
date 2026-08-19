import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist

import time

class DriveTurtlebot(Node):
    def __init__(self):
        super().__init__('TB1_driver')

        self.twist_publisher = self.create_publisher(Twist, 
                                                     '/cmd_vel', 
                                                     qos_profile = 10,)

        self.odom_subscriber = self.create_subscription(Odometry, 
                                                        '/odom', 
                                                        self.get_coordinates,
                                                        qos_profile = 10,)

        self.timer_callback = self.create_timer(0.1, self.drive_forward)

        self.msg = Twist()
        self.coordinates = Odometry()

    def get_coordinates(self, msg):

        self.x = round(msg.pose.pose.position.x, 3)
        self.y = round(msg.pose.pose.position.y, 3)

        print(f"x: {self.x}")
        print(f"y: {self.y}")
        

    def drive_forward(self):
        try:
            self.msg.linear.x = 0.3
        except KeyboardInterrupt:
            self.msg.linear.x = 0.0 

        self.twist_publisher.publish(self.msg)
    

def main(args=None):
    rclpy.init(args=args)
    node = DriveTurtlebot()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

