ascii = """
    __  _______  ______   ____  ___    ____  ________     _    __ ___
   /  |/  / __ \/ ____/  / __ \/   |  / __ \/  _/ __ \   | |  / /<  /
  / /|_/ / / / / __/    / /_/ / /| | / / / // // / / /   | | / / / / 
 / /  / / /_/ / /___   / _, _/ ___ |/ /_/ _/ // /_/ /    | |/ _ / /  
/_/  /_/\____/_____/  /_/ |_/_/  |_/_____/___/\____/     |___(_/_/   
                                                                                                                                     
-----------------"""  

import os
import sys
import logging

# Setup initial loggers

log = logging.getLogger('Moe')
log.setLevel(logging.DEBUG)

sh = logging.StreamHandler(stream=sys.stdout)
sh.setFormatter(logging.Formatter(
    fmt="[%(asctime)s] - %(levelname)s: %(message)s"
))

sh.setLevel(logging.INFO)
log.addHandler(sh)

def bugger_off(msg="Press enter to continue . . .", code=1):
    input(msg)
    sys.exit(code)

def run():
    try:
        from core.bot import Moe
        m = Moe()
        print(ascii)
        print("Connecting...\n")
        m.run()
    except Exception as e:
        log.warning(f"Closing bot : {e}")
        bugger_off()
        os.system("PAUSE")
        
if __name__ == "__main__":
    run()
