import os

def delete_directory_content(directory: str):
    for file in os.listdir(directory):
        path = os.path.join(directory, file)
        if os.path.isfile(path):
            os.unlink(path)
        elif os.path.isdir(path):
            delete_directory_content(path)
            os.rmdir(path)