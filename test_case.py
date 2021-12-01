#!/usr/bin/env python3
import json
import iroha2

from random import randrange
from abc import ABC, abstractmethod
from time import sleep
from iroha2 import Client
from iroha2.data_model import *
from iroha2.data_model import asset, account, query, Value, Identifiable, Id
from iroha2.data_model.domain import *
from iroha2.data_model.events import EventFilter, pipeline
from iroha2.data_model.expression import *
from iroha2.data_model.isi import *


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
        except Exception as e:
            print(f"Discovered exception during check: {e}")
            return False

    def wait(self):
        i = 0
        while not self._check():
            print(f"chk {i}")
            i += 1
            sleep(10)

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
        self.asset_def_id = asset.DefinitionId.parse(asset_name)
        self.asset = asset.Id(
            definition_id=self.asset_def_id,
            account_id=self.cl.account,
        )
        self.q = 0

        try:
            inst = Unregister.id(self.asset_def_id)
            print(inst.to_rust())
            self.cl.submit_isi_blocking(Unregister.id(self.asset_def_id))
        except:
            pass

        inst = Register.identifiable(
            asset.Definition(
                value_type=asset.ValueType.Quantity(),
                id=self.asset_def_id,
                metadata={},
                mintable=True,
            ))
        print(inst.to_rust())
        self.cl.submit_isi_blocking(inst)

    def check(self):
        asset = self.cl.query(query.FindAssetById.id(self.asset))
        print(f"asset - {asset}")
        return asset["value"]["Quantity"] == self.q

    def step(self):
        for i in range(randrange(1, 20)):
            q = randrange(1, 5)
            self.q += q
            mint = Mint(
                object=Expression(Value(q)),
                destination_id=Expression(Value(Id(self.asset))),
            )
            self.cl.submit_isi(mint)
            sleep(0.01)
        print(f"Mint {self.q}")


if __name__ == "__main__":
    cfg = json.loads(open("./config.json").read())
    asset_id = 'single_asset_scenario#wonderland'
    SingleAssetScenario(cfg, asset_id).run()
