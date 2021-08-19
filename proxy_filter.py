def fastlink(configs:tuple):
    filtered = []
    for config in configs:
        remark = config['remark']
        if ('港' in remark or '日' in remark or '台' in remark) and config['multi'] < 3:
            filtered.append(config)
    return filtered