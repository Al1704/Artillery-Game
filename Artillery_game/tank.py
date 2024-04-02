import numpy as np
import random 
import time
import math

class tank: 
    """
    Represents a tank object in the game.

    Attributes:
    - counter (int): A class variable to keep track of the number of tanks created.
    - position (numpy.ndarray): Current position of the tank.
    - max_position (list): Maximum allowed position of the tank.
    - frame (int): Current frame of the tank's animation.
    - angle (int): Current angle of the tank's cannon.
    - missiles (list): List of missiles fired by the tank.
    - num_missiles (int): Number of missiles available for the tank to fire.
    - life (int): Current life points of the tank.
    - move_direction (int): Direction of tank movement (-1 for left, 1 for right, 0 for no movement).
    - move_direction_previous (int): Previous direction of tank movement.
    - imgs (list): Images representing the tank's animation.
    - points (int): Score accumulated by the tank.
    - last_reloaded (float): Timestamp of the last missile reload.

    Methods:
    - __init__: Initializes a tank object.
    - shoot: Fires a missile from the tank.
    - reloading: Reloads missiles for the tank.
    - move: Moves the tank.
    - falling: Simulates the tank's falling motion.
    - angle_adjust: Adjusts the cannon angle of the tank.
    """
    counter = -1

    def __init__(self, window_width, window_height, imgs):
        tank.counter += 1 # first (player) tank gets the number 0, computer tank gets the number 1 
        self.counter = tank.counter
        self.max_position = [window_width, window_height]
        self.position = np.array([50 + self.counter * 830, 150])
        self.frame = 3
        self.angle = 0
        self.missiles = []
        self.num_missiles = 3
        self.life = 100
        self.move_direction = 0
        self.move_direction_previous = 0
        self.imgs = imgs
        self.points = 0 
        self.last_reloaded = 0 # last time missiles were reloaded
        
    def shoot(self, vel_norm): 
        if self.num_missiles > 0: # no shooting while missiles are reloading
            self.missiles.append(missile(self.angle, self.position + np.array([0, - 10]), self.counter, vel_norm))
            self.num_missiles -= 1
            self.reload = False # end reloading if missiles are fired
        
    def reloading(self): 
        if self.num_missiles < 3 and time.time() - self.last_reloaded > 1: 
        # reload at most 1 missile per 1 second
            self.num_missiles += 1
            self.last_reloaded = time.time()
            

    def move(self, move_direction): 
        self.position += move_direction
        if self.position[0] < 0: 
            self.position[0] = 0
        elif self.position[0] >= self.max_position[0] - 20:
            self.position[0] = int(self.max_position[0]) - 20 

    def falling(self, ground): 
        m = int(self.position[0])
        n = int(self.position[1]) 

        if ground[n+1, m] == 1: 
            self.move_direction_previous = self.move_direction

        if ground[n+1, m] == 0: 
            # set moving direction to 0 while falling
            self.move_direction = 0
            # falling at most 10 pixel per iteration such that the tank lands exactly on the ground
            self.position[1] += min(12, np.where(ground[:, m] == 0)[0][-1] - n ) + 1

            # while falling the moving direction was 0, i.e. there was no horicontal movement of the tank 
            # when the tank lands the movement before the fall should continue without having to press 
            # 'right' / 'left' again
            if ground[self.position[1],self.position[0]] == 1:
                self.move_direction = self.move_direction_previous
               
      
    def angle_adjust(self, direction):
        angles = [-40, -10, 0, 20, 50, 80] # possible angels
        if direction == "pos" and self.frame < 6: 
            self.angle = angles[self.frame]
            self.frame += 1
        elif direction == "neg" and self.frame > 1: 
            self.angle = angles[self.frame - 2]
            self.frame -= 1
        
    
class missile: 
    """
    Represents a missile object in the game.

    Attributes:
    - angle (float): Launch angle of the missile.
    - v_init (numpy.ndarray): Initial velocity vector of the missile.
    - position_prev (numpy.ndarray): Previous position of the missile.
    - position_cur (numpy.ndarray): Current position of the missile.

    Methods:
    - __init__: Initializes a missile object.
    - position_update: Updates the position of the missile based on gravity and terrain collision.
    """


    def __init__(self, angle, init_position, counter, vel_norm): 
        time_step = 0.2
        self.counter = counter
        self.angle = math.radians(angle)
        
        self.v_init = np.array([(- 2 * counter + 1) * vel_norm * math.cos(self.angle), - vel_norm * math.sin(self.angle)])
        self.position_prev = init_position + np.array([0, - 5])
        self.position_cur = self.position_prev + time_step * self.v_init

    def position_update(self, g, ground): 
            time_step = 0.2

            self.position = 2 * self.position_cur - self.position_prev + [0, g * (time_step ** 2)]

            self.position_prev = self.position_cur
            self.position_cur = self.position
   
            if 0 <= self.position[0] <= 929:
                if self.position[1] > np.where(ground[:, int(self.position[0])] == 0)[0][-1]:
                    self.position[1] = np.where(ground[:, int(self.position[0])] == 0)[0][-1]
            self.position = np.array([int(self.position[0]), int(self.position[1])])
        
      

class AI_enemy: 
    """
    Represents an AI enemy tank in the game.

    Attributes:
    - distance (int): Distance between the AI tank and the last missile (from the player) that exploded on the ground 
    - time_decision_shooting (float): Timestamp of the last shooting decision.
    - time_decision_moving (float): Timestamp of the last moving decision.
    - tank_computer (tank): Instance of the AI tank.

    Methods:
    - __init__: Initializes an AI_enemy object.
    - decision_running: Makes a decision for AI tank movement.
    - decision_movement: Makes a decision for AI tank movement.
    - decision_shooting: Makes a decision for AI tank shooting.
    - decision_reloading: Makes a decision for AI tank reloading.
    - decision_angle_adjusting: Makes a decision for AI tank adjusting cannon angle.
    """
    def __init__(self, tank_computer): 
        self.distance = 110
        self.time_decision_shooting = time.time()
        self.time_decision_moving = time.time()
        self.tank_computer = tank_computer

    def decision_running(self, tank_computer): 
        if self.distance < 110: 
            self.distance = 110
            random_direction = random.choice([-1, 1])
            tank_computer.move_direction = random_direction

    def decision_movement(self, tank_computer): 
        if time.time() - self.time_decision_moving > 5 + random.random():
            random_direction = random.choice([-1, 0, 1])
            tank_computer.move_direction = random_direction
            self.time_decision_moving = time.time()

    def decision_shooting(self, tank_computer, vel_norm): 
        if time.time() - self.time_decision_shooting > 0.2 + random.random(): 
            self.time_decision_shooting = time.time()
            if random.choice([-1, 1]) == 1: 
                tank_computer.shoot(vel_norm)
                self.decision_angle_adjusting(tank_computer)
                
    def decision_reloading(self, tank_computer):
        if tank_computer.num_missiles == 0: 
            tank_computer.reloading()

    def decision_angle_adjusting(self, tank_computer): 
        
            rnd = random.choice([-1, 0, 1])
            if rnd == 1 or tank_computer.frame == 1: 
                tank_computer.angle_adjust("pos")
            elif rnd == -1 or tank_computer.frame == 6:
                tank_computer.angle_adjust("neg")


            
            

        
        
