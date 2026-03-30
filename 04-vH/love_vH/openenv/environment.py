# openenv environment wrapper

from environment.env import LoveEnv

class OpenEnvWrapper:
    def __init__(self):
        self.env = LoveEnv()

    def reset(self):
        return self.env.reset()

    def step(self, action):
        state, reward, done, info = self.env.step(action)

        return {
            "observation": state,
            "reward": reward,
            "done": done,
            "info": info
        }

    def state(self):
        return self.env._build_state(self.env._current_user_msg, self.env._tasks.turn)