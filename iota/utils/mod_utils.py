import re


def parse_to_regexes(config: dict) -> list:
    reg = re.compile(r'\{[^\}]+\}')
    commands = []
    for command in config["command_words"]:
        for placeholder in reg.findall(command):
            name = placeholder[1:-1]
            command = command.replace(
                placeholder,
                f"(?P<{name}>{config['regexes'][name]})"
            )
        commands.append(re.compile(command))
    return commands
