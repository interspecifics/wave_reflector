import pygame
import os
import subprocess
import time

# Initialize Pygame
pygame.init()

# Set up the display
WIDTH, HEIGHT = 720, 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("_wave_reflector")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
DARKGREEN = (0, 128, 0)

# Fonts
#button_font = pygame.font.Font(None, 36)
#list_font = pygame.font.Font(None, 24)
roboto_font = pygame.font.Font("./Sanseriffic.otf", 56) 
button_font = pygame.font.Font("./Sanseriffic.otf", 32) 
list_font = pygame.font.Font("./Sanseriffic.otf", 32) 


# Button dimensions
BUTTON_WIDTH, BUTTON_HEIGHT = 300, 60
BUTTON_MARGIN = 40

# File list
current_path = "."
file_list = []
selected_index = 0

def update_file_list():
    global file_list
    file_list = os.listdir(current_path)
    file_list.sort()

def draw_buttons():
    pygame.draw.rect(screen, GREEN, (BUTTON_MARGIN, BUTTON_MARGIN+40, BUTTON_WIDTH, BUTTON_HEIGHT), 3)
    pygame.draw.rect(screen, GREEN, (WIDTH - BUTTON_WIDTH - BUTTON_MARGIN, BUTTON_MARGIN+40, BUTTON_WIDTH, BUTTON_HEIGHT), 3)
    
    show_files_text = button_font.render("__c__", True, GREEN)
    open_file_text = button_font.render("__r__", True, GREEN)
    
    screen.blit(show_files_text, (BUTTON_MARGIN + 80, BUTTON_MARGIN + 5+50))
    screen.blit(open_file_text, (WIDTH - BUTTON_WIDTH - BUTTON_MARGIN + 80, BUTTON_MARGIN + 5+50))

def draw_file_list():
    list_start = BUTTON_MARGIN + BUTTON_HEIGHT + 100
    
    pygame.draw.rect(screen, GREEN, (BUTTON_MARGIN, list_start-20, WIDTH-2*BUTTON_MARGIN, len(file_list)*30+240), 3)

    for i, file in enumerate(file_list):
        color = GREEN if i == selected_index else GRAY
        text = list_font.render(file, True, color)
        screen.blit(text, (BUTTON_MARGIN+10, list_start + i * 30))

def show_presentation():
    screen.fill(BLACK)
    text = roboto_font.render("_wave_reflector", True, WHITE)
    text_rect = text.get_rect(center=(WIDTH // 2 + 140, HEIGHT // 2 + 480))
    screen.blit(text, text_rect)
    pygame.display.flip()
    time.sleep(2)

def main():
    global selected_index, current_path
    
    update_file_list()
    
    show_presentation()
    
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
                        #result = subprocess.run(["dir", current_path], capture_output=True, text=True)
                        #print(result.stdout)
                        os.system("""python ICA_gradient_LFO_coms.py""")
                    elif WIDTH - BUTTON_WIDTH - BUTTON_MARGIN <= x <= WIDTH - BUTTON_MARGIN:
                        # Open File button clicked
                        if file_list:
                            print(f"Opening: {file_list[selected_index]}")
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_index = (selected_index - 1) % len(file_list)
                elif event.key == pygame.K_DOWN:
                    selected_index = (selected_index + 1) % len(file_list)
        
        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    main()
