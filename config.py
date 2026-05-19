"""Static game configuration, technology data, AI archetypes, and contract templates."""

OPTION_TEXT = {
    "19th Century": {"en": "19th Century", "zh": "19 世纪剧本"},
    "Custom": {"en": "Custom", "zh": "自定义剧本"},
    "Easy": {"en": "Easy", "zh": "简单"},
    "Normal": {"en": "Normal", "zh": "普通"},
    "Hard": {"en": "Hard", "zh": "困难"},
    "Efficiency": {"en": "Efficiency", "zh": "效率研发"},
    "Quality": {"en": "Quality", "zh": "质量研发"},
    "Brand": {"en": "Brand", "zh": "品牌研发"},
    "Carnegie": {"en": "Andrew Carnegie", "zh": "安德鲁·卡内基"},
    "Krupp": {"en": "Alfred Krupp", "zh": "阿尔弗雷德·克虏伯"},
    "Schneider": {"en": "Schneider Brothers", "zh": "施耐德兄弟"},
    "Bessemer": {"en": "Henry Bessemer", "zh": "亨利·贝塞麦"},
    "Ural": {"en": "Ural Metallurgy", "zh": "乌拉尔冶金"},
    "Skoda": {"en": "Skoda Works", "zh": "斯柯达"},
    "Cost Leader": {"en": "Cost Leader", "zh": "成本领先"},
    "Premium": {"en": "Premium", "zh": "高端路线"},
    "Balanced": {"en": "Balanced", "zh": "均衡经营"},
    "Innovator": {"en": "Innovator", "zh": "技术创新"},
    "Survivor": {"en": "Survivor", "zh": "生存优先"},
    "Flexible": {"en": "Flexible", "zh": "灵活经营"}
    ,"Infinite": {"en": "Infinite", "zh": "无限"}
}

AI_ARCHETYPES = {
    "Carnegie": {
        "style": "Cost Leader",
        "research_focus": "Efficiency",
        "target_margin": 1.22,
        "inventory_cover": 1.05,
        "risk_tolerance": 0.72,
        "sell_pressure": 1.25
    },
    "Krupp": {
        "style": "Premium",
        "research_focus": "Quality",
        "target_margin": 1.55,
        "inventory_cover": 0.78,
        "risk_tolerance": 0.65,
        "sell_pressure": 1.45
    },
    "Schneider": {
        "style": "Balanced",
        "research_focus": "Brand",
        "target_margin": 1.36,
        "inventory_cover": 0.9,
        "risk_tolerance": 0.68,
        "sell_pressure": 1.35
    },
    "Bessemer": {
        "style": "Innovator",
        "research_focus": "Efficiency",
        "target_margin": 1.32,
        "inventory_cover": 0.92,
        "risk_tolerance": 0.7,
        "sell_pressure": 1.38
    },
    "Ural": {
        "style": "Survivor",
        "research_focus": "Efficiency",
        "target_margin": 1.18,
        "inventory_cover": 1.12,
        "risk_tolerance": 0.58,
        "sell_pressure": 1.15
    },
    "Skoda": {
        "style": "Flexible",
        "research_focus": "Quality",
        "target_margin": 1.4,
        "inventory_cover": 0.86,
        "risk_tolerance": 0.66,
        "sell_pressure": 1.32
    }
}

ARCHETYPE_ORDER = ["Carnegie", "Krupp", "Schneider", "Bessemer", "Ural", "Skoda"]

TECHNOLOGIES = {
    "Puddling Furnace": {
        "name": {"en": "Puddling Furnace", "zh": "泡钢法"},
        "description": {"en": "The starting ironmaking method. Already available at game start.", "zh": "开局掌握的炼铁方法。"},
        "cost": 1800,
        "turns": 2,
        "prerequisites": [],
        "effects": {}
    },
    "Rolling Mill": {
        "name": {"en": "Rolling Mill", "zh": "轧钢机"},
        "description": {"en": "Mechanized rolling improves throughput.", "zh": "机械化轧制提高产能。"},
        "cost": 2600,
        "turns": 3,
        "prerequisites": [],
        "effects": {"capacity_bonus": 80}
    },
    "Railway Logistics": {
        "name": {"en": "Railway Logistics", "zh": "铁路物流"},
        "description": {"en": "Rail contracts reduce inventory pressure and expand storage reach.", "zh": "铁路运输降低库存压力并扩大仓储覆盖。"},
        "cost": 2200,
        "turns": 2,
        "prerequisites": [],
        "effects": {"storage_capacity": 250, "reputation": 1}
    },
    "Bessemer Process": {
        "name": {"en": "Bessemer Converter", "zh": "贝塞麦转炉"},
        "description": {"en": "Mass steelmaking lowers unit cost and raises output quality.", "zh": "大规模炼钢降低单位成本，并提升产品质量。"},
        "cost": 4200,
        "turns": 4,
        "prerequisites": ["Puddling Furnace"],
        "effects": {}
    },
    "Scientific Management": {
        "name": {"en": "Scientific Management", "zh": "科学管理"},
        "description": {"en": "Better shop-floor organization raises labor efficiency.", "zh": "更好的车间组织提升劳动效率。"},
        "cost": 3500,
        "turns": 3,
        "prerequisites": ["Rolling Mill"],
        "effects": {"workforce": 5, "reputation": 2}
    },
    "Open Hearth Furnace": {
        "name": {"en": "Open Hearth Furnace", "zh": "平炉"},
        "description": {"en": "Flexible steelmaking improves quality and industrial reliability.", "zh": "更灵活的炼钢技术提升质量和工业可靠性。"},
        "cost": 6500,
        "turns": 5,
        "prerequisites": ["Bessemer Process"],
        "effects": {}
    },
    "Electric Arc Furnace": {
        "name": {"en": "Electric Arc Furnace", "zh": "电弧炉"},
        "description": {"en": "A highly flexible modern furnace method for advanced steel output.", "zh": "高度灵活的现代炼钢方法，适合先进钢材生产。"},
        "cost": 9000,
        "turns": 6,
        "prerequisites": ["Open Hearth Furnace"],
        "effects": {}
    },
    "Alloy Steel": {
        "name": {"en": "Alloy Steel", "zh": "合金钢"},
        "description": {"en": "Specialty steel opens higher-value markets.", "zh": "特种钢打开更高价值的市场。"},
        "cost": 7200,
        "turns": 5,
        "prerequisites": ["Open Hearth Furnace"],
        "effects": {"product_quality": 12, "reputation": 3}
    }
}

PRODUCTION_METHODS = {
    "Puddling Furnace": {
        "rank": 1,
        "capacity": 100,
        "min_workers": 6,
        "optimal_workers": 10,
        "max_workers": 14,
        "maintenance": 280,
        "idle_maintenance": 90,
        "unit_cost_modifier": 0,
        "quality_bonus": 0,
        "upgrade_cost": 0
    },
    "Bessemer Process": {
        "rank": 2,
        "capacity": 140,
        "min_workers": 7,
        "optimal_workers": 11,
        "max_workers": 15,
        "maintenance": 390,
        "idle_maintenance": 130,
        "unit_cost_modifier": -4,
        "quality_bonus": 4,
        "upgrade_cost": 4200
    },
    "Open Hearth Furnace": {
        "rank": 3,
        "capacity": 170,
        "min_workers": 8,
        "optimal_workers": 12,
        "max_workers": 16,
        "maintenance": 520,
        "idle_maintenance": 170,
        "unit_cost_modifier": -3,
        "quality_bonus": 8,
        "upgrade_cost": 6500
    },
    "Electric Arc Furnace": {
        "rank": 4,
        "capacity": 210,
        "min_workers": 6,
        "optimal_workers": 9,
        "max_workers": 12,
        "maintenance": 700,
        "idle_maintenance": 230,
        "unit_cost_modifier": -5,
        "quality_bonus": 12,
        "upgrade_cost": 9000
    }
}

STARTING_TECHNOLOGIES = {"Puddling Furnace"}

CONTRACT_TEMPLATES = {
    "Railway": {
        "name": {"en": "Railway Steel Order", "zh": "铁路钢材订单"},
        "description": {"en": "A railway company needs steady rail and structural steel deliveries.", "zh": "铁路公司需要稳定供应钢轨和结构钢。"},
        "units_range": (70, 115),
        "price_range": (58, 72),
        "duration_range": (4, 7),
        "quality_requirement": 48,
        "reputation_requirement": 42,
        "penalty_rate": 0.45
    },
    "Military": {
        "name": {"en": "Military Steel Order", "zh": "军工钢材订单"},
        "description": {"en": "A government arsenal wants high-quality steel under a strict delivery schedule.", "zh": "政府军工部门需要高质量钢材，并要求严格交付。"},
        "units_range": (45, 85),
        "price_range": (78, 98),
        "duration_range": (3, 6),
        "quality_requirement": 58,
        "reputation_requirement": 48,
        "penalty_rate": 0.65
    },
    "Construction": {
        "name": {"en": "Construction Steel Order", "zh": "建筑钢材订单"},
        "description": {"en": "Urban builders need bulk structural steel with forgiving quality requirements.", "zh": "城市建筑商需要大量结构钢，对质量要求较宽松。"},
        "units_range": (95, 150),
        "price_range": (50, 64),
        "duration_range": (3, 5),
        "quality_requirement": 42,
        "reputation_requirement": 36,
        "penalty_rate": 0.35
    }
}
