from flask import Flask, render_template, redirect, jsonify
import threading
import bot

app = Flask(__name__)

bot_thread = None


@app.route("/")
def home():
    return render_template("dashboard.html", running=bot.BOT_RUNNING)


@app.route("/start")
def start():

    global bot_thread

    if bot_thread is None or not bot_thread.is_alive():

        bot.BOT_RUNNING = True

        bot_thread = threading.Thread(target=bot.run_bot, daemon=True)

        bot_thread.start()

    return redirect("/")


@app.route("/pause")
def pause():

    bot.BOT_RUNNING = False

    return redirect("/")


@app.route("/status")
def status():

    return jsonify({"logs": bot.STATUS_LOG})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
