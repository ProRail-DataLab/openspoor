from pathlib import Path
import yaml


def read_config():
    default_filename = 'config.yaml'
    config_file = get_package_root().absolute() / default_filename

    with open(config_file) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
    return config


def get_package_root() -> Path:
    """Returns package root folder."""
    conf_folder = Path(__file__).parent.parent
    dirs_in_scope = [x.name for x in conf_folder.iterdir() if x.is_dir()]

    if "mapservices" not in dirs_in_scope:
        msg = (
            f"Not the right root directory. ({conf_folder.absolute()}) "
            "Did you change the project structure?"
        )
        raise ValueError(msg)

    return conf_folder
