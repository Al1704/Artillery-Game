import pygame
import pygame.gfxdraw
import numpy as np 
import math 
from tank import tank, AI_enemy
import sys
import time
    
# window size
window_width, window_height = [int(620 * 1.5), int(480 * 1.5)] 

def integer_ball(ground, point,radius):
    """
    Returns a list of points within a specified radius around a given point on the ground grid.

    Parameters:
        ground (numpy.ndarray): 2D numpy array representing the ground.
        point (tuple): Tuple containing the coordinates of the center point.
        radius (int): Integer specifying the radius of the circle around the center point.

    Returns:
        list: List of points (tuples) within the specified radius.
    """

    points = []
    for i in range(point[0] - radius, point[0] + radius + 1):
        for j in range(point[1] - radius, point[1] + radius + 1):
            if 0 <= i < ground.shape[0] - 1 and j < ground.shape[1]:
                if math.sqrt((i - point[0])**2 + (j - point[1])**2) <= radius:
                    points.append((i, j))
    return points

def collision(rect1, rect2):
    """
    Checks if two rectangles overlap.

    Parameters:
        rect1 (list): List containing the coordinates and dimensions of the first rectangle [x, y, width, height].
        rect2 (list): List containing the coordinates and dimensions of the second rectangle [x, y, width, height].

    Returns:
        bool: Boolean value indicating whether the rectangles overlap.
    """

    # extract coordinates and dimensions of rectangles
    x1, y1 = rect1[0] # upper left coordinates of rectangle 1
    w1, h1 = rect1[1:] # length and height of rectangle 1
    x2, y2 = rect2[0] # upper left coordinates of rectangle 2
    w2, h2 = rect2[1:] # length and height of rectangle 2

    # check overlap along x-axis
    overlap_x = (x1 < x2 + w2) and (x2 < x1 + w1)

    # check overlap along y-axis
    overlap_y = (y1 < y2 + h2) and (y2 < y1 + h1)

    # Return True if rectangles overlap both along x-axis and y-axis
    return(overlap_x and overlap_y)

def func_to_ground(f): 
    """
    Converts a given function to a ground matrix.

    Parameters:
        f (function): Function representing the ground profile.

    Returns:
        numpy.ndarray: 2D numpy array representing the ground matrix.
    """
    ground = np.zeros((window_height, window_width))
    n = 0
    for x in range(0, window_width): 
        m = int(f(x)) 
        if m < 1: 
            ground[:,n] = 0
        else: 
            ground[-m:, n] = 1 # set row (of pixels) beneath function value to 1 
        n = n + 1
    return(ground)

def update_ground(miss, ground, destruction_radius): 
    """
    Updates the ground matrix based on the impact of a missile.

    Parameters:
        miss (missile): Missile object representing the missile.
        ground (numpy.ndarray): 2D numpy array representing the ground.
        destruction_radius (int): Integer specifying the radius of destruction caused by the missile.

    Returns:
        bool: Boolean value indicating whether the ground was updated due to the missile impact.
    """
    
    m = int(miss.position[0]) 
    n = int(miss.position[1]) 

    # indicates that missile is out of screen
    if not (0 <= m < np.shape(ground)[1] - 2  and n < np.shape(ground)[0] - 2): 
        return(True)

    # set ground to zero where it was hit by the missile
    if n > 2 and 1 in [ground[k,j] for k in range((n-2), (n+3)) for j in range((m-2), (m+3))]:
        bombed_area = integer_ball(ground, [n,m], destruction_radius)
        rows, cols = zip(*bombed_area)
        ground[rows,cols] = 0

        return(True)
    else: 
        return(False)
    
def ground_earth(x): 
    """
    Calculates the height of the ground at a given x-coordinate on Earth.

    Parameters:
    - x (float): The x-coordinate at which to calculate the height of the ground.

    Returns:
    - float: The height of the ground at the specified x-coordinate on Earth.
    """
    return(60 * np.sin(x / 45) + 150 + 0.12*x)

def ground_moon(x): 
    """
    Calculates the height of the ground at a given x-coordinate on the Moon.

    Parameters:
    - x (float): The x-coordinate at which to calculate the height of the ground.

    Returns:
    - float: The height of the ground at the specified x-coordinate on the Moon.
    """
    return(- 10**(-3.6) * (x-480)**2 + 200 - 5 * np.sin(x / 25))

def ground_mars(x):
    """
    Calculates the height of the ground at a given x-coordinate on Mars.

    Parameters:
    - x (float): The x-coordinate at which to calculate the height of the ground.

    Returns:
    - float: The height of the ground at the specified x-coordinate on Mars.
    """
    return(150 + 40 * np.sin(x / 80) + 30 * np.cos(x / 30) + 15 * np.sin(x / 300) ) 

def ground_ice(x):
    """
    Calculates the height of the ground at a given x-coordinate on an ice planet.

    Parameters:
    - x (float): The x-coordinate at which to calculate the height of the ground.

    Returns:
    - float: The height of the ground at the specified x-coordinate on the ice planet.
    """
    # Define the range of y values
    y_min = 150
    y_max = 400
    
    # Normalize x to the range [0, period)
    x_normalized = x % 60
    
    # Map x_normalized to the range [y_min, y_max]
    return( y_min + 0.5 * (y_max - y_min) * (x_normalized / 100)  + 20 * np.cos(x / 30))

def current_fraction_of_second():
    """
    Calculates the current fraction of a second.

    Returns:
        float: Fraction of the current second.
    """
    # Get the current time in seconds
    current_time = time.time()
    # Get the fraction of the current second
    fraction_of_second = current_time - int(current_time)
    return fraction_of_second
                
def pixel_to_position(n,m):
    """
    Converts pixel coordinates to position coordinates.

    Parameters:
        n (int): Pixel coordinate along the x-axis.
        m (int): Pixel coordinate along the y-axis.

    Returns:
        numpy.ndarray: Numpy array containing the position coordinates.
    """
    pos = np.array([n, m])
    return(pos)

def draw_smooth_rect(screen, color, x, y, width, height):
    """
    Draws a smoothed rectangle on the screen.

    Parameters:
        screen (pygame.Surface): Pygame display surface.
        color (tuple): Color of the rectangle.
        x (int): x-coordinate of the top-left corner of the rectangle.
        y (int): y-coordinate of the top-left corner of the rectangle.
        width (int): Width of the rectangle.
        height (int): Height of the rectangle.
    """

    # Function to draw a smoothed rectangle
    pygame.gfxdraw.filled_polygon(screen, [(x, y), (x + width, y), (x + width, y + height), (x, y + height)], color)
    #pygame.gfxdraw.aapolygon(screen, [(x, y), (x + width, y), (x + width, y + height), (x, y + height)], color)

def draw_ground(ground, col): 
    """
    Draws the ground on the screen.

    Parameters:
        ground (numpy.ndarray): 2D numpy array representing the ground.
        col (tuple): Color of the ground.
    """
    # draw every column of the ground starting from the first (from buttom) 0 in ground matrix column 
    for m in range(0, ground.shape[1]):
        n = np.where(ground[:, m] == 0)[0][-1]
        ground[0:n, m] = 0
        y_rect, x_rect = pixel_to_position(n,m)
        draw_smooth_rect(screen, col, x_rect, y_rect, block_size, (ground.shape[0] - n))

def gradient(tank_pos, move_direction, ground):
    """
    Calculates the gradient (slope) of the ground at the current position of the tank.

    Parameters:
    - tank_pos (tuple): A tuple containing the current position of the tank in the form (x, y).
    - move_direction (int): The direction in which the tank is moving (-1 for left, 1 for right).
    - ground (numpy.ndarray): An array representing the ground terrain.

    Returns:
    - float: The gradient (slope) of the ground at the current position of the tank.
    """
    # x coordinate 4 steps in moving direction (less than 4 steps yields low variability in gradient values)
    column_tank = int(tank_pos[0]) + 4 * move_direction
    # new height of tank
    y_tank = np.nonzero(ground[:, column_tank])[0][0] 
    # increase / decrease in height of tank (when going 4 steps / pixel in moving direction)
    gradient = -(y_tank - tank_pos[1])
    return(gradient)

def moving_speed(grad_tank): 
    """
    Calculates the moving speed of the tank based on the gradient of the ground.

    Parameters:
    - grad_tank (float): The gradient (slope) of the ground at the current position of the tank.

    Returns:
    - float: The moving speed of the tank.
    """
    if grad_tank > 8: 
        speed = 0
    elif grad_tank in [4, 5, 6, 7]: 
        speed = 2
    elif grad_tank in [2, 3]:
        speed = 2.5
    elif grad_tank in [-1, 0, 1]: 
        speed = 3
    elif -8 < grad_tank < -1: 
        speed = 4
    else:
        speed = 5
    return(speed)

def load_images(player): 
    """
    Loads tank images for a given player.

    Parameters:
    - player (str): A string indicating the player / computer for whom tank images are to be loaded.

    Returns:
    - list: A list of pygame.Surface objects representing the tank images.
    """
    j = 0
    angles = [-40, -10, 0, 20, 50, 80]
    images = ["" for _ in angles]
    for k in angles:
        # name of the imagine
        name = "tanks_imgs/" + player + "_" + str(k) + "_deg.png"
        images[j] = pygame.image.load(name)
        j += 1
    return(images)


def draw_text(text, font, color, x, y, size=None):
    """
    Renders text on the screen.

    Parameters:
    - text (str): The text to be rendered.
    - font (pygame.font.Font): The font object to render the text.
    - color (tuple): The color of the text in RGB format.
    - x (int): The x-coordinate of the text.
    - y (int): The y-coordinate of the text.
    - size (int, optional): The font size. If None, the font size of the provided font is used.

    Returns:
    - None
    """
    if size:
        font = pygame.font.Font(None, size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.center = (x, y)
    screen.blit(text_surface, text_rect)


def artillery_game(planet):  
    """
    Main function to run the artillery game.

    Parameters:
    - planet (int): An integer representing the chosen planet (1 for Earth, 2 for Moon, 3 for Mars, 4 for Ice Planet).
    """

    # settings depending on the chosen planet 
    if planet == 1: 
        # earth 
        COL_GROUND = ( 76, 153, 0)
        COL_SCORE = (0, 0, 0)
        g = 9.81 
        path_background_img = "backgrounds/background_earth.jpg"
        ground_func = ground_earth
        vel_norm = 95
    elif planet == 2: 
        # moon
        COL_GROUND = (128, 128, 128)
        COL_SCORE = (255, 255, 255)
        g = 1.62
        path_background_img = "backgrounds/background_moon.jpg"
        ground_func = ground_moon
        vel_norm = 40
    elif planet == 3: 
        # mars
        COL_GROUND = (204, 102, 0)
        COL_SCORE = (0,0,0)
        g = 3.71
        path_background_img = "backgrounds/background_mars.jpg"
        ground_func = ground_mars
        vel_norm = 60
    else:
        # ice planet 
        COL_GROUND = (185, 242, 255)
        COL_SCORE = (255,255,51)
        g = 12 
        path_background_img = "backgrounds/background_ice.jpg"
        ground_func = ground_ice
        vel_norm = 100

    # radius of destruction from missiles 
    destruction_radius = 12
    
    WEISS   = ( 255, 255, 255)
    COL_MISSILES_ACTIVE = (255, 153,51)
    COL_MISSILES_INACTIVE = (160, 160, 160)
    EXPLOSION = (255, 153, 51)

    # create matrix from given function that is used to draw the ground
    ground = func_to_ground(ground_func)

    # create instance of tank for player tank
    tank_player = tank(window_width, window_height, load_images("player"))
    # create instance of tank for computer tank
    tank_computer = tank( window_width, window_height, load_images("computer"))
   
    # collect tanks in list
    tanks = [tank_player, tank_computer]

    # Load the background image
    background_image = pygame.image.load(path_background_img)
    background_image_scalled = pygame.transform.scale(background_image, (window_width, window_height))
    
    # window update on 
    clock = pygame.time.Clock()

    # create instance of AI enemy
    computer = AI_enemy(tank_computer)

    # main loop 
    while True:
        # check if user has clicked on keys to perform some action 
        for event in pygame.event.get():
            # quiting game
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:

                # keys for player
                if event.key == pygame.K_RIGHT:
                    tank_player.move_direction = 1
                elif event.key == pygame.K_LEFT:
                    tank_player.move_direction = - 1
                elif event.key == pygame.K_UP:
                    tank_player.angle_adjust("pos")
                elif event.key == pygame.K_DOWN:
                    tank_player.angle_adjust("neg")
                elif event.key == pygame.K_SPACE:
                    tank_player.shoot(vel_norm)
                elif event.key == pygame.K_ESCAPE:
                    print("The game has been closed.")
                    pygame.quit()
                    sys.exit()
                
            # stops the movement of the player tank when right/left arrows are no longer pressed
            if event.type == pygame.KEYUP: 
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    tank_player.move_direction = 0

        # AI decisions
        computer.decision_running(tank_computer)
        computer.decision_shooting(tank_computer, vel_norm)
        computer.decision_reloading(tank_computer)
        computer.decision_movement( tank_computer)

        # fill screen white
        screen.fill(WEISS) 

        # blit the background image onto the screen
        screen.blit(background_image_scalled, (0, 0))

        # drawing the ground
        draw_ground(ground, COL_GROUND)

        # show score
        score = str(tanks[0].points) + " : " + str(tanks[1].points)
        draw_text(score, font, COL_SCORE, window_width // 2, 40, size = 55)
 
        for panzer in tanks: 
            # if the tank is in the air its y-coordinate is changed in every iteration such that the tank falls to the ground
            panzer.falling(ground)

            # reload ammunition 
            panzer.reloading()
            
            # if tank is moving: 
            if not panzer.move_direction == 0:
                
                # gradient of current position of tank
                grad = gradient(panzer.position, panzer.move_direction, ground) 
                # new x-coordinate of tank 1
                panzer.position[0] += moving_speed(grad) * panzer.move_direction 
                panzer.position[0] = min(panzer.position[0], window_width - 20)
                # coresponding new column of tank 1 
                column_tank = int(panzer.position[0])
                # coresponding new row of tank 1
                row_tank = np.nonzero(ground[:, column_tank])[0][0]

                # new height of the tank:     
                # if there is ground beneath the tank the height changes by falling (see falling function)
                # and not by moving
                if ground[panzer.position[1] + 10, panzer.position[0]] == 1:
                    panzer.position[1] = row_tank 

            # hitbox of tank 
            panzer.hitbox = [[panzer.position[0] - 18 + panzer.counter * 10, panzer.position[1] - 20], 35, 25]
            
            # show imagine of tank
            screen.blit(panzer.imgs[panzer.frame - 1], (panzer.position[0] - 20, panzer.position[1] - 50))
            
            # setting up colors of available / unavailable missiles
            col_missiles = [COL_MISSILES_ACTIVE for _ in range(3)]

            if panzer.num_missiles == 0: 
                col_missiles[0:3] = [COL_MISSILES_INACTIVE] * 3
            elif panzer.num_missiles == 1: 
                col_missiles[0:2] = [COL_MISSILES_INACTIVE] * 2 
            elif panzer.num_missiles == 2:
                col_missiles[0:1] = [COL_MISSILES_INACTIVE] * 1
    
            # drawing of the 3 available / unavailable missiles 
            for k in range(3): 
                pygame.draw.ellipse(screen, col_missiles[k], [10 + panzer.counter * 875 , 50 + k * 40,35,25]) # inner ellipse
                pygame.draw.ellipse(screen, (204,102,0), [10 + panzer.counter * 875, 50 + k * 40,35,25], 2)  # outer ellipse 

            # life bar - constists of a grey and a red bar
            # grey bar
            pygame.draw.rect(screen, (192, 192, 192), [10 + panzer.counter * 810, 10, 100, 25])
            # red bar
            pygame.draw.rect(screen, (210,0,0), [10 + panzer.counter * (810 + 100 - panzer.life), 10, panzer.life, 25])

            # update positions of every missile that is in the air 
            for miss in panzer.missiles: 
                miss.position_update(g, ground)
                # draw missile
                pygame.draw.circle(screen, ( 255, 0, 0), miss.position, 10, 10)
                
                # collision control if missile hits enemy tank
                if collision(tanks[-panzer.counter + 1].hitbox, [[miss.position[0] - 10, miss.position[1] - 10], 20, 20]):
                    tanks[-panzer.counter + 1].life -= 50

                    # save distance of last missile to computer tank for ai decision making
                    computer.distance = 0
                        
                    # draw explosion
                    pygame.draw.circle(screen, EXPLOSION, miss.position + [4, - 4], 20, 10)
                    # remove current missile from list
                    panzer.missiles.remove(miss)

                    # if one of the tanks has no life left
                    if tanks[-panzer.counter + 1].life == 0: 
                        # update score of other tank
                        panzer.points += 1
                        if panzer.points == 3: 
                            # go to end screen when one tank reacher 3 points
                            score = str(tanks[0].points) + " : " + str(tanks[1].points)
                            winner = panzer
                            end_screen(score, winner, planet) 
                        else:  
                            time.sleep(0.2)
                            # set life of destroyed tank to 100
                            tanks[-panzer.counter + 1].life = 100
                            for tnk in tanks: 
                                # respawn tanks
                                tnk.position = np.array([50 + tnk.counter * 830, 150])
                                # delete all current missiles that are in the air
                                tnk.missiles = []
                                # instant reloading of missiles
                                tnk.num_missiles = 3

                            
                # updates ground if hit by missile
                elif update_ground(miss, ground, destruction_radius): 
                    # draw explosion
                    pygame.draw.circle(screen, EXPLOSION, miss.position, 20, 10)

                    # update distance of player missile to computer tank (for AI decision making)
                    if panzer.counter == 0: 
                        computer.distance = abs(miss.position[0] - tanks[1].position[0] )
    
                    # remove current missile from list
                    panzer.missiles.remove(miss)

        # update display
        pygame.display.flip()

        # regulating frame rate
        clock.tick(25)
    
# initialisation of pygame
pygame.init()

# seting up screen 
screen = pygame.display.set_mode((window_width, window_height))

# title for screen
pygame.display.set_caption("Interplanetary Artillery game")

# fonts
font = pygame.font.Font(None, 36)

# colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN   = (34, 139, 34)
GREEN2 = (102, 204, 0)
BLUE = (0, 0, 255)

MOON = (192, 192, 192)
MARS = (193,68,14)
ICE = (185, 242, 255)

# size of the blocks
block_size = 1

def start_screen(): 
    """
    Displays the start screen of the game where the player can choose the planet.

    Parameters:
    - None

    Returns:
    - None
    """
    
    # initialise planet variable by 1 
    planet = 1 

    # Load the background image
    background_image = pygame.image.load("backgrounds/star_background.jpg")
    background_image_scalled = pygame.transform.scale(background_image, (window_width, window_height))

    # main loop for start screen
    while True: 
        screen.fill(WHITE)

        # Blit the background image onto the screen
        screen.blit(background_image_scalled, (0, 0))

        # show text
        draw_text("Interplanetary Artillery Game", font, WHITE, window_width // 2, window_height // 8, size = 48)
        draw_text("Choose the world to conquer", font, WHITE, window_width // 2, window_height // 5)
        draw_text("Press enter to confirm", font, WHITE, window_width // 2, window_height // 4, size = 25)
        
        # different options for the worlds to choose 
        draw_text("Earth", font, GREEN2, window_width // 2, 280, size = 45)
        draw_text("Moon", font, MOON, window_width // 2,  380, size = 45)
        draw_text("Mars", font, RED, window_width // 2, 480, size = 45)
        draw_text("Ice Planet", font, ICE, window_width // 2, 580, size = 45)

        # user input keys
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN: 
                    if planet < 4: 
                        planet += 1
                if event.key == pygame.K_UP: 
                    if planet > 1: 
                        planet -= 1
                if event.key == pygame.K_RETURN:
                    # Start the game here
                    artillery_game(planet)
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        # blinking triangle 
        if current_fraction_of_second() > 0.5:
            pointer_height = 270 + (planet - 1) * 100
            pygame.draw.polygon(screen, RED, ((300,pointer_height + 20),(300,pointer_height),(325,pointer_height + 10)))

        # update display
        pygame.display.flip()

        
def end_screen(score, winner, planet): 
    """
    Displays the end screen of the game showing the winner and options to play again.

    Parameters:
    - score (str): The score of the game.
    - winner (str): The winner of the game.
    - planet (int): The (previously) chosen planet.

    Returns:
    - None
    """

    if winner.counter == 0: 
        winner = "player" 
    else: 
        winner = "computer"

    option = 1

    # main loop end screen
    while True: 
        screen.fill((0,0,0))

        # show text 
        draw_text(score, font, (255, 255, 255), window_width // 2, 100, size = 50)
        draw_text(winner + " has won the game.", font, (255, 255, 255), window_width // 2, 150, size = 50)
        draw_text("Do you want to play another round?", font, (255, 255, 255), window_width // 2, 200, size = 50)

        draw_text("Yes", font, (255, 255, 255), window_width // 2, 350, size = 50)
        draw_text("Yes, choose new world.", font, (255, 255, 255), window_width // 2, 450, size = 50)
        draw_text("No", font, (255, 255, 255), window_width // 2, 550, size = 50)

        # user input keys
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN: 
                    if option < 3: 
                        option += 1
                if event.key == pygame.K_UP: 
                    if option > 1: 
                        option -= 1
                if event.key == pygame.K_RETURN:
                    if option == 1: 
                        # reset counter of the tank class
                        tank.counter = -1
                        artillery_game(planet)
                    elif option == 2:
                        # reset counter of the tank class
                        tank.counter = -1
                        start_screen()
                    else: 
                        pygame.quit()
                        sys.exit()
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        # blinking triangle
        if current_fraction_of_second() > 0.5:
            pointer_height = 340 + (option - 1) * 100
            pygame.draw.polygon(screen, RED, ((200,pointer_height + 20),(200,pointer_height),(225,pointer_height + 10)))
       
       # update display
        pygame.display.flip()

start_screen()