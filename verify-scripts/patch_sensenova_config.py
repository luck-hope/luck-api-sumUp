"""把 .env 的 SENSENOVA_API_KEY 补进 usage-gateway/config.json 的 sensenova 条目，保留其他内容。"""
import json
import os
import re
import io

CONFIG_PATH = r"D:\Hermes\usage-gateway\data\config.json"
ENV_PATH = r"D:\Hermes\Hermes Agent CN Desktop\data\hermes-home\.env"

# 1. 从 .env 读商汤 key
env_key = None
for line in io.open(ENV_PATH, encoding="utf-8"):
    line = line.strip()
    if line.startswith("SENSENOVA_API_KEY="):
        env_key = line.split("=", 1)[1].strip()
        break
if not env_key:
    raise SystemExit("未在 .env 找到 SENSENOVA_API_KEY")

# 2. 读 config.json
cfg = json.loads(io.open(CONFIG_PATH, encoding="utf-8").read())

# 3. 找到 sensenova 条目并补 key（保留已有内容）
found = False
for up in cfg.get("upstreams", []):
    if up.get("name") == "sensenova":
        if not up.get("api_key"):
            up["api_key"] = env_key
            found = True
        else:
            print("sensenova 已有 api_key，保留不动")
            found = True
        break
if not found:
    raise SystemExit("config.json 中没有 sensenova 条目")

# 4. 写回（保留缩进/顺序）
with io.open(CONFIG_PATH, "w", encoding="utf-8") as f:
    f.write(json.dumps(cfg, ensure_ascii=False, indent=2))
print("已补入商汤 key（长度 %d），其余配置保留" % len(env_key))

# 5. 校验写回后的 JSON 可读
reload = json.loads(io.open(CONFIG_PATH, encoding="utf-8").read())
for up in reload["upstreams"]:
    key_show = (up["api_key"][:5] + "…" + up["api_key"][-3:]) if up.get("api_key") else "(空)"
    print(f"  {up['name']:<12} protocol={up['protocol']:<10} key={key_show}")
