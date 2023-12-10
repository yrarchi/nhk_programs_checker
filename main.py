import yaml
from nhk_programs_checker.nhk_programs_checker import ProgramChecker
from nhk_programs_checker.slack_notifier import SlackNotifier


def main():
    with open("program_config.yml", "r") as f:
        program_config = yaml.safe_load(f)
    if has_interesting_programs(program_config):
        checker = ProgramChecker(program_config)
        target_term, check_result = checker.check_programs()
        notifier = SlackNotifier(target_term, check_result)
        notifier.send_slack_message()
    else:
        print(
            "No programs of interest have been registered, "
            "so the process is terminated."
        )


def has_interesting_programs(program_config):
    return (
        any(program_config.get("program_titles_of_interest"))
        or any(program_config.get("program_contents_of_interest"))
    )


if __name__ == "__main__":
    main()
