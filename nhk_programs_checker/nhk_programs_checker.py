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
        self.api_key = os.getenv("API_KEY")

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
        target_programs = [
            self._fetct_program_details(program) for program in formatted_programs
        ]
        return (target_term, target_programs)

    def _get_target_dates(self, today) -> list:
        first_target_date = today.strftime("%Y-%m-%d")
        last_target_date = (
            today + datetime.timedelta(days=self.num_days_to_check - 1)
        ).strftime("%Y-%m-%d")
        return [first_target_date, last_target_date]

    def _fetch_programs_for_date(self, target_date) -> list:
        programs_for_date = []
        for service_id in self.service_ids:
            api_endpoint = (
                "https://api.nhk.or.jp/v2/pg/list/"
                f"{self.area}/{service_id}/{target_date}.json?key={self.api_key}"
            )
            try:
                response = requests.get(api_endpoint)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                error_msg = str(e)
                print(error_msg.replace(f"?key={api_key}", "?key=***"))
                sys.exit()
            programs = response.json()["list"][service_id]
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
        key = (program["title"], program["content"], program["subtitle"])
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
        return any(re.search(pattern, program[attribute]) for pattern in search_list)

    def _format_program_info(self, program: dict) -> dict:
        DATETIME_FORMAT_LENGTH = 19
        start_time = datetime.datetime.strptime(
            program["start_time"][:DATETIME_FORMAT_LENGTH], "%Y-%m-%dT%H:%M:%S"
        ).strftime("%Y-%m-%d %H:%M")
        return {
            "title": program["title"],
            "subtitle": program["subtitle"],
            "content": program["content"],
            "start_time": start_time,
            "service_id": program["service"]["id"],
            "id": program["id"],
        }

    def _fetct_program_details(self, program: dict) -> dict:
        service_id = program["service_id"]
        id = program["id"]
        api_endpoint = (
            "https://api.nhk.or.jp/v2/pg/info/"
            f"{self.area}/{service_id}/{id}.json?key={self.api_key}"
        )
        response = requests.get(api_endpoint)
        program_details = response.json()["list"][service_id][0]
        for detail in ("program_url", "episode_url"):
            if detail in program_details:
                program[detail] = "https:" + program_details[detail]
        return program
