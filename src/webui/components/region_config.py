REGIONS = {
    "江苏省": {
        "key": "jiangsu",
        "cities": {
            "南京市": {"key": "nanjing", "skills": []},
            "无锡市": {"key": "wuxi", "skills": []},
            "徐州市": {"key": "xuzhou", "skills": []},
            "常州市": {"key": "changzhou", "skills": []},
            "苏州市": {"key": "suzhou", "skills": []},
            "南通市": {"key": "nantong", "skills": []},
            "连云港市": {"key": "lianyungang", "skills": []},
            "淮安市": {"key": "huaian", "skills": []},
            "盐城市": {"key": "yancheng", "skills": []},
            "扬州市": {"key": "yangzhou", "skills": []},
            "镇江市": {"key": "zhenjiang", "skills": []},
            "泰州市": {"key": "taizhou", "skills": []},
            "宿迁市": {"key": "suqian", "skills": []}
        }
    },
    "浙江省": {
        "key": "zhejiang",
        "cities": {
            "杭州市": {"key": "hangzhou", "skills": []},
            "宁波市": {"key": "ningbo", "skills": []},
            "温州市": {"key": "wenzhou", "skills": []},
            "嘉兴市": {"key": "jiaxing", "skills": []},
            "湖州市": {"key": "huzhou", "skills": []},
            "绍兴市": {"key": "shaoxing", "skills": []},
            "金华市": {"key": "jinhua", "skills": []},
            "衢州市": {"key": "quzhou", "skills": []},
            "舟山市": {"key": "zhoushan", "skills": []},
            "台州市": {"key": "taizhou", "skills": []},
            "丽水市": {"key": "lishui", "skills": []}
        }
    },
    "安徽省": {
        "key": "anhui",
        "cities": {
            "合肥市": {"key": "hefei", "skills": []},
            "淮北市": {"key": "huaibei", "skills": []},
            "亳州市": {"key": "bozhou", "skills": []},
            "宿州市": {"key": "suzhou_anhui", "skills": []},
            "蚌埠市": {"key": "bengbu", "skills": []},
            "阜阳市": {"key": "fuyang", "skills": []},
            "淮南市": {"key": "huainan", "skills": []},
            "滁州市": {"key": "chuzhou", "skills": []},
            "六安市": {"key": "liuan", "skills": []},
            "马鞍山市": {"key": "maanshan", "skills": []},
            "芜湖市": {"key": "wuhu", "skills": []},
            "宣城市": {"key": "xuancheng", "skills": []},
            "铜陵市": {"key": "tongling", "skills": []},
            "池州市": {"key": "chizhou", "skills": []},
            "安庆市": {"key": "anqing", "skills": []},
            "黄山市": {"key": "huangshan", "skills": []}
        }
    },
    "上海市": {
        "key": "shanghai",
        "cities": {
            "上海市": {"key": "shanghai", "skills": []}
        }
    }
}


def get_provinces():
    return list(REGIONS.keys())


def get_provinces_with_keys():
    result = []
    for name in REGIONS.keys():
        result.append((REGIONS[name]["key"], name))
    return result


def get_cities(province_name):
    province = REGIONS.get(province_name)
    if not province:
        return []
    return list(province["cities"].keys())


def get_cities_with_keys(province_name):
    result = []
    province = REGIONS.get(province_name)
    if not province:
        return result
    for city_name in province["cities"].keys():
        result.append((province["cities"][city_name]["key"], city_name))
    return result


def get_province_key(province_name):
    return REGIONS.get(province_name, {}).get("key", province_name)


def get_city_key(province_name, city_name):
    return REGIONS.get(province_name, {}).get("cities", {}).get(city_name, {}).get("key", city_name)


def get_region_skills(province_name, city_name):
    province = REGIONS.get(province_name)
    if not province:
        return []
    city = province["cities"].get(city_name)
    if not city:
        return []
    return city.get("skills", [])


def get_region_name(province_name, city_name):
    if province_name and city_name:
        return f"{province_name}-{city_name}"
    return city_name or province_name or "未选择"