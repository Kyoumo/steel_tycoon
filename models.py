"""Company and AI player models."""

import random

from config import AI_ARCHETYPES, PRODUCTION_METHODS, STARTING_TECHNOLOGIES, TECHNOLOGIES
from localization import display_option, tr


class Company:
    # Represents one firm's assets, finances, production, and R&D state.
    def __init__(
        self,
        name,
        cash=10000,
        production_lines=2,
        technology=1,
        workforce=20,
        storage_capacity=500,
        reputation=50,
        bonus_multiplier=1.0,
        is_player=False
    ):
        '''
        Initcializing a company
        '''
        self.name = name
        self.cash = cash
        self.inventory = 0
        self.production_lines = production_lines
        self.technology = technology
        self.workforce = workforce
        self.factory_buildings = [
            {
                "name": "Main Works",
                "slots": max(4, production_lines),
                "owned": True,
                "expansions": 0,
                "rent": 0
            }
        ]
        self.production_line_details = self.create_initial_production_lines(production_lines, workforce)
        self.storage_capacity = storage_capacity
        self.reputation = reputation
        self.product_quality = 50
        self.research_points = 0
        self.research_focus = "Efficiency"
        self.known_technologies = set(STARTING_TECHNOLOGIES)
        self.active_research = []
        self.capacity_bonus = 0
        self.price = 40
        self.market_share = 0.0
        self.debt = 0
        self.base_interest_rate = 0.035
        self.interest_rate = self.base_interest_rate
        self.credit_limit = cash * 0.75
        self.insolvency_turns = 0
        self.bonus_multiplier = bonus_multiplier
        self.bankrupt = False
        self.is_player = is_player

        self.last_production = 0
        self.last_sales = 0
        self.last_revenue = 0
        self.last_cost = 0
        self.last_production_cost = 0
        self.last_fixed_cost = 0
        self.last_storage_cost = 0
        self.last_interest_cost = 0
        self.last_wage_cost = 0
        self.last_maintenance_cost = 0
        self.last_rent_cost = 0
        self.last_overhead_cost = 0
        self.last_contract_revenue = 0
        self.last_contract_penalty = 0
        self.last_contract_units = 0
        self.last_unit_cost = 0
        self.last_profit = 0
        self.last_market_demand = 0
        self.last_marketing_spend = 0
        self.strategy = "Balanced"

        self.cash_history = [cash]
        self.debt_history = [self.debt]
        self.credit_limit_history = [self.credit_limit]
        self.profit_history = []

    def create_initial_production_lines(self, production_lines, workforce):
        lines = []
        assigned_workers = workforce // max(production_lines, 1)
        remainder = workforce % max(production_lines, 1)

        for index in range(production_lines):
            lines.append(
                {
                    "method": "Puddling Furnace",
                    "factory_index": 0,
                    "active": True,
                    "workers": assigned_workers + (1 if index < remainder else 0)
                }
            )

        return lines

    def sync_production_line_count(self):
        self.production_lines = len(self.production_line_details)

    def get_factory_slots(self):
        return sum(factory["slots"] for factory in self.factory_buildings)

    def get_used_factory_slots(self):
        return len(self.production_line_details)

    def get_factory_used_slots(self, factory_index):
        return len(self.get_factory_line_indices(factory_index))

    def get_factory_free_slots(self, factory_index):
        factory = self.factory_buildings[factory_index]
        return factory["slots"] - self.get_factory_used_slots(factory_index)

    def get_unassigned_workers(self):
        assigned_workers = sum(line["workers"] for line in self.production_line_details)
        return self.workforce - assigned_workers

    def get_line_worker_targets(self, line):
        method = PRODUCTION_METHODS[line["method"]]
        return method["min_workers"], method["optimal_workers"], method["max_workers"]

    def get_line_base_capacity(self, line):
        return PRODUCTION_METHODS[line["method"]]["capacity"]

    def get_line_capacity(self, line):
        if not line["active"]:
            return 0

        min_workers, optimal_workers, max_workers = self.get_line_worker_targets(line)
        effective_workers = min(line["workers"], max_workers)

        if effective_workers < min_workers:
            return 0

        labor_efficiency = min(1.0, effective_workers / optimal_workers)
        return self.get_line_base_capacity(line) * labor_efficiency

    def get_production_capacity(self):
        base_capacity = sum(self.get_line_capacity(line) for line in self.production_line_details)
        management_multiplier = 1.08 if "Scientific Management" in self.known_technologies else 1.0
        return int((base_capacity + self.capacity_bonus) * management_multiplier * self.bonus_multiplier)

    def get_fixed_cost(self, market=None):
        return sum(self.get_fixed_cost_breakdown(market).values())

    def get_fixed_cost_breakdown(self, market=None):
        line_cost = 0

        for line in self.production_line_details:
            if line["active"]:
                line_cost += PRODUCTION_METHODS[line["method"]]["maintenance"]
            else:
                line_cost += PRODUCTION_METHODS[line["method"]]["idle_maintenance"]

        factory_rent = sum(factory.get("rent", 0) for factory in self.factory_buildings)
        labor_multiplier = market.labor_price_index if market else 1.0
        workforce_cost = self.workforce * 50 * labor_multiplier
        tech_cost = len(self.known_technologies) * 80
        quality_cost = max(0, self.product_quality - 50) * 12
        return {
            "maintenance": line_cost,
            "rent": factory_rent,
            "wages": workforce_cost,
            "overhead": tech_cost + quality_cost
        }

    def get_storage_cost(self):
        maintenance_cost = self.storage_capacity * 0.15
        overflow = max(0, self.inventory - self.storage_capacity)
        overflow_cost = overflow * 2.5
        return maintenance_cost + overflow_cost

    def get_unit_production_cost(self, market=None):
        base_cost = 30 if market is None else market.get_material_unit_cost()
        method_modifier = self.get_average_method_unit_cost_modifier()
        logistics_discount = 1.5 if "Railway Logistics" in self.known_technologies else 0
        quality_premium = max(0, self.product_quality - 50) * 0.12
        return max(14, base_cost + method_modifier - logistics_discount + quality_premium)

    def get_average_method_unit_cost_modifier(self):
        active_lines = [
            line for line in self.production_line_details
            if line["active"] and self.get_line_capacity(line) > 0
        ]

        if not active_lines:
            return 0

        weighted_modifier = 0
        total_capacity = 0

        for line in active_lines:
            capacity = self.get_line_capacity(line)
            weighted_modifier += PRODUCTION_METHODS[line["method"]]["unit_cost_modifier"] * capacity
            total_capacity += capacity

        return weighted_modifier / max(total_capacity, 1)

    def get_average_method_quality_bonus(self):
        active_lines = [
            line for line in self.production_line_details
            if line["active"] and self.get_line_capacity(line) > 0
        ]

        if not active_lines:
            return 0

        weighted_bonus = 0
        total_capacity = 0

        for line in active_lines:
            capacity = self.get_line_capacity(line)
            weighted_bonus += PRODUCTION_METHODS[line["method"]]["quality_bonus"] * capacity
            total_capacity += capacity

        return weighted_bonus / max(total_capacity, 1)

    def get_effective_product_quality(self):
        return min(100, self.product_quality + self.get_average_method_quality_bonus())

    def get_asset_value(self):
        return (
            self.production_lines * 4500
            + sum(factory["slots"] * 1800 for factory in self.factory_buildings if factory.get("owned", True))
            + len(self.known_technologies) * 1800
            + self.workforce * 450
            + self.storage_capacity * 5
            + self.get_effective_product_quality() * 80
            + self.inventory * max(self.get_unit_production_cost() * 0.6, 1)
        )

    def update_credit_limit(self):
        revenue_power = self.last_revenue * 1.6
        cash_buffer = max(self.cash, 0) * 0.25
        reputation_factor = 0.7 + self.reputation / 250
        market_factor = 0.75 + min(self.market_share, 55) / 220
        self.credit_limit = max(
            1800,
            (self.get_asset_value() * 0.22 + revenue_power + cash_buffer)
            * reputation_factor
            * market_factor
        )
        self.update_interest_rate()
        return self.credit_limit

    def update_interest_rate(self):
        stress = min(self.get_solvency_ratio(), 1.4)
        reputation_discount = max(0, (self.reputation - 50) * 0.00025)
        self.interest_rate = max(
            0.02,
            min(0.13, self.base_interest_rate + stress * 0.055 - reputation_discount)
        )
        return self.interest_rate

    def get_credit_available(self):
        return max(0, self.credit_limit - self.debt)

    def get_solvency_ratio(self):
        if self.credit_limit <= 0:
            return 1
        return self.debt / self.credit_limit

    def spend_money(self, amount):
        if amount < 0:
            raise ValueError("Spending amount cannot be negative.")

        self.update_credit_limit()

        if self.cash >= amount:
            self.cash -= amount
            self.record_finance_history()
            return

        shortage = amount - self.cash

        if self.debt + shortage > self.credit_limit:
            raise ValueError(
                f"Not enough financing. Need ${shortage:.2f} credit, "
                f"but only ${self.get_credit_available():.2f} is available."
            )

        self.cash = 0
        self.debt += shortage
        self.record_finance_history()

    def record_finance_history(self, profit=None):
        self.cash_history.append(self.cash)
        self.debt_history.append(self.debt)
        self.credit_limit_history.append(self.credit_limit)
        if profit is not None:
            self.profit_history.append(profit)

    def get_finance_position(self):
        return self.cash - self.debt

    def get_finance_position_history(self):
        length = max(len(self.cash_history), len(self.debt_history))
        positions = []

        for index in range(length):
            cash = self.cash_history[index] if index < len(self.cash_history) else self.cash
            debt = self.debt_history[index] if index < len(self.debt_history) else self.debt
            positions.append(cash - debt)

        return positions

    def settle_cash_position(self):
        self.update_credit_limit()

        if self.cash < 0:
            shortage = abs(self.cash)
            self.cash = 0
            self.debt += shortage

        if self.cash > 0 and self.debt > 0:
            repayment = min(self.cash, self.debt)
            self.cash -= repayment
            self.debt -= repayment

        self.update_credit_limit()

    def produce(self, quantity, market=None):
        capacity = self.get_production_capacity()

        if quantity < 0:
            raise ValueError("Production quantity cannot be negative.")

        if quantity > capacity:
            raise ValueError(f"Production exceeds capacity. Maximum capacity is {capacity}.")

        unit_cost = self.get_unit_production_cost(market)
        production_cost = quantity * unit_cost

        self.inventory += quantity
        self.last_production = quantity
        self.last_unit_cost = unit_cost

        return production_cost

    def sell(self, demand):
        actual_sales = min(self.inventory, demand)
        revenue = actual_sales * self.price

        self.inventory -= actual_sales
        self.last_sales = actual_sales
        self.last_revenue = revenue

        return revenue

    def pay_costs_and_update_cash(self, revenue, production_cost, fixed_cost, storage_cost, fixed_breakdown=None):
        interest_cost = self.debt * self.update_interest_rate() / 4
        total_cost = production_cost + fixed_cost + storage_cost + interest_cost
        profit = revenue - total_cost

        self.cash += profit
        self.settle_cash_position()

        fixed_breakdown = fixed_breakdown or {}
        self.last_production_cost = production_cost
        self.last_fixed_cost = fixed_cost
        self.last_storage_cost = storage_cost
        self.last_interest_cost = interest_cost
        self.last_wage_cost = fixed_breakdown.get("wages", 0)
        self.last_maintenance_cost = fixed_breakdown.get("maintenance", 0)
        self.last_rent_cost = fixed_breakdown.get("rent", 0)
        self.last_overhead_cost = fixed_breakdown.get("overhead", 0)
        self.last_cost = total_cost
        self.last_profit = profit
        self.record_finance_history(profit)

        return profit

    def update_reputation(self):
        if self.last_sales > 0:
            self.reputation += 1
        else:
            self.reputation -= 2

        if self.price > 80:
            self.reputation -= 1

        if self.last_sales >= self.last_production and self.last_production > 0:
            self.reputation += 1

        self.reputation = max(10, min(100, self.reputation))

    def check_bankruptcy(self):
        self.update_credit_limit()

        if self.debt > self.credit_limit:
            self.insolvency_turns += 1
        else:
            self.insolvency_turns = 0

        if self.insolvency_turns >= 2:
            self.bankrupt = True

    def get_acquisition_value(self):
        asset_value = (
            self.production_lines * 2600
            + len(self.known_technologies) * 1600
            + self.workforce * 250
            + self.storage_capacity * 2
            + max(self.cash, 0) * 0.35
            + self.product_quality * 70
            - self.debt * 0.55
        )
        reputation_value = self.reputation * 35
        distress_discount = 0.65 if self.cash < 2500 or self.market_share < 8 else 1.0
        return max(1000, int((asset_value + reputation_value) * distress_discount))

    def evaluate_acquisition_offer(self, offer):
        fair_value = self.get_acquisition_value()
        solvency_pressure = self.get_solvency_ratio()
        survival_confidence = (
            self.cash > 2500
            and self.last_profit >= -500
            and solvency_pressure < 0.82
            and self.market_share >= 10
        )

        if survival_confidence:
            asking_price = fair_value * 1.75
        else:
            asking_price = fair_value * (1.05 + max(0, 0.8 - solvency_pressure) * 0.45)

        return offer >= asking_price, asking_price

    def can_afford(self, cost):
        self.update_credit_limit()
        return self.cash + self.get_credit_available() >= cost

    def buy_production_line(self, factory_index=None):
        cost = 5200 + self.production_lines * 1400
        factory_index = self.get_default_factory_index() if factory_index is None else factory_index

        if self.get_factory_free_slots(factory_index) <= 0:
            raise ValueError("No free slots in this factory. Build, lease, or expand a factory first.")

        if not self.can_afford(cost):
            raise ValueError(f"Not enough cash. New production line costs ${cost:.2f}.")

        self.spend_money(cost)
        self.production_line_details.append(
            {
                "method": "Puddling Furnace",
                "factory_index": factory_index,
                "active": False,
                "workers": 0
            }
        )
        self.sync_production_line_count()
        return cost

    def get_default_factory_index(self):
        for index, factory in enumerate(self.factory_buildings):
            if self.get_factory_free_slots(index) > 0:
                return index

        raise ValueError("No free factory slots. Build, lease, or expand a factory first.")

    def upgrade_production_line(self, line_index):
        line = self.production_line_details[line_index]
        target_method = self.get_best_available_production_method()

        if target_method == line["method"]:
            raise ValueError("This production line already uses the best available method.")

        cost = self.get_line_upgrade_cost(line["method"], target_method)

        if not self.can_afford(cost):
            raise ValueError(f"Not enough cash. Production line upgrade costs ${cost:.2f}.")

        self.spend_money(cost)
        line["method"] = target_method
        return cost, target_method

    def get_best_available_production_method(self):
        available_methods = [
            method for method in PRODUCTION_METHODS
            if method in self.known_technologies
        ]
        return max(available_methods, key=lambda method: PRODUCTION_METHODS[method]["rank"])

    def get_line_upgrade_cost(self, current_method, target_method):
        current_rank = PRODUCTION_METHODS[current_method]["rank"]
        target = PRODUCTION_METHODS[target_method]

        if target["rank"] <= current_rank:
            return 0

        return int(target["upgrade_cost"] * (0.85 if current_rank > 1 else 1.0))

    def get_factory_line_indices(self, factory_index):
        return [
            index for index, line in enumerate(self.production_line_details)
            if line.get("factory_index", 0) == factory_index
        ]

    def get_factory_expansion_limit(self, factory_index):
        factory = self.factory_buildings[factory_index]

        if not factory.get("owned", True):
            return 0

        limit = 1
        if "Rolling Mill" in self.known_technologies:
            limit += 1
        if "Scientific Management" in self.known_technologies:
            limit += 1
        if "Railway Logistics" in self.known_technologies:
            limit += 1

        return limit

    def get_factory_expand_cost(self, factory_index=0, added_slots=2):
        factory = self.factory_buildings[factory_index]
        expansion_count = factory.get("expansions", 0)
        return int(3200 + factory["slots"] * 700 + expansion_count * 1800 + added_slots * 450)

    def expand_factory(self, factory_index=0, added_slots=2):
        factory = self.factory_buildings[factory_index]

        if not factory.get("owned", True):
            raise ValueError("Leased factories cannot expand.")

        if factory.get("expansions", 0) >= self.get_factory_expansion_limit(factory_index):
            raise ValueError("This factory has reached its expansion limit.")

        cost = self.get_factory_expand_cost(factory_index, added_slots)

        if not self.can_afford(cost):
            raise ValueError(f"Not enough cash. Factory expansion costs ${cost:.2f}.")

        self.spend_money(cost)
        factory["slots"] += added_slots
        factory["expansions"] = factory.get("expansions", 0) + 1
        return cost

    def get_build_factory_cost(self):
        owned_count = len([factory for factory in self.factory_buildings if factory.get("owned", True)])
        return 11500 + owned_count * 3800

    def build_factory(self):
        cost = self.get_build_factory_cost()

        if not self.can_afford(cost):
            raise ValueError(f"Not enough cash. New factory costs ${cost:.2f}.")

        self.spend_money(cost)
        factory = {
            "name": f"Works {len(self.factory_buildings) + 1}",
            "slots": 3,
            "owned": True,
            "expansions": 0,
            "rent": 0
        }
        self.factory_buildings.append(factory)
        return cost, factory["name"]

    def get_lease_factory_cost(self):
        leased_count = len([factory for factory in self.factory_buildings if not factory.get("owned", True)])
        return 2200 + leased_count * 900

    def get_next_lease_rent(self):
        leased_count = len([factory for factory in self.factory_buildings if not factory.get("owned", True)])
        return 650 + leased_count * 250

    def lease_factory(self):
        cost = self.get_lease_factory_cost()

        if not self.can_afford(cost):
            raise ValueError(f"Not enough cash. Factory lease costs ${cost:.2f}.")

        self.spend_money(cost)
        factory = {
            "name": f"Leased Works {len(self.factory_buildings) + 1}",
            "slots": 2,
            "owned": False,
            "expansions": 0,
            "rent": self.get_next_lease_rent()
        }
        self.factory_buildings.append(factory)
        return cost, factory["name"]

    def adjust_workers_on_line(self, line_index, delta):
        line = self.production_line_details[line_index]
        new_workers = line["workers"] + delta

        if new_workers < 0:
            raise ValueError("Worker assignment cannot be negative.")

        if delta > self.get_unassigned_workers():
            raise ValueError("Not enough unassigned workers available.")

        line["workers"] = new_workers
        return delta

    def adjust_workers_in_factory(self, factory_index, delta):
        line_indices = self.get_factory_line_indices(factory_index)

        if not line_indices:
            raise ValueError("This factory has no production lines.")

        if delta > 0:
            needed_workers = delta * len(line_indices)
            if needed_workers > self.get_unassigned_workers():
                raise ValueError("Not enough unassigned workers available.")
        else:
            for line_index in line_indices:
                if self.production_line_details[line_index]["workers"] + delta < 0:
                    raise ValueError("One or more production lines do not have enough assigned workers.")

        for line_index in line_indices:
            self.production_line_details[line_index]["workers"] += delta

        return delta

    def get_factory_upgrade_plan(self, factory_index):
        target_method = self.get_best_available_production_method()
        line_indices = self.get_factory_line_indices(factory_index)
        upgradeable_lines = [
            line_index for line_index in line_indices
            if self.production_line_details[line_index]["method"] != target_method
        ]
        total_cost = sum(
            self.get_line_upgrade_cost(
                self.production_line_details[line_index]["method"],
                target_method
            )
            for line_index in upgradeable_lines
        )
        return total_cost, len(upgradeable_lines), target_method

    def upgrade_factory_lines(self, factory_index):
        total_cost, upgraded_count, target_method = self.get_factory_upgrade_plan(factory_index)

        if upgraded_count <= 0:
            raise ValueError("All production lines already use the best available method.")

        if not self.can_afford(total_cost):
            raise ValueError(f"Not enough cash. Factory line upgrades cost ${total_cost:.2f}.")

        self.spend_money(total_cost)

        for line_index in self.get_factory_line_indices(factory_index):
            if self.production_line_details[line_index]["method"] != target_method:
                self.production_line_details[line_index]["method"] = target_method

        return total_cost, upgraded_count, target_method

    def set_production_line_active(self, line_index, active):
        self.production_line_details[line_index]["active"] = active

    def assign_workers_to_line(self, line_index, workers):
        if workers < 0:
            raise ValueError("Worker assignment cannot be negative.")

        other_workers = sum(
            line["workers"]
            for index, line in enumerate(self.production_line_details)
            if index != line_index
        )

        if other_workers + workers > self.workforce:
            raise ValueError("Not enough workers available.")

        self.production_line_details[line_index]["workers"] = workers

    def fire_workers(self, count=5):
        if count <= 0:
            raise ValueError("Worker count must be positive.")

        assigned_workers = sum(line["workers"] for line in self.production_line_details)

        if self.workforce - count < assigned_workers:
            raise ValueError("Cannot fire workers already assigned to production lines.")

        self.workforce -= count
        return count

    def hire_workers(self, count=5):
        cost = count * 700

        if not self.can_afford(cost):
            raise ValueError(f"Not enough cash. Hiring {count} workers costs ${cost:.2f}.")

        self.spend_money(cost)
        self.workforce += count
        return cost

    def expand_storage(self, amount=250):
        cost = amount * 8

        if not self.can_afford(cost):
            raise ValueError(f"Not enough cash. Storage expansion costs ${cost:.2f}.")

        self.spend_money(cost)
        self.storage_capacity += amount
        return cost

    def run_marketing_campaign(self, spend=1200):
        if not self.can_afford(spend):
            raise ValueError(f"Not enough cash. Marketing campaign costs ${spend:.2f}.")

        self.spend_money(spend)
        self.reputation = min(100, self.reputation + 4)
        self.last_marketing_spend = spend
        return spend

    def is_researching(self, technology_id):
        return any(project["technology_id"] == technology_id for project in self.active_research)

    def can_research_technology(self, technology_id):
        technology = TECHNOLOGIES[technology_id]

        if technology_id in self.known_technologies:
            return False

        if self.is_researching(technology_id):
            return False

        return all(prerequisite in self.known_technologies for prerequisite in technology["prerequisites"])

    def start_technology_research(self, technology_id):
        if technology_id not in TECHNOLOGIES:
            raise ValueError("Unknown technology.")

        if not self.can_research_technology(technology_id):
            raise ValueError("Technology prerequisites are not met or research is already active.")

        technology = TECHNOLOGIES[technology_id]
        self.spend_money(technology["cost"])
        self.active_research.append(
            {
                "technology_id": technology_id,
                "remaining_turns": technology["turns"]
            }
        )
        return technology["cost"]

    def apply_technology_effects(self, technology_id):
        effects = TECHNOLOGIES[technology_id]["effects"]
        self.technology += effects.get("technology", 0)
        self.product_quality = min(100, self.product_quality + effects.get("product_quality", 0))
        self.reputation = min(100, self.reputation + effects.get("reputation", 0))
        self.workforce += effects.get("workforce", 0)
        self.storage_capacity += effects.get("storage_capacity", 0)
        self.capacity_bonus += effects.get("capacity_bonus", 0)

    def complete_technology(self, technology_id):
        self.known_technologies.add(technology_id)
        self.apply_technology_effects(technology_id)
        self.research_points += 1

    def advance_research(self):
        completed = []

        for project in self.active_research:
            project["remaining_turns"] -= 1

        still_active = []

        for project in self.active_research:
            if project["remaining_turns"] <= 0:
                self.complete_technology(project["technology_id"])
                completed.append(project["technology_id"])
            else:
                still_active.append(project)

        self.active_research = still_active
        return completed

    def get_research_summary(self, language="en"):
        if not self.active_research:
            return tr(language, "no_active_research")

        parts = []

        for project in self.active_research:
            technology = TECHNOLOGIES[project["technology_id"]]
            parts.append(
                tr(
                    language,
                    "research_project_summary",
                    technology=technology["name"][language],
                    turns=project["remaining_turns"]
                )
            )

        return "; ".join(parts)

    def evaluate_technology_sale(self, technology_id, offer):
        if technology_id not in self.known_technologies:
            return False, 0

        technology = TECHNOLOGIES[technology_id]
        base_price = technology["cost"] * 2.4
        strategic_multiplier = 1.7 if self.get_solvency_ratio() < 0.75 and self.last_profit >= -800 else 0.95
        asking_price = base_price * strategic_multiplier
        return offer >= asking_price, asking_price

    def buy_known_technology(self, technology_id):
        if technology_id in self.known_technologies:
            return

        self.complete_technology(technology_id)

    def emergency_restructure(self):
        if self.debt <= 0:
            raise ValueError("No debt to restructure.")

        debt_reduction = self.debt * 0.3
        self.debt -= debt_reduction
        self.cash += 2500
        self.reputation = max(10, self.reputation - 12)
        self.product_quality = max(20, self.product_quality - 3)
        self.insolvency_turns = 0
        self.settle_cash_position()
        self.record_finance_history()
        return debt_reduction

    def get_status_sections(self, language="en"):
        # Groups company metrics for the structured company information panel.
        self.update_credit_limit()
        return [
            (
                tr(language, "status_section_identity"),
                [
                    (tr(language, "status_company"), self.name),
                    (tr(language, "status_strategy"), display_option(getattr(self, "strategy_style", self.strategy), language)),
                    (tr(language, "status_bonus"), f"{self.bonus_multiplier * 100:.0f}%"),
                    (tr(language, "status_market_share"), f"{self.market_share:.2f}%")
                ]
            ),
            (
                tr(language, "status_section_finance"),
                [
                    (tr(language, "status_cash"), f"${self.cash:.2f}"),
                    (tr(language, "status_debt"), f"${self.debt:.2f}"),
                    (tr(language, "status_credit_limit"), f"${self.credit_limit:.2f}"),
                    (tr(language, "status_interest_rate"), f"{self.interest_rate * 100:.2f}%"),
                    (tr(language, "status_solvency_ratio"), f"{self.get_solvency_ratio() * 100:.1f}%")
                ]
            ),
            (
                tr(language, "status_section_operations"),
                [
                    (tr(language, "status_price"), f"${self.price:.2f}"),
                    (tr(language, "status_inventory"), f"{self.inventory} {tr(language, 'units')}"),
                    (tr(language, "status_storage"), f"{self.storage_capacity} {tr(language, 'units')}"),
                    (tr(language, "status_reputation"), str(self.reputation))
                ]
            ),
            (
                tr(language, "status_section_production"),
                [
                    (tr(language, "status_capacity"), f"{self.get_production_capacity()} {tr(language, 'units_per_turn')}"),
                    (tr(language, "status_production_lines"), str(self.production_lines)),
                    (tr(language, "status_factories"), f"{len(self.factory_buildings)}"),
                    (tr(language, "factory_slots"), f"{self.get_used_factory_slots()}/{self.get_factory_slots()}"),
                    (tr(language, "status_workforce"), str(self.workforce)),
                    (tr(language, "unassigned_workers"), str(self.get_unassigned_workers()))
                ]
            ),
            (
                tr(language, "status_section_technology"),
                [
                    (tr(language, "status_technology"), TECHNOLOGIES[self.get_best_available_production_method()]["name"][language]),
                    (tr(language, "status_quality"), str(self.product_quality)),
                    (tr(language, "status_effective_quality"), f"{self.get_effective_product_quality():.1f}"),
                    (tr(language, "status_known_technologies"), str(len(self.known_technologies) - len(STARTING_TECHNOLOGIES))),
                    (tr(language, "status_active_research"), self.get_research_summary(language))
                ]
            ),
            (
                tr(language, "status_section_last_turn"),
                [
                    (tr(language, "status_last_production"), str(self.last_production)),
                    (tr(language, "status_last_sales"), str(self.last_sales)),
                    (tr(language, "status_last_demand"), str(self.last_market_demand)),
                    (tr(language, "status_last_revenue"), f"${self.last_revenue:.2f}"),
                    (tr(language, "status_last_cost"), f"${self.last_cost:.2f}"),
                    (tr(language, "status_last_production_cost"), f"${self.last_production_cost:.2f}"),
                    (tr(language, "status_last_wage_cost"), f"${self.last_wage_cost:.2f}"),
                    (tr(language, "status_last_maintenance_cost"), f"${self.last_maintenance_cost:.2f}"),
                    (tr(language, "status_last_rent_cost"), f"${self.last_rent_cost:.2f}"),
                    (tr(language, "status_last_fixed_cost"), f"${self.last_fixed_cost:.2f}"),
                    (tr(language, "status_last_storage_cost"), f"${self.last_storage_cost:.2f}"),
                    (tr(language, "status_last_interest_cost"), f"${self.last_interest_cost:.2f}"),
                    (tr(language, "status_last_contract_revenue"), f"${self.last_contract_revenue:.2f}"),
                    (tr(language, "status_last_contract_penalty"), f"${self.last_contract_penalty:.2f}"),
                    (tr(language, "status_unit_cost"), f"${self.last_unit_cost:.2f}"),
                    (tr(language, "status_last_profit"), f"${self.last_profit:.2f}")
                ]
            )
        ]

    def get_status_text(self, language="en"):
        lines = []

        for section_title, items in self.get_status_sections(language):
            if lines:
                lines.append("")
            lines.append(f"[{section_title}]")
            for label, value in items:
                lines.append(f"{label}: {value}")

        return "\n".join(lines)

    def to_dict(self):
        # Converts company state into JSON-friendly data.
        return {
            "class": self.__class__.__name__,
            "name": self.name,
            "cash": self.cash,
            "inventory": self.inventory,
            "production_lines": self.production_lines,
            "technology": self.technology,
            "workforce": self.workforce,
            "factory_buildings": self.factory_buildings,
            "production_line_details": self.production_line_details,
            "storage_capacity": self.storage_capacity,
            "reputation": self.reputation,
            "product_quality": self.product_quality,
            "research_points": self.research_points,
            "research_focus": self.research_focus,
            "known_technologies": sorted(self.known_technologies),
            "active_research": self.active_research,
            "capacity_bonus": self.capacity_bonus,
            "price": self.price,
            "market_share": self.market_share,
            "debt": self.debt,
            "base_interest_rate": self.base_interest_rate,
            "interest_rate": self.interest_rate,
            "credit_limit": self.credit_limit,
            "insolvency_turns": self.insolvency_turns,
            "bonus_multiplier": self.bonus_multiplier,
            "bankrupt": self.bankrupt,
            "is_player": self.is_player,
            "last_production": self.last_production,
            "last_sales": self.last_sales,
            "last_revenue": self.last_revenue,
            "last_cost": self.last_cost,
            "last_production_cost": self.last_production_cost,
            "last_fixed_cost": self.last_fixed_cost,
            "last_storage_cost": self.last_storage_cost,
            "last_interest_cost": self.last_interest_cost,
            "last_wage_cost": self.last_wage_cost,
            "last_maintenance_cost": self.last_maintenance_cost,
            "last_rent_cost": self.last_rent_cost,
            "last_overhead_cost": self.last_overhead_cost,
            "last_contract_revenue": self.last_contract_revenue,
            "last_contract_penalty": self.last_contract_penalty,
            "last_contract_units": self.last_contract_units,
            "last_unit_cost": self.last_unit_cost,
            "last_profit": self.last_profit,
            "last_market_demand": self.last_market_demand,
            "last_marketing_spend": self.last_marketing_spend,
            "strategy": self.strategy,
            "strategy_style": getattr(self, "strategy_style", self.strategy),
            "cash_history": self.cash_history,
            "debt_history": self.debt_history,
            "credit_limit_history": self.credit_limit_history,
            "profit_history": self.profit_history
        }

    @classmethod
    def from_dict(cls, data):
        # Rebuilds a Company or AICompany from saved JSON data.
        if data.get("class") == "AICompany":
            company = AICompany(
                name=data["name"],
                difficulty=data.get("difficulty", "Normal"),
                archetype=data.get("archetype", data.get("strategy", "Carnegie")),
                cash=data.get("cash", 10000),
                production_lines=data.get("production_lines", 2),
                technology=data.get("technology", 1),
                workforce=data.get("workforce", 20),
                storage_capacity=data.get("storage_capacity", 500),
                reputation=data.get("reputation", 50),
                bonus_multiplier=data.get("bonus_multiplier", 1.0)
            )
        else:
            company = cls(
                name=data["name"],
                cash=data.get("cash", 10000),
                production_lines=data.get("production_lines", 2),
                technology=data.get("technology", 1),
                workforce=data.get("workforce", 20),
                storage_capacity=data.get("storage_capacity", 500),
                reputation=data.get("reputation", 50),
                bonus_multiplier=data.get("bonus_multiplier", 1.0),
                is_player=data.get("is_player", False)
            )

        company.inventory = data.get("inventory", 0)
        company.factory_buildings = data.get("factory_buildings", company.factory_buildings)
        company.production_line_details = data.get("production_line_details", company.production_line_details)
        company.sync_production_line_count()
        company.product_quality = data.get("product_quality", company.product_quality)
        company.research_points = data.get("research_points", company.research_points)
        company.research_focus = data.get("research_focus", company.research_focus)
        company.known_technologies = set(data.get("known_technologies", STARTING_TECHNOLOGIES))
        if not company.known_technologies:
            company.known_technologies.update(STARTING_TECHNOLOGIES)
        company.active_research = data.get("active_research", [])
        company.capacity_bonus = data.get("capacity_bonus", 0)
        company.price = data.get("price", company.price)
        company.market_share = data.get("market_share", 0.0)
        saved_cash = data.get("cash", company.cash)
        saved_debt = data.get("debt", 0)
        net_position = saved_cash - saved_debt
        company.cash = max(0, net_position)
        company.debt = max(0, -net_position)
        company.base_interest_rate = data.get("base_interest_rate", company.base_interest_rate)
        company.interest_rate = data.get("interest_rate", company.interest_rate)
        company.credit_limit = data.get("credit_limit", company.credit_limit)
        company.insolvency_turns = data.get("insolvency_turns", 0)
        company.bankrupt = data.get("bankrupt", False)
        company.is_player = data.get("is_player", company.is_player)
        company.last_production = data.get("last_production", 0)
        company.last_sales = data.get("last_sales", 0)
        company.last_revenue = data.get("last_revenue", 0)
        company.last_cost = data.get("last_cost", 0)
        company.last_production_cost = data.get("last_production_cost", 0)
        company.last_fixed_cost = data.get("last_fixed_cost", 0)
        company.last_storage_cost = data.get("last_storage_cost", 0)
        company.last_interest_cost = data.get("last_interest_cost", 0)
        company.last_wage_cost = data.get("last_wage_cost", 0)
        company.last_maintenance_cost = data.get("last_maintenance_cost", 0)
        company.last_rent_cost = data.get("last_rent_cost", 0)
        company.last_overhead_cost = data.get("last_overhead_cost", 0)
        company.last_contract_revenue = data.get("last_contract_revenue", 0)
        company.last_contract_penalty = data.get("last_contract_penalty", 0)
        company.last_contract_units = data.get("last_contract_units", 0)
        company.last_unit_cost = data.get("last_unit_cost", 0)
        company.last_profit = data.get("last_profit", 0)
        company.last_market_demand = data.get("last_market_demand", 0)
        company.last_marketing_spend = data.get("last_marketing_spend", 0)
        company.strategy = data.get("strategy", company.strategy)
        if isinstance(company, AICompany):
            company.strategy_style = data.get("strategy_style", company.strategy_style)
        company.cash_history = data.get("cash_history", [company.cash])
        company.debt_history = data.get("debt_history", [company.debt])
        company.credit_limit_history = data.get("credit_limit_history", [company.credit_limit])
        company.profit_history = data.get("profit_history", [])
        return company


class AICompany(Company):
    # AI firms use strategy presets plus a small search over price/production options.
    def __init__(self, name, difficulty="Normal", archetype="Carnegie", **kwargs):
        super().__init__(name, **kwargs)
        self.difficulty = difficulty
        self.archetype = archetype
        self.profile = AI_ARCHETYPES.get(archetype, AI_ARCHETYPES["Carnegie"])
        self.strategy = archetype
        self.strategy_style = self.profile["style"]
        self.research_focus = self.profile["research_focus"]

    def to_dict(self):
        # Adds AI strategy metadata to saved company data.
        data = super().to_dict()
        data["difficulty"] = self.difficulty
        data["archetype"] = self.archetype
        return data

    def make_decision(self, player_company, market, competitors):
        active_competitors = [
            company for company in competitors
            if company is not self and not company.bankrupt
        ]
        competitor_prices = [company.price for company in active_competitors]
        average_price = sum(competitor_prices) / len(competitor_prices) if competitor_prices else 40
        unit_cost = self.get_unit_production_cost(market)

        target_margin = self.profile["target_margin"] * random.uniform(0.94, 1.08)
        target_inventory_cover = self.profile["inventory_cover"] * random.uniform(0.92, 1.1)

        if self.strategy_style == "Cost Leader":
            desired_price = min(average_price * 0.94, unit_cost * target_margin)
            target_inventory_cover += 0.15
        elif self.strategy_style == "Premium":
            desired_price = max(average_price * 1.08, unit_cost * (target_margin + 0.25))
            target_inventory_cover -= 0.1
        elif self.strategy_style == "Aggressive":
            desired_price = min(player_company.price * 0.96, average_price * 0.98)
            target_inventory_cover += 0.25
        elif self.strategy_style == "Innovator":
            desired_price = max(average_price * 1.04, unit_cost * (target_margin + 0.18))
            target_inventory_cover += 0.05
        elif self.strategy_style == "Survivor":
            desired_price = max(unit_cost * 1.15, min(average_price * 0.96, unit_cost * target_margin))
            target_inventory_cover += 0.2
        elif self.strategy_style == "Flexible":
            desired_price = (average_price * 0.45) + (unit_cost * target_margin * 0.55)
            target_inventory_cover += 0.02
        else:
            desired_price = (average_price * 0.55) + (unit_cost * target_margin * 0.45)

        if self.inventory > self.storage_capacity * 0.8:
            desired_price *= 0.92
        elif self.last_sales >= self.last_production and self.last_production > 0:
            desired_price *= 1.04

        capacity = self.get_production_capacity()
        active_count = max(1, len([company for company in competitors if not company.bankrupt]))
        expected_demand = market.forecast_demand(active_count)
        share_goal = max(0.08, min(0.45, (self.market_share or 100 / active_count) / 100))
        target_stock = int(expected_demand * share_goal * target_inventory_cover)
        baseline_production = max(0, min(capacity, target_stock - self.inventory))

        self.price, production = self.choose_best_offer(
            desired_price,
            baseline_production,
            market,
            competitors
        )

        self.consider_investment(market)

        return production, self.price

    def choose_best_offer(self, desired_price, baseline_production, market, competitors):
        price_candidates = [
            desired_price * 0.9,
            desired_price,
            desired_price * 1.1,
            self.price * 0.95,
            self.price * 1.05
        ]
        production_candidates = [
            int(baseline_production * 0.75),
            baseline_production,
            int(baseline_production * 1.2)
        ]

        best_score = None
        best_price = self.price
        best_production = baseline_production
        unit_cost = self.get_unit_production_cost(market)
        active_count = max(1, len([company for company in competitors if not company.bankrupt]))
        average_quality = sum(
            company.get_effective_product_quality()
            for company in competitors
            if not company.bankrupt
        ) / active_count

        for candidate_price in price_candidates:
            candidate_price = max(unit_cost + 2, min(130, candidate_price))

            for candidate_production in production_candidates:
                candidate_production = max(0, min(self.get_production_capacity(), candidate_production))
                available_inventory = self.inventory + candidate_production
                score = market.estimate_company_score(
                    price=candidate_price,
                    reputation=self.reputation,
                    inventory=available_inventory,
                    market_share=self.market_share,
                    product_quality=self.get_effective_product_quality(),
                    marketing_spend=self.last_marketing_spend,
                    average_price=sum(company.price for company in competitors if not company.bankrupt) / active_count,
                    average_quality=average_quality
                )
                score_pool = max(score + (active_count - 1), 1)
                expected_sales = min(available_inventory, int(market.forecast_demand(active_count) * score / score_pool))
                expected_profit = (
                    expected_sales * candidate_price
                    - candidate_production * unit_cost
                    - self.get_fixed_cost(market)
                    - self.debt * self.interest_rate
                    - max(0, available_inventory - expected_sales - self.storage_capacity) * 4
                )
                survival_bonus = -self.get_solvency_ratio() * 1200
                strategic_bonus = 0

                if self.strategy_style == "Premium":
                    strategic_bonus += candidate_price * 8
                elif self.strategy_style in ["Cost Leader", "Aggressive", "Survivor"]:
                    strategic_bonus += expected_sales * 2

                candidate_score = expected_profit + survival_bonus + strategic_bonus

                if best_score is None or candidate_score > best_score:
                    best_score = candidate_score
                    best_price = candidate_price
                    best_production = candidate_production

        return best_price, best_production

    def consider_investment(self, market):
        self.update_credit_limit()

        if self.get_solvency_ratio() > self.profile["risk_tolerance"] or self.last_profit < -1500:
            return None

        upgrade_line_index = self.get_affordable_line_upgrade()
        if upgrade_line_index is not None and random.random() < 0.45:
            return self.consider_line_upgrades(upgrade_line_index)

        investment_chance = 0.16

        if random.random() > investment_chance:
            return None

        try:
            if self.strategy_style == "Innovator" and self.product_quality < 85:
                return self.consider_technology_research(["Bessemer Process", "Open Hearth Furnace", "Alloy Steel"])
            if self.strategy_style in ["Cost Leader", "Survivor"]:
                return self.consider_technology_research(["Bessemer Process", "Scientific Management", "Rolling Mill"])
            if market.demand_trend > 1.03 and self.production_lines < 8:
                self.prepare_factory_capacity_for_line()
                return ("production line", self.buy_production_line())
            if self.strategy_style in ["Premium", "Flexible"] and self.reputation < 85:
                return self.consider_technology_research(["Open Hearth Furnace", "Alloy Steel", "Railway Logistics"])
            if market.demand_trend > 1.05 and self.storage_capacity < 1600:
                return ("storage", self.expand_storage())
        except ValueError:
            return None

        return None

    def prepare_factory_capacity_for_line(self):
        try:
            self.get_default_factory_index()
        except ValueError:
            owned_factories = [
                index for index, factory in enumerate(self.factory_buildings)
                if factory.get("owned", True)
                and factory.get("expansions", 0) < self.get_factory_expansion_limit(index)
            ]
            if owned_factories:
                self.expand_factory(owned_factories[0])
            else:
                self.lease_factory()

    def get_affordable_line_upgrade(self):
        target_method = self.get_best_available_production_method()
        upgradeable = [
            index for index, line in enumerate(self.production_line_details)
            if line["method"] != target_method
        ]

        if not upgradeable:
            return None

        upgradeable.sort(
            key=lambda index: self.get_line_upgrade_cost(
                self.production_line_details[index]["method"],
                target_method
            )
        )

        for line_index in upgradeable:
            cost = self.get_line_upgrade_cost(
                self.production_line_details[line_index]["method"],
                target_method
            )
            if cost > 0 and self.can_afford(cost):
                return line_index

        return None

    def consider_line_upgrades(self, line_index=None):
        if line_index is None:
            line_index = self.get_affordable_line_upgrade()

        if line_index is None:
            return None

        return ("line upgrade", self.upgrade_production_line(line_index))

    def consider_technology_research(self, priorities):
        for technology_id in priorities:
            if technology_id in TECHNOLOGIES and self.can_research_technology(technology_id):
                return ("technology", self.start_technology_research(technology_id))

        for technology_id in TECHNOLOGIES:
            if self.can_research_technology(technology_id):
                return ("technology", self.start_technology_research(technology_id))

        return None
