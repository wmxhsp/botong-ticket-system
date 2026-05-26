"""
博通 — 统一金额计算器单元测试
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

import pytest
from domain.amount_calculator import AmountCalculator


class TestLaborFee:
    def test_single_technician(self):
        techs = [{"name": "张三", "hours": 5}]
        fee = AmountCalculator.calc_labor_fee(techs, fee_rate=80)
        assert fee == 400.0

    def test_multiple_technicians(self):
        techs = [
            {"name": "张三", "hours": 3},
            {"name": "李四", "hours": 2},
        ]
        fee = AmountCalculator.calc_labor_fee(techs, fee_rate=60)
        assert fee == 300.0

    def test_default_fee_rate(self):
        techs = [{"name": "张三", "hours": 10}]
        fee = AmountCalculator.calc_labor_fee(techs)
        assert fee == 600.0

    def test_zero_hours(self):
        techs = [{"name": "张三", "hours": 0}]
        fee = AmountCalculator.calc_labor_fee(techs, fee_rate=80)
        assert fee == 0.0

    def test_empty_name_ignored(self):
        techs = [
            {"name": "", "hours": 5},
            {"name": "李四", "hours": 3},
        ]
        fee = AmountCalculator.calc_labor_fee(techs, fee_rate=80)
        assert fee == 240.0

    def test_empty_list(self):
        fee = AmountCalculator.calc_labor_fee([], fee_rate=80)
        assert fee == 0.0

    def test_none_hours_treated_as_zero(self):
        techs = [{"name": "张三", "hours": None}]
        fee = AmountCalculator.calc_labor_fee(techs, fee_rate=80)
        assert fee == 0.0

    def test_decimal_hours(self):
        techs = [{"name": "张三", "hours": 2.5}]
        fee = AmountCalculator.calc_labor_fee(techs, fee_rate=80)
        assert fee == 200.0

    def test_rounding(self):
        techs = [{"name": "张三", "hours": 1.333}]
        fee = AmountCalculator.calc_labor_fee(techs, fee_rate=70)
        assert fee == 93.31


class TestLaborCost:
    def test_with_explicit_cost_rate(self):
        techs = [{"name": "张三", "hours": 5, "cost_rate": 50}]
        cost = AmountCalculator.calc_labor_cost(techs)
        assert cost == 250.0

    def test_default_fallback_cost_rate(self):
        techs = [{"name": "张三", "hours": 4}]
        cost = AmountCalculator.calc_labor_cost(techs)
        assert cost > 0

    def test_zero_hours_skipped(self):
        techs = [{"name": "张三", "hours": 0, "cost_rate": 50}]
        cost = AmountCalculator.calc_labor_cost(techs)
        assert cost == 0.0

    def test_empty_name_skipped(self):
        techs = [{"name": "", "hours": 5, "cost_rate": 50}]
        cost = AmountCalculator.calc_labor_cost(techs)
        assert cost == 0.0

    def test_multiple_technicians(self):
        techs = [
            {"name": "张三", "hours": 3, "cost_rate": 50},
            {"name": "李四", "hours": 2, "cost_rate": 40},
        ]
        cost = AmountCalculator.calc_labor_cost(techs)
        assert cost == 230.0

    def test_empty_list(self):
        cost = AmountCalculator.calc_labor_cost([])
        assert cost == 0.0


class TestMaterialFee:
    def test_with_total_field(self):
        materials = [{"total": 100}, {"total": 50.5}]
        fee = AmountCalculator.calc_material_fee(materials)
        assert fee == 150.5

    def test_with_total_cost_field(self):
        materials = [{"total_cost": 200}, {"total_cost": 75}]
        fee = AmountCalculator.calc_material_fee(materials)
        assert fee == 275.0

    def test_mixed_fields(self):
        materials = [{"total": 100}, {"total_cost": 50}]
        fee = AmountCalculator.calc_material_fee(materials)
        assert fee == 150.0

    def test_empty_list(self):
        fee = AmountCalculator.calc_material_fee([])
        assert fee == 0.0

    def test_none_list(self):
        fee = AmountCalculator.calc_material_fee(None)
        assert fee == 0.0

    def test_missing_total_fields(self):
        materials = [{"name": "螺丝"}]
        fee = AmountCalculator.calc_material_fee(materials)
        assert fee == 0.0


class TestTravelFee:
    def test_normal_calculation(self):
        fee = AmountCalculator.calc_travel_fee(10.0, 2.5)
        assert fee == 25.0

    def test_zero_distance(self):
        fee = AmountCalculator.calc_travel_fee(0, 2.5)
        assert fee == 0.0

    def test_zero_rate(self):
        fee = AmountCalculator.calc_travel_fee(10, 0)
        assert fee == 0.0

    def test_both_zero(self):
        fee = AmountCalculator.calc_travel_fee(0, 0)
        assert fee == 0.0

    def test_negative_distance(self):
        fee = AmountCalculator.calc_travel_fee(-5, 2.5)
        assert fee == 0.0

    def test_negative_rate(self):
        fee = AmountCalculator.calc_travel_fee(10, -2.5)
        assert fee == 0.0


class TestCalcDiscount:
    def test_percent_discount(self):
        discount_amount, final = AmountCalculator.calc_discount(1000, "percent", 10)
        assert discount_amount == 100.0
        assert final == 900.0

    def test_fixed_discount(self):
        discount_amount, final = AmountCalculator.calc_discount(1000, "fixed", 80)
        assert discount_amount == 80.0
        assert final == 920.0

    def test_fixed_discount_exceeds_total(self):
        discount_amount, final = AmountCalculator.calc_discount(100, "fixed", 200)
        assert discount_amount == 100.0
        assert final == 0.0

    def test_no_discount_type(self):
        discount_amount, final = AmountCalculator.calc_discount(1000, "", 50)
        assert discount_amount == 0.0
        assert final == 1000.0

    def test_zero_discount_value(self):
        discount_amount, final = AmountCalculator.calc_discount(1000, "percent", 0)
        assert discount_amount == 0.0
        assert final == 1000.0

    def test_percent_100_discount(self):
        discount_amount, final = AmountCalculator.calc_discount(500, "percent", 100)
        assert discount_amount == 500.0
        assert final == 0.0

    def test_unknown_discount_type(self):
        discount_amount, final = AmountCalculator.calc_discount(1000, "unknown", 50)
        assert discount_amount == 0.0
        assert final == 1000.0


class TestCalcTotal:
    def test_basic_total(self):
        total = AmountCalculator.calc_total(300, 100, 50)
        assert total == 450.0

    def test_with_percent_discount(self):
        total = AmountCalculator.calc_total(500, 100, 0, "percent", 10)
        assert total == 540.0

    def test_with_fixed_discount(self):
        total = AmountCalculator.calc_total(500, 100, 0, "fixed", 100)
        assert total == 500.0

    def test_no_travel_fee(self):
        total = AmountCalculator.calc_total(300, 200)
        assert total == 500.0

    def test_all_zero(self):
        total = AmountCalculator.calc_total(0, 0)
        assert total == 0.0