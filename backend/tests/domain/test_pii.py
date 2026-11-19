from dar.domain.pii import redact


def test_email_is_replaced_by_placeholder():
    result = redact("Contact me at jane.doe@example.com please")
    assert "jane.doe@example.com" not in result.text
    assert "[EMAIL_1]" in result.text


def test_phone_is_replaced_by_placeholder():
    result = redact("Call +966 50 123 4567 today")
    assert "123 4567" not in result.text
    assert "[PHONE_1]" in result.text


def test_same_value_gets_same_placeholder_and_different_values_differ():
    result = redact("a@x.com then b@x.com then a@x.com")
    assert result.text == "[EMAIL_1] then [EMAIL_2] then [EMAIL_1]"


def test_text_without_pii_is_unchanged():
    text = "3 bedroom apartment in Riyadh, 1,200,000 SAR, 120 sqm"
    assert redact(text).text == text


def test_vault_can_restore_within_the_call_but_is_not_part_of_the_text():
    result = redact("mail a@x.com")
    assert result.restore(result.text) == "mail a@x.com"


def test_phone_at_the_end_of_a_sentence_is_still_redacted():
    for text in ("Call +971 4 123 4567.", "Call +971 4 123 4567, thanks", "(Call +971 4 123 4567)"):
        assert "123 4567" not in redact(text).text


def test_decimal_numbers_and_prices_ending_a_sentence_are_untouched():
    text = "Price is 1,200,000 SAR. Area 350.5 sqm."
    assert redact(text).text == text


def test_prices_and_areas_are_not_mistaken_for_phones():
    text = "Price 2500000 SAR, area 350 sqm, built 2024"
    assert redact(text).text == text
