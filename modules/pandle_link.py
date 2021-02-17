#! python3
# pw_module.py - creates passwords, checks for password strength
import logging

logging.basicConfig(
    level=logging.ERROR, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)

import subprocess
import locale
import os

class CaptureOutput():
    @staticmethod
    def PW(account_name): # gets account password from Pandle application
        cwd = os.getcwd()
        cwd = cwd.split("\\")
        root_directory = []
        for dir in cwd:
            root_directory.append("..")
        os.chdir(
            os.path.abspath(os.path.join(*root_directory)) # change the cwd back to 
            )                                              # the root directory to run command
        proccess_obj = subprocess.run(
            [
                "python", 
                    os.path.join(
                        "C:", "users", "eliro", "onedrive", 
                        "programming", "applications", "pandle", 
                        "remote_pandle.py"
                    ), 
                account_name # run subprocess command and capture output
            ], 
            stdout=subprocess.PIPE
            )
        output = proccess_obj.stdout.decode(
            locale.getdefaultlocale()[1]
            )
        return output