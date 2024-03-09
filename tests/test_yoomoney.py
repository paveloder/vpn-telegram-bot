import uuid

from services.yoomoney import _create_new_bill


def test_yoomoney_payments():
    _create_new_bill(uuid.uuid4())
