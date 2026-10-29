# WhatsApp Message Automation

A Python-based browser automation project that uses Selenium and Google Chrome to interact with WhatsApp Web.

## Features

- Automated Google Chrome launch
- Persistent browser profile for WhatsApp login
- Manual QR-code authentication and contact selection
- Explicit confirmation before sending messages
- Configurable message scheduling
- Execution logging and error handling

## Technology Stack

- Python
- Selenium WebDriver
- Google Chrome
- WhatsApp Web

## Project Structure

```text
Whatsapp_Message_Automate/
├── whatsapp.py
├── README.md
├── requirements.txt
└── .gitignore
```

## Installation

Install the required dependency:

```bash
python -m pip install -r requirements.txt
```

## Usage

Run the application:

```bash
python whatsapp.py
```

Follow the terminal instructions to open WhatsApp Web, authenticate if required, select a conversation, and confirm the intended action.

## Security and Responsible Use

Keep browser profiles, session data, credentials, and private logs out of version control. Use automation responsibly and respect recipient consent, privacy, and WhatsApp's applicable terms.

## Limitations

The application depends on WhatsApp Web's interface and may require maintenance when its HTML structure changes. Successful browser interaction does not guarantee message delivery.
