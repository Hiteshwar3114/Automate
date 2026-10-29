
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, WebDriverException

# ============================================================
# CONFIGURATION
# ============================================================

MESSAGE = "Oyee Chinnu I Love You So Much"
INTERVAL_SECONDS = 60
MAX_MESSAGES = 400

STOP_HOUR = 7
STOP_MINUTE = 0
LOGIN_TIMEOUT = 300

BASE_DIR = Path(__file__).resolve().parent
PROFILE_DIR = BASE_DIR / "chrome_whatsapp_profile"
LOG_FILE = BASE_DIR / "whatsapp_scheduler.log"

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    encoding="utf-8",
)


def log(status, message):
    line = (
        f"[{datetime.now().astimezone():%Y-%m-%d %H:%M:%S %Z}] "
        f"{status}: {message}"
    )
    print(line, flush=True)

    if status == "SUCCESS":
        logging.info(message)
    else:
        logging.error(message)


# ============================================================
# CHROME
# ============================================================

def launch_chrome():
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={PROFILE_DIR.resolve()}")
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)
    driver.get("https://web.whatsapp.com/")

    log("SUCCESS", "Google Chrome launched and WhatsApp Web opened.")
    return driver


def wait_for_login(driver):
    print("\nScan the QR code if required.")

    try:
        WebDriverWait(driver, LOGIN_TIMEOUT).until(
            lambda d: bool(d.find_elements(By.ID, "pane-side"))
        )
        log("SUCCESS", "WhatsApp chat list detected.")
        return True
    except TimeoutException:
        log("ERROR", "WhatsApp login timed out.")
        return False


# ============================================================
# CHAT AND COMPOSER
# ============================================================

def get_chat_title(driver):
    selectors = [
        '[data-testid="conversation-info-header-chat-title"]',
        'header span[title]',
    ]

    for selector in selectors:
        for element in driver.find_elements(By.CSS_SELECTOR, selector):
            try:
                title = (
                    element.get_attribute("title") or element.text or ""
                ).strip()
                if title and title.lower() not in ("whatsapp", "search"):
                    return title
            except WebDriverException:
                pass

    return None


def get_composer(driver):
    selectors = [
        'footer [data-testid="conversation-compose-box-input"]',
        'footer [contenteditable="true"][role="textbox"]',
        'footer [contenteditable="true"]',
    ]

    for selector in selectors:
        for element in driver.find_elements(By.CSS_SELECTOR, selector):
            try:
                if element.is_displayed() and element.is_enabled():
                    return element
            except WebDriverException:
                pass

    return None


def select_chat(driver):
    input(
        "\nSelect the intended contact manually in Chrome, "
        "then press ENTER here..."
    )

    if "web.whatsapp.com" not in driver.current_url:
        raise RuntimeError("WhatsApp Web is not open.")

    if not driver.find_elements(By.ID, "pane-side"):
        raise RuntimeError("WhatsApp chat list is unavailable.")

    title = get_chat_title(driver)

    if not title or get_composer(driver) is None:
        raise RuntimeError(
            "Could not verify the selected conversation and message box."
        )

    log("SUCCESS", f"Selected contact verified: {title}")
    return title, driver.current_url


# ============================================================
# SEND ONE MESSAGE
# ============================================================

def send_one_message(driver, expected_title, expected_url):
    if "web.whatsapp.com" not in driver.current_url:
        raise RuntimeError("WhatsApp Web is no longer open.")

    if driver.current_url != expected_url:
        raise RuntimeError("WhatsApp page changed. Sending cancelled.")

    if get_chat_title(driver) != expected_title:
        raise RuntimeError("Selected contact changed. Sending cancelled.")

    composer = get_composer(driver)
    if composer is None:
        raise RuntimeError("Message box is unavailable.")

    composer.click()
    composer.send_keys(MESSAGE)

    entered = composer.get_attribute("textContent") or ""
    if entered.strip() != MESSAGE:
        composer.clear()
        raise RuntimeError("Could not verify message text.")

    send_button = None

    for selector in [
        'footer [data-testid="send"]',
        'footer button[aria-label="Send"]',
        'footer [role="button"][aria-label="Send"]',
    ]:
        for element in driver.find_elements(By.CSS_SELECTOR, selector):
            try:
                if element.is_displayed() and element.is_enabled():
                    send_button = element
                    break
            except WebDriverException:
                pass

        if send_button is not None:
            break

    if send_button is None:
        composer.clear()
        raise RuntimeError("Send button not found.")

    # One send attempt only; no automatic retry.
    send_button.click()

    try:
        WebDriverWait(driver, 10).until(
            lambda d: (
                get_composer(d) is not None
                and not (
                    get_composer(d).get_attribute("textContent") or ""
                ).strip()
            )
        )
        log(
            "SUCCESS",
            f"Send action completed for {expected_title}. "
            "Recipient delivery is not independently verified.",
        )
        return True

    except TimeoutException:
        log(
            "ERROR",
            "Send outcome is uncertain. Check WhatsApp manually "
            "before attempting another send.",
        )
        return False


# ============================================================
# REPEATED SCHEDULE WITH LIMITS
# ============================================================

def tomorrow_six_am():
    now = datetime.now().astimezone()
    target = now.replace(
        hour=STOP_HOUR,
        minute=STOP_MINUTE,
        second=0,
        microsecond=0,
    )

    if now >= target:
        target += timedelta(days=1)

    return target


def run_schedule(driver, chat_title, chat_url):
    stop_at = tomorrow_six_am()

    print("\nSchedule settings")
    print(f"Message: {MESSAGE}")
    print(f"Recipient: {chat_title}")
    print(f"Interval: {INTERVAL_SECONDS} seconds")
    print(f"Maximum sends: {MAX_MESSAGES}")
    print(f"Stop time: {stop_at:%Y-%m-%d %H:%M:%S %Z}")

    answer = input(
        "\nConfirm this limited schedule? [y/n]: "
    ).strip().lower()

    if answer not in ("y", "yes"):
        log("SUCCESS", "Schedule cancelled. No repeated messages sent.")
        return

    sent_count = 0

    while sent_count < MAX_MESSAGES:
        if datetime.now().astimezone() >= stop_at:
            log("SUCCESS", "Stop time reached.")
            break

        try:
            result = send_one_message(driver, chat_title, chat_url)
            sent_count += 1

            if not result:
                log(
                    "ERROR",
                    "Stopping because send completion could not be verified.",
                )
                break

        except Exception as exc:
            log("ERROR", f"Stopping schedule: {type(exc).__name__}: {exc}")
            break

        if sent_count >= MAX_MESSAGES:
            break

        remaining = (
            stop_at - datetime.now().astimezone()
        ).total_seconds()

        if remaining <= 0:
            break

        print(
            f"Next attempt in {INTERVAL_SECONDS} seconds. "
            f"Completed {sent_count}/{MAX_MESSAGES}. "
            "Press Ctrl+C to stop.",
            flush=True,
        )

        try:
            time.sleep(min(INTERVAL_SECONDS, remaining))
        except KeyboardInterrupt:
            log("SUCCESS", "Schedule stopped by user.")
            break

    log("SUCCESS", f"Schedule ended. Send attempts: {sent_count}.")


# ============================================================
# MAIN
# ============================================================

def main():
    driver = None

    try:
        print("=" * 55)
        print("WHATSAPP CHROME SCHEDULER")
        print("=" * 55)

        driver = launch_chrome()

        if not wait_for_login(driver):
            return

        chat_title, chat_url = select_chat(driver)

        print(f"\nVerified contact: {chat_title}")
        print(f"Message configured in code: {MESSAGE}")

        run_schedule(driver, chat_title, chat_url)

    except KeyboardInterrupt:
        log("SUCCESS", "Stopped by user.")

    except Exception as exc:
        log("ERROR", f"{type(exc).__name__}: {exc}")
        print(f"\nERROR: {exc}")

    finally:
        if driver is not None:
            answer = input(
                "\nClose automated Chrome? [y/n]: "
            ).strip().lower()

            if answer in ("y", "yes"):
                try:
                    driver.quit()
                except WebDriverException:
                    pass
            else:
                print(
                    "Chrome remains open. The Python scheduler has ended."
                )


if __name__ == "__main__":
    main()
