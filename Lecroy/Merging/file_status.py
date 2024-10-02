import os

def get_status(path: str) -> str:
    with open(path, "r") as f:
        return f.read().strip()

def write_status(file_path: str, status: bool) -> None:
    with open(file_path, "w") as file:
        file.write(str(status)) #not sure if str is necessary

def is_data_ready(name: str, data_path:str, status_path:str, force=False) -> bool:
    is_data_done = get_status(status_path) == "True"
    data_file_exists = os.path.isfile(data_path)

    #display status
    print(f"{name}: STATUS_FLAG={is_data_done}  and  FILE_EXISTS={data_file_exists}")

    if force:
        if not data_file_exists:
            print(f"Cannot merge data from ({data_path}) because it does not exist!")
        return data_file_exists
    return is_data_done and data_file_exists