#!/usr/bin/env python3
import json
import iroha2

from random import randrange
from abc import ABC, abstractmethod
from time import sleep
from iroha2 import Client
from iroha2.data_model.isi import *
from iroha2.data_model.domain import *
from iroha2.data_model.expression import *
from iroha2.data_model import asset, account, query, Value, Identifiable, Id


def unregister(id) -> Instruction:
    return Instruction.Unregister(Expression.Raw(Id(id)))

def register(identifiable) -> Instruction:
    return Instruction.Register(Expression.Raw(Identifiable(identifiable)))

def parse_asset_def_id(id) -> asset.DefinitionId:
    name, domain_name = id.split('#')
    return asset.DefinitionId(name=name, domain_name=domain_name)

def asset_mint_u32(q, asset: asset.Id):
    return Instruction(Mint(
        object=Expression(Value.U32(q)),
        destination_id=Expression(Value(Id(asset)),
    )))

def find_asset_by_id(cl: Client, asset: asset.Id):
    q = query.asset.FindAssetById(Expression(Value(Id(asset))))
    out = cl.query(q)
    return out["Identifiable"]["Asset"]


class Scenario(ABC):
    @abstractmethod
    def check(self) -> bool:
        pass

    @abstractmethod
    def step(self):
        pass

    def _check(self):
        try:
            return self.check()
        except:
            return False

    def wait(self):
        while not self._check():
            sleep(0.1)

    def run(self):
        step = 1
        print("Start")
        while True:
            self.step()
            self.wait()
            print(f"Step {step}")
            step += 1


class SingleAssetScenario(Scenario):
    def __init__(self, cfg, asset_name):
        self.cl = Client(cfg)
        self.asset_def_id = parse_asset_def_id('single_asset_scenario#wonderland')
        self.asset = asset.Id(
            definition_id=self.asset_def_id,
            account_id=self.cl.account,
        )
        self.q = 0

        try:
            self.cl.submit_isi_blocking(unregister(self.asset_def_id))
        except:
            pass

        isi = register(asset.Definition(
            value_type=asset.ValueType.Quantity(),
            id=self.asset_def_id,
        ))
        self.cl.submit_isi_blocking(isi)

    def check(self):
        asset = find_asset_by_id(self.cl, self.asset)
        print(asset["value"]["Quantity"], self.q, asset["value"]["Quantity"] == self.q)
        return asset["value"]["Quantity"] == self.q

    def step(self):
        for i in range(randrange(1, 20)):
            q = randrange(1, 5)
            print(f"Mint {q}")
            self.q += q
            self.cl.submit_isi(asset_mint_u32(q, self.asset))
            sleep(0.1)


if __name__ == "__main__":
    cfg = json.loads(open("./config.json").read())
    asset_id = 'single_asset_scenario#wonderland'
    SingleAssetScenario(cfg, asset_id).run()
