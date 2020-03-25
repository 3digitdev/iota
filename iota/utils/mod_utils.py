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


def get_params(command, regex, groups) -> dict:
    match = re.match(regex, command)
    params = {}
    for group_name in groups:
        try:
            params[group_name] = match.group(group_name)
        except IndexError:
            params[group_name] = ""
    return params
