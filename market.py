"""Market demand, factor prices, and sales allocation."""

import math
import random

from localization import tr


class Market:
    # Generates demand and distributes sales according to price, quality, reputation, and availability.
    def __init__(self, scenario="19th Century"):
        self.scenario = scenario
        self.base_demand = self.get_base_demand_by_scenario()
        self.current_demand = self.base_demand
        self.turn = 0
        self.demand_trend = 1.0
        self.event_name = "Stable Market"
        self.event_multiplier = 1.0
        self.iron_ore_price_index = 1.0
        self.coal_price_index = 1.0
        self.labor_price_index = 1.0

    def get_base_demand_by_scenario(self):
        if self.scenario == "19th Century":
            return 720
        elif self.scenario == "Custom":
            return 620
        else:
            return 600

    def forecast_demand(self, active_company_count=1):
        competition_bonus = min(1.2, 0.92 + active_company_count * 0.04)
        return int(self.base_demand * self.demand_trend * self.event_multiplier * competition_bonus)

    def generate_event(self):
        event_roll = random.random()

        if event_roll < 0.08:
            self.event_name = "Supply Chain Shock"
            self.event_multiplier = 0.82
        elif event_roll < 0.16:
            self.event_name = "Consumer Hype"
            self.event_multiplier = 1.18
        elif event_roll < 0.22:
            self.event_name = "New Regulation"
            self.event_multiplier = 0.9
        else:
            self.event_name = "Stable Market"
            self.event_multiplier = 1.0

    def generate_factor_prices(self):
        self.iron_ore_price_index *= random.uniform(0.96, 1.06)
        self.coal_price_index *= random.uniform(0.95, 1.07)
        self.labor_price_index *= random.uniform(0.985, 1.025)

        if self.event_name == "Supply Chain Shock":
            self.iron_ore_price_index *= 1.08
            self.coal_price_index *= 1.1
        elif self.event_name == "New Regulation":
            self.labor_price_index *= 1.04

        self.iron_ore_price_index = max(0.65, min(1.75, self.iron_ore_price_index))
        self.coal_price_index = max(0.65, min(1.85, self.coal_price_index))
        self.labor_price_index = max(0.75, min(1.55, self.labor_price_index))

    def get_material_price_index(self):
        return self.iron_ore_price_index * 0.58 + self.coal_price_index * 0.42

    def get_material_unit_cost(self):
        return 30 * self.get_material_price_index()

    def generate_demand(self, companies=None):
        self.turn += 1
        self.generate_event()
        self.generate_factor_prices()

        if self.scenario == "19th Century":
            fluctuation = random.uniform(0.82, 1.28)
            self.demand_trend *= random.uniform(1.0, 1.02)
        elif self.scenario == "Custom":
            fluctuation = random.uniform(0.72, 1.3)
            self.demand_trend *= random.uniform(0.99, 1.02)
        else:
            fluctuation = random.uniform(0.75, 1.25)
            self.demand_trend *= random.uniform(0.995, 1.018)

        self.demand_trend = max(0.65, min(1.65, self.demand_trend))

        price_pressure = 1.0
        reputation_lift = 1.0
        quality_lift = 1.0

        if companies:
            active_companies = [company for company in companies if not company.bankrupt]

            if active_companies:
                average_price = sum(company.price for company in active_companies) / len(active_companies)
                average_reputation = sum(company.reputation for company in active_companies) / len(active_companies)
                average_quality = sum(company.get_effective_product_quality() for company in active_companies) / len(active_companies)
                price_pressure = max(0.7, min(1.25, 42 / max(average_price, 1)))
                reputation_lift = max(0.85, min(1.18, average_reputation / 55))
                quality_lift = max(0.88, min(1.16, average_quality / 55))

        seasonal_multiplier = 1 + 0.1 * math.sin((self.turn - 1) / 4 * math.pi)
        self.current_demand = int(
            self.base_demand
            * self.demand_trend
            * fluctuation
            * seasonal_multiplier
            * self.event_multiplier
            * price_pressure
            * reputation_lift
            * quality_lift
        )
        return self.current_demand
    
    def estimate_company_score(
        self,
        price,
        reputation,
        inventory,
        market_share,
        product_quality,
        marketing_spend,
        average_price,
        average_quality
    ):
        if inventory <= 0:
            return 0

        price_ratio = average_price / max(price, 1)
        price_score = max(0.08, min(5.0, price_ratio ** 2.35))
        reputation_score = (reputation / 50) ** 1.1
        quality_score = (product_quality / max(average_quality, 1)) ** 1.25
        availability_score = min(inventory / max(self.current_demand * 0.25, 1), 2)
        momentum_score = 1 + min(market_share, 45) / 140
        marketing_score = 1 + min(marketing_spend / 1200, 1.5) * 0.12

        non_price_score = (
            reputation_score * 0.34
            + quality_score * 0.27
            + availability_score * 0.2
            + momentum_score * 0.19
        )
        score = price_score * non_price_score * marketing_score

        return max(score, 0)

    def calculate_company_score(self, company, average_price, average_quality):
        if company.bankrupt:
            return 0

        if company.inventory <= 0:
            return 0

        return self.estimate_company_score(
            price=company.price,
            reputation=company.reputation,
            inventory=company.inventory,
            market_share=company.market_share,
            product_quality=company.get_effective_product_quality(),
            marketing_spend=company.last_marketing_spend,
            average_price=average_price,
            average_quality=average_quality
        ) * company.bonus_multiplier

    def distribute_sales(self, companies):
        active_companies = [
            company for company in companies
            if not company.bankrupt and company.inventory > 0
        ]

        sales_distribution = {
            company.name: 0
            for company in companies
        }

        if not active_companies:
            return sales_distribution

        average_price = sum(company.price for company in active_companies) / len(active_companies)
        average_quality = sum(company.get_effective_product_quality() for company in active_companies) / len(active_companies)
        scores = {
            company.name: self.calculate_company_score(company, average_price, average_quality)
            for company in active_companies
        }

        total_score = sum(scores.values())

        if total_score <= 0:
            equal_share = self.current_demand // len(active_companies)

            for company in active_companies:
                sales_distribution[company.name] = equal_share

            return sales_distribution

        for company in active_companies:
            raw_demand = self.current_demand * (scores[company.name] / total_score)
            sales_distribution[company.name] = min(company.inventory, int(raw_demand))

        unmet_demand = self.current_demand - sum(sales_distribution.values())

        if unmet_demand > 0:
            companies_with_stock = [
                company for company in active_companies
                if company.inventory > sales_distribution[company.name]
            ]

            while unmet_demand > 0 and companies_with_stock:
                extra_per_company = max(1, unmet_demand // len(companies_with_stock))
                next_round = []

                for company in companies_with_stock:
                    if unmet_demand <= 0:
                        break
                    available = company.inventory - sales_distribution[company.name]
                    extra_sales = min(available, extra_per_company)
                    sales_distribution[company.name] += extra_sales
                    unmet_demand -= extra_sales

                    if company.inventory > sales_distribution[company.name]:
                        next_round.append(company)

                if len(next_round) == len(companies_with_stock) and extra_per_company == 0:
                    break

                companies_with_stock = next_round

        return sales_distribution

    def get_event_text(self, language="en"):
        event_keys = {
            "Stable Market": "stable_market",
            "Supply Chain Shock": "supply_chain_shock",
            "Consumer Hype": "consumer_hype",
            "New Regulation": "new_regulation"
        }
        return tr(language, event_keys.get(self.event_name, "stable_market"))

    def get_market_summary(self, language="en"):
        return tr(
            language,
            "market_summary",
            trend=self.demand_trend,
            event=self.get_event_text(language),
            multiplier=self.event_multiplier,
            materials=self.get_material_price_index(),
            labor=self.labor_price_index
        )

    def to_dict(self):
        # Converts market state into JSON-friendly data.
        return {
            "scenario": self.scenario,
            "base_demand": self.base_demand,
            "current_demand": self.current_demand,
            "turn": self.turn,
            "demand_trend": self.demand_trend,
            "event_name": self.event_name,
            "event_multiplier": self.event_multiplier,
            "iron_ore_price_index": self.iron_ore_price_index,
            "coal_price_index": self.coal_price_index,
            "labor_price_index": self.labor_price_index
        }

    @classmethod
    def from_dict(cls, data):
        # Rebuilds market state from saved JSON data.
        market = cls(data.get("scenario", "19th Century"))
        market.base_demand = data.get("base_demand", market.base_demand)
        market.current_demand = data.get("current_demand", market.current_demand)
        market.turn = data.get("turn", 0)
        market.demand_trend = data.get("demand_trend", 1.0)
        market.event_name = data.get("event_name", "Stable Market")
        market.event_multiplier = data.get("event_multiplier", 1.0)
        market.iron_ore_price_index = data.get("iron_ore_price_index", 1.0)
        market.coal_price_index = data.get("coal_price_index", 1.0)
        market.labor_price_index = data.get("labor_price_index", 1.0)
        return market
