from datetime import date, timedelta
import pytest
from playwright.sync_api import Page, expect


def tomorrow() -> str:
    return (date.today() + timedelta(days=1)).isoformat()


VALID_BOOKING = {
    "room": "Средняя · до 10 человек",
    "date": tomorrow(),
    "start": "10:00",
    "end": "11:00",
    "guests": 8,
    "name": "Иван",
    "email": "ivan@company.ru",
}
LONG_BOOKING = {**VALID_BOOKING, "start": "01:00", "end": "23:00"}
REQUIRED_FIELD_CASES = [
    # (ключ поля, пустое значение, текст ошибки под полем)
    ("room", "Выберите комнату", "Выберите комнату."),
    ("date", "", "Укажите дату."),
    ("start", "", "Укажите время начала."),
    ("end", "", "Укажите время окончания."),
    ("guests", "", "Укажите количество участников."),
    ("name", "", "Укажите имя."),
    ("email", "", "Укажите рабочую почту."),
]
FORM_ERROR = "Проверьте, пожалуйста, заполнение формы."
FIELDS = {
    "room": "room",
    "date": "date",
    "start": "startTime",
    "end": "endTime",
    "guests": "participants",
    "name": "name",
    "email": "email",
}


def field(page: Page, key: str):
    return page.locator(f"[name='{FIELDS[key]}']")


def open_form(page: Page, base_url: str) -> None:
    page.goto(base_url, wait_until="domcontentloaded")


def fill_form(page: Page, data: dict) -> None:
    field(page, "room").select_option(label=data["room"])
    field(page, "date").fill(data["date"])
    field(page, "start").fill(data["start"])
    field(page, "end").fill(data["end"])
    field(page, "guests").fill(str(data["guests"]))
    field(page, "name").fill(data["name"])
    field(page, "email").fill(data["email"])


def submit(page: Page) -> None:
    page.get_by_role("button", name="Забронировать").click()


def success_message(page: Page):
    return page.get_by_text("Бронирование создано.")


def expected_summary(data: dict) -> str:
    room = data["room"].split(" · ")[0]
    return f"{room}, {data['date']}, {data['start']}–{data['end']} · {data['name']}"


def test_successful_booking(page: Page, base_url: str):
    open_form(page, base_url)
    fill_form(page, VALID_BOOKING)
    submit(page)

    expect(success_message(page)).to_be_visible()
    expect(page.get_by_role("status")).to_contain_text(expected_summary(VALID_BOOKING))


@pytest.mark.parametrize(
    "field_key, empty_value, error_text",
    REQUIRED_FIELD_CASES,
    ids=[case[0] for case in REQUIRED_FIELD_CASES],
)
def test_required_field_is_empty(
    page: Page, base_url: str, field_key, empty_value, error_text
):
    open_form(page, base_url)
    fill_form(page, {**VALID_BOOKING, field_key: empty_value})
    submit(page)

    expect(page.get_by_text(error_text, exact=True)).to_be_visible()
    expect(page.get_by_text(FORM_ERROR)).to_be_visible()
    expect(success_message(page)).not_to_be_visible()


@pytest.mark.xfail(
    strict=True,
    reason="BUG-03: можно забронировать комнату более чем на 4 часа",
    raises=AssertionError,
)
def test_discovered_defect(page: Page, base_url: str):
    open_form(page, base_url)
    fill_form(page, LONG_BOOKING)
    submit(page)

    expect(success_message(page)).not_to_be_visible()
