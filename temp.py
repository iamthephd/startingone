result = {
    k: dict(sorted(v.items(), key=lambda item: item[1], reverse=True)[:n])
    for k, v in data.items()
}