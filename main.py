from botwpm import BotWPM

if __name__ == "__main__":
  BotWPM(
    "chrome", "https://typetest.io/",
    WPM=100, TIME=60
  ).run()