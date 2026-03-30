from flask import Flask, request, jsonify, render_template

from environment.env import LoveEnv
from agent.agent import LoveAgent
from reward.reward_system import RewardSystem

#  CREATE APP FIRST
app = Flask(__name__, template_folder="templates")

#  INIT SYSTEM
env = LoveEnv()
agent = LoveAgent()
reward_system = RewardSystem()

state = env.reset()


#  HOME ROUTE
@app.route("/")
def home():
    return """
    <h1>LOVE vH is Running 🚀</h1>
    <p>API is live.</p>
    """


#  CHAT ROUTE
@app.route("/chat", methods=["POST"])
def chat():
    global state

    user_input = request.json.get("message", "")

    # Update state with user message
    state["user_message"] = user_input

    # Agent acts
    action = agent.act(state)

    # Environment step
    next_state, reward, done, info = env.step(action)

    # Update state
    state = next_state

    return jsonify({
        "response": action["response"],
        "reward": reward,
        "done": done
    })


#  RUN APP
if __name__ == "__main__":
    app.run(host="0.0.0.0",port=7860)