from flask import Flask, render_template, redirect
import threading
import bot

app = Flask(__name__)

bot_thread = None


@app.route("/")
def home():
    return render_template("dashboard.html", running=bot.BOT_RUNNING, status=bot.get_status())


@app.route("/start")
def start():

    global bot_thread

    if not bot.BOT_RUNNING:
        bot.BOT_RUNNING = True
        bot_thread = threading.Thread(target=bot.run_bot)
        bot_thread.start()

    return redirect("/")


@app.route("/pause")
def pause():

    bot.BOT_RUNNING = False
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
