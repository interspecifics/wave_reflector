import pygame
import os
import time
import subprocess
import sys  # Add this import
import random  # Add this import

# Initialize Pygame
pygame.init()

# Set up the display
WIDTH, HEIGHT = 600, 1024
screen = pygame.display.set_mode((WIDTH, HEIGHT), display=0)
pygame.display.set_caption("_wave_reflector")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
GREEN = (0, 255, 0)

# Fonts
roboto_font = pygame.font.Font("./Sanseriffic.otf", 56) 
button_font = pygame.font.Font("./Sanseriffic.otf", 32) 
list_font = pygame.font.Font("./Sanseriffic.otf", 32) 

# Button dimensions
BUTTON_WIDTH, BUTTON_HEIGHT = 250, 60
BUTTON_MARGIN = 40

# File list
current_path = "."
file_list = []
selected_index = 0

# readings_folder = 'records_RAW'
readings_folder = 'epocx_readings'

def update_file_list():
    global file_list
    file_list = os.listdir(current_path +'/'+ readings_folder)
    file_list.sort()
    random.shuffle(file_list)  # Shuffle the file list
    file_list = file_list[:10]  # Truncate to show only 10 files
    # file_list = [f[:20] for f in file_list]

def draw_buttons():
    pygame.draw.rect(screen, GREEN, (BUTTON_MARGIN, BUTTON_MARGIN+40, BUTTON_WIDTH, BUTTON_HEIGHT), 3)
    pygame.draw.rect(screen, GREEN, (WIDTH - BUTTON_WIDTH - BUTTON_MARGIN, BUTTON_MARGIN+40, BUTTON_WIDTH, BUTTON_HEIGHT), 3)
    
    show_files_text = button_font.render("c__", True, GREEN)
    open_file_text = button_font.render("r__", True, GREEN)
    
    screen.blit(show_files_text, (BUTTON_MARGIN + 80, BUTTON_MARGIN + 5+50))
    screen.blit(open_file_text, (WIDTH - BUTTON_WIDTH - BUTTON_MARGIN + 80, BUTTON_MARGIN + 5+50))

    # Draw Up and Down buttons
    pygame.draw.rect(screen, GREEN, (BUTTON_MARGIN, HEIGHT - BUTTON_HEIGHT - BUTTON_MARGIN - 80, BUTTON_WIDTH, BUTTON_HEIGHT), 3)
    pygame.draw.rect(screen, GREEN, (WIDTH - BUTTON_WIDTH - BUTTON_MARGIN, HEIGHT - BUTTON_HEIGHT - BUTTON_MARGIN - 80, BUTTON_WIDTH, BUTTON_HEIGHT), 3)
    
    # Use a larger font for the up and down button text
    large_button_font = pygame.font.Font("./Sanseriffic.otf", 48)
    up_button_text = large_button_font.render("<", True, GREEN)
    down_button_text = large_button_font.render(">", True, GREEN)
    
    screen.blit(up_button_text, (BUTTON_MARGIN + 80, HEIGHT - BUTTON_HEIGHT - BUTTON_MARGIN - 75))
    screen.blit(down_button_text, (WIDTH - BUTTON_WIDTH - BUTTON_MARGIN + 80, HEIGHT - BUTTON_HEIGHT - BUTTON_MARGIN - 75))

def draw_file_list():
    list_start = BUTTON_MARGIN + BUTTON_HEIGHT + 100
    
    pygame.draw.rect(screen, GREEN, (BUTTON_MARGIN, list_start-20, WIDTH-2*BUTTON_MARGIN, len(file_list)*30+120), 3)

    for i, file in enumerate(file_list):
        color = GREEN if i == selected_index else GRAY
        text = list_font.render(file[:20][:-4], True, color)
        screen.blit(text, (BUTTON_MARGIN+10, list_start + i * 30))

def main():
    global selected_index, current_path
    
    update_file_list()
    
    running = True
    while running:
        screen.fill(BLACK)
        draw_buttons()
        draw_file_list()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if BUTTON_MARGIN+40 <= y <= BUTTON_MARGIN+40 + BUTTON_HEIGHT:
                    if BUTTON_MARGIN <= x <= BUTTON_MARGIN + BUTTON_WIDTH:
                        # Show Files button clicked
                        pass
                    elif WIDTH - BUTTON_WIDTH - BUTTON_MARGIN <= x <= WIDTH - BUTTON_MARGIN:
                        # Open File button clicked
                        if file_list:
                            time.sleep(2)
                            screen.fill(BLACK)
                            pygame.display.flip()
                            time.sleep(10)

                            print(f"Opening: {file_list[selected_index]}")
                            subprocess.Popen([sys.executable, "EEG_udp_server_replay.py", "--file_path", f"{readings_folder}/{file_list[selected_index]}"])
                            subprocess.Popen([sys.executable, "ICAanalysis_udp_client.py"])
                            subprocess.Popen([sys.executable, "PSDanalysis_udp_client.py"])
                            time.sleep(10)
                            subprocess.Popen([sys.executable, "ICA_gradient_LFO_coms.py"])
                            subprocess.Popen([sys.executable, "launch_psd_gradients.py"])

                            time.sleep(60 * 50)  # Wait for 15 minutes (900 seconds)
                            main()
                elif HEIGHT - BUTTON_HEIGHT - BUTTON_MARGIN - 80 <= y <= HEIGHT - BUTTON_MARGIN - 80:
                    if BUTTON_MARGIN <= x <= BUTTON_MARGIN + BUTTON_WIDTH:
                        # Up button clicked
                        selected_index = (selected_index - 1) % len(file_list)
                    elif WIDTH - BUTTON_WIDTH - BUTTON_MARGIN <= x <= WIDTH - BUTTON_MARGIN:
                        # Down button clicked
                        selected_index = (selected_index + 1) % len(file_list)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_index = (selected_index - 1) % len(file_list)
                elif event.key == pygame.K_DOWN:
                    selected_index = (selected_index + 1) % len(file_list)
        
        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    main()