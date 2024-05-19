import time
import sgf2anim
from sgf2anim._graphics_settings import get_settings

def main():
    start_time = time.time()
    sgf2anim.process_directory("diagrams")
    #get_settings().set_for_animated_diagram()
    #sgf2anim.save_GIF("work.sgf", save_as_diagram=False)
    #get_settings().set_for_diagram()
    #sgf2anim.save_GIF("work.sgf", save_as_diagram=True)
    elapsed = time.time() - start_time
    print(f"that took {elapsed:>.2f} seconds")
    
main()