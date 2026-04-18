from apps.payments.models import Payment

def extract_payment_method_details(payment_entity: dict) -> tuple[str, dict]:
    method = payment_entity.get("method") or Payment.Method.UNKNOWN

    if method == Payment.Method.CARD:
        card = payment_entity.get("card", {}) or {}
        return method, {
            "last4": card.get("last4", ""),
            "network": card.get("network", ""),
            "issuer": card.get("issuer", ""),
            "card_type": card.get("type", ""),
        }

    if method == Payment.Method.UPI:
        return method, {
            "vpa": payment_entity.get("vpa", ""),
        }

    if method == Payment.Method.NETBANKING:
        return method, {
            "bank": payment_entity.get("bank", ""),
        }

    if method == Payment.Method.WALLET:
        return method, {
            "wallet": payment_entity.get("wallet", ""),
        }

    return method, {}