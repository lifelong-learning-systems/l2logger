"""
Copyright © 2021-2022 The Johns Hopkins University Applied Physics Laboratory LLC

Permission is hereby granted, free of charge, to any person obtaining a copy 
of this software and associated documentation files (the “Software”), to 
deal in the Software without restriction, including without limitation the 
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or 
sell copies of the Software, and to permit persons to whom the Software is 
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in 
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR 
IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import json
from collections import deque
from l2logger import l2logger


class SequenceNums:
    def __init__(self, block, exp):
        self._block, self._exp = block, exp

    @property
    def block_num(self):
        return self._block

    @property
    def exp_num(self):
        return self._exp


class Experience:
    def __init__(self, agent, task_name, seq_nums: SequenceNums, block_type="train"):
        self._agent = agent
        self._task_name = task_name
        self._seq_nums = seq_nums
        self._block_type = block_type
        self._update_model = block_type == "train"

    @property
    def task_name(self):
        return self._task_name

    @property
    def block_type(self):
        return self._block_type

    @property
    def sequence_nums(self):
        return self._seq_nums

    @property
    def params(self):
        return {"param1": "str1", "param2": 2}

    def run(self):
        # do ML stuff here, maybe launch gym environment with task_name
        reward = 1
        if self._update_model:
            # update self._agent model and such
            pass
        return {"reward": reward, "debug_info": "mock"}


class MockAgent:
    def __init__(self, scenario):
        self._scenario = scenario
        self._init_queue()

    def complete(self):
        return not len(self._exp_queue)

    def next_experience(self):
        assert len(self._exp_queue)
        return self._exp_queue.popleft()

    # add all experiences to a deque for processing
    def _init_queue(self):
        self._exp_queue = deque()
        exp_num = -1
        for block_num, block in enumerate(self._scenario):
            block_type = block["type"]
            for regime in block["regimes"]:
                for _ in range(0, regime["count"]):
                    exp_num += 1
                    task_name = regime["task"]
                    seq = SequenceNums(block_num, exp_num)
                    exp = Experience(self, task_name, seq, block_type)
                    self._exp_queue.append(exp)
