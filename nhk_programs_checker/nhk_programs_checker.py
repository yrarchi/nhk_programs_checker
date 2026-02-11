import datetime
import os
import re
import requests
import sys


class ProgramChecker:
    def __init__(self, program_config: dict):
        self.seen_programs = set()
        self.service_ids = program_config["service_ids"]
        self.area = program_config["area"]
        self.num_days_to_check = program_config["num_days_to_check"]
        self.titles_of_interest = (
            program_config["program_titles_of_interest"]
            if program_config["program_titles_of_interest"] != [None] else []
        )
        self.contents_of_interest = (
            program_config["program_contents_of_interest"]
            if program_config["program_contents_of_interest"] != [None] else []
        )

    def check_programs(self):
        all_programs = []
        today = datetime.date.today()
        target_term: list = self._get_target_dates(today)
        for i in range(self.num_days_to_check):
            target_date = (today + datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            programs_for_date: list = self._fetch_programs_for_date(target_date)
            all_programs.extend(programs_for_date)
        programs_of_interest: list = self._filter_programs_of_interest(all_programs)
        formatted_programs = [
            self._format_program_info(program) for program in programs_of_interest
        ]
        return (target_term, formatted_programs)

    def _get_target_dates(self, today) -> list:
        first_target_date = today.strftime("%Y-%m-%d")
        last_target_date = (
            today + datetime.timedelta(days=self.num_days_to_check - 1)
        ).strftime("%Y-%m-%d")
        return [first_target_date, last_target_date]

    def _fetch_programs_for_date(self, target_date) -> list:
        programs_for_date = []
        api_key = os.getenv("API_KEY")
        for service_id in self.service_ids:
            api_endpoint = (
                "https://program-api.nhk.jp/v3/papiPgDateTv?"
                f"service={service_id}&area={self.area}&date={target_date}&key={api_key}"
            )
            try:
                response = requests.get(api_endpoint)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                error_msg = str(e)
                print(error_msg.replace(f"?key={api_key}", "?key=***"))
                sys.exit()
            programs = response.json()[service_id]["publication"]
            programs_for_date.extend(programs)
        return programs_for_date

    def _filter_programs_of_interest(self, programs: list) -> list:
        return [
            program for program in programs
            if self._is_new_program(program)
            and (
                self._is_program_of_interest(program, "title")
                or self._is_program_of_interest(program, "content")
            )
        ]

    def _is_new_program(self, program: dict) -> bool:
        key = (
            program["name"],
            program.get("about", {}).get("description", ""),
            program.get("description", "")
        )
        for seen_key in self.seen_programs:
            if key[0] == seen_key[0] or key[1] == seen_key[1] or key[2] == seen_key[2]:
                return False
        self.seen_programs.add(key)
        return True

    def _is_program_of_interest(self, program: dict, attribute: str) -> bool:
        search_list = (
            self.titles_of_interest if attribute == "title"
            else self.contents_of_interest if attribute == "content"
            else []
        )
        text_to_search = ""
        if attribute == "title":
            text_to_search = program.get("name", "")
        elif attribute == "content":
            text_to_search = program.get("about", {}).get("description", "")

        return any(re.search(pattern, text_to_search) for pattern in search_list)

    def _format_program_info(self, program: dict) -> dict:
        DATETIME_FORMAT_LENGTH = 19
        start_time = datetime.datetime.strptime(
            program["startDate"][:DATETIME_FORMAT_LENGTH], "%Y-%m-%dT%H:%M:%S"
        ).strftime("%Y-%m-%d %H:%M")
        return {
            "title": program["name"],
            "subtitle": program.get("description", ""),
            "content": program.get("about", {}).get("description", ""),
            "start_time": start_time,
            "service_id": program["identifierGroup"]["serviceId"],
        }