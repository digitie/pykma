from kma.codes import label_for, normalize_value, parse_amount


def test_labels() -> None:
    assert label_for("SKY", "1") == "맑음"
    assert label_for("SKY", "2") is None
    assert label_for("PTY", "4", endpoint="getVilageFcst") == "소나기"
    assert label_for("PTY", "4", endpoint="getUltraSrtFcst") == "소나기"
    assert label_for("PTY", "4", endpoint="getUltraSrtNcst") is None
    assert label_for("PTY", "5", endpoint="getUltraSrtNcst") == "빗방울"
    assert label_for("PTY", None) is None


def test_normalize_value_keeps_pcp_and_sno_labels() -> None:
    assert normalize_value("TMP", "12.3") == 12.3
    assert normalize_value("PCP", "1.0mm 미만") == "1.0mm 미만"
    assert normalize_value("SNO", "적설없음") == "적설없음"
    assert normalize_value("TMP", "bad") == "bad"
    assert normalize_value("PTY", "4") == "4"


def test_parse_amount() -> None:
    assert parse_amount("강수없음") == 0.0
    assert parse_amount("적설없음") == 0.0
    assert parse_amount("없음") == 0.0
    assert parse_amount("") == 0.0
    assert parse_amount(None) is None
    assert parse_amount("1.0mm 미만") == 0.5
    assert parse_amount("<1.0mm") == 0.5
    assert parse_amount("30.0~50.0mm") == 40.0
    assert parse_amount("50.0mm 이상") == 50.0
    assert parse_amount("trace") is None
