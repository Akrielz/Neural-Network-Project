import pygame
from nn_model import *
import copy
import time

molecules = None 
score = None
nr_allies_left = None

neural_network = Neural_Network()
if TEST_MODE:
    neural_network.load(TEST_MODEL_ID, False)

if CONTINUE_MODEL:
    neural_network.load(TEST_MODEL_ID, True)

def render_molecule(screen, molecules):
    for m in molecules:
        color = None
        if m.status == ENEMY:
            color = RED
        elif m.status == ALLY:
            color = GREEN
        elif m.status == PLAYER:
            color = BLUE

        pygame.draw.circle(screen, color, (m.x, m.y), m.r)


def eval_position(action, molecules_updated, in_game_score):
    # molecules copied
    action_score = 0

    molecules_updated[-1].alpha_dir = action/NR_ACTIONS*2*PI
    molecules_updated[-1].update()

    for i, m in enumerate(molecules_updated[:-1]):
        if molecules_updated[-1].is_coliding(m):
            if m.status == ENEMY:
                action_score -= 1
            else:
                action_score += 1

    p = molecules_updated[-1]
    PR = 2*p.r
    if p.x - PR < 0 or p.x + PR > GAME_WIDTH or p.y - PR < 0 or p.y + PR > GAME_HEIGHT:
        action_score -= 10

    action_score += in_game_score
    for i, m in enumerate(molecules_updated[:-1]):
        action_score += 0.5 * m.r * m.status / molecules_updated[-1].distance_to(m)

    return action_score


def eval_score(action, molecules_updated, in_game_score):
    return 0.0 + in_game_score


def eval_imidiate_reward(action, molecules_updated, in_game_score):
    imediate_reward = 0.0

    molecules_updated[-1].alpha_dir = action/NR_ACTIONS*2*PI
    molecules_updated[-1].update()

    for i, m in enumerate(molecules_updated[:-1]):
        if molecules_updated[-1].is_coliding(m):
            if m.status == ENEMY:
                imediate_reward -= 1.0
            else:
                imediate_reward += 1.0

    return 0.0 + imediate_reward


def init_new_game():
    global molecules, score, nr_allies_left, neural_network
    molecules = []
    for _ in range(NR_ENEMIES_INIT + NR_ALLIES_INIT + 1):
        x = np.random.random_sample() * (GAME_WIDTH - OFFSET) + OFFSET / 2
        y = np.random.random_sample() * (GAME_HEIGHT - OFFSET) + OFFSET / 2

        status = None
        if _ < NR_ENEMIES_INIT:
            status = ENEMY
        elif _ < NR_ALLIES_INIT + NR_ENEMIES_INIT:
            status = ALLY
        else:
            status = PLAYER
        molecule = Molecule(x=x, y=y, status=status)
        molecules.append(molecule)

    score = 0
    nr_allies_left = NR_ALLIES_INIT

if VISUAL_ACTIVATED:
    pygame.init()
    font = pygame.font.Font('freesansbold.ttf', 32)
    screen = pygame.display.set_mode([GAME_WIDTH, GAME_HEIGHT])

init_new_game()

running = True
frame = 0
generation = 1
start_time = time.time()
total_frames = 0
average_score = 0
while running:
    # Did the user click the window close button?
    if VISUAL_ACTIVATED:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

    # Fill the background with white - TO CLEAR THE BACKGROUND
    if VISUAL_ACTIVATED:
        screen.fill(WHITE)

    # Draw
    if VISUAL_ACTIVATED:
        text = font.render("Score: " + str(score), True, BLACK, WHITE)
        textRect = text.get_rect() 
        textRect.center = (100, 50)
        screen.blit(text, textRect)

        text = font.render("Frame: " + str(frame), True, BLACK, WHITE)
        textRect = text.get_rect() 
        textRect.center = (GAME_WIDTH-100, 50)
        screen.blit(text, textRect)

        render_molecule(screen, molecules)

    input_values = [
        molecules[-1].x / GAME_WIDTH, 
        molecules[-1].y / GAME_HEIGHT,
        molecules[-1].r / MAXIMUM_RADIUS, 
        molecules[-1].speed / MAXIMUM_RADIUS
    ]
    for i, m in enumerate(molecules[:-1]):
        input_values.append(m.x / GAME_WIDTH)
        input_values.append(m.y / GAME_HEIGHT)
        input_values.append(m.r / MAXIMUM_RADIUS)
        input_values.append(m.speed / MAXIMUM_RADIUS)
        input_values.append((m.status + 1) / 2)
        input_values.append(m.alpha_dir / (2*PI))
        input_values.append(molecules[-1].distance_to(m) / GAME_MAX_DISTANCE)
    
    for i, m in enumerate(molecules[:-1]):
        m.update()
    
    if not TEST_MODE:
        action = neural_network.feed(input_values, eval_func=eval_imidiate_reward, 
                                    molecules=copy.deepcopy(molecules), in_game_score = score)
    else:
        action = neural_network.best_act(input_values)
    molecules[-1].alpha_dir = action/NR_ACTIONS*2*PI
    molecules[-1].update()

    for i, m in enumerate(molecules[:-1]):
        if molecules[-1].is_coliding(m):
            if m.status == ENEMY:
                score -= 1
            else:
                score += 1
                nr_allies_left -= 1

            x = np.random.random_sample() * (GAME_WIDTH - OFFSET) + OFFSET / 2
            y = np.random.random_sample() * (GAME_HEIGHT - OFFSET) + OFFSET / 2
            status = ENEMY if np.random.random_sample() < ENEMY_CHANCE or m.status == ENEMY else ALLY
            
            if status == ALLY:
                nr_allies_left += 1

            molecules[i] = Molecule(x=x, y=y, status=status)

    # Flip the display
    if VISUAL_ACTIVATED:
        pygame.display.update()

    if nr_allies_left == 0 or frame >= NR_MAX_FRAMES:
        if generation % NR_GEN_CHECK == 0:
            print("Generation[", generation - NR_GEN_CHECK + 1,"-",generation, "]: " , 
                  average_score / NR_GEN_CHECK, sep="")
            average_score = 0
            end_time = time.time()
            duration = end_time - start_time
            print("FPS: ", total_frames // duration, sep="")
            start_time = time.time()
            total_frames = 0
            
        if not TEST_MODE:
            neural_network.update(generation)
        average_score += score
        init_new_game()
        total_frames += frame
        frame = 0
        generation += 1

    frame += 1
    if VISUAL_ACTIVATED and SLEEP_DELAY:
        time.sleep(SLEEP_DELAY)

pygame.quit()