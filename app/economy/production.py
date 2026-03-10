from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class ProductionRecipe:
    inputs: Dict[str, float]
    outputs: Dict[str, float]
    energy_cost: float


@dataclass
class ProductionChain:
    recipes: Dict[str, ProductionRecipe] = field(default_factory=dict)

    def register_recipe(self, name: str, recipe: ProductionRecipe) -> None:
        self.recipes[name] = recipe

    def produce(self, name: str, inventory: Dict[str, float], energy_available: float) -> Dict[str, float]:
        recipe = self.recipes[name]
        if energy_available < recipe.energy_cost:
            raise ValueError("insufficient energy")
        for res, qty in recipe.inputs.items():
            if inventory.get(res, 0) < qty:
                raise ValueError("insufficient inputs")
        for res, qty in recipe.inputs.items():
            inventory[res] -= qty
        for res, qty in recipe.outputs.items():
            inventory[res] = inventory.get(res, 0) + qty
        return inventory
