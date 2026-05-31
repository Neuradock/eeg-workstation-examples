from psychopy import visual, core, event, logging
import os

# ================= Configuration =================
# Screen parameters
SCREEN_REFRESH_RATE = 60  # Please set to your actual monitor refresh rate
STIM_FREQUENCY = 4      # Target stimulus frequency (Hz)
# Calculate frames per cycle (e.g., 60Hz screen for 10Hz stimulus = 6 frames per cycle)
# Note: ideally (refresh rate / frequency) should be an integer
FRAMES_PER_CYCLE = int(SCREEN_REFRESH_RATE / STIM_FREQUENCY)

# Experiment parameters
TRIAL_NUM = 6            # Number of trials (total flickers)
STIM_DURATION = 1.0       # Stimulus duration per trial (seconds)
REST_DURATION = 1.0       # Rest duration between stimuli (seconds)

# File paths
MARKER_FILE = '1.txt'
IMG_TARGET = 'white.png'
IMG_BG = 'black.png'
# ===========================================

def write_marker():
    """
    Write marker to 1.txt
    Use 'a' (append) mode to avoid overwriting previous records
    """
    try:
        with open(MARKER_FILE, 'a') as f:
            f.write('marker\n')
        print(f"Marker written to {MARKER_FILE}")
    except Exception as e:
        print(f"Error writing marker: {e}")

def run_experiment():
    # 1. Create window (fullscr=True for fullscreen, set False for testing)
    win = visual.Window(
        size=[900, 900],
        fullscr=True, 
        screen=0, 
        units='pix',
        color='black'
    )

    # 2. Load image stimuli
    # background (black.png) usually serves as base/off state
    stim_off = visual.ImageStim(win, image=IMG_BG,size=[400, 400])
    # target (white.png) serves as on state
    stim_on = visual.ImageStim(win, image=IMG_TARGET, size=[400, 400])
    
    # Instruction text
    text_instr = visual.TextStim(win, text='Press space to start the experiment...', color='white')
    text_instr.draw()
    win.flip()
    event.waitKeys(keyList=['space'])

    # 3. Experiment loop
    for i in range(TRIAL_NUM):
        # ---------------- Rest phase ----------------
        rest_text = visual.TextStim(win, text=f'Rest ({i+1}/{TRIAL_NUM})', color='grey')
        rest_text.draw()
        win.flip()
        core.wait(REST_DURATION)

        # ---------------- Stimulus phase ----------------
        
        # !! Key step: write marker just before stimulus onset !!
        

        # Calculate total frames to flip
        total_frames = int(STIM_DURATION * SCREEN_REFRESH_RATE)

        write_marker()
        for frame_n in range(total_frames):
            # SSVEP logic (square-wave flicker):
            # Logic: first half of cycle shows White, second half shows Black
            # Example 60Hz 10Hz: cycle=6 frames. 0,1,2 show White; 3,4,5 show Black
            
            phase = frame_n % FRAMES_PER_CYCLE
            if phase < (FRAMES_PER_CYCLE / 2):
                stim_on.draw()  # Display white.png
            else:
                stim_off.draw() # Display black.png (or nothing, showing background)
            
            win.flip() # Flip screen
            
            # Allow ESC to exit
            if 'escape' in event.getKeys():
                win.close()
                core.quit()

    # End
    end_text = visual.TextStim(win, text='Experiment finished', color='white')
    end_text.draw()
    win.flip()
    core.wait(2)
    
    win.close()
    core.quit()

if __name__ == "__main__":
    # Clear previous file (optional, reset file on each run)
    with open(MARKER_FILE, 'w') as f:
        f.write("HEADER_DEF,_,C,C,C,C,C,C,C\n")
        
    run_experiment()