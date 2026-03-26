# VideoSnap 套餐配置
# 价格单位：人民币（CNY）

PLANS = {
    "free": {
        "name": "免费版",
        "price_monthly": 0,
        "price_yearly": 0,
        "daily_downloads": 3,       # 每天最多下载次数
        "max_quality": 480,          # 最高画质 480p
        "features": [
            "每天 3 次下载",
            "最高 480p 画质",
            "支持主流平台",
        ],
        "limits": [
            "不支持 1080p/4K",
            "每天限 3 次",
            "无优先队列",
        ],
    },
    "pro": {
        "name": "专业版",
        "price_monthly": 18,         # ¥18/月
        "price_yearly": 128,         # ¥128/年（约 ¥10.7/月，省 40%）
        "daily_downloads": 100,      # 每天最多 100 次
        "max_quality": 1080,         # 最高 1080p
        "stripe_price_monthly": "",  # 填入 Stripe Price ID
        "stripe_price_yearly": "",
        "features": [
            "每天 100 次下载",
            "最高 1080p 画质",
            "支持 1800+ 平台",
            "优先下载队列",
            "无广告",
        ],
    },
    "annual": {
        "name": "年度旗舰版",
        "price_monthly": None,
        "price_yearly": 198,         # ¥198/年（约 ¥16.5/月）
        "daily_downloads": -1,       # 无限制
        "max_quality": 9999,         # 支持 4K
        "stripe_price_yearly": "",   # 填入 Stripe Price ID
        "features": [
            "无限次下载",
            "最高 4K 画质",
            "支持 1800+ 平台",
            "最高优先级队列",
            "无广告",
            "批量下载（即将上线）",
            "API 访问（即将上线）",
        ],
    },
}
