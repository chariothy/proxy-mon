def fastlink(configs:tuple):
    filtered = []
    for config in configs:
        remark = config['remark']
        if '广' in remark or '港' in remark or '日' in remark or '韩' in remark or '台' in remark:
            filtered.append(config)
    return filtered