"""Core game-state orchestration: turns, contracts, acquisitions, and victory checks."""

import random

from config import ARCHETYPE_ORDER, CONTRACT_TEMPLATES, TECHNOLOGIES
from localization import display_option, tr
from market import Market
from models import AICompany, Company


class GameState:
    # Owns one running game: companies, market state, turn processing, and win/loss checks.
    def __init__(
        self,
        scenario="19th Century",
        difficulty="Normal",
        ai_count=6,
        ai_archetypes=None,
        start_cash=10000,
        player_name="Player Company",
        max_turns=120,
        show_ai_stats=True,
        language="en"
    ):
        self.turn = 1
        self.max_turns = max_turns

        self.scenario = scenario
        self.difficulty = difficulty
        self.ai_count = 6 if scenario == "19th Century" else max(1, min(6, ai_count))
        self.ai_archetypes = ai_archetypes or ARCHETYPE_ORDER[:self.ai_count]
        self.show_ai_stats = show_ai_stats
        self.language = language

        self.market = Market(scenario)
        self.contracts = []
        self.next_contract_id = 1

        player_bonus = 1.1 if difficulty == "Easy" else 1.0
        ai_bonus = 1.1 if difficulty == "Hard" else 1.0

        self.player = Company(
            name=player_name,
            cash=start_cash,
            production_lines=2,
            technology=1,
            workforce=20,
            storage_capacity=500,
            reputation=50,
            bonus_multiplier=player_bonus,
            is_player=True
        )

        self.ai_companies = []

        for i, archetype in enumerate(self.ai_archetypes):
            ai_name = display_option(archetype, language) if scenario == "19th Century" else f"AI Company {i + 1}"
            ai = AICompany(
                name=ai_name,
                difficulty=difficulty,
                archetype=archetype,
                cash=start_cash,
                production_lines=2,
                technology=1,
                workforce=20,
                storage_capacity=500,
                reputation=50,
                bonus_multiplier=ai_bonus
            )
            self.ai_companies.append(ai)

        self.generate_contracts(target_available=3)

    def to_dict(self):
        # Converts the whole running game into JSON-friendly data.
        return {
            "turn": self.turn,
            "max_turns": self.max_turns,
            "scenario": self.scenario,
            "difficulty": self.difficulty,
            "ai_count": self.ai_count,
            "ai_archetypes": self.ai_archetypes,
            "show_ai_stats": self.show_ai_stats,
            "language": self.language,
            "market": self.market.to_dict(),
            "player": self.player.to_dict(),
            "ai_companies": [ai.to_dict() for ai in self.ai_companies],
            "contracts": self.contracts,
            "next_contract_id": self.next_contract_id
        }

    @classmethod
    def from_dict(cls, data):
        # Rebuilds a full running game from saved JSON data.
        state = cls(
            scenario=data.get("scenario", "19th Century"),
            difficulty=data.get("difficulty", "Normal"),
            ai_count=data.get("ai_count", 6),
            ai_archetypes=data.get("ai_archetypes", ARCHETYPE_ORDER[:]),
            start_cash=data.get("player", {}).get("cash", 10000),
            player_name=data.get("player", {}).get("name", "Player Company"),
            max_turns=data.get("max_turns", 120),
            show_ai_stats=data.get("show_ai_stats", True),
            language=data.get("language", "en")
        )
        state.turn = data.get("turn", 1)
        state.max_turns = data.get("max_turns", 120)
        state.market = Market.from_dict(data.get("market", {}))
        state.player = Company.from_dict(data.get("player", state.player.to_dict()))
        state.ai_companies = [
            Company.from_dict(ai_data)
            for ai_data in data.get("ai_companies", [])
        ]
        state.contracts = data.get("contracts", state.contracts)
        state.next_contract_id = data.get("next_contract_id", state.next_contract_id)
        return state

    def get_all_companies(self):
        return [self.player] + self.ai_companies

    def get_company_by_name(self, company_name):
        for company in self.get_all_companies():
            if company.name == company_name:
                return company
        return None

    def get_contract_name(self, contract):
        return CONTRACT_TEMPLATES[contract["type"]]["name"][self.language]

    def create_contract(self):
        contract_type = random.choice(list(CONTRACT_TEMPLATES))
        template = CONTRACT_TEMPLATES[contract_type]
        duration = random.randint(*template["duration_range"])
        unit_price = random.randint(*template["price_range"])
        units_per_turn = random.randint(*template["units_range"])

        contract = {
            "id": self.next_contract_id,
            "type": contract_type,
            "units_per_turn": units_per_turn,
            "unit_price": unit_price,
            "duration": duration,
            "remaining_turns": duration,
            "quality_requirement": template["quality_requirement"],
            "reputation_requirement": template["reputation_requirement"],
            "penalty_rate": template["penalty_rate"],
            "holder": None
        }
        self.next_contract_id += 1
        return contract

    def generate_contracts(self, target_available=2):
        available_count = len([contract for contract in self.contracts if contract.get("holder") is None])
        while available_count < target_available:
            self.contracts.append(self.create_contract())
            available_count += 1

    def score_contract_bid(self, company, contract, bid_price):
        if company.bankrupt:
            return -1

        quality_gap = company.get_effective_product_quality() - contract["quality_requirement"]
        reputation_gap = company.reputation - contract["reputation_requirement"]
        price_score = max(0.1, contract["unit_price"] / max(bid_price, 1))
        quality_score = max(0.2, 1 + quality_gap / 75)
        reputation_score = max(0.2, 1 + reputation_gap / 90)
        reliability_score = 1 + min(company.market_share, 35) / 160
        capacity_score = min(1.25, max(0.45, company.get_production_capacity() / max(contract["units_per_turn"], 1)))

        return price_score * quality_score * reputation_score * reliability_score * capacity_score * company.bonus_multiplier

    def get_ai_contract_bid(self, ai, contract):
        style_discount = {
            "Cost Leader": 0.88,
            "Survivor": 0.86,
            "Flexible": 0.92,
            "Balanced": 0.94,
            "Innovator": 0.96,
            "Premium": 1.02
        }.get(ai.strategy_style, 0.94)
        unit_cost = ai.get_unit_production_cost(self.market)
        floor_price = unit_cost * 1.12
        bid_price = contract["unit_price"] * style_discount * random.uniform(0.96, 1.04)
        return max(floor_price, bid_price)

    def compete_for_contract(self, contract_id, player_bid_price):
        contract = next(
            (item for item in self.contracts if item["id"] == contract_id and item.get("holder") is None),
            None
        )

        if contract is None:
            raise ValueError(tr(self.language, "no_available_contracts"))

        if player_bid_price <= 0:
            raise ValueError("Bid price must be positive.")

        bids = [
            {
                "company": self.player,
                "price": player_bid_price,
                "score": self.score_contract_bid(self.player, contract, player_bid_price)
            }
        ]

        for ai in self.ai_companies:
            if ai.bankrupt:
                continue
            bid_price = self.get_ai_contract_bid(ai, contract)
            bids.append(
                {
                    "company": ai,
                    "price": bid_price,
                    "score": self.score_contract_bid(ai, contract, bid_price)
                }
            )

        winning_bid = max(bids, key=lambda bid: bid["score"])
        contract["holder"] = winning_bid["company"].name
        contract["unit_price"] = winning_bid["price"]

        if winning_bid["company"].is_player:
            return tr(
                self.language,
                "contract_won",
                contract=self.get_contract_name(contract),
                price=winning_bid["price"],
                duration=contract["duration"]
            )

        return tr(
            self.language,
            "contract_lost",
            contract=self.get_contract_name(contract),
            winner=winning_bid["company"].name,
            price=winning_bid["price"]
        )

    def process_contracts(self, companies):
        contract_finance = {
            company.name: {"revenue": 0, "penalty": 0}
            for company in companies
        }
        reports = []
        expired_contracts = []

        for company in companies:
            company.last_contract_revenue = 0
            company.last_contract_penalty = 0
            company.last_contract_units = 0

        for contract in self.contracts:
            holder_name = contract.get("holder")
            if not holder_name:
                continue

            holder = self.get_company_by_name(holder_name)
            if holder is None or holder.bankrupt:
                expired_contracts.append(contract)
                continue

            required_units = contract["units_per_turn"]
            delivered_units = min(holder.inventory, required_units)
            shortfall = required_units - delivered_units
            revenue = delivered_units * contract["unit_price"]
            penalty = shortfall * contract["unit_price"] * contract["penalty_rate"]

            holder.inventory -= delivered_units
            holder.last_contract_revenue += revenue
            holder.last_contract_penalty += penalty
            holder.last_contract_units += delivered_units
            contract_finance[holder.name]["revenue"] += revenue
            contract_finance[holder.name]["penalty"] += penalty

            reports.append(
                tr(
                    self.language,
                    "contract_fulfilled_report",
                    name=holder.name,
                    contract=self.get_contract_name(contract),
                    delivered=delivered_units,
                    required=required_units,
                    revenue=revenue,
                    penalty=penalty
                )
            )

            contract["remaining_turns"] -= 1
            if contract["remaining_turns"] <= 0:
                expired_contracts.append(contract)
                reports.append(
                    tr(self.language, "contract_expired_report", contract=self.get_contract_name(contract))
                )

        if expired_contracts:
            self.contracts = [
                contract for contract in self.contracts
                if contract not in expired_contracts
            ]

        self.generate_contracts(target_available=2)
        return contract_finance, reports

    def negotiate_acquisition(self, target_name, offer):
        target = None

        for ai in self.ai_companies:
            if ai.name == target_name and not ai.bankrupt:
                target = ai
                break

        if target is None:
            raise ValueError(tr(self.language, "no_acquisition_target"))

        accepted, asking_price = target.evaluate_acquisition_offer(offer)

        if not accepted:
            raise ValueError(
                tr(
                    self.language,
                    "acquisition_rejected",
                    target=target.name,
                    asking_price=asking_price
                )
            )

        self.player.spend_money(offer)
        gained_lines = max(1, len(target.production_line_details) // 2)
        acquired_factory_index = len(self.player.factory_buildings)
        self.player.factory_buildings.append(
            {
                "name": f"{target.name} Works",
                "slots": gained_lines,
                "owned": True,
                "expansions": 0,
                "rent": 0
            }
        )

        for line in target.production_line_details[:gained_lines]:
            self.player.production_line_details.append(
                {
                    "method": line.get("method", "Puddling Furnace"),
                    "factory_index": acquired_factory_index,
                    "active": False,
                    "workers": 0
                }
            )

        self.player.sync_production_line_count()
        self.player.technology = max(self.player.technology, target.technology)
        self.player.known_technologies.update(target.known_technologies)
        self.player.product_quality = max(self.player.product_quality, target.product_quality - 4)
        self.player.workforce += max(1, target.workforce // 2)
        self.player.storage_capacity += max(100, target.storage_capacity // 2)
        self.player.reputation = min(100, self.player.reputation + max(1, target.reputation // 12))
        self.player.inventory += target.inventory

        target.bankrupt = True
        target.inventory = 0
        target.market_share = 0

        return (
            tr(self.language, "acquired_report", target=target.name, cost=offer)
        )

    def negotiate_technology_purchase(self, seller_name, technology_id, offer):
        seller = None

        for ai in self.ai_companies:
            if ai.name == seller_name and not ai.bankrupt:
                seller = ai
                break

        if seller is None:
            raise ValueError(tr(self.language, "no_acquisition_target"))

        accepted, asking_price = seller.evaluate_technology_sale(technology_id, offer)

        if not accepted:
            raise ValueError(
                tr(
                    self.language,
                    "technology_sale_rejected",
                    seller=seller.name,
                    technology=TECHNOLOGIES[technology_id]["name"][self.language],
                    asking_price=asking_price
                )
            )

        self.player.spend_money(offer)
        seller.cash += offer
        seller.record_finance_history()
        self.player.buy_known_technology(technology_id)
        return tr(
            self.language,
            "technology_bought",
            technology=TECHNOLOGIES[technology_id]["name"][self.language],
            seller=seller.name,
            cost=offer
        )
    
    def process_turn(self, player_production, player_price):
        if self.player.bankrupt:
            return tr(self.language, "player_bankrupt_process")

        self.player.price = player_price

        turn_report = []

        # 1. Generate market demand
        companies = self.get_all_companies()
        market_demand = self.market.generate_demand(companies)
        turn_report.append(tr(self.language, "market_demand_report", demand=market_demand))
        turn_report.append(self.market.get_market_summary(self.language))

        # 2. Player production
        player_production_cost = self.player.produce(player_production, self.market)
        turn_report.append(
            tr(self.language, "produced_report", name=self.player.name, quantity=player_production)
        )

        # 3. AI decisions and production
        production_costs = {
            self.player.name: player_production_cost
        }

        for ai in self.ai_companies:
            if ai.bankrupt:
                production_costs[ai.name] = 0
                continue

            cash_before_decision = ai.cash
            ai_production, ai_price = ai.make_decision(self.player, self.market, companies)
            ai.price = ai_price

            ai_production_cost = ai.produce(ai_production, self.market)
            production_costs[ai.name] = ai_production_cost

            turn_report.append(
                tr(
                    self.language,
                    "ai_report",
                    name=ai.name,
                    strategy=display_option(ai.strategy_style, self.language),
                    quantity=ai_production,
                    price=ai_price
                )
            )

            if cash_before_decision > ai.cash:
                turn_report.append(
                    tr(
                        self.language,
                        "ai_invested_report",
                        name=ai.name,
                        amount=cash_before_decision - ai.cash
                    )
                )

        for company in companies:
            if company.bankrupt:
                continue

            completed_technologies = company.advance_research()

            for technology_id in completed_technologies:
                turn_report.append(
                    tr(
                        self.language,
                        "technology_completed_report",
                        name=company.name,
                        technology=TECHNOLOGIES[technology_id]["name"][self.language]
                    )
                )

        # 4. Long-term contracts are fulfilled before the open market sees remaining inventory
        contract_finance, contract_reports = self.process_contracts(companies)
        turn_report.extend(contract_reports)

        # 5. Market distributes sales
        sales_distribution = self.market.distribute_sales(companies)

        total_actual_sales = 0

        # 6. Companies sell products
        for company in companies:
            if company.bankrupt:
                continue

            expected_sales = sales_distribution.get(company.name, 0)
            company.last_market_demand = expected_sales
            market_revenue = company.sell(expected_sales)
            contract_revenue = contract_finance.get(company.name, {}).get("revenue", 0)
            contract_penalty = contract_finance.get(company.name, {}).get("penalty", 0)
            company.last_revenue = market_revenue + contract_revenue - contract_penalty
            total_actual_sales += company.last_sales

            turn_report.append(
                tr(
                    self.language,
                    "sold_report",
                    name=company.name,
                    sales=company.last_sales,
                    revenue=market_revenue
                )
            )

        # 7. Pay costs and update cash
        for company in companies:
            if company.bankrupt:
                continue

            revenue = company.last_revenue
            production_cost = production_costs.get(company.name, 0)
            fixed_breakdown = company.get_fixed_cost_breakdown(self.market)
            fixed_cost = sum(fixed_breakdown.values())
            storage_cost = company.get_storage_cost()

            company.pay_costs_and_update_cash(
                revenue=revenue,
                production_cost=production_cost,
                fixed_cost=fixed_cost,
                storage_cost=storage_cost,
                fixed_breakdown=fixed_breakdown
            )

            if total_actual_sales > 0:
                company.market_share = company.last_sales / total_actual_sales * 100
            else:
                company.market_share = 0

            company.update_reputation()
            company.check_bankruptcy()
            company.last_marketing_spend = 0

            turn_report.append(
                tr(
                    self.language,
                    "profit_report",
                    name=company.name,
                    profit=company.last_profit,
                    cash=company.cash,
                    debt=company.debt
                )
            )

            if company.is_player:
                turn_report.append(
                    tr(
                        self.language,
                        "cash_flow_report",
                        revenue=company.last_revenue,
                        production=company.last_production_cost,
                        wages=company.last_wage_cost,
                        maintenance=company.last_maintenance_cost,
                        rent=company.last_rent_cost,
                        storage=company.last_storage_cost,
                        interest=company.last_interest_cost,
                        profit=company.last_profit
                    )
                )

            if company.bankrupt:
                turn_report.append(
                    tr(self.language, "bankrupt_report", name=company.name)
                )
            elif company.get_solvency_ratio() > 0.85:
                turn_report.append(
                    tr(
                        self.language,
                        "credit_crisis_report",
                        name=company.name,
                        ratio=company.get_solvency_ratio() * 100
                    )
                )

        # 8. Move to next turn
        self.turn += 1

        return "\n".join(turn_report)

    def is_game_over(self):
        if self.player.bankrupt:
            return True

        if self.max_turns is not None and self.turn > self.max_turns:
            return True

        active_ai_count = 0

        for ai in self.ai_companies:
            if not ai.bankrupt:
                active_ai_count += 1

        if active_ai_count == 0:
            return True

        return False

    def get_game_result_text(self):
        if self.player.bankrupt:
            return tr(self.language, "game_over_bankrupt")

        active_ai = [ai for ai in self.ai_companies if not ai.bankrupt]

        if len(active_ai) == 0:
            return tr(self.language, "victory_all_bankrupt")

        if self.max_turns is not None and self.turn > self.max_turns:
            companies = self.get_all_companies()
            companies = sorted(
                companies,
                key=lambda company: company.cash + company.get_asset_value() - company.debt,
                reverse=True
            )

            result = tr(self.language, "game_finished")

            for index, company in enumerate(companies, start=1):
                company_value = company.cash + company.get_asset_value() - company.debt
                result += tr(
                    self.language,
                    "ranking_line",
                    index=index,
                    name=company.name,
                    value=company_value
                )

            if companies[0].is_player:
                result += tr(self.language, "you_won")
            else:
                result += tr(self.language, "you_lost")

            return result

        return tr(self.language, "game_running")
