from openenv.environment import OpenEnvWrapper
from agent.agent import LoveAgent

env = OpenEnvWrapper()
agent = LoveAgent()

def main():
    state = env.reset()
    total_reward = 0

    for step in range(6):
        action = agent.act(state)
        result = env.step(action)

        state = result["observation"]
        reward = result["reward"]
        total_reward += reward

        print(f"Step {step+1} | Reward: {reward:+.2f}")

        if result["done"]:
            break

    print("\nFINAL SCORE:", total_reward)

if __name__ == "__main__":
    main()