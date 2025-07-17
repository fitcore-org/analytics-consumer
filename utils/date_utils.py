from datetime import date, datetime

def parse_date(val):
    if isinstance(val, list) and len(val) == 3:
        return date(val[0], val[1], val[2])
    elif isinstance(val, str):
        return date.fromisoformat(val)
    else:
        return None

def parse_datetime(val):
    if isinstance(val, str):
        return datetime.fromisoformat(val)
    elif isinstance(val, list) and len(val) >= 3:
        args = val[:6]
        if len(val) > 6:
            micro = int(str(val[6])[:6])
            args.append(micro)
        return datetime(*args)
    return None