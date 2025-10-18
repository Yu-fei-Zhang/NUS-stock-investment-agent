import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

key = input("请输入要检查的键名：").strip()
if not key:
    exit()

# 查看类型
key_type = r.type(key)
print(f"\n🔍 键 '{key}' 的类型是：{key_type}")

# 按类型读取
if key_type == 'string':
    print("值：", r.get(key))

elif key_type == 'list':
    print("值（前10条）：", r.lrange(key, 0, 9))

elif key_type == 'hash':
    print("字段和值：")
    for field, val in r.hgetall(key).items():
        print(f"  {field}: {val}")

elif key_type == 'set':
    print("成员：", r.smembers(key))

elif key_type == 'zset':
    print("有序集合前10条：", r.zrange(key, 0, 9, withscores=True))

else:
    print("⚠️ 未知类型或键不存在")
