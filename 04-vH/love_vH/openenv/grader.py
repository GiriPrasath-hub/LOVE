from reward.reward_system import RewardSystem

reward_system = RewardSystem()

def grade(action, user_msg, context):
    result = reward_system.compute(action, user_msg, context)

    return {
        "score": max(0.0, min(1.0, result["total"] / 25)),
        "details": result
    }