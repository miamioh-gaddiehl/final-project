import time
from typing import Optional

import pytest
import requests
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


@pytest.fixture
def driver():
    firefox_options = Options()
    firefox_options.profile = webdriver.FirefoxProfile()
    firefox_options.add_argument("--no-sandbox")
    firefox_options.add_argument("--disable-dev-shm-usage")
    firefox_options.add_argument("--headless")
    service = Service(executable_path="/usr/local/bin/geckodriver")
    driver = webdriver.Firefox(options=firefox_options, service=service)
    yield driver
    driver.quit()


@pytest.fixture
def clean_notes(driver, url_base):
    driver.get(f"{url_base}/")
    time.sleep(1)

    delete_all_notes(driver)
    yield
    delete_all_notes(driver)


def delete_all_notes(driver):
    notes = driver.find_elements(By.CLASS_NAME, "note")
    for note in notes:
        delete_note(driver, note)


def delete_note(driver, note):
    trash = driver.find_element(By.ID, "trash")
    actions = ActionChains(driver)
    actions.click_and_hold(note).move_to_element(trash).pause(0.5).release().perform()
    time.sleep(0.5)


def add_note(driver, url_base) -> Optional[WebElement]:
    driver.get(f"{url_base}/")

    add_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "addNoteBtn")))
    add_button.click()

    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "note")))

    notes = driver.find_elements(By.CLASS_NAME, "note")
    try:
        return sorted(notes, key=lambda x: -int(x.get_attribute("data-id")))[0]
    except IndexError:
        return None


def get_note_by_id(driver, note_id: int) -> Optional[WebElement]:
    try:
        return driver.find_element(By.XPATH, f"//div[contains(@class, 'note') and @data-id='{note_id}']")
    except NoSuchElementException:
        return None


def test_index_loads(driver, url_base):
    driver.get(f"{url_base}/")
    time.sleep(1)
    assert "Add Note" in driver.page_source


def test_add_note(driver, url_base, clean_notes):
    note = add_note(driver, url_base)
    assert note is not None


def test_update_note(driver, url_base, clean_notes):
    note = add_note(driver, url_base)
    assert note is not None

    textarea = note.find_element(By.TAG_NAME, "textarea")
    note_id = note.get_attribute("data-id")
    assert note_id is not None

    actions = ActionChains(driver)
    actions.double_click(note).perform()
    textarea.send_keys("Test Note")

    time.sleep(1)

    res = requests.get(f"{url_base}/api/notes/{note_id}")
    assert res.status_code == 200
    assert res.json()["content"] == "Test Note"


def test_delete_note(driver, url_base, clean_notes):
    note = add_note(driver, url_base)
    note_id = int(note.get_attribute("data-id"))
    assert note is not None

    delete_note(driver, note)
    assert get_note_by_id(driver, note_id) is None

    res = requests.get(f"{url_base}/api/notes/{note_id}")
    assert res.status_code == 404
