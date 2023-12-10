import os
from jinja2 import Template
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class SlackNotifier:
    def __init__(self, target_term: list, check_result: list):
        self.target_term = target_term
        self.check_result = check_result

    def send_slack_message(self):
        token = os.getenv("SLACK_BOT_TOKEN")
        channel_id = os.getenv("CHANNEL_ID")
        client = WebClient(token=token)
        message = self._render_message()
        try:
            client.chat_postMessage(
                channel=channel_id,
                blocks=message,
                text="Notify program information."
            )
        except SlackApiError as e:
            print(f"Got an error: {e.response['error']}")

    def _render_message(self):
        template_path = os.path.join(os.path.dirname(__file__), "template.json")
        with open(template_path, "r") as file:
            template_content = file.read()
            message_template = Template(template_content)
        return message_template.render(
            data=self.check_result, target_term=self.target_term
        )
