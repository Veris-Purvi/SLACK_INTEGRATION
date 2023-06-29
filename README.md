# SLACK_INTEGRATION

```
# Slack Bot for Meeting Scheduling

This is a Slack bot developed in Python for scheduling meetings using the Slack API and Veris API.

## Features

- Schedule meetings with team members using natural language commands.
- Validate meeting details such as date, venue, and participant information.
- Interact with the Veris API to create meeting invitations.
- Send OTP for user verification via email.
- Verify user input OTP for authentication.
- Post messages and replies to Slack channels.

## Installation

1. Clone the repository:

   ```shell
   git clone https://github.com/Veris-Purvi/SLACK_INTEGRATION.git
   ```

2. Install the required Python packages:

   ```shell
   pip install -r requirements.txt
   ```

3. Set up the necessary environment variables:

   - `OPENAI_KEY`: Your OpenAI API key.
   - `SLACK_BOT_TOKEN`: Your Slack bot token.

4. Run the Flask application:

   ```shell
   flask run
   ```

5. Set up the Slack Bot:

   - Create a new Slack app and enable the Socket Mode feature.
   - Add the necessary bot scopes and install the app to your workspace.
   - Copy the bot token and set it as the `SLACK_BOT_TOKEN` environment variable.

## Usage

To use the Slack bot, invite it to the desired Slack channel and interact with it using natural language commands. Here are some example commands:

- "Please schedule my meeting with Ms. Anusha in test on 23/03/2023 at 13:30:30 on her email ID anusha.shet@veris.in"
- "Schedule a meeting with John at the office on 25/03/2023 from 10:00 AM to 12:00 PM"

The bot will validate the meeting details and interact with the Veris API to create the meeting invitations. It will notify you of the status and provide any necessary instructions.


